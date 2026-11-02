"""Etapa `bio`: fontes (Wikipédia → Tavily) + resumo em pt-BR via OpenAI.

A bio vai para `catalog/summaries.json` (`autoria:{slug}`) com `approved: false`.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from .. import summaries
from ..http import CacheMiss
from ..names import unify_key
from ..providers import openai_client, tavily, wikidata, wikipedia
from ..providers.serpapi import _domain
from .context import Context
from .photo import _tavily_query

BIO_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["insufficient", "text", "source_index"],
    "properties": {
        "insufficient": {"type": "boolean"},
        "text": {"type": "string"},
        "source_index": {"type": "integer"},
    },
}


class BioError(Exception):
    pass


_EMPHASIS = re.compile(r"(\*\*|\*|__|_)(?=\S)(.+?)(?<=\S)\1")
_STRAIGHT_QUOTES = re.compile(r'"([^"\n]+)"')


def clean_text(text: str) -> str:
    """Texto puro para o app: sem ênfase Markdown e com aspas tipográficas uniformes.

    Títulos marcados com *…* ou "…" viram “…” (o app não renderiza Markdown).
    """
    text = _EMPHASIS.sub(lambda m: f"“{m.group(2)}”", text.strip())
    text = _STRAIGHT_QUOTES.sub(lambda m: f"“{m.group(1)}”", text)
    text = text.replace("““", "“").replace("””", "”")
    return re.sub(r"\s+", " ", text)


def surname(name: str) -> str:
    parts = name.split()
    return parts[-1] if parts else name


def wikipedia_source(ctx: Context, author: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    qid = (author.get("wikidata") or {}).get("id")
    entity = ctx.entity(qid) if qid else None
    if not entity:
        return None
    min_chars = int(ctx.config.get("minIntroChars", 300))
    min_fallback = int(ctx.config.get("minFallbackIntroChars", 120))
    longest: Optional[Dict[str, Any]] = None
    for lang in ctx.bio_languages():
        title = wikidata.sitelink(entity, lang)
        text = wikipedia.intro(ctx.http, lang, title) if title else None
        if not text:
            continue
        source = {"label": f"Wikipédia ({lang})", "url": wikipedia.page_url(lang, title), "language": lang,
                  "text": text}
        if len(text) >= min_chars:
            return source
        if longest is None or len(text) > len(longest["text"]):
            longest = source
    return longest if longest and len(longest["text"]) >= min_fallback else None


def tavily_sources(ctx: Context, author: Dict[str, Any]) -> List[Dict[str, Any]]:
    state = ctx.author_state(author["slug"])
    results = state.get("tavilySources")
    if results is None:
        key = ctx.env.get("TAVILY_API_KEY")
        if not key:
            return []
        found = tavily.search(ctx.http, key, _tavily_query(ctx, author), ctx.config.get("excludedDomains", []))
        results = state["tavilySources"] = found["results"]
        state["tavilyImages"] = found["images"]
    cfg = ctx.config.get("bio", {})
    wanted = unify_key(surname(author["name"]))
    out, total = [], 0
    for r in results:
        content = (r.get("content") or "").strip()
        if not content or wanted not in unify_key(content):
            continue
        room = int(cfg.get("maxSourceChars", 4000)) - total
        if room <= 200:
            break
        content = content[:room]
        total += len(content)
        out.append({"label": r.get("title") or _domain(r["url"]), "url": r["url"], "language": None,
                    "text": content})
        if len(out) >= int(cfg.get("maxSources", 3)):
            break
    return out


def collect_sources(ctx: Context, author: Dict[str, Any]) -> List[Dict[str, Any]]:
    state = ctx.author_state(author["slug"])
    tried = set(state.get("bioTried", []))
    sources: List[Dict[str, Any]] = []
    if "wikipedia" in ctx.waves.bio_sources:
        wiki = wikipedia_source(ctx, author)
        tried.add("wikipedia")
        state["bioWikipediaQid"] = (author.get("wikidata") or {}).get("id")
        if wiki:
            sources = [wiki]
    if not sources and "tavily" in ctx.waves.bio_sources and ctx.waves.llm:
        sources = tavily_sources(ctx, author)
        if ctx.env.get("TAVILY_API_KEY"):
            tried.add("tavily")
    state["bioTried"] = sorted(tried)
    state["bioSource"] = sources[0]["label"] if sources else None
    return sources


def build_input(ctx: Context, author: Dict[str, Any], sources: List[Dict[str, Any]], retry_reason: Optional[str]) -> str:
    works = [w["title"] for w in ctx.works_by_author.get(author["slug"], [])][:5]
    country = author.get("country")
    names = {c["code"]: c["name"] for c in (ctx.catalog.vocabularies or {}).get("countries", [])}
    lines = [f"Pessoa: {author['name']}"]
    if author.get("aliases"):
        lines.append("Outras grafias: " + ", ".join(author["aliases"]))
    if country:
        lines.append(f"País: {names.get(country, country)}")
    lines.append("Livros dela(e) na estante (só para desambiguar): " + "; ".join(works))
    lines.append("")
    for i, s in enumerate(sources, start=1):
        lang = f", idioma {s['language']}" if s.get("language") else ""
        lines.append(f"[{i}] {s['label']}{lang} — {s['url']}")
        lines.append(s["text"])
        lines.append("")
    if retry_reason:
        lines.append(f"A resposta anterior foi recusada: {retry_reason}. Corrija e responda de novo.")
    return "\n".join(lines).strip()


def validate_bio(ctx: Context, author: Dict[str, Any], obj: Dict[str, Any], n_sources: int) -> Optional[str]:
    cfg = ctx.config.get("bio", {})
    text = (obj.get("text") or "").strip()
    if not (int(cfg.get("minChars", 80)) <= len(text) <= int(cfg.get("maxChars", 450))):
        return f"o texto tem {len(text)} caracteres (esperado entre {cfg.get('minChars', 80)} e {cfg.get('maxChars', 450)})"
    if unify_key(surname(author["name"])) not in unify_key(text):
        return f"o texto não menciona {surname(author['name'])!r}"
    if not (1 <= int(obj.get("source_index") or 0) <= n_sources):
        return f"source_index {obj.get('source_index')} inválido"
    return None


def run(ctx: Context, author: Dict[str, Any]) -> Tuple[str, List[str]]:
    slug = author["slug"]
    scope = f"autoria:{slug}"
    state = ctx.author_state(slug)
    sources = collect_sources(ctx, author)
    if not sources:
        return "sem fonte", ["nenhuma fonte para a bio"]
    if not ctx.waves.llm:
        return f"fonte coletada: {sources[0]['label']}", []

    cfg = ctx.config.get("bio", {})
    prompt_version = cfg.get("promptVersion", "author-bio-v1")
    instructions = (ctx.prompts_dir / f"{prompt_version}.md").read_text(encoding="utf-8").replace(
        "{{name}}", author["name"])
    model = ctx.env.get("OPENAI_MODEL")
    key = ctx.env.get("OPENAI_API_KEY")
    price_in = float(ctx.env.get("OPENAI_PRICE_INPUT_PER_M", "0") or 0)
    price_out = float(ctx.env.get("OPENAI_PRICE_OUTPUT_PER_M", "0") or 0)

    reason = None
    for attempt in range(2):
        user_input = build_input(ctx, author, sources, reason)
        try:
            obj, usage, cached = openai_client.respond_json(
                ctx.http, key, model, instructions, user_input, "author_bio", BIO_SCHEMA)
        except CacheMiss:
            if ctx.dry_run:
                est_in = (len(instructions) + len(user_input)) // 4
                est_out = int(cfg.get("estimatedOutputTokens", 150))
                ctx.estimated_usd += (est_in * price_in + est_out * price_out) / 1_000_000
            raise
        if not cached:
            ctx.budget.add_openai(usage.input_tokens, usage.output_tokens, usage.cost(price_in, price_out))
        if obj.get("insufficient"):
            state["bioInsufficient"] = prompt_version
            return "fontes insuficientes", [f"modelo indicou fontes insuficientes ({sources[0]['label']})"]
        reason = validate_bio(ctx, author, obj, len(sources))
        if reason is None:
            source = sources[int(obj["source_index"]) - 1]
            summaries.upsert(ctx.catalog, scope, clean_text(obj["text"]), ctx.today,
                             source=source["label"], sourceUrl=source["url"], sourceLanguage=source.get("language"),
                             model=model, promptVersion=prompt_version)
            state.pop("bioInsufficient", None)
            return f"bio proposta ({source['label']})", []
    raise BioError(f"bio inválida após nova tentativa: {reason}")

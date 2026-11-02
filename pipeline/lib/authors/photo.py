"""Etapa `photo`: retrato da autoria.

Commons (P18) é aceito automaticamente. As demais fontes só geram candidatas
para revisão humana; a escolha fica em `pipeline/config/author_photos.json`.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..images import sniff
from ..providers import commons, serpapi, tavily, wikidata, wikipedia
from .context import Context

MEDIA_SUBDIR = "authors"


class PhotoError(Exception):
    pass


def clean_url(url: str) -> str:
    return url.split("?utm_", 1)[0].split("&utm_", 1)[0]


def download(ctx: Context, author: Dict[str, Any], url: str) -> Tuple[str, List[str]]:
    """Baixa para o diretório temporário. Devolve (caminho relativo, avisos)."""
    cfg = ctx.config.get("photo", {})
    resp = ctx.http.get_bytes("images", clean_url(url))
    if resp.status != 200 or not resp.content:
        raise PhotoError(f"download falhou (HTTP {resp.status})")
    info = sniff(resp.content)
    if info is None:
        raise PhotoError("arquivo baixado não é uma imagem reconhecida")
    if info.min_side < int(cfg.get("rejectBelow", 200)):
        raise PhotoError(f"imagem pequena demais ({info.width}×{info.height})")
    warnings = []
    if info.min_side < int(cfg.get("minSide", 400)):
        warnings.append(f"foto com lado menor de {info.min_side}px (abaixo de {cfg.get('minSide', 400)})")
    rel = f"{MEDIA_SUBDIR}/{author['slug']}.{info.ext}"
    ctx.staging.mkdir(parents=True, exist_ok=True)
    (ctx.staging / f"{author['slug']}.{info.ext}").write_bytes(resp.content)
    return rel, warnings


def _sha(path: Path) -> Optional[str]:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def _first_work_title(ctx: Context, slug: str) -> str:
    works = ctx.works_by_author.get(slug, [])
    return works[0]["title"] if works else ""


def gather_candidates(ctx: Context, author: Dict[str, Any], entity: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Acrescenta candidatas das fontes permitidas (sem repetir), até o máximo."""
    cfg = ctx.config.get("photo", {})
    state = ctx.author_state(author["slug"])
    candidates: List[Dict[str, Any]] = list(state.get("photoCandidates", []))
    tried: List[str] = list(state.get("photoTried", []))
    max_c = int(cfg.get("maxCandidates", 3))
    seen = {c["url"] for c in candidates}
    excluded = ctx.config.get("excludedDomains", [])

    def add(items: List[Dict[str, Any]]) -> None:
        for item in items:
            url = clean_url(item["url"])
            if url not in seen and len(candidates) < max_c:
                seen.add(url)
                candidates.append({**item, "url": url})

    for source in ctx.waves.photo_sources:
        if source == "commons" or source in tried or len(candidates) >= max_c:
            continue
        if source == "wikipedia" and entity:
            for lang in ctx.bio_languages():
                title = wikidata.sitelink(entity, lang)
                img = wikipedia.page_image(ctx.http, lang, title, int(cfg.get("commonsWidth", 1200))) if title else None
                if img:
                    add([{"url": img["url"], "width": img["width"], "height": img["height"], "source": "wikipedia",
                          "title": f"Wikipédia ({lang}): {title}", "pageUrl": wikipedia.page_url(lang, title)}])
                    break
        elif source == "serpapi":
            key = ctx.env.get("SERP_API_KEY")
            if not key:
                continue
            query = ctx.config["queries"]["serpapiPhoto"].format(
                name=author["name"], work=_first_work_title(ctx, author["slug"])).strip()
            found = serpapi.images(ctx.http, key, query, int(cfg.get("minSide", 400)), excluded)
            add([{**f, "source": "serpapi"} for f in found])
        elif source == "tavily":
            images = state.get("tavilyImages")
            if images is None:
                key = ctx.env.get("TAVILY_API_KEY")
                if not key:
                    continue
                result = tavily.search(ctx.http, key, _tavily_query(ctx, author), excluded)
                state["tavilySources"] = result["results"]
                images = state["tavilyImages"] = result["images"]
            add([{"url": i["url"], "width": None, "height": None, "source": "tavily",
                  "title": i.get("description"), "pageUrl": None} for i in images])
        tried.append(source)
    state["photoCandidates"] = candidates
    state["photoTried"] = sorted(set(tried))
    return candidates


def _tavily_query(ctx: Context, author: Dict[str, Any]) -> str:
    return ctx.config["queries"]["tavilyBio"].format(
        name=author["name"], work=_first_work_title(ctx, author["slug"])).strip()


def run(ctx: Context, author: Dict[str, Any]) -> Tuple[str, List[str]]:
    """Executa a etapa. Devolve (resultado curto, notas)."""
    slug = author["slug"]
    choice = ctx.author_photos.get(slug)
    notes: List[str] = []
    if choice is not None and choice.get("none"):
        _set_photo(ctx, author, None)
        return "sem foto (decisão manual)", notes
    if choice is not None:
        rel, warn = download(ctx, author, choice["url"])
        _set_photo(ctx, author, {
            "file": rel, "license": choice.get("license"), "author": choice.get("author"),
            "sourceUrl": choice.get("pageUrl") or choice["url"], "source": choice.get("source") or "manual"})
        return f"escolhida ({choice.get('source') or 'manual'})", warn

    qid = (author.get("wikidata") or {}).get("id")
    entity = ctx.entity(qid) if qid else None
    if entity and "commons" in ctx.waves.photo_sources:
        state = ctx.author_state(slug)
        state["photoCommonsQid"] = qid  # Commons já tentado para este QID
        files = wikidata.claim_strings(entity, "P18")
        if files:
            info = commons.image_info(ctx.http, files[0], int(ctx.config.get("photo", {}).get("commonsWidth", 1200)))
            if info and info.get("url"):
                rel, warn = download(ctx, author, info["url"])
                _set_photo(ctx, author, {"file": rel, "license": info.get("license"), "author": info.get("author"),
                                         "sourceUrl": info.get("pageUrl") or clean_url(info["url"]),
                                         "source": "commons"})
                return "commons", warn
            notes.append(f"P18 sem metadados no Commons: {files[0]}")
    candidates = gather_candidates(ctx, author, entity)
    return (f"{len(candidates)} candidata(s) para revisão" if candidates else "sem candidatas"), notes


def _set_photo(ctx: Context, author: Dict[str, Any], photo: Optional[Dict[str, Any]]) -> None:
    """Troca a foto; o arquivo antigo é removido depois da gravação, se mudou de nome."""
    old = author.get("photo")
    if old and old.get("file") and (photo is None or photo.get("file") != old.get("file")):
        ctx.photos_to_delete.append(Path(old["file"]))
    author["photo"] = photo

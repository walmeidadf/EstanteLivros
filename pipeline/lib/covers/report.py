"""Relatórios das capas: folha de revisão, backlog da 2ª onda e log de execuções."""

from __future__ import annotations

import html
import json
from collections import Counter
from typing import Any, Dict, List

from . import apply as apply_step
from .context import CoverContext, CoverResult
from .measure import LABELS
from .select import priority_key

# Handoff §3.2: cor do idioma original (fundo, texto). Idioma novo cai em "outros".
LANGUAGE_COLORS = {
    "português": ("#C89B3C", "#1A1408"), "inglês": ("#2F5D9E", "#F4EFE6"),
    "espanhol": ("#A8432C", "#F7EDE6"), "francês": ("#6B4F9A", "#F3EEF8"),
    "italiano": ("#3F7A5C", "#F2F0E8"), "russo": ("#7E2433", "#F6E9EB"),
    "japonês": ("#E8DFCB", "#2A2418"), "alemão": ("#5A5A5A", "#F2F2F2"),
    "hebraico": ("#2A7F86", "#EEF7F7"), "coreano": ("#E3A9B0", "#2A1418"),
}
OTHER_COLOR = ("#4B5E55", "#EDE6D6")
CANDIDATES_REL = "../../pipeline/cache/covers/candidates"


def _authors(ctx: CoverContext, work: Dict[str, Any]) -> str:
    return "; ".join((ctx.catalog.authors.get(a) or {}).get("name", a) for a in work.get("authors", []))


def _typographic_mock(ctx: CoverContext, work: Dict[str, Any]) -> str:
    bg, fg = LANGUAGE_COLORS.get(work.get("language"), OTHER_COLOR)
    return (f'<div class="typo" style="background:{bg};color:{fg}"><b>{html.escape(work["title"])}</b>'
            f'<small>{html.escape(_authors(ctx, work))}</small></div>')


def review_items(ctx: CoverContext) -> List[Dict[str, Any]]:
    """Obras sem decisão aplicada que têm candidatas, na ordem de visibilidade."""
    out = []
    for slug in sorted(ctx.catalog.works, key=lambda s: priority_key(ctx, s)):
        work = ctx.catalog.works[slug]
        choice = ctx.choices.get(slug)
        if choice is not None and apply_step.applied(work, choice):
            continue
        candidates = ctx.state.get(slug, {}).get("candidates") or []
        if candidates:
            out.append({"work": work, "candidates": candidates})
    return out


def render_review_html(ctx: CoverContext) -> str:
    cards = []
    for item in review_items(ctx):
        work, slug = item["work"], item["work"]["slug"]
        figures = []
        for c in item["candidates"]:
            choice = {slug: {"url": c["url"], "source": c["origin"] if c["origin"] != "catalog" else
                             (work.get("cover") or {}).get("source")}}
            klass = LABELS.get(c.get("klass"), "?")
            flag = ' <span class="warn">verificar enquadramento (adicione "focus": "top" ou "bottom")</span>' \
                if c.get("checkFraming") else ""
            figures.append(
                f'<figure><img src="{CANDIDATES_REL}/{html.escape(c["file"])}" alt="" loading="lazy">'
                f'<figcaption><b>{klass}</b> · {c.get("width", "?")}×{c.get("height", "?")} · '
                f'{html.escape(c["origin"])}{flag}'
                f'<pre>{html.escape(json.dumps(choice, ensure_ascii=False, indent=2)[2:-2])}</pre></figcaption></figure>')
        figures.append(f'<figure>{_typographic_mock(ctx, work)}<figcaption>tipográfica (atual)'
                       f'<pre>"{slug}": {{ "typographic": true }}</pre></figcaption></figure>')
        cards.append(f'<section><h2>{html.escape(work["title"])} <small>{html.escape(_authors(ctx, work))}'
                     f' · {slug}</small></h2><div class="row">{"".join(figures)}</div>'
                     f'<pre class="none">"{slug}": {{ "none": true }}</pre></section>')
    body = "".join(cards) or "<p>Nenhuma capa aguardando revisão.</p>"
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><title>Revisão de capas</title>
<style>
body{{font-family:system-ui,sans-serif;background:#0E1714;color:#EDE6D6;margin:24px}}
section{{border-top:1px solid #2D3E37;padding:16px 0}} h2 small{{color:#A9B5AE;font-weight:400}}
.row{{display:flex;gap:16px;flex-wrap:wrap}} figure{{margin:0;width:200px}}
img,.typo{{width:200px;height:300px;object-fit:cover;object-position:center;background:#15211D;display:block}}
.typo{{box-sizing:border-box;padding:16px;display:flex;flex-direction:column;justify-content:space-between;font-style:italic}}
.typo small{{font-style:normal;text-transform:uppercase;letter-spacing:.1em;font-size:10px}}
figcaption{{font-size:12px;color:#BFC8C2}} pre{{white-space:pre-wrap;font-size:11px;background:#15211D;padding:6px}}
.warn{{color:#E8C678}}
</style></head><body>
<h1>Revisão de capas</h1>
<p>As imagens aparecem em 2:3 com corte central, como no app. Copie o bloco escolhido para
<code>pipeline/config/cover_choices.json</code> (<code>url</code> usa a capa real,
<code>typographic</code> mantém a tipográfica, <code>none</code> marca sem capa aceitável).
Se o corte central cortar o título, acrescente <code>"focus": "top"</code> ou <code>"bottom"</code>.
Depois rode <code>python3 pipeline/enrich_covers.py --steps apply</code>.</p>
{body}
</body></html>
"""


def backlog_items(ctx: CoverContext) -> List[Dict[str, Any]]:
    """Obras que nenhuma fonte gratuita resolveu e que seguem sem capa real."""
    out = []
    for slug in sorted(ctx.catalog.works, key=lambda s: priority_key(ctx, s)):
        work = ctx.catalog.works[slug]
        if (work.get("cover") or {}).get("file"):
            continue
        st = ctx.state.get(slug, {})
        choice = ctx.choices.get(slug) or {}
        if st.get("noFreeSource") or choice.get("none"):
            out.append(work)
    return out


def render_backlog(ctx: CoverContext) -> str:
    items = backlog_items(ctx)
    lines = [
        "# Capas: backlog da segunda onda",
        "",
        "Gerado por `python3 pipeline/enrich_covers.py`. Não editar à mão.",
        "",
        "Obras sem capa real depois das fontes gratuitas (URL do catálogo e Open Library por ISBN).",
        "Seguem com a capa tipográfica. Uma segunda onda (paga: SerpApi/Tavily) pode tentar resolvê-las.",
        "",
        f"{len(items)} obra(s).",
        "",
    ]
    if items:
        lines += ["| Obra | Autoria | ISBN-13 | ISBN-10 |", "|---|---|---|---|"]
        for w in items:
            ed = w.get("edition") or {}
            lines.append(f"| {w['title']} (`{w['slug']}`) | {_authors(ctx, w)} | "
                         f"{ed.get('isbn13') or ''} | {ed.get('isbn10') or ''} |")
        lines.append("")
    return "\n".join(lines)


def render_run_entry(date: str, label: str, results: List[CoverResult], http: Any, failures: int) -> str:
    per_step: Dict[str, Counter] = {}
    for r in results:
        for step, outcome in r.done.items():
            per_step.setdefault(step, Counter())[outcome] += 1
    lines = [f"## {date} · {label} · {len(results)} obras", "", "| Etapa | Resultado |", "|---|---|"]
    for step in ("download", "measure", "search", "apply"):
        if step in per_step:
            summary = " · ".join(f"{k} {v}" for k, v in sorted(per_step[step].items(), key=lambda kv: (-kv[1], kv[0])))
            lines.append(f"| {step} | {summary} |")
    providers = sorted(set(http.network) | set(http.cached))
    calls = " · ".join(f"{p} {http.network[p]} (cache {http.cached[p]})" for p in providers) or "nenhuma"
    lines += ["", f"Chamadas: {calls} · Falhas: {failures}"]
    return "\n".join(lines) + "\n"

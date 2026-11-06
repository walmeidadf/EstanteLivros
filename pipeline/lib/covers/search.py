"""Etapa `search`: capas em fontes GRATUITAS para as obras sem capa boa (R3).

Só a Open Library Covers por ISBN. SerpApi e Tavily ficam para uma segunda onda
(paga): obras sem resolução aqui entram em `docs/plans/capas-backlog.md`.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ..images import sniff
from ..providers import openlibrary
from .context import CoverContext
from .download import store_candidate
from .measure import GOOD, LOW, classify, describe


def _usable(entry: Dict[str, Any]) -> bool:
    return entry.get("klass") not in (None, LOW)


def _good(entry: Dict[str, Any]) -> bool:
    return entry.get("klass") == GOOD


def pending(ctx: CoverContext, work: Dict[str, Any]) -> bool:
    """Busca quando a obra ainda não tem uma capa BOA (lado menor ≥ goodMinSide).

    Inclui as sem capa, as baixas e as limítrofes: para estas, a Open Library
    pode oferecer uma alternativa melhor, e a Lila compara na revisão."""
    st = ctx.work_state(work["slug"])
    if st.get("searched") and not ctx.refresh:
        return False
    cover = work.get("cover")
    if cover and cover.get("sourceUrl"):
        # Espera o download da própria sourceUrl antes de decidir se falta capa.
        attempted = any(c["origin"] == "catalog" for c in st["candidates"]) or \
            st.get("downloadError", {}).get("url") == cover["sourceUrl"]
        if not attempted:
            return False
    return not any(_good(c) for c in st["candidates"])


def isbns(work: Dict[str, Any]) -> List[str]:
    edition = work.get("edition") or {}
    return [i for i in (edition.get("isbn13"), edition.get("isbn10")) if i]


def run(ctx: CoverContext, work: Dict[str, Any]) -> str:
    slug = work["slug"]
    st = ctx.work_state(slug)
    cfg = ctx.cover_config
    size = cfg.get("openLibrarySize", "L")
    notes: List[str] = []
    found = False
    for isbn in isbns(work):
        content = openlibrary.fetch_cover(ctx.http, isbn, size)
        if content is None:
            continue
        info = sniff(content)
        if info is None or classify(cfg, info) == LOW:
            notes.append(f"{isbn}: descartada (inválida ou abaixo de {cfg.get('rejectBelow', 250)}px)")
            continue
        entry = store_candidate(ctx, slug, openlibrary.cover_url(isbn, size), "openlibrary", content)
        entry.update(describe(cfg, info))
        found = True
        break
    st["searched"] = ctx.today().isoformat()
    st["noFreeSource"] = not found and not any(_usable(c) for c in st["candidates"])
    st["searchNotes"] = notes
    if found:
        return "Open Library"
    if not isbns(work):
        return "sem ISBN: backlog"
    return "sem capa gratuita: backlog"

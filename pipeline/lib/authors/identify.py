"""Etapa `identify`: liga uma autoria a um QID do Wikidata, com evidência."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple

from ..names import unify_key
from ..providers import wikidata
from .context import Context, title_variants

EVIDENCE_ORDER = {"ISBN": 0, "Open Library": 1, "título": 2}


def _catalog_keys(work: Dict[str, Any]) -> Tuple[Set[str], Set[str], Set[str]]:
    edition = work.get("edition") or {}
    isbns = {x for x in (edition.get("isbn13"), edition.get("isbn10")) if x}
    ol = set()
    for ref in work.get("references", []):
        if ref.get("provider") == "openlibrary" and ref.get("id"):
            ol.add(ref["id"].rsplit("/", 1)[-1])
    titles: Set[str] = set()
    for value in (work.get("title"), work.get("originalTitle"), work.get("originalTitleRomanized"),
                  edition.get("title")):
        titles |= title_variants(value)
    return isbns, ol, titles


def match_work(work: Dict[str, Any], wd_work: wikidata.WikidataWork) -> Optional[str]:
    """Tipo de casamento ('ISBN', 'Open Library', 'título') ou None."""
    isbns, ol, titles = _catalog_keys(work)
    if isbns & wd_work.isbns:
        return "ISBN"
    if ol & wd_work.openlibrary:
        return "Open Library"
    wd_titles: Set[str] = set()
    for label in wd_work.labels:
        wd_titles |= title_variants(label)
    if titles & wd_titles:
        return "título"
    return None


def _evidence(kind: str, work: Dict[str, Any]) -> str:
    edition = work.get("edition") or {}
    if kind == "ISBN":
        return f'P50 em "{work["title"]}" (ISBN {edition.get("isbn13") or edition.get("isbn10")})'
    return f'P50 em "{work["title"]}" ({kind})'


def _result(ctx: Context, status: str, qid: Optional[str], evidence: Optional[str]) -> Dict[str, Any]:
    return {"id": qid, "status": status, "evidence": evidence, "rulesVersion": ctx.rules_version}


def identify(ctx: Context, author: Dict[str, Any]) -> Dict[str, Any]:
    """Devolve o objeto `wikidata` da autoria e anota candidatos no estado."""
    slug = author["slug"]
    state = ctx.author_state(slug)
    manual = ctx.author_wikidata.get(slug)
    if manual is not None:
        if manual.get("none"):
            return _result(ctx, "none", None, "marcado à mão como sem Wikidata")
        return _result(ctx, "manual", manual["id"], "escolha manual")

    # 1. candidatos
    candidates: List[str] = []
    for name in [author["name"], *author.get("aliases", [])]:
        for lang in ("pt", "en"):
            for qid in wikidata.search(ctx.http, name, lang):
                if qid not in candidates:
                    candidates.append(qid)
    entities = wikidata.entities(ctx.http, candidates) if candidates else {}
    ctx.entity_cache.update(entities)
    humans = [q for q in candidates if q in entities and wikidata.is_human(entities[q])]
    state["identifyCandidates"] = [
        {"id": q, "description": wikidata.description(entities[q])} for q in humans[:8]]
    if not humans:
        return _result(ctx, "not_found", None, "nenhum humano na busca do Wikidata")

    # 2. confirmação por obra
    works = ctx.works_by_author.get(slug, [])
    label_langs = set(ctx.bio_languages()) | {"pt", "en", "de"}
    label_langs |= {ctx.iso(w.get("language")) for w in works if ctx.iso(w.get("language"))}
    by_author = wikidata.works_of(ctx.http, humans, sorted(label_langs))
    confirmed: Dict[str, Tuple[int, str]] = {}
    for qid in humans:
        best: Optional[Tuple[int, str]] = None
        for work in works:
            for wd_work in by_author.get(qid, {}).values():
                kind = match_work(work, wd_work)
                if kind and (best is None or EVIDENCE_ORDER[kind] < best[0]):
                    best = (EVIDENCE_ORDER[kind], _evidence(kind, work))
        if best:
            confirmed[qid] = best
    if len(confirmed) == 1:
        qid, (_, evidence) = next(iter(confirmed.items()))
        return _result(ctx, "confirmed", qid, evidence)
    if len(confirmed) > 1:
        return _result(ctx, "ambiguous", None, "várias pessoas com obra casada: " + ", ".join(sorted(confirmed)))

    # 3. provável: único escritor com nome igual
    wanted = {unify_key(n) for n in [author["name"], *author.get("aliases", [])]}
    writers = [
        q for q in humans
        if set(wikidata.claim_ids(entities[q], "P106")) & set(ctx.occupations)
        and wanted & {unify_key(n) for n in wikidata.names(entities[q])}
    ]
    if len(writers) == 1:
        return _result(ctx, "probable", writers[0], "único escritor com o mesmo nome (sem obra casada)")
    if len(writers) > 1:
        return _result(ctx, "ambiguous", None, "vários escritores com o mesmo nome: " + ", ".join(writers))
    return _result(ctx, "not_found", None, "nenhum escritor com o mesmo nome nem obra casada")


def apply(ctx: Context, author: Dict[str, Any], result: Dict[str, Any]) -> str:
    author["wikidata"] = result
    refs = [r for r in author.get("references", []) if r.get("provider") != "wikidata"]
    if result.get("id"):
        refs.insert(0, {"provider": "wikidata", "id": result["id"], "url": wikidata.entity_url(result["id"])})
    author["references"] = refs
    return result["status"]

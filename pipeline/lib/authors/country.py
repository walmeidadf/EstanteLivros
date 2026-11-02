"""Etapa `country`: país principal da autoria (código ISO 3166-1 alfa-2)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from ..providers import wikidata
from .context import Context

MIN_CITIZENSHIP_END = 1800  # cidadanias encerradas antes disso são ignoradas


def map_country(ctx: Context, qid: str) -> Tuple[Optional[str], Optional[str]]:
    """(ISO, nota). Usa countries.json e, para Estados extintos, a tabela `defunct`."""
    for code, info in ctx.countries.get("countries", {}).items():
        if info.get("qid") == qid or qid in info.get("altQids", []):
            return code, None
    defunct = ctx.countries.get("defunct", {}).get(qid)
    if defunct:
        return defunct["to"], f"Estado extinto {defunct['name']} → {defunct['to']}"
    return None, f"país {qid} não mapeado em countries.json"


def _birth_country(ctx: Context, entity: Dict[str, Any]) -> List[str]:
    places = wikidata.claim_ids(entity, "P19")
    if not places:
        return []
    place = ctx.entity(places[0])
    if not place:
        return []
    if place.get("id") and map_country(ctx, place["id"])[0]:  # o próprio lugar é um país
        return [place["id"]]
    return wikidata.claim_ids(place, "P17")


def choose_country(ctx: Context, author: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], List[str]]:
    """(país, origem, notas para o relatório)."""
    override = ctx.override_for(author).get("country")
    if override:
        return override, "override", []
    qid = (author.get("wikidata") or {}).get("id")
    if not qid:
        return None, None, []
    entity = ctx.entity(qid)
    if not entity:
        return None, None, [f"entidade {qid} não carregada"]
    notes: List[str] = []
    mapped: List[str] = []
    for c_qid, end in wikidata.claim_ids_with_end(entity, "P27"):
        if end is not None and end < MIN_CITIZENSHIP_END:
            continue
        code, note = map_country(ctx, c_qid)
        if note:
            notes.append(note)
        if code and code not in mapped:
            mapped.append(code)

    if len(mapped) == 1:
        return mapped[0], "wikidata-citizenship", notes
    birth = [c for c in (map_country(ctx, q)[0] for q in _birth_country(ctx, entity)) if c]
    if len(mapped) > 1:
        lang = author.get("primaryLanguage")
        by_lang = [c for c in mapped if lang in ctx.countries["countries"].get(c, {}).get("languages", [])]
        pool = by_lang or mapped
        if len(pool) > 1:
            pool = [c for c in pool if c in birth] or pool
        chosen = pool[0]
        notes.append("país escolhido entre vários: " + ", ".join(mapped) + f" → {chosen}")
        return chosen, "wikidata-citizenship", notes
    if birth:
        return birth[0], "wikidata-birthplace", notes
    notes.append("sem cidadania nem local de nascimento mapeável")
    return None, None, notes


def apply(ctx: Context, author: Dict[str, Any], country: Optional[str], source: Optional[str]) -> str:
    author["country"] = country
    author["countrySource"] = source if country else None
    return country or "sem país"

"""Wikidata: busca de entidades, leitura de claims e obras por autoria (SPARQL)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from ..http import Http

API = "https://www.wikidata.org/w/api.php"
SPARQL = "https://query.wikidata.org/sparql"
PROVIDER = "wikidata"
HUMAN = "Q5"
BATCH = 50


def search(http: Http, name: str, language: str, limit: int = 10) -> List[str]:
    resp = http.get_json(PROVIDER, API, {
        "action": "wbsearchentities", "search": name, "language": language,
        "uselang": language, "type": "item", "limit": limit, "format": "json",
    })
    return [item["id"] for item in (resp.data or {}).get("search", []) if "id" in item]


def entities(http: Http, ids: Iterable[str], props: str = "claims|labels|aliases|sitelinks|descriptions",
             languages: str = "pt|en") -> Dict[str, Dict[str, Any]]:
    """Carrega entidades em lotes de 50 (IDs ordenados, para o cache ser estável)."""
    unique = sorted(set(ids), key=lambda q: (len(q), q))
    out: Dict[str, Dict[str, Any]] = {}
    for start in range(0, len(unique), BATCH):
        batch = unique[start:start + BATCH]
        resp = http.get_json(PROVIDER, API, {
            "action": "wbgetentities", "ids": "|".join(batch), "props": props,
            "languages": languages, "format": "json",
        })
        for qid, entity in ((resp.data or {}).get("entities") or {}).items():
            if "missing" not in entity:
                out[qid] = entity
    return out


# -- leitura de claims ------------------------------------------------------

_RANK_ORDER = {"preferred": 0, "normal": 1}


def _claims(entity: Dict[str, Any], prop: str) -> List[Dict[str, Any]]:
    claims = [c for c in entity.get("claims", {}).get(prop, []) if c.get("rank") != "deprecated"]
    return sorted(claims, key=lambda c: _RANK_ORDER.get(c.get("rank"), 1))  # sort estável


def claim_ids(entity: Dict[str, Any], prop: str) -> List[str]:
    """QIDs de uma propriedade, preferidos primeiro, sem os depreciados."""
    out = []
    for claim in _claims(entity, prop):
        value = claim.get("mainsnak", {}).get("datavalue", {}).get("value")
        if isinstance(value, dict) and value.get("id") and value["id"] not in out:
            out.append(value["id"])
    return out


def claim_strings(entity: Dict[str, Any], prop: str) -> List[str]:
    out = []
    for claim in _claims(entity, prop):
        value = claim.get("mainsnak", {}).get("datavalue", {}).get("value")
        if isinstance(value, str) and value not in out:
            out.append(value)
    return out


def _year(time_value: Any) -> Optional[int]:
    if isinstance(time_value, dict) and isinstance(time_value.get("time"), str):
        try:
            return int(time_value["time"][:5].replace("+", ""))
        except ValueError:
            return None
    return None


def claim_ids_with_end(entity: Dict[str, Any], prop: str) -> List[Tuple[str, Optional[int]]]:
    """(QID, ano de fim do qualificador P582) — usado em cidadanias."""
    out = []
    for claim in _claims(entity, prop):
        value = claim.get("mainsnak", {}).get("datavalue", {}).get("value")
        if not (isinstance(value, dict) and value.get("id")):
            continue
        end = None
        for q in claim.get("qualifiers", {}).get("P582", []):
            end = _year(q.get("datavalue", {}).get("value"))
        out.append((value["id"], end))
    return out


def is_human(entity: Dict[str, Any]) -> bool:
    return HUMAN in claim_ids(entity, "P31")


def names(entity: Dict[str, Any]) -> List[str]:
    """Rótulos e aliases em todos os idiomas carregados."""
    out = [v["value"] for v in entity.get("labels", {}).values() if v.get("value")]
    for items in entity.get("aliases", {}).values():
        out += [v["value"] for v in items if v.get("value")]
    return out


def description(entity: Dict[str, Any]) -> Optional[str]:
    descs = entity.get("descriptions", {})
    for lang in ("pt", "en"):
        if descs.get(lang, {}).get("value"):
            return descs[lang]["value"]
    return None


def sitelink(entity: Dict[str, Any], lang: str) -> Optional[str]:
    return entity.get("sitelinks", {}).get(f"{lang}wiki", {}).get("title")


def entity_url(qid: str) -> str:
    return f"https://www.wikidata.org/wiki/{qid}"


# -- obras por autoria ------------------------------------------------------

@dataclass
class WikidataWork:
    qid: str
    labels: Set[str] = field(default_factory=set)
    openlibrary: Set[str] = field(default_factory=set)
    isbns: Set[str] = field(default_factory=set)


def works_of(http: Http, author_qids: Sequence[str], label_languages: Sequence[str]) -> Dict[str, Dict[str, WikidataWork]]:
    """{autoria: {obra: WikidataWork}} para os candidatos dados."""
    if not author_qids:
        return {}
    values = " ".join(f"wd:{q}" for q in sorted(set(author_qids)))
    langs = ", ".join(f'"{lang}"' for lang in sorted(set(label_languages)))
    query = f"""SELECT ?author ?work ?label ?ol ?isbn WHERE {{
  VALUES ?author {{ {values} }}
  ?work wdt:P50 ?author .
  {{ ?work rdfs:label ?label . FILTER(LANG(?label) IN ({langs})) }}
  UNION {{ ?work wdt:P1476 ?label }}
  UNION {{ ?work wdt:P648 ?ol }}
  UNION {{ ?work wdt:P212|wdt:P957 ?isbn }}
  UNION {{ ?ed wdt:P629 ?work . ?ed wdt:P212|wdt:P957 ?isbn }}
}} LIMIT 20000"""
    resp = http.get_json(PROVIDER, SPARQL, {"query": query, "format": "json"},
                         headers={"Accept": "application/sparql-results+json"})
    out: Dict[str, Dict[str, WikidataWork]] = {}
    for row in ((resp.data or {}).get("results") or {}).get("bindings", []):
        author = row["author"]["value"].rsplit("/", 1)[-1]
        work_qid = row["work"]["value"].rsplit("/", 1)[-1]
        work = out.setdefault(author, {}).setdefault(work_qid, WikidataWork(work_qid))
        if "label" in row:
            work.labels.add(row["label"]["value"])
        if "ol" in row:
            work.openlibrary.add(row["ol"]["value"])
        if "isbn" in row:
            work.isbns.add(row["isbn"]["value"].replace("-", "").replace(" ", "").upper())
    return out


def sparql(http: Http, query: str) -> List[Dict[str, Any]]:
    resp = http.get_json(PROVIDER, SPARQL, {"query": query, "format": "json"},
                         headers={"Accept": "application/sparql-results+json"})
    return ((resp.data or {}).get("results") or {}).get("bindings", [])

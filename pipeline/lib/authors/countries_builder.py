"""Gera `pipeline/config/countries.json` a partir do Wikidata (`--build-countries`)."""

from __future__ import annotations

from typing import Any, Dict

from ..providers import wikidata
from .context import Context

DEFUNCT = {
    "Q15180": {"name": "União Soviética", "to": "RU"},
    "Q34266": {"name": "Império Russo", "to": "RU"},
    "Q2184": {"name": "RSFS da Rússia", "to": "RU"},
    "Q33946": {"name": "Tchecoslováquia", "to": "CZ"},
    "Q36704": {"name": "Iugoslávia", "to": "RS"},
    "Q16957": {"name": "Alemanha Oriental", "to": "DE"},
    "Q43287": {"name": "Império Alemão", "to": "DE"},
    "Q28513": {"name": "Áustria-Hungria", "to": "AT"},
    "Q174193": {"name": "Reino Unido da Grã-Bretanha e Irlanda", "to": "GB"},
}

QUERY = """SELECT ?c ?iso ?label ?lang WHERE {
  ?c wdt:P297 ?iso .
  FILTER NOT EXISTS { ?c wdt:P576 ?dissolved }
  OPTIONAL { ?c rdfs:label ?label . FILTER(LANG(?label) = "pt") }
  OPTIONAL { ?c wdt:P37 ?lang }
}"""


def build_countries(ctx: Context, existing: Dict[str, Any]) -> Dict[str, Any]:
    """Países com ISO alfa-2, nome pt e idiomas oficiais (só os do catálogo).

    Nomes e idiomas já revisados em `existing` vencem os do Wikidata, e a tabela
    `defunct` existente é preservada.
    """
    lang_by_qid = {info["qid"]: name for name, info in ctx.languages.items()}
    found: Dict[str, Dict[str, Any]] = {}
    for row in wikidata.sparql(ctx.http, QUERY):
        iso = row["iso"]["value"].upper()
        if len(iso) != 2:
            continue
        qid = row["c"]["value"].rsplit("/", 1)[-1]
        entry = found.setdefault(iso, {}).setdefault(qid, {"name": None, "languages": []})
        if "label" in row and not entry["name"]:
            entry["name"] = row["label"]["value"]
        if "lang" in row:
            lang = lang_by_qid.get(row["lang"]["value"].rsplit("/", 1)[-1])
            if lang and lang not in entry["languages"]:
                entry["languages"].append(lang)
    old = existing.get("countries", {})
    out = {}
    for iso in sorted(found):
        # Mais de uma entidade com o mesmo ISO (ex.: Países Baixos Q55 e Reino Q29999):
        # a de menor QID é a principal; as outras viram altQids.
        qids = sorted(found[iso], key=lambda q: int(q[1:]))
        main = found[iso][qids[0]]
        names = [found[iso][q]["name"] for q in qids if found[iso][q]["name"]]
        langs = sorted({lang for q in qids for lang in found[iso][q]["languages"]})
        prev = old.get(iso) or {}
        entry = {"qid": qids[0], "name": prev.get("name") or main["name"] or (names[0] if names else iso),
                 "languages": sorted(prev.get("languages") or langs)}
        alt = sorted(set(qids[1:]) | set(prev.get("altQids", [])), key=lambda q: int(q[1:]))
        if alt:
            entry["altQids"] = alt
        out[iso] = entry
    defunct = dict(DEFUNCT)
    defunct.update(existing.get("defunct", {}))
    return {"countries": out, "defunct": dict(sorted(defunct.items()))}

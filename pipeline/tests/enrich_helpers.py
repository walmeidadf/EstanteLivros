"""Fixtures do enriquecimento: catálogo pequeno, Wikimedia simulado e contexto."""

from __future__ import annotations

import datetime as dt
import json
import tempfile
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional

import helpers
from lib.authors.context import CONFIG, Context, Waves
from lib.authors.countries_builder import DEFUNCT
from lib.budget import Budget
from lib.checks import Catalog
from lib.env import Env
from lib.http import Http

TODAY = lambda: dt.date(2026, 11, 2)  # noqa: E731

ENV = {
    "WIKIMEDIA_USER_AGENT": "UA-teste (teste@exemplo.com)",
    "OPENAI_API_KEY": "sk-teste", "OPENAI_MODEL": "gpt-teste",
    "OPENAI_PRICE_INPUT_PER_M": "1.0", "OPENAI_PRICE_OUTPUT_PER_M": "4.0",
    "TAVILY_API_KEY": "tvly-teste", "SERP_API_KEY": "serp-teste",
    "BIO_SOURCE_LANGUAGES": "pt,en",
}

COUNTRIES = {
    "countries": {
        "BR": {"qid": "Q155", "name": "Brasil", "languages": ["português"]},
        "PT": {"qid": "Q45", "name": "Portugal", "languages": ["português"]},
        "KR": {"qid": "Q884", "name": "Coreia do Sul", "languages": ["coreano"]},
        "RU": {"qid": "Q159", "name": "Rússia", "languages": ["russo"]},
        "UA": {"qid": "Q212", "name": "Ucrânia", "languages": []},
        "GB": {"qid": "Q145", "name": "Reino Unido", "languages": ["inglês"]},
        "US": {"qid": "Q30", "name": "Estados Unidos", "languages": ["inglês"]},
    },
    "defunct": DEFUNCT,
}


def config() -> Dict[str, Any]:
    return json.loads((CONFIG / "enrich.json").read_text(encoding="utf-8"))


def _work(slug, title, authors, language="português", isbn13=None, original=None, ol=None):
    w = helpers._work(slug, authors)
    w.update(title=title, language=language, originalTitle=original)
    w["edition"]["isbn13"] = isbn13
    if ol:
        w["references"] = [{"provider": "openlibrary", "id": f"/works/{ol}", "url": None, "fields": None}]
    return w


def _author(slug, name, language="português"):
    a = helpers._author(slug)
    a.update(name=name, country=None, countrySource=None, languages=[language], primaryLanguage=language)
    return a


def catalog() -> Catalog:
    works = {
        "a-vegetariana-han-kang": _work("a-vegetariana-han-kang", "A Vegetariana", ["han-kang"], "coreano",
                                        "9788588808294", "채식주의자"),
        "torto-arado-itamar-vieira-junior": _work("torto-arado-itamar-vieira-junior", "Torto Arado",
                                                  ["itamar-vieira-junior"], isbn13="9786580309313"),
        "livro-raro-fulana-de-tal": _work("livro-raro-fulana-de-tal", "Livro Raro", ["fulana-de-tal"]),
    }
    authors = {
        "han-kang": _author("han-kang", "Han Kang", "coreano"),
        "itamar-vieira-junior": _author("itamar-vieira-junior", "Itamar Vieira Junior"),
        "fulana-de-tal": _author("fulana-de-tal", "Fulana de Tal"),
    }
    readings = [
        {"sequence": 1, "year": None, "work": "livro-raro-fulana-de-tal", "reread": False, "originalEntry": "x", "notes": None},
        {"sequence": 2, "year": 2025, "work": "torto-arado-itamar-vieira-junior", "reread": False, "originalEntry": "x", "notes": None},
        {"sequence": 3, "year": 2026, "work": "a-vegetariana-han-kang", "reread": False, "originalEntry": "x", "notes": None},
        {"sequence": 4, "year": 2026, "work": "a-vegetariana-han-kang", "reread": True, "originalEntry": "x", "notes": None},
    ]
    return Catalog(
        works=works, authors=authors, readings={"readings": readings}, summaries={"summaries": []},
        vocabularies={"languages": ["coreano", "português"], "workTypes": ["romance"], "genres": ["humor"],
                      "themes": ["memória"], "countries": []},
        media=set(),
    )


def entity(qid, label, human=True, occupations=("Q36180",), p27=(), p18=None, p19=None, p17=(),
           sitelinks=None, description=None, aliases=()):
    def claim(prop_value, qualifiers=None, rank="normal"):
        c = {"rank": rank, "mainsnak": {"datavalue": {"value": prop_value}}}
        if qualifiers:
            c["qualifiers"] = qualifiers
        return c
    claims: Dict[str, List[Any]] = {"P31": [claim({"id": "Q5" if human else "Q4022"})]}
    claims["P106"] = [claim({"id": o}) for o in occupations]
    p27_claims = []
    for item in p27:
        q, end = (item, None) if isinstance(item, str) else item
        quals = {"P582": [{"datavalue": {"value": {"time": f"+{end}-01-01T00:00:00Z"}}}]} if end else None
        p27_claims.append(claim({"id": q}, quals))
    claims["P27"] = p27_claims
    if p18:
        claims["P18"] = [claim(p18)]
    if p19:
        claims["P19"] = [claim({"id": p19})]
    if p17:
        claims["P17"] = [claim({"id": q}) for q in p17]
    return {"id": qid, "labels": {"pt": {"value": label}, "en": {"value": label}},
            "aliases": {"pt": [{"value": a} for a in aliases]},
            "descriptions": {"pt": {"value": description or "escritora"}},
            "claims": claims, "sitelinks": {f"{k}wiki": {"title": v} for k, v in (sitelinks or {}).items()}}


class FakeWeb:
    """Wikimedia, Commons, SerpApi, Tavily e OpenAI simulados num só transporte."""

    def __init__(self):
        self.search: Dict[str, List[str]] = {}
        self.entities: Dict[str, Dict[str, Any]] = {}
        self.works: Dict[str, List[Dict[str, Any]]] = {}
        self.intros: Dict[tuple, str] = {}
        self.pageimages: Dict[tuple, Dict[str, Any]] = {}
        self.commons: Dict[str, Dict[str, Any]] = {}
        self.images: Dict[str, bytes] = {}
        self.serp: List[Dict[str, Any]] = []
        self.tavily: Dict[str, Any] = {"results": [], "images": []}
        self.openai: List[Any] = []  # respostas em ordem (dict do modelo ou exceção HTTP)
        self.fake = helpers.FakeTransport([
            ("GET", "wbsearchentities", self._search),
            ("GET", "wbgetentities", self._entities),
            ("GET", "query.wikidata.org", self._sparql),
            ("GET", "wikipedia.org/w/api.php", self._wikipedia),
            ("GET", "commons.wikimedia.org/w/api.php", self._commons),
            ("GET", "serpapi.com/search", lambda u, b: {"images_results": self.serp}),
            ("GET", "serpapi.com/account", {"this_month_usage": 0}),
            ("GET", "api.tavily.com/usage", {"account": {"plan_usage": 0}}),
            ("POST", "api.tavily.com/search", lambda u, b: self.tavily),
            ("POST", "api.openai.com", self._openai),
            ("GET", "img.test", self._image),
        ])

    @staticmethod
    def _q(url):
        return dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query))

    def _search(self, url, body):
        q = self._q(url)
        return {"search": [{"id": i} for i in self.search.get(q["search"], [])]}

    def _entities(self, url, body):
        ids = self._q(url)["ids"].split("|")
        return {"entities": {i: self.entities[i] if i in self.entities else {"id": i, "missing": ""} for i in ids}}

    def _sparql(self, url, body):
        query = self._q(url)["query"]
        rows = []
        for author, works in self.works.items():
            if f"wd:{author}" not in query:
                continue
            for w in works:
                base = {"author": {"value": f"http://www.wikidata.org/entity/{author}"},
                        "work": {"value": f"http://www.wikidata.org/entity/{w['qid']}"}}
                rows += [dict(base, label={"value": lab}) for lab in w.get("labels", [])]
                rows += [dict(base, isbn={"value": i}) for i in w.get("isbns", [])]
                rows += [dict(base, ol={"value": o}) for o in w.get("ol", [])]
        return {"results": {"bindings": rows}}

    def _wikipedia(self, url, body):
        lang = urllib.parse.urlsplit(url).netloc.split(".")[0]
        q = self._q(url)
        title = q["titles"]
        if q.get("prop") == "pageimages":
            img = self.pageimages.get((lang, title))
            return {"query": {"pages": [{"title": title, **({"thumbnail": img, "pageimage": "x.jpg"} if img else {})}]}}
        text = self.intros.get((lang, title))
        if text is None:
            return {"query": {"pages": [{"title": title, "missing": True}]}}
        return {"query": {"pages": [{"title": title, "extract": text}]}}

    def _commons(self, url, body):
        name = self._q(url)["titles"][len("File:"):]
        info = self.commons.get(name)
        if not info:
            return {"query": {"pages": [{"title": name, "missing": True}]}}
        return {"query": {"pages": [{"imageinfo": [{
            "thumburl": info["url"], "thumbwidth": 1200, "thumbheight": 1600,
            "descriptionurl": f"https://commons.wikimedia.org/wiki/File:{name}",
            "extmetadata": {"LicenseShortName": {"value": info.get("license", "CC BY-SA 4.0")},
                            "Artist": {"value": info.get("artist", '<a href="//x">Fotógrafa</a>')}}}]}]}}

    def _image(self, url, body):
        data = self.images.get(url.split("?")[0])
        return (200, data, {"content-type": "image/png"}) if data else (404, b"", {})

    def _openai(self, url, body):
        item = self.openai.pop(0) if self.openai else {"insufficient": True, "text": "", "source_index": 0}
        if isinstance(item, tuple):
            return item
        return {"status": "completed", "usage": {"input_tokens": 1000, "output_tokens": 100},
                "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(item)}]}]}

    # -- cenários prontos ----------------------------------------------------

    def han_kang(self):
        self.search["Han Kang"] = ["Q5646626", "Q55500", "Q17030180"]
        self.entities["Q5646626"] = entity("Q5646626", "Han Kang", occupations=("Q6625963",), p27=("Q884",),
                                           p18="Han Kang.jpg", sitelinks={"pt": "Han Kang", "en": "Han Kang"},
                                           description="escritora sul-coreana")
        self.entities["Q55500"] = entity("Q55500", "Han", human=False)
        self.entities["Q17030180"] = entity("Q17030180", "Han Kang", occupations=("Q39631",),
                                            description="médico da dinastia Han")
        self.works["Q5646626"] = [{"qid": "Q24082770", "labels": ["A Vegetariana", "The Vegetarian", "채식주의자"],
                                   "isbns": ["9780553448184"]}]
        self.intros[("pt", "Han Kang")] = "Han Kang é uma escritora sul-coreana." * 3  # ~111 caracteres
        self.intros[("en", "Han Kang")] = ("Han Kang is a South Korean writer. She won the 2024 Nobel Prize in "
                                          "Literature for her intense poetic prose. ") * 4
        self.commons["Han Kang.jpg"] = {"url": "https://img.test/han-kang-1200.png"}
        self.images["https://img.test/han-kang-1200.png"] = helpers.tiny_png(1200, 1600)
        return self


def make_ctx(web: FakeWeb, wave: Optional[int] = None, tmp: Optional[Path] = None, cat: Optional[Catalog] = None,
             env: Optional[Dict[str, str]] = None, budgets: Optional[Dict[str, Any]] = None, **kw) -> Context:
    tmp = tmp or Path(tempfile.mkdtemp())
    cfg = config()
    budget = Budget(budgets or {"serpapi": {"monthly": 250, "reserve": 0, "perRun": 100},
                                "tavily": {"monthly": 1000, "reserve": 0, "perRun": 100},
                                "openai": {"maxUsdPerRun": 1.0}},
                    tmp / "usage", today=TODAY)
    http = Http(tmp / "cache", transport=web.fake, user_agent=ENV["WIKIMEDIA_USER_AGENT"],
                sleep=lambda s: None, budget=budget, offline=kw.pop("offline", False))
    return Context(
        catalog=cat or catalog(), http=http, env=Env(env or ENV), budget=budget, config=cfg,
        waves=Waves.for_wave(wave, cfg["photo"]["order"]), state={}, staging=tmp / "staging",
        countries=COUNTRIES, languages=json.loads((CONFIG / "languages.json").read_text(encoding="utf-8")),
        occupations=json.loads((CONFIG / "writer_occupations.json").read_text(encoding="utf-8")),
        today=TODAY, **kw)

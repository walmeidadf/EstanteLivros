"""Testes de parsing dos provedores (tarefas 7–9), com respostas reais recortadas."""

import json
import tempfile
import unittest
from pathlib import Path

import helpers
from lib.http import Http
from lib.providers import commons, openai_client, serpapi, tavily, wikidata, wikipedia

FIXTURES = Path(__file__).parent / "fixtures" / "enrich"


def fixture(name):
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


class ProviderCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.fake = helpers.FakeTransport()
        self.http = Http(Path(self.tmp.name), transport=self.fake, sleep=lambda s: None)

    def tearDown(self):
        self.tmp.cleanup()


class WikidataTest(ProviderCase):
    def setUp(self):
        super().setUp()
        self.fake.add("GET", "wbsearchentities", fixture("wikidata_search_han_kang"))
        self.fake.add("GET", "wbgetentities", fixture("wikidata_entities_han_kang"))
        self.fake.add("GET", "query.wikidata.org", fixture("wikidata_works_han_kang"))

    def test_busca_e_entidades(self):
        ids = wikidata.search(self.http, "Han Kang", "pt")
        self.assertEqual(ids[0], "Q5646626")
        ents = wikidata.entities(self.http, ids)
        hk = ents["Q5646626"]
        self.assertTrue(wikidata.is_human(hk))
        self.assertFalse(wikidata.is_human(ents["Q55500"]))  # o rio
        self.assertEqual(wikidata.claim_ids_with_end(hk, "P27"), [("Q884", None)])
        self.assertIn("Q6625963", wikidata.claim_ids(hk, "P106"))
        self.assertEqual(wikidata.claim_strings(hk, "P18"),
                         ["Han Kang, 2024 Nobel Prize Laureate in Literature (cropped).jpg"])
        self.assertEqual(wikidata.sitelink(hk, "pt"), "Han Kang")
        self.assertIn("Han Kang", wikidata.names(hk))
        self.assertEqual(wikidata.description(hk), "escritora sul-coreana")

    def test_entidades_em_lotes_de_50(self):
        wikidata.entities(self.http, [f"Q{i}" for i in range(1, 121)])
        self.assertEqual(self.fake.count("wbgetentities"), 3)

    def test_obras(self):
        works = wikidata.works_of(self.http, ["Q5646626"], ["pt", "en", "ko"])
        veg = works["Q5646626"]["Q24082770"]
        self.assertIn("A Vegetariana", veg.labels)
        self.assertIn("9780553448184", veg.isbns)
        self.assertIn("OL17334243W", veg.openlibrary)

    def test_ranks(self):
        entity = {"claims": {"P27": [
            {"rank": "normal", "mainsnak": {"datavalue": {"value": {"id": "Q1"}}}},
            {"rank": "deprecated", "mainsnak": {"datavalue": {"value": {"id": "Q2"}}}},
            {"rank": "preferred", "mainsnak": {"datavalue": {"value": {"id": "Q3"}}},
             "qualifiers": {"P582": [{"datavalue": {"value": {"time": "+1991-12-26T00:00:00Z"}}}]}},
        ]}}
        self.assertEqual(wikidata.claim_ids_with_end(entity, "P27"), [("Q3", 1991), ("Q1", None)])


class WikipediaCommonsTest(ProviderCase):
    def test_intro_e_imagem(self):
        self.fake.add("GET", "pt.wikipedia.org", fixture("wikipedia_intro_pt_han_kang"))
        self.fake.add("GET", "en.wikipedia.org/w/api.php?action=query&format=json&formatversion=2&redirects=1&prop=pageimages",
                      fixture("wikipedia_pageimage_en_han_kang"))
        self.fake.add("GET", "en.wikipedia.org", fixture("wikipedia_intro_en_han_kang"))
        self.assertEqual(len(wikipedia.intro(self.http, "pt", "Han Kang")), 284)
        self.assertGreater(len(wikipedia.intro(self.http, "en", "Han Kang")), 500)
        img = wikipedia.page_image(self.http, "en", "Han Kang", 1200)
        self.assertEqual(img["width"], 1200)
        self.assertEqual(wikipedia.page_url("en", "Han Kang"), "https://en.wikipedia.org/wiki/Han_Kang")

    def test_verbete_inexistente(self):
        self.fake.add("GET", "wikipedia", {"query": {"pages": [{"title": "X", "missing": True}]}})
        self.assertIsNone(wikipedia.intro(self.http, "pt", "X"))

    def test_commons(self):
        self.fake.add("GET", "commons", fixture("commons_han_kang"))
        info = commons.image_info(self.http, "Han Kang, 2024 Nobel Prize Laureate in Literature (cropped).jpg", 1200)
        self.assertEqual((info["width"], info["license"], info["author"]), (1200, "CC BY-SA 4.0", "John Sears"))
        self.assertTrue(info["pageUrl"].startswith("https://commons.wikimedia.org/wiki/File:"))

    def test_strip_html(self):
        self.assertEqual(commons.strip_html('<a href="//x">John&nbsp;Sears</a>\n (<i>own</i>)'), "John Sears (own)")
        self.assertIsNone(commons.strip_html(""))


class SerpTavilyTest(ProviderCase):
    EXCLUDED = ["linkedin.com", "instagram.com"]

    def test_serpapi_filtra_tamanho_e_dominio(self):
        self.fake.add("GET", "serpapi.com/search", {"images_results": [
            {"original": "https://pt.wikipedia.org/a.jpg", "original_width": 1699, "original_height": 1542,
             "source": "Wikipédia", "title": "Itamar", "link": "https://pt.wikipedia.org/wiki/Itamar"},
            {"original": "https://x.org/peq.jpg", "original_width": 300, "original_height": 300},
            {"original": "https://lookaside.instagram.com/a.jpg", "original_width": 900, "original_height": 900},
        ]})
        out = serpapi.images(self.http, "CHAVE", "Itamar Vieira Junior escritor", 400, self.EXCLUDED)
        self.assertEqual([i["url"] for i in out], ["https://pt.wikipedia.org/a.jpg"])
        self.assertNotIn("CHAVE", json.dumps([c["url"] for c in self.fake.calls if "CHAVE" not in c["url"]]))

    def test_tavily(self):
        self.fake.add("POST", "api.tavily.com/search", {"results": [
            {"url": "https://pt.wikipedia.org/wiki/Itamar_Vieira_Junior", "title": "Itamar", "content": "Itamar Vieira Junior é..."},
            {"url": "https://www.linkedin.com/in/x", "title": "x", "content": "x"},
        ], "images": [
            {"url": "https://upload.wikimedia.org/a.jpg?utm_source=x", "description": "Itamar sorrindo"},
            "https://cdn.org/b.jpg",
        ]})
        out = tavily.search(self.http, "CHAVE", "Itamar escritor", self.EXCLUDED)
        self.assertEqual([r["url"] for r in out["results"]], ["https://pt.wikipedia.org/wiki/Itamar_Vieira_Junior"])
        self.assertEqual(out["images"][0], {"url": "https://upload.wikimedia.org/a.jpg", "description": "Itamar sorrindo"})
        self.assertEqual(self.fake.calls[0]["headers"]["Authorization"], "Bearer CHAVE")
        self.assertEqual(self.fake.calls[0]["body"]["exclude_domains"], sorted(self.EXCLUDED))

    def test_uso_mensal_sem_cache(self):
        self.fake.add("GET", "serpapi.com/account", {"this_month_usage": 7})
        self.fake.add("GET", "api.tavily.com/usage", {"account": {"plan_usage": 12}})
        self.assertEqual(serpapi.month_usage(self.http, "K"), 7)
        self.assertEqual(serpapi.month_usage(self.http, "K"), 7)
        self.assertEqual(tavily.month_usage(self.http, "K"), 12)
        self.assertEqual(self.fake.count("serpapi.com/account"), 2)


class OpenAITest(ProviderCase):
    SCHEMA = {"type": "object", "required": ["insufficient", "text", "source_index"], "properties": {}}

    def response(self, text, status="completed"):
        return {"status": status, "usage": {"input_tokens": 1200, "output_tokens": 90},
                "output": [{"type": "message", "content": [{"type": "output_text", "text": text}]}]}

    def test_resposta_estruturada_e_cache(self):
        self.fake.add("POST", "api.openai.com", self.response(
            json.dumps({"insufficient": False, "text": "Han Kang é...", "source_index": 1})))
        obj, usage, cached = openai_client.respond_json(self.http, "sk", "m", "inst", "in", "bio", self.SCHEMA)
        self.assertEqual((obj["source_index"], usage.input_tokens, cached), (1, 1200, False))
        self.assertAlmostEqual(usage.cost(0.75, 4.5), (1200 * 0.75 + 90 * 4.5) / 1e6)
        body = self.fake.calls[0]["body"]
        self.assertEqual(body["text"]["format"]["type"], "json_schema")
        self.assertTrue(body["text"]["format"]["strict"])
        _, _, cached = openai_client.respond_json(self.http, "sk", "m", "inst", "in", "bio", self.SCHEMA)
        self.assertTrue(cached)

    def test_erros(self):
        cases = [
            self.response("não é json"),
            self.response(json.dumps({"text": "x"})),
            self.response("{}", status="incomplete"),
            {"status": "completed", "output": [{"content": [{"type": "refusal", "refusal": "não"}]}]},
        ]
        for i, case in enumerate(cases):
            with self.subTest(i=i):
                self.fake.routes = [("POST", "api.openai.com", case)]
                with self.assertRaises(openai_client.OpenAIError):
                    openai_client.respond_json(self.http, "sk", "m", "inst", f"in-{i}", "bio", self.SCHEMA)


if __name__ == "__main__":
    unittest.main()

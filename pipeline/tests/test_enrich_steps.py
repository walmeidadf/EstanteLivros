"""Testes das etapas e da seleção (tarefas 11–15), offline."""

import json
import tempfile
import unittest
from pathlib import Path

import enrich_helpers as eh
import helpers
from lib import summaries
from lib.authors import bio, country, identify, photo
from lib.authors.context import normalize_title, title_variants
from lib.authors.countries_builder import build_countries
from lib.budget import BudgetExhausted
from lib.selection import PENDING, select


def run_identify(ctx, slug):
    author = ctx.catalog.authors[slug]
    result = identify.identify(ctx, author)
    identify.apply(ctx, author, result)
    return result


class TitleTest(unittest.TestCase):
    def test_normalizacao(self):
        self.assertEqual(normalize_title("A Vegetariana!"), "a vegetariana")
        self.assertEqual(normalize_title("채식주의자"), "채식주의자")
        self.assertIn("emburrecimento programado", title_variants("Emburrecimento Programado: O Currículo Oculto"))


class IdentifyTest(unittest.TestCase):
    def setUp(self):
        self.web = eh.FakeWeb().han_kang()
        self.ctx = eh.make_ctx(self.web)

    def test_confirmada_por_titulo_entre_homonimos(self):
        r = run_identify(self.ctx, "han-kang")
        self.assertEqual((r["status"], r["id"]), ("confirmed", "Q5646626"))
        self.assertIn('"A Vegetariana" (título)', r["evidence"])
        author = self.ctx.catalog.authors["han-kang"]
        self.assertEqual(author["references"][0]["url"], "https://www.wikidata.org/wiki/Q5646626")
        cands = [c["id"] for c in self.ctx.author_state("han-kang")["identifyCandidates"]]
        self.assertEqual(cands, ["Q5646626", "Q17030180"])  # o rio não é humano

    def test_isbn_vence_titulo(self):
        self.web.works["Q5646626"][0]["isbns"].append("9788588808294")
        self.assertIn("ISBN 9788588808294", run_identify(self.ctx, "han-kang")["evidence"])

    def test_open_library(self):
        self.ctx.catalog.works["a-vegetariana-han-kang"]["references"] = [
            {"provider": "openlibrary", "id": "/works/OL1W", "url": None, "fields": None}]
        self.ctx.catalog.works["a-vegetariana-han-kang"].update(title="Outro", originalTitle=None)
        self.ctx.catalog.works["a-vegetariana-han-kang"]["edition"].update(isbn13=None, title=None)
        self.web.works["Q5646626"] = [{"qid": "Q1", "labels": ["Sem relação"], "ol": ["OL1W"]}]
        self.assertIn("(Open Library)", run_identify(self.ctx, "han-kang")["evidence"])

    def test_ambigua_com_duas_obras_casadas(self):
        self.web.works["Q17030180"] = [{"qid": "Q9", "labels": ["A Vegetariana"]}]
        r = run_identify(self.ctx, "han-kang")
        self.assertEqual((r["status"], r["id"]), ("ambiguous", None))
        self.assertEqual(self.ctx.catalog.authors["han-kang"]["references"], [])

    def test_provavel_e_ambigua_por_nome(self):
        self.web.works = {}
        r = run_identify(self.ctx, "han-kang")
        self.assertEqual((r["status"], r["id"]), ("probable", "Q5646626"))  # o médico não é escritor
        self.web.entities["Q17030180"] = eh.entity("Q17030180", "Han Kang", occupations=("Q49757",))
        ctx = eh.make_ctx(self.web)
        self.assertEqual(run_identify(ctx, "han-kang")["status"], "ambiguous")

    def test_nome_so_no_rotulo_mul(self):
        self.web.search["valter hugo mãe"] = ["Q2509574"]
        ent = eh.entity("Q2509574", "x", occupations=("Q36180",))
        ent["labels"] = {"mul": {"value": "valter hugo mãe"}}
        self.web.entities["Q2509574"] = ent
        self.ctx.catalog.authors["fulana-de-tal"]["name"] = "valter hugo mãe"
        r = run_identify(self.ctx, "fulana-de-tal")
        self.assertEqual((r["status"], r["id"]), ("probable", "Q2509574"))
        self.assertIn("mul", self.web.fake.calls[-2]["url"].split("languages=")[1])

    def test_nao_encontrada(self):
        self.assertEqual(run_identify(self.ctx, "fulana-de-tal")["status"], "not_found")

    def test_manual_e_none(self):
        self.ctx.author_wikidata = {"fulana-de-tal": {"id": "Q42"}, "itamar-vieira-junior": {"none": True}}
        self.assertEqual(run_identify(self.ctx, "fulana-de-tal")["status"], "manual")
        self.assertEqual(run_identify(self.ctx, "itamar-vieira-junior")["status"], "none")
        self.assertEqual(self.web.fake.count("wbsearchentities"), 0)


class CountryTest(unittest.TestCase):
    def setUp(self):
        self.web = eh.FakeWeb()
        self.ctx = eh.make_ctx(self.web)
        self.author = self.ctx.catalog.authors["itamar-vieira-junior"]
        self.author["wikidata"] = {"id": "Q1", "status": "confirmed", "evidence": "x", "rulesVersion": 1}

    def choose(self, **ent):
        self.web.entities["Q1"] = eh.entity("Q1", "Itamar", **ent)
        self.ctx.entity_cache.clear()
        self.ctx.http.refresh = True  # a mesma URL devolve uma entidade diferente em cada caso
        return country.choose_country(self.ctx, self.author)

    def test_uma_cidadania(self):
        self.assertEqual(self.choose(p27=("Q155",))[:2], ("BR", "wikidata-citizenship"))

    def test_varias_desempate_por_idioma(self):
        code, _, notes = self.choose(p27=("Q30", "Q45"))
        self.assertEqual(code, "PT")
        self.assertIn("entre vários", notes[0])

    def test_varias_desempate_por_nascimento_e_ordem(self):
        self.web.entities["Q999"] = eh.entity("Q999", "Salvador", human=False, p17=("Q45",))
        self.assertEqual(self.choose(p27=("Q155", "Q45"), p19="Q999")[0], "PT")
        self.assertEqual(self.choose(p27=("Q155", "Q45"))[0], "BR")

    def test_estado_extinto_e_cidadania_antiga(self):
        code, _, notes = self.choose(p27=("Q15180",))
        self.assertEqual(code, "RU")
        self.assertTrue(any("União Soviética" in n for n in notes))
        self.assertEqual(self.choose(p27=(("Q34266", 1700), "Q212"))[0], "UA")

    def test_nao_mapeado_e_nascimento(self):
        code, source, notes = self.choose(p27=("Q123456",))
        self.assertIsNone(code)
        self.assertTrue(any("não mapeado" in n for n in notes))
        self.web.entities["Q999"] = eh.entity("Q999", "Salvador", human=False, p17=("Q155",))
        self.assertEqual(self.choose(p19="Q999")[:2], ("BR", "wikidata-birthplace"))

    def test_override_e_sem_qid(self):
        self.ctx.overrides = {"itamar-vieira-junior": {"country": "PT"}}
        self.assertEqual(country.choose_country(self.ctx, self.author)[:2], ("PT", "override"))
        self.ctx.overrides = {}
        self.author["wikidata"] = None
        self.assertEqual(country.choose_country(self.ctx, self.author)[:2], (None, None))


class CountriesBuilderTest(unittest.TestCase):
    def test_build(self):
        web = eh.FakeWeb()
        web.fake.routes.insert(0, ("GET", "query.wikidata.org", {"results": {"bindings": [
            {"c": {"value": "http://www.wikidata.org/entity/Q155"}, "iso": {"value": "BR"},
             "label": {"value": "Brasil"}, "lang": {"value": "http://www.wikidata.org/entity/Q5146"}},
            {"c": {"value": "http://www.wikidata.org/entity/Q30"}, "iso": {"value": "US"},
             "label": {"value": "Estados Unidos da América"}, "lang": {"value": "http://www.wikidata.org/entity/Q1860"}},
            {"c": {"value": "http://www.wikidata.org/entity/Q999"}, "iso": {"value": "XYZ"}},
            {"c": {"value": "http://www.wikidata.org/entity/Q29999"}, "iso": {"value": "NL"},
             "label": {"value": "Reino dos Países Baixos"}},
            {"c": {"value": "http://www.wikidata.org/entity/Q55"}, "iso": {"value": "NL"},
             "label": {"value": "Países Baixos"}, "lang": {"value": "http://www.wikidata.org/entity/Q7411"}},
        ]}}))
        ctx = eh.make_ctx(web)
        data = build_countries(ctx, {"countries": {"US": {"name": "Estados Unidos"}}})
        self.assertEqual(data["countries"]["BR"], {"qid": "Q155", "name": "Brasil", "languages": ["português"]})
        self.assertEqual(data["countries"]["US"]["name"], "Estados Unidos")  # nome revisado vence
        self.assertNotIn("XYZ", data["countries"])
        self.assertEqual(data["defunct"]["Q15180"]["to"], "RU")
        self.assertEqual(data["countries"]["NL"], {"qid": "Q55", "name": "Países Baixos",
                                                   "languages": ["holandês"], "altQids": ["Q29999"]})
        ctx.countries = data
        self.assertEqual(__import__("lib.authors.country", fromlist=["x"]).map_country(ctx, "Q29999"), ("NL", None))


class PhotoTest(unittest.TestCase):
    def setUp(self):
        self.web = eh.FakeWeb().han_kang()
        self.tmp = Path(tempfile.mkdtemp())
        self.ctx = eh.make_ctx(self.web, tmp=self.tmp)
        run_identify(self.ctx, "han-kang")

    def test_commons_automatico(self):
        outcome, notes = photo.run(self.ctx, self.ctx.catalog.authors["han-kang"])
        p = self.ctx.catalog.authors["han-kang"]["photo"]
        self.assertEqual(outcome, "commons")
        self.assertEqual((p["file"], p["license"], p["author"], p["source"]),
                         ("authors/han-kang.png", "CC BY-SA 4.0", "Fotógrafa", "commons"))
        self.assertTrue((self.ctx.staging / "han-kang.png").is_file())

    def test_candidatas_sem_p18_na_ordem_e_sem_repetir(self):
        del self.web.entities["Q5646626"]["claims"]["P18"]
        self.ctx.entity_cache.clear()
        self.web.pageimages[("pt", "Han Kang")] = {"source": "https://img.test/wiki.png?utm_source=x",
                                                   "width": 800, "height": 1000}
        self.web.serp = [
            {"original": "https://img.test/wiki.png", "original_width": 800, "original_height": 1000},
            {"original": "https://img.test/serp.png", "original_width": 900, "original_height": 1200},
            {"original": "https://img.test/peq.png", "original_width": 100, "original_height": 100},
        ]
        self.web.tavily = {"results": [], "images": [{"url": "https://img.test/tav.png", "description": "Han"}]}
        outcome, _ = photo.run(self.ctx, self.ctx.catalog.authors["han-kang"])
        cands = self.ctx.author_state("han-kang")["photoCandidates"]
        self.assertEqual([c["url"] for c in cands],
                         ["https://img.test/wiki.png", "https://img.test/serp.png", "https://img.test/tav.png"])
        self.assertEqual(outcome, "3 candidata(s) para revisão")
        self.assertIsNone(self.ctx.catalog.authors["han-kang"]["photo"])
        self.assertFalse(PENDING["photo"](self.ctx, self.ctx.catalog.authors["han-kang"]))

    def test_commons_depois_de_identificada(self):
        author = self.ctx.catalog.authors["han-kang"]
        self.ctx.author_state("han-kang").update(photoCandidates=[{"url": f"https://img.test/{i}.png"} for i in range(3)],
                                                 photoTried=["serpapi", "tavily", "wikipedia"])
        self.assertTrue(PENDING["photo"](self.ctx, author))
        photo.run(self.ctx, author)
        self.assertEqual(author["photo"]["source"], "commons")

    def test_onda_1_nao_usa_cota(self):
        del self.web.entities["Q5646626"]["claims"]["P18"]
        ctx = eh.make_ctx(self.web, wave=1)
        run_identify(ctx, "han-kang")
        photo.run(ctx, ctx.catalog.authors["han-kang"])
        self.assertEqual(self.web.fake.count("serpapi.com/search") + self.web.fake.count("tavily.com/search"), 0)

    def test_escolha_manual_e_none(self):
        self.web.images["https://img.test/escolhida.png"] = helpers.tiny_png(500, 300)
        self.ctx.author_photos = {"han-kang": {"url": "https://img.test/escolhida.png", "source": "serpapi"}}
        outcome, warn = photo.run(self.ctx, self.ctx.catalog.authors["han-kang"])
        self.assertEqual(self.ctx.catalog.authors["han-kang"]["photo"]["source"], "serpapi")
        self.assertTrue(any("300px" in w for w in warn))
        self.ctx.author_photos = {"han-kang": {"none": True}}
        self.assertTrue(PENDING["photo"](self.ctx, self.ctx.catalog.authors["han-kang"]))
        photo.run(self.ctx, self.ctx.catalog.authors["han-kang"])
        self.assertIsNone(self.ctx.catalog.authors["han-kang"]["photo"])
        self.assertEqual([p.as_posix() for p in self.ctx.photos_to_delete], ["authors/han-kang.png"])

    def test_imagem_invalida_ou_pequena(self):
        self.web.images["https://img.test/han-kang-1200.png"] = helpers.tiny_png(150, 220)
        outcome, notes = photo.run(self.ctx, self.ctx.catalog.authors["han-kang"])
        self.assertIn("descartada", notes[0])  # Commons pequeno: vira nota e segue para candidatas
        self.assertIsNone(self.ctx.catalog.authors["han-kang"]["photo"])
        self.web.images["https://img.test/mini.png"] = helpers.tiny_png(150, 150)
        self.ctx.author_photos = {"han-kang": {"url": "https://img.test/mini.png"}}
        with self.assertRaises(photo.PhotoError):
            photo.run(self.ctx, self.ctx.catalog.authors["han-kang"])
        self.assertIsNone(self.ctx.catalog.authors["han-kang"]["photo"])


BIO_OK = {"insufficient": False, "source_index": 1,
          "text": "Han Kang é uma escritora sul-coreana. Sua prosa poética trata de violência, corpo e memória."}


class BioTest(unittest.TestCase):
    def setUp(self):
        self.web = eh.FakeWeb().han_kang()
        self.ctx = eh.make_ctx(self.web)
        run_identify(self.ctx, "han-kang")
        self.author = self.ctx.catalog.authors["han-kang"]

    def test_fonte_por_tamanho_e_bio_proposta(self):
        self.web.openai = [BIO_OK]
        outcome, _ = bio.run(self.ctx, self.author)
        item = summaries.get(self.ctx.catalog, "autoria:han-kang")
        self.assertEqual(outcome, "bio proposta (Wikipédia (en))")  # pt curta demais (111 < 300)
        self.assertEqual((item["sourceLanguage"], item["approved"], item["promptVersion"], item["model"]),
                         ("en", False, self.ctx.config["bio"]["promptVersion"], "gpt-teste"))
        body = self.web.fake.calls[-1]["body"]
        self.assertIn("Han Kang", body["instructions"])
        self.assertIn("[1] Wikipédia (en)", body["input"])
        self.assertAlmostEqual(self.ctx.budget.openai_usd, (1000 * 1.0 + 100 * 4.0) / 1e6)

    def test_fallback_mais_longa_e_tavily(self):
        self.ctx.config["minIntroChars"] = 5000
        self.assertEqual(bio.wikipedia_source(self.ctx, self.author)["language"], "en")
        self.ctx.config["minFallbackIntroChars"] = 5000
        self.web.tavily = {"results": [
            {"url": "https://a.org/1", "title": "Perfil", "content": "Han Kang nasceu em Gwangju e escreve romances."},
            {"url": "https://b.org/2", "title": "Outro", "content": "Texto sobre outra pessoa."},
        ], "images": [{"url": "https://img.test/t.png", "description": None}]}
        sources = bio.collect_sources(self.ctx, self.author)
        self.assertEqual([s["url"] for s in sources], ["https://a.org/1"])  # filtro pelo sobrenome
        self.assertEqual(self.ctx.author_state("han-kang")["tavilyImages"][0]["url"], "https://img.test/t.png")

    def test_insuficiente(self):
        self.web.openai = [{"insufficient": True, "text": "", "source_index": 0}]
        self.assertEqual(bio.run(self.ctx, self.author)[0], "fontes insuficientes")
        self.assertIsNone(summaries.get(self.ctx.catalog, "autoria:han-kang"))
        self.assertFalse(PENDING["bio"](self.ctx, self.author))

    def test_validacao_com_nova_tentativa(self):
        self.web.openai = [dict(BIO_OK, text="Curto."), BIO_OK]
        self.assertTrue(bio.run(self.ctx, self.author)[0].startswith("bio proposta"))
        self.assertIn("foi recusada", self.web.fake.calls[-1]["body"]["input"])
        web = eh.FakeWeb().han_kang()
        web.openai = [dict(BIO_OK, text="x" * 200), dict(BIO_OK, source_index=7)]
        ctx = eh.make_ctx(web)
        run_identify(ctx, "han-kang")
        with self.assertRaises(bio.BioError):
            bio.run(ctx, ctx.catalog.authors["han-kang"])

    def test_aprovada_rejeitada_e_regenerar(self):
        self.web.openai = [BIO_OK, BIO_OK]
        bio.run(self.ctx, self.author)
        self.assertFalse(PENDING["bio"](self.ctx, self.author))
        self.ctx.regenerate_prompt = self.ctx.config["bio"]["promptVersion"]
        self.assertTrue(PENDING["bio"](self.ctx, self.author))
        summaries.approve(self.ctx.catalog, "autoria:han-kang")
        self.ctx.regenerate = True
        self.assertFalse(PENDING["bio"](self.ctx, self.author))  # aprovada nunca
        self.ctx.catalog.summaries["summaries"] = []
        self.ctx.regenerate, self.ctx.regenerate_prompt = False, None
        self.ctx.rejections = ["autoria:han-kang"]
        self.assertFalse(PENDING["bio"](self.ctx, self.author))

    def test_wikipedia_de_novo_depois_de_identificada(self):
        state = self.ctx.author_state("han-kang")
        state.update(bioTried=["wikipedia"], bioWikipediaQid=None)  # tentada antes de ter QID
        self.assertTrue(PENDING["bio"](self.ctx, self.author))
        bio.collect_sources(self.ctx, self.author)
        self.assertEqual(state["bioWikipediaQid"], "Q5646626")

    def test_onda_1_so_coleta(self):
        ctx = eh.make_ctx(self.web, wave=1)
        run_identify(ctx, "han-kang")
        self.assertEqual(bio.run(ctx, ctx.catalog.authors["han-kang"])[0], "fonte coletada: Wikipédia (en)")
        self.assertEqual(self.web.fake.count("openai"), 0)

    def test_teto_openai(self):
        ctx = eh.make_ctx(self.web, budgets={"openai": {"maxUsdPerRun": 0.0}})
        run_identify(ctx, "han-kang")
        with self.assertRaises(BudgetExhausted):
            bio.run(ctx, ctx.catalog.authors["han-kang"])


class SelectionTest(unittest.TestCase):
    def test_prioridade_e_pendencias(self):
        ctx = eh.make_ctx(eh.FakeWeb())
        # han-kang: 2 leituras; itamar: 1 (ano corrente? não: 2025); fulana: 1 sem ano
        self.assertEqual(select(ctx), ["han-kang", "fulana-de-tal", "itamar-vieira-junior"])
        for a in ctx.catalog.authors.values():
            a["wikidata"] = {"id": None, "status": "none", "evidence": "x", "rulesVersion": 1}
        ctx.author_photos = {s: {"none": True} for s in ctx.catalog.authors}
        ctx.rejections = [f"autoria:{s}" for s in ctx.catalog.authors]
        self.assertEqual(select(ctx), [])
        self.assertEqual(select(ctx, only=["fulana-de-tal"]), ["fulana-de-tal"])
        with self.assertRaises(KeyError):
            select(ctx, only=["ninguem"])

    def test_nada_fica_pendente_para_sempre(self):
        ctx = eh.make_ctx(eh.FakeWeb(), wave=1)
        a = ctx.catalog.authors["fulana-de-tal"]
        a["wikidata"] = {"id": "Q1", "status": "confirmed", "evidence": "x", "rulesVersion": ctx.rules_version}
        st = ctx.author_state("fulana-de-tal")
        st.update(countryQid="Q1", photoCommonsQid="Q1", photoTried=["wikipedia"], bioTried=["wikipedia"])
        self.assertEqual([step for step in ctx.waves.steps if PENDING[step](ctx, a)], [])
        a["wikidata"]["id"] = "Q2"  # QID mudou: tenta país, Commons e verbete de novo
        self.assertEqual([step for step in ctx.waves.steps if PENDING[step](ctx, a)], ["country", "photo"])
        st["bioWikipediaQid"] = "Q1"
        self.assertTrue(PENDING["bio"](ctx, a))

    def test_rules_version_reabre_ambiguas(self):
        ctx = eh.make_ctx(eh.FakeWeb())
        a = ctx.catalog.authors["fulana-de-tal"]
        a["wikidata"] = {"id": None, "status": "ambiguous", "evidence": "x", "rulesVersion": ctx.rules_version}
        self.assertFalse(PENDING["identify"](ctx, a))
        ctx.config["rulesVersion"] = ctx.rules_version + 1
        self.assertTrue(PENDING["identify"](ctx, a))

    def test_ondas(self):
        ctx = eh.make_ctx(eh.FakeWeb(), wave=2)
        self.assertEqual(ctx.waves.steps, ["bio"])
        self.assertEqual(eh.make_ctx(eh.FakeWeb(), wave=1).waves.photo_sources, ["commons", "wikipedia"])
        self.assertEqual(eh.make_ctx(eh.FakeWeb(), wave=3).waves_providers(), ["serpapi", "tavily"])
        self.assertEqual(eh.make_ctx(eh.FakeWeb(), wave=1).waves_providers(), [])


if __name__ == "__main__":
    unittest.main()

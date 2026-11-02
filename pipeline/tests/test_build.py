import tempfile
import unittest
from pathlib import Path

import helpers
from lib.build import build, vocab_sort_key
from lib.checks import check_catalog, load_schemas
from lib.legacy_reader import LegacyDataError, read_legacy
from lib.slugs import SlugRegistry

OVERRIDES = {"valter hugo mae": {"name": "valter hugo mãe", "slug": "valter-hugo-mae"}}


def run_build(**kwargs):
    with tempfile.TemporaryDirectory() as tmp:
        legacy = read_legacy(helpers.write_legacy(Path(tmp), **kwargs))
    return build(legacy, SlugRegistry(), OVERRIDES)


class BuildTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run_build()
        cls.cat = cls.result.catalog

    def test_contagens(self):
        self.assertEqual(len(self.cat.works), 4)
        self.assertEqual(len(self.cat.authors), 4)  # Veríssimo unificado
        self.assertEqual(len(self.cat.readings["readings"]), 5)

    def test_modelo_valido(self):
        issues = check_catalog(self.cat, load_schemas(helpers.SCHEMA_DIR))
        self.assertEqual(issues, [])

    def test_unificacao(self):
        a = self.cat.authors["luis-fernando-verissimo"]
        self.assertEqual(a["name"], "Luís Fernando Veríssimo")
        self.assertEqual(a["aliases"], ["Luis Fernando Verissimo"])
        self.assertEqual(self.cat.works["comedias-para-se-ler-na-escola-luis-fernando-verissimo"]["authors"],
                         ["luis-fernando-verissimo"])
        self.assertEqual([g.name for g in self.result.unified], ["Luís Fernando Veríssimo"])

    def test_autoria_nula_na_f1(self):
        a = self.cat.authors["han-kang"]
        self.assertEqual((a["country"], a["countrySource"], a["wikidata"], a["photo"]), (None, None, None, None))
        self.assertNotIn("bio", a)
        self.assertEqual((a["languages"], a["primaryLanguage"]), (["coreano"], "coreano"))

    def test_romanizacao_e_capa(self):
        w = self.cat.works["a-vegetariana-han-kang"]
        self.assertEqual((w["originalTitle"], w["originalTitleRomanized"]), ("채식주의자", "Chaesikjuuija"))
        self.assertEqual(w["cover"], {"sourceUrl": "https://example.org/vegetariana.jpg", "source": "literal"})
        self.assertEqual(w["audit"]["sourceConflicts"], "Anos divergentes.")

    def test_ausencias_viram_null_ou_lista_vazia(self):
        w = self.cat.works["comedias-para-se-ler-na-escola-luis-fernando-verissimo"]
        self.assertIsNone(w["cover"])  # cover_source existe, mas sem URL
        self.assertIsNone(w["edition"]["format"])  # "desconhecido"
        self.assertIsNone(w["edition"]["isbn13"])
        self.assertIsNone(w["originalTitle"])
        self.assertEqual(w["references"], [])
        for value in (w["edition"]["isbn10"], w["audit"]["sourceConflicts"]):
            self.assertIsNone(value)

    def test_isbn_normalizado_e_lista_limpa(self):
        w = self.cat.works["belas-maldicoes-neil-gaiman"]
        self.assertEqual(w["edition"]["isbn10"], "852861234X")
        self.assertEqual(w["themes"], ["apocalipse", "amizade"])
        self.assertEqual(w["authors"], ["neil-gaiman", "terry-pratchett"])
        self.assertEqual(self.cat.works["os-espioes-luis-fernando-verissimo"]["edition"]["isbn13"],
                         "9788560281725")

    def test_referencias_sem_duplicatas(self):
        refs = self.cat.works["a-vegetariana-han-kang"]["references"]
        self.assertEqual([(r["provider"], r["id"], r["url"]) for r in refs], [
            ("openlibrary", "/works/OL1W", "https://openlibrary.org/works/OL1W"),
            ("web", None, "https://example.org/a"),
            ("web", None, "https://example.org/b"),
        ])
        lit = self.cat.works["os-espioes-luis-fernando-verissimo"]["references"]
        self.assertEqual([(r["id"], r["fields"]) for r in lit],
                         [("lit-book-1", "edição, ISBN, editora, capa"), ("lit-work-1", "obra")])

    def test_releitura_aponta_para_mesma_obra(self):
        rs = self.cat.readings["readings"]
        self.assertEqual([r["sequence"] for r in rs], [1, 2, 3, 4, 5])
        self.assertEqual(rs[0]["work"], rs[4]["work"])
        self.assertEqual((rs[0]["reread"], rs[4]["reread"]), (False, True))
        self.assertIsNone(rs[0]["notes"])

    def test_obra_sem_campos_de_leitura(self):
        for w in self.cat.works.values():
            self.assertFalse({"readings", "year", "sequence", "readingCount"} & set(w))

    def test_vocabularios_ordenados_sem_acento(self):
        self.assertEqual(self.cat.vocabularies["languages"], ["coreano", "inglês", "português"])
        themes = self.cat.vocabularies["themes"]
        self.assertEqual(themes, sorted(themes, key=vocab_sort_key))
        self.assertEqual(self.cat.summaries, {"summaries": []})
        self.assertEqual(self.cat.vocabularies["countries"], [])

    def test_ano_da_leitura(self):
        readings = [dict(r) for r in helpers.READINGS]
        readings[1]["read_year"] = "2014"
        cat = run_build(readings=readings).catalog
        self.assertEqual(cat.readings["readings"][1]["year"], 2014)

    def test_leitura_sem_obra_e_erro(self):
        readings = [dict(r) for r in helpers.READINGS] + [
            {"reading_sequence": "6", "work_id": "work-9999", "original_entry": "?"}]
        with self.assertRaises(LegacyDataError):
            run_build(readings=readings)

    def test_resumos_existentes_preservados(self):
        with tempfile.TemporaryDirectory() as tmp:
            legacy = read_legacy(helpers.write_legacy(Path(tmp)))
        existing = {"summaries": [helpers.summary("ano:2024")]}
        result = build(legacy, SlugRegistry(), OVERRIDES, existing)
        self.assertEqual(result.files["summaries.json"], existing)


class PreserveEnrichmentTest(unittest.TestCase):
    def test_preserva_campos_enriquecidos(self):
        first = run_build().catalog
        enriched = helpers.clone(first)
        han = enriched.authors["han-kang"]
        han.update(country="KR", countrySource="wikidata-citizenship",
                   wikidata={"id": "Q5646626", "status": "confirmed", "evidence": "P50", "rulesVersion": 1},
                   photo={"file": "authors/han-kang.jpg", "license": "CC BY-SA 4.0", "author": "X",
                          "sourceUrl": "https://commons.wikimedia.org/x", "source": "commons"},
                   references=[{"provider": "wikidata", "id": "Q5646626",
                                "url": "https://www.wikidata.org/wiki/Q5646626"}])
        enriched.vocabularies["countries"] = [{"code": "KR", "name": "Coreia do Sul", "languages": ["coreano"]}]
        with tempfile.TemporaryDirectory() as tmp:
            legacy = read_legacy(helpers.write_legacy(Path(tmp)))
        again = build(legacy, SlugRegistry(), OVERRIDES, None, enriched).catalog
        self.assertEqual(again.authors["han-kang"], han)
        self.assertEqual(again.vocabularies["countries"], enriched.vocabularies["countries"])
        self.assertIsNone(again.authors["neil-gaiman"]["country"])


if __name__ == "__main__":
    unittest.main()

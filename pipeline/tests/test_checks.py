import json
import tempfile
import unittest
from pathlib import Path

import helpers
from lib.checks import check_catalog, load_catalog, load_schemas
from lib.jsonio import dumps_canonical

HEAD = 1  # nos testes, só a leitura 1 é "sem ano"


class ChecksTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schemas = load_schemas(helpers.SCHEMA_DIR)

    def codes(self, cat):
        return [i.code for i in check_catalog(cat, self.schemas, undated_head=HEAD)]

    def test_catalogo_valido(self):
        self.assertEqual(self.codes(helpers.valid_catalog()), [])

    def test_schema(self):
        cat = helpers.valid_catalog()
        cat.works["obra-a"]["confidence"] = "altíssima"
        self.assertIn("schema", self.codes(cat))

    def test_file_slug_diferente(self):
        cat = helpers.valid_catalog()
        cat.works["obra-a"]["slug"] = "outra"
        self.assertIn("file.slug", self.codes(cat))

    def test_ref_reading_work(self):
        cat = helpers.valid_catalog()
        cat.readings["readings"][1]["work"] = "nao-existe"
        codes = self.codes(cat)
        self.assertIn("ref.reading-work", codes)
        self.assertIn("orphan.work", codes)  # obra-b ficou sem leitura

    def test_ref_work_author(self):
        cat = helpers.valid_catalog()
        cat.works["obra-a"]["authors"] = ["fantasma"]
        self.assertIn("ref.work-author", self.codes(cat))

    def test_orphan_author(self):
        cat = helpers.valid_catalog()
        cat.authors["sobrando"] = dict(cat.authors["autor-b"], slug="sobrando")
        self.assertEqual(self.codes(cat), ["orphan.author"])

    def test_seq_lacuna_e_repetida(self):
        cat = helpers.valid_catalog()
        cat.readings["readings"][2]["sequence"] = 4
        self.assertIn("seq.contiguous", self.codes(cat))
        cat = helpers.valid_catalog()
        cat.readings["readings"][2]["sequence"] = 2
        self.assertIn("seq.contiguous", self.codes(cat))

    def test_ano_decrescente(self):
        cat = helpers.valid_catalog()
        cat.readings["readings"][2]["year"] = 2013
        self.assertEqual(self.codes(cat), ["year.monotonic"])

    def test_cabeca_sem_ano(self):
        cat = helpers.valid_catalog()
        cat.readings["readings"][0]["year"] = 2010
        self.assertEqual(self.codes(cat), ["year.undated-head"])

    def test_releitura_fora_de_ordem(self):
        cat = helpers.valid_catalog()
        cat.readings["readings"][0]["reread"] = True
        cat.readings["readings"][2]["reread"] = False
        self.assertEqual(self.codes(cat), ["reread.order", "reread.order"])

    def test_vocab(self):
        cat = helpers.valid_catalog()
        cat.works["obra-a"]["themes"] = ["memória", "tema-novo"]
        cat.authors["autora-a"]["primaryLanguage"] = "klingon"
        self.assertEqual(self.codes(cat), ["vocab", "vocab"])

    def test_resumo_aprovado(self):
        base = {"text": "Texto.", "approved": True, "updatedAt": "2026-11-01", "source": None}
        cat = helpers.valid_catalog()
        cat.summaries["summaries"] = [
            dict(base, scope="autoria:autora-a"), dict(base, scope="ano:2014"), dict(base, scope="pais:BR"),
            dict(base, scope="ano:1999", approved=False, text=""),
        ]
        self.assertEqual(self.codes(cat), [])
        cat.summaries["summaries"] = [
            dict(base, scope="autoria:ninguem"), dict(base, scope="ano:1999"),
            dict(base, scope="pais:JP"), dict(base, scope="ano:2014", text="  "),
        ]
        self.assertEqual(self.codes(cat), ["summary.approved"] * 4)

    def test_varios_erros_todos_reportados(self):
        cat = helpers.valid_catalog()
        cat.works["obra-a"]["confidence"] = "x"
        cat.works["obra-b"]["authors"] = ["fantasma"]
        cat.readings["readings"][2]["year"] = 2000
        codes = self.codes(cat)
        for code in ("schema", "ref.work-author", "year.monotonic", "orphan.author"):
            self.assertIn(code, codes)


class LoadCatalogTest(unittest.TestCase):
    def test_carrega_do_disco_e_coleta_json_malformado(self):
        cat = helpers.valid_catalog()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for sub, items in (("works", cat.works), ("authors", cat.authors)):
                (root / sub).mkdir()
                for slug, data in items.items():
                    (root / sub / f"{slug}.json").write_text(dumps_canonical(data), encoding="utf-8")
            (root / "works" / "quebrada.json").write_text("{ não é json", encoding="utf-8")
            (root / "readings.json").write_text(json.dumps(cat.readings), encoding="utf-8")
            (root / "vocabularies.json").write_text(json.dumps(cat.vocabularies), encoding="utf-8")
            loaded = load_catalog(root)
        codes = [i.code for i in loaded.load_issues]
        self.assertEqual(sorted(codes), ["file.json", "file.missing"])  # quebrada + summaries ausente
        self.assertEqual(set(loaded.works), {"obra-a", "obra-b"})


if __name__ == "__main__":
    unittest.main()

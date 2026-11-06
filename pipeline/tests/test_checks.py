import json
import tempfile
import unittest
from pathlib import Path

import helpers
from lib.checks import check_catalog, load_catalog, load_schemas
from lib.jsonio import dumps_canonical

HEAD = 1  # nos testes, só a leitura 1 é "sem ano"


def themes_cfg():
    from lib.themes import ThemeConfig

    return ThemeConfig.from_dict({
        "version": 1, "targetSize": [1, 10], "taxonomy": ["família", "memória"],
        "map": {"memória": ["memória"], "tempo e memória": ["memória"],
                "família": ["família"], "Nova York": []},
    })


class ThemeChecksTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schemas = load_schemas(helpers.SCHEMA_DIR)

    def issues(self, cat, cfg="default"):
        cfg = themes_cfg() if cfg == "default" else cfg
        return check_catalog(cat, self.schemas, undated_head=HEAD, themes_cfg=cfg)

    def codes(self, cat, cfg="default"):
        return [i.code for i in self.issues(cat, cfg)]

    def test_catalogo_coerente_com_o_mapa(self):
        cat = helpers.valid_catalog()
        cat.works["obra-a"]["tags"] = ["tempo e memória", "Nova York"]
        self.assertEqual(self.codes(cat), [])

    def test_tema_de_obra_fora_da_taxonomia(self):
        cat = helpers.valid_catalog()
        cat.works["obra-a"]["themes"] = ["memória", "identidade"]
        cat.vocabularies["themes"] = ["identidade", "memória"]  # o vocabulário "concorda", o arquivo não
        self.assertEqual(self.codes(cat).count("theme.taxonomy"), 2)  # a obra e o vocabulário
        self.assertNotIn("vocab", self.codes(cat))

    def test_deriva_themes_diferente_do_mapa(self):
        cat = helpers.valid_catalog()
        cat.works["obra-a"]["tags"] = ["tempo e memória", "família"]   # mapa dá [memória, família]
        issues = [i for i in self.issues(cat) if i.code == "theme.drift"]
        self.assertEqual(len(issues), 1)
        self.assertIn("migrate_legacy.py", issues[0].message)

    def test_tag_sem_entrada_no_mapa_e_deriva(self):
        cat = helpers.valid_catalog()
        cat.works["obra-a"]["tags"] = ["memória", "tema que saiu do mapa"]
        issues = [i for i in self.issues(cat) if i.code == "theme.drift"]
        self.assertIn("tema que saiu do mapa", issues[0].message)

    def test_obra_sem_tags_nao_e_conferida_quanto_a_deriva(self):
        self.assertEqual(self.codes(helpers.valid_catalog()), [])

    def test_sem_configuracao_as_regras_sao_puladas(self):
        cat = helpers.valid_catalog()
        cat.works["obra-a"]["themes"] = ["memória", "identidade"]
        cat.vocabularies["themes"] = ["identidade", "memória"]
        cat.works["obra-a"]["tags"] = ["qualquer coisa"]
        self.assertEqual(self.codes(cat, cfg=None), [])


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
        s = helpers.summary
        cat = helpers.valid_catalog()
        cat.summaries["summaries"] = [
            s("autoria:autora-a", approved=True), s("ano:2014", approved=True), s("pais:BR", approved=True),
            s("ano:1999", text=""),
        ]
        self.assertEqual(self.codes(cat), [])
        cat.summaries["summaries"] = [
            s("autoria:ninguem", approved=True), s("ano:1999", approved=True),
            s("pais:JP", approved=True), s("ano:2015", text="  ", approved=True),
        ]
        self.assertEqual(self.codes(cat), ["summary.approved"] * 4)

    def test_escopo_unico(self):
        cat = helpers.valid_catalog()
        cat.summaries["summaries"] = [helpers.summary("ano:2014"), helpers.summary("ano:2014")]
        self.assertEqual(self.codes(cat), ["summary.scope-unique"])

    def test_pais_fora_do_vocabulario(self):
        cat = helpers.valid_catalog()
        cat.authors["autor-b"]["country"] = "JP"
        self.assertEqual(self.codes(cat), ["vocab.country"])

    def test_foto_inexistente(self):
        cat = helpers.valid_catalog()
        cat.authors["autora-a"]["photo"] = {"file": "authors/autora-a.jpg", "license": None, "author": None,
                                            "sourceUrl": "https://x.org/a.jpg", "source": "manual"}
        cat.media = set()
        self.assertEqual(self.codes(cat), ["photo.file"])
        cat.media = {"authors/autora-a.jpg"}
        self.assertEqual(self.codes(cat), [])

    def test_capa_inexistente(self):
        cat = helpers.valid_catalog()
        cat.works["obra-a"]["cover"] = {"sourceUrl": "https://x.org/a.jpg", "source": "openlibrary",
                                        "file": "covers/obra-a.jpg", "license": None, "credit": None,
                                        "focus": "top", "display": None}
        cat.media = set()
        self.assertEqual(self.codes(cat), ["cover.file"])
        cat.media = {"covers/obra-a.jpg"}
        self.assertEqual(self.codes(cat), [])

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


class ValidateThemesCliTest(unittest.TestCase):
    """validate_catalog procura themes.json em ../pipeline/config do catálogo."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.catalog = helpers.make_catalog_dir(self.root / "catalog")
        from lib.jsonio import write_catalog

        cat = helpers.valid_catalog()
        files = {f"works/{s}.json": w for s, w in cat.works.items()}
        files.update({f"authors/{s}.json": a for s, a in cat.authors.items()})
        files.update({"readings.json": cat.readings, "summaries.json": cat.summaries,
                      "vocabularies.json": cat.vocabularies})
        write_catalog(files, self.catalog)

    def tearDown(self):
        self.tmp.cleanup()

    def run_validate(self):
        import contextlib
        import io

        import validate_catalog
        from unittest import mock

        out, err = io.StringIO(), io.StringIO()
        with mock.patch("lib.checks.UNDATED_HEAD", HEAD), contextlib.redirect_stdout(out), \
                contextlib.redirect_stderr(err):
            code = validate_catalog.run(self.catalog, None)
        return code, out.getvalue() + err.getvalue()

    def write_config(self, text):
        config = self.root / "pipeline" / "config"
        config.mkdir(parents=True, exist_ok=True)
        (config / "themes.json").write_text(text, encoding="utf-8")

    def test_sem_themes_json_a_regra_e_pulada(self):
        self.assertEqual(self.run_validate()[0], 0)

    def test_com_themes_json_acusa_tema_fora_da_taxonomia(self):
        self.write_config(json.dumps({
            "version": 1, "targetSize": [1, 10], "taxonomy": ["família"],
            "map": {"família": ["família"]}}))
        code, out = self.run_validate()
        self.assertEqual(code, 1)
        self.assertIn("theme.taxonomy", out)

    def test_themes_json_invalido_codigo_1(self):
        self.write_config('{"version": 7}')
        code, out = self.run_validate()
        self.assertEqual(code, 1)
        self.assertIn("themes.json inválido", out)

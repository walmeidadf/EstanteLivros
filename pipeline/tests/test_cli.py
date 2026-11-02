"""Testes ponta a ponta das CLIs de migração e validação."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import helpers
import migrate_legacy
import validate_catalog


def quiet(fn, *args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = fn(*args)
    return code, out.getvalue(), err.getvalue()


class MigrateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.legacy = helpers.write_legacy(root / "legacy")
        self.catalog = helpers.make_catalog_dir(root / "catalog")
        self.config = root / "config"
        self.config.mkdir()
        (self.config / "author_overrides.json").write_text("{}", encoding="utf-8")
        self.report = root / "docs" / "cobertura.md"

    def tearDown(self):
        self.tmp.cleanup()

    def migrate(self, dry_run=False, legacy=None):
        return quiet(migrate_legacy.run, legacy or self.legacy, self.catalog, self.config,
                     self.report, dry_run)

    def test_migra_e_valida(self):
        code, out, err = self.migrate()
        self.assertEqual(code, 0, err)
        self.assertIn("obras: 4 · leituras: 5 · autorias: 4 (1 unificadas) · releituras: 1", out)
        self.assertEqual(len(list((self.catalog / "works").glob("*.json"))), 4)
        self.assertTrue(self.report.exists())
        slugs = json.loads((self.config / "slugs.json").read_text(encoding="utf-8"))
        self.assertEqual(slugs["works"]["work-0003"], "a-vegetariana-han-kang")
        code, out, _ = quiet(validate_catalog.run, self.catalog, None)
        self.assertEqual(code, 0, out)

    def test_idempotente_byte_a_byte(self):
        self.migrate()
        first = helpers.tree_bytes(self.catalog.parent)
        code, out, _ = self.migrate()
        self.assertEqual(code, 0)
        self.assertIn("reutilizados: 8", out)
        self.assertEqual(helpers.tree_bytes(self.catalog.parent), first)

    def test_preserva_enriquecimento_e_continua_idempotente(self):
        self.migrate()
        path = self.catalog / "authors" / "han-kang.json"
        author = json.loads(path.read_text(encoding="utf-8"))
        author.update(country="KR", countrySource="wikidata-citizenship",
                      photo={"file": "authors/han-kang.jpg", "license": None, "author": None,
                             "sourceUrl": "https://x.org/h.jpg", "source": "manual"})
        path.write_text(json.dumps(author, ensure_ascii=False), encoding="utf-8")
        vocab_path = self.catalog / "vocabularies.json"
        vocab = json.loads(vocab_path.read_text(encoding="utf-8"))
        vocab["countries"] = [{"code": "KR", "name": "Coreia do Sul", "languages": ["coreano"]}]
        vocab_path.write_text(json.dumps(vocab, ensure_ascii=False), encoding="utf-8")
        (self.catalog / "media" / "authors").mkdir(parents=True)
        (self.catalog / "media" / "authors" / "han-kang.jpg").write_bytes(b"\xff\xd8\xff")
        code, _, err = self.migrate()
        self.assertEqual(code, 0, err)
        again = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual((again["country"], again["photo"]["file"]), ("KR", "authors/han-kang.jpg"))
        first = helpers.tree_bytes(self.catalog.parent)
        self.migrate()
        self.assertEqual(helpers.tree_bytes(self.catalog.parent), first)

    def test_legado_nao_e_alterado(self):
        before = helpers.tree_bytes(self.legacy)
        self.migrate()
        self.assertEqual(helpers.tree_bytes(self.legacy), before)

    def test_dry_run_nao_grava(self):
        before = helpers.tree_bytes(self.catalog.parent)
        code, out, _ = self.migrate(dry_run=True)
        self.assertEqual(code, 0)
        self.assertIn("nada foi gravado", out)
        self.assertEqual(helpers.tree_bytes(self.catalog.parent), before)
        self.assertFalse((self.config / "slugs.json").exists())

    def test_coluna_ausente_codigo_2_catalogo_intacto(self):
        self.migrate()
        broken = helpers.write_legacy(Path(self.tmp.name) / "broken", drop_column="reread")
        before = helpers.tree_bytes(self.catalog.parent)
        code, _, err = self.migrate(legacy=broken)
        self.assertEqual(code, 2)
        self.assertIn("reread", err)
        self.assertEqual(helpers.tree_bytes(self.catalog.parent), before)

    def test_dado_invalido_codigo_1_nada_gravado(self):
        readings = [dict(r) for r in helpers.READINGS]
        readings[0]["read_year"] = "2020"  # leitura 1 com ano viola year.undated-head
        bad = helpers.write_legacy(Path(self.tmp.name) / "bad", readings=readings)
        before = helpers.tree_bytes(self.catalog.parent)
        code, _, err = self.migrate(legacy=bad)
        self.assertEqual(code, 1)
        self.assertIn("year.undated-head", err)
        self.assertEqual(helpers.tree_bytes(self.catalog.parent), before)


class ValidateCliTest(unittest.TestCase):
    def test_dois_erros_codigo_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalog = helpers.make_catalog_dir(root / "catalog")
            legacy = helpers.write_legacy(root / "legacy")
            config = root / "config"
            config.mkdir()
            quiet(migrate_legacy.run, legacy, catalog, config, None, False)
            work = catalog / "works" / "a-vegetariana-han-kang.json"
            data = json.loads(work.read_text(encoding="utf-8"))
            data["confidence"] = "x"
            data["authors"] = ["fantasma"]
            work.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            report = root / "cobertura.md"
            code, out, _ = quiet(validate_catalog.run, catalog, report)
            self.assertTrue(report.exists())
        self.assertEqual(code, 1)
        self.assertIn("  schema  ", out)
        self.assertIn("  ref.work-author  ", out)
        self.assertIn("orphan.author", out)  # han-kang ficou sem obra
        self.assertTrue(out.strip().endswith("3 erros"))


if __name__ == "__main__":
    unittest.main()

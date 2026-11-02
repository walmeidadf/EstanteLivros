import tempfile
import unittest
from pathlib import Path
from unittest import mock

import helpers  # noqa: F401
from lib import jsonio
from lib.jsonio import TMP_DIR_NAME, dumps_canonical, read_json, write_catalog


class DumpsTest(unittest.TestCase):
    def test_formato(self):
        self.assertEqual(dumps_canonical({"b": "ção", "a": [1]}),
                         '{\n  "b": "ção",\n  "a": [\n    1\n  ]\n}\n')


class WriteCatalogTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "schema").mkdir()
        (self.root / "schema" / "x.schema.json").write_text("{}", encoding="utf-8")
        (self.root / "source").mkdir()
        (self.root / "source" / "lista.txt").write_text("original", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def files(self, slug):
        return {f"works/{slug}.json": {"slug": slug}, "authors/a.json": {"slug": "a"},
                "readings.json": {"readings": []}}

    def test_grava_e_remove_orfao(self):
        write_catalog(self.files("velha"), self.root)
        self.assertEqual(read_json(self.root / "works" / "velha.json"), {"slug": "velha"})
        write_catalog(self.files("nova"), self.root)
        self.assertEqual([p.name for p in (self.root / "works").iterdir()], ["nova.json"])
        self.assertFalse((self.root / TMP_DIR_NAME).exists())

    def test_preserva_schema_e_source(self):
        write_catalog(self.files("x"), self.root)
        self.assertEqual((self.root / "source" / "lista.txt").read_text(encoding="utf-8"), "original")
        self.assertTrue((self.root / "schema" / "x.schema.json").exists())

    def test_falha_no_meio_deixa_catalogo_intacto(self):
        write_catalog(self.files("velha"), self.root)
        before = helpers.tree_bytes(self.root)
        with mock.patch.object(jsonio, "_swap", side_effect=OSError("disco cheio")):
            with self.assertRaises(OSError):
                write_catalog(self.files("nova"), self.root)
        self.assertEqual(helpers.tree_bytes(self.root), before)
        self.assertFalse((self.root / TMP_DIR_NAME).exists())

    def test_conteudo_nao_serializavel_nao_toca_catalogo(self):
        write_catalog(self.files("velha"), self.root)
        before = helpers.tree_bytes(self.root)
        with self.assertRaises(TypeError):
            write_catalog({"works/z.json": {"x": object()}}, self.root)
        self.assertEqual(helpers.tree_bytes(self.root), before)


if __name__ == "__main__":
    unittest.main()

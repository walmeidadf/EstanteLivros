import datetime as dt
import tempfile
import unittest
from pathlib import Path

import helpers
from lib import summaries
from lib.checks import check_catalog, load_schemas
from lib.summaries import SummaryError

DAY1 = lambda: dt.date(2026, 11, 2)  # noqa: E731
DAY2 = lambda: dt.date(2026, 11, 5)  # noqa: E731


class SummariesTest(unittest.TestCase):
    def setUp(self):
        self.cat = helpers.valid_catalog()

    def test_upsert_ordena_e_valida(self):
        summaries.upsert(self.cat, "autoria:autor-b", "B.", DAY1, source="Wikipédia (pt)")
        summaries.upsert(self.cat, "autoria:autora-a", "A.", DAY1, promptVersion="author-bio-v1")
        scopes = [s["scope"] for s in self.cat.summaries["summaries"]]
        self.assertEqual(scopes, ["autoria:autor-b", "autoria:autora-a"])
        self.assertEqual(check_catalog(self.cat, load_schemas(helpers.SCHEMA_DIR), undated_head=1), [])
        item = summaries.get(self.cat, "autoria:autora-a")
        self.assertEqual((item["approved"], item["updatedAt"], item["promptVersion"]), (False, "2026-11-02", "author-bio-v1"))

    def test_upsert_sem_mudanca_preserva_data(self):
        summaries.upsert(self.cat, "ano:2014", "X.", DAY1, model="m")
        summaries.upsert(self.cat, "ano:2014", "X.", DAY2, model="m")
        self.assertEqual(summaries.get(self.cat, "ano:2014")["updatedAt"], "2026-11-02")
        summaries.upsert(self.cat, "ano:2014", "Y.", DAY2, model="m")
        self.assertEqual(summaries.get(self.cat, "ano:2014")["updatedAt"], "2026-11-05")
        self.assertEqual(len(self.cat.summaries["summaries"]), 1)

    def test_aprovado_nao_e_sobrescrito(self):
        summaries.upsert(self.cat, "ano:2014", "X.", DAY1)
        summaries.approve(self.cat, "ano:2014")
        with self.assertRaises(SummaryError):
            summaries.upsert(self.cat, "ano:2014", "Outro.", DAY2)

    def test_editar_marca_humano_e_desaprova(self):
        summaries.upsert(self.cat, "ano:2014", "X.", DAY1)
        summaries.approve(self.cat, "ano:2014")
        item = summaries.edit(self.cat, "ano:2014", " Novo texto. ", DAY2)
        self.assertEqual((item["text"], item["editedBy"], item["approved"]), ("Novo texto.", "human", False))
        with self.assertRaises(SummaryError):
            summaries.edit(self.cat, "ano:2014", "  ")

    def test_rejeitar_registra(self):
        summaries.upsert(self.cat, "ano:2014", "X.", DAY1)
        rejections = []
        summaries.reject(self.cat, "ano:2014", rejections)
        self.assertIsNone(summaries.get(self.cat, "ano:2014"))
        self.assertEqual(rejections, ["ano:2014"])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rej.json"
            summaries.save_rejections(path, rejections + ["ano:2014"])
            self.assertEqual(summaries.load_rejections(path), ["ano:2014"])

    def test_aprovar_inexistente_ou_vazio(self):
        with self.assertRaises(SummaryError):
            summaries.approve(self.cat, "ano:2099")
        summaries.upsert(self.cat, "ano:2014", "", DAY1)
        with self.assertRaises(SummaryError):
            summaries.approve(self.cat, "ano:2014")


if __name__ == "__main__":
    unittest.main()

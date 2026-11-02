import unittest

import helpers
from lib.coverage import author_rows, render_coverage, work_rows


class CoverageTest(unittest.TestCase):
    def setUp(self):
        self.cat = helpers.valid_catalog()
        a = self.cat.works["obra-a"]
        a.update(language="coreano", originalTitle="채식주의자", originalTitleRomanized=None,
                 cover={"sourceUrl": "https://x.org/c.jpg", "source": "literal"})
        self.cat.authors["autora-a"]["aliases"] = ["autora a"]

    def test_denominadores(self):
        rows = {name: (filled, total) for name, filled, total in work_rows(list(self.cat.works.values()))}
        self.assertEqual(rows["Capa"], (1, 2))
        self.assertEqual(rows["Título original (obras não escritas em português)"], (1, 1))
        self.assertEqual(rows["Romanização (títulos originais não latinos)"], (0, 1))
        authors = {name: (f, t) for name, f, t in author_rows(list(self.cat.authors.values()))}
        self.assertEqual(authors["País"], (2, 2))
        self.assertEqual(authors["Bio aprovada"], (0, 2))
        self.assertEqual(authors["Foto"], (0, 2))

    def test_bios_status_e_orfas(self):
        self.cat.summaries["summaries"] = [helpers.summary("autoria:autora-a", approved=True)]
        self.cat.authors["autor-b"]["wikidata"] = {"id": None, "status": "ambiguous", "evidence": "x", "rulesVersion": 1}
        self.cat.media = {"authors/sobrou.jpg"}
        text = render_coverage(self.cat)
        self.assertIn("| Bio aprovada | 1 | 2 | 50,0% |", text)
        self.assertIn("| ambígua | 1 |", text)
        self.assertIn("- Autor B (`autor-b`)", text)
        self.assertIn("`authors/sobrou.jpg`", text)

    def test_conteudo_e_determinismo(self):
        text = render_coverage(self.cat)
        self.assertEqual(text, render_coverage(helpers.clone(self.cat)))
        self.assertIn("| Capa | 1 | 2 | 50,0% |", text)
        self.assertIn("- Autora A ← autora a", text)
        self.assertIn("| Releituras | 1 |", text)
        self.assertNotIn("2026-", text)  # sem data de execução


if __name__ == "__main__":
    unittest.main()

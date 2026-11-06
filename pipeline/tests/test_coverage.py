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
        self.assertEqual(rows["Capa com URL de origem"], (1, 2))
        self.assertEqual(rows["Capa local escolhida (mestre em `catalog/media/covers/`)"], (0, 2))
        self.assertEqual(rows["Capa revisada: fica a tipográfica"], (0, 2))
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

    def test_secao_de_temas(self):
        self.cat.works["obra-a"]["tags"] = ["tempo e memória", "Nova York"]
        text = render_coverage(self.cat)
        self.assertIn("## Temas", text)
        self.assertIn("| Temas em uso | 1 |", text)
        self.assertIn("| Média de temas por obra | 1,00 |", text)
        self.assertIn("| Obras com um único tema | 2 |", text)
        self.assertIn("| Tags (temas originais guardados) | 2 |", text)
        self.assertIn("| memória | 2 |", text)
        self.assertIn("### Temas abaixo do piso (5 obras)", text)
        self.assertIn("- memória (2)", text)
        self.assertLess(text.index("## Autorias"), text.index("## Temas"))
        self.assertLess(text.index("## Temas"), text.index("## Autorias unificadas"))

    def test_conteudo_e_determinismo(self):
        text = render_coverage(self.cat)
        self.assertEqual(text, render_coverage(helpers.clone(self.cat)))
        self.assertIn("| Capa com URL de origem | 1 | 2 | 50,0% |", text)
        self.assertIn("- Autora A ← autora a", text)
        self.assertIn("| Releituras | 1 |", text)
        self.assertNotIn("2026-", text)  # sem data de execução


if __name__ == "__main__":
    unittest.main()

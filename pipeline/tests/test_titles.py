import unittest

import helpers  # noqa: F401
from lib.titles import has_non_latin, split_original

REAL_CASES = {
    "スプートニクの恋人 (Supūtoniku no Koibito)": ("スプートニクの恋人", "Supūtoniku no Koibito"),
    "卍 (Manji)": ("卍", "Manji"),
    "종의 기원 (Jong-ui Giwon)": ("종의 기원", "Jong-ui Giwon"),
    "채식주의자 (Chaesikjuuija)": ("채식주의자", "Chaesikjuuija"),
    "딸에 대하여 (Ttal-e Daehayeo)": ("딸에 대하여", "Ttal-e Daehayeo"),
    "ער (Er)": ("ער", "Er"),
    "つぐみ (Tsugumi)": ("つぐみ", "Tsugumi"),
    "キッチン (Kitchin)": ("キッチン", "Kitchin"),
}


class SplitOriginalTest(unittest.TestCase):
    def test_oito_casos_reais(self):
        for raw, expected in REAL_CASES.items():
            with self.subTest(raw=raw):
                self.assertEqual(split_original(raw), expected)

    def test_cirilico_sem_parenteses(self):
        self.assertEqual(split_original("Мастер и Маргарита"), ("Мастер и Маргарита", None))

    def test_latino_com_parenteses_intacto(self):
        self.assertEqual(split_original("Pedro Páramo (edición crítica)"),
                         ("Pedro Páramo (edición crítica)", None))

    def test_vazio_e_none(self):
        self.assertEqual(split_original(""), (None, None))
        self.assertEqual(split_original("   "), (None, None))
        self.assertEqual(split_original(None), (None, None))

    def test_has_non_latin(self):
        self.assertFalse(has_non_latin("Ærø, Łódź, Nguyễn"))
        self.assertTrue(has_non_latin("abc ש"))


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from pathlib import Path

import helpers  # noqa: F401  (ajusta sys.path)
from lib.slugs import MAX_SLUG_LENGTH, SlugRegistry, slugify, truncate


class SlugifyTest(unittest.TestCase):
    def test_remove_acentos_e_caixa(self):
        self.assertEqual(slugify("Érico Veríssimo"), "erico-verissimo")

    def test_pontuacao_vira_um_hifen(self):
        self.assertEqual(slugify("  Cem anos — de solidão!?  "), "cem-anos-de-solidao")

    def test_cedilha_e_til(self):
        self.assertEqual(slugify("Coração, Cabeça e Estômago"), "coracao-cabeca-e-estomago")

    def test_nao_latino_some(self):
        self.assertEqual(slugify("채식주의자"), "")
        self.assertEqual(slugify("Мастер и Маргарита 1967"), "1967")


class TruncateTest(unittest.TestCase):
    def test_curto_intacto(self):
        self.assertEqual(truncate("a-b-c", 80), "a-b-c")

    def test_corta_no_ultimo_hifen(self):
        self.assertEqual(truncate("abc-def-ghi", 9), "abc-def")

    def test_corte_exato_em_hifen(self):
        self.assertEqual(truncate("abc-def-ghi", 7), "abc-def")

    def test_sem_hifen_corte_seco(self):
        self.assertEqual(truncate("abcdefghij", 4), "abcd")

    def test_caso_real_longo(self):
        title = "Emburrecimento Programado: O Currículo Oculto da Escolarização Obrigatória John Taylor Gatto"
        slug = truncate(slugify(title))
        self.assertLessEqual(len(slug), MAX_SLUG_LENGTH)
        self.assertFalse(slug.endswith("-"))
        self.assertTrue(slugify(title).startswith(slug))


class RegistryTest(unittest.TestCase):
    def test_desempate_por_ano_depois_sufixo(self):
        reg = SlugRegistry()
        self.assertEqual(reg.work_slug("w1", "Obra Autora", 1990), "obra-autora")
        self.assertEqual(reg.work_slug("w2", "Obra Autora", 2001), "obra-autora-2001")
        self.assertEqual(reg.work_slug("w3", "Obra Autora", 2001), "obra-autora-2001-2")
        self.assertEqual(reg.work_slug("w4", "Obra Autora", None), "obra-autora-2")

    def test_reuso_mesmo_com_titulo_alterado(self):
        reg = SlugRegistry(works={"w1": "titulo-antigo-autora"})
        self.assertEqual(reg.work_slug("w1", "Título Novo Autora", 2000), "titulo-antigo-autora")
        self.assertEqual(reg.reused, 1)
        self.assertEqual(reg.created, 0)

    def test_slug_novo_nao_rouba_antigo(self):
        reg = SlugRegistry(works={"w-velho": "obra-autora"})
        self.assertEqual(reg.work_slug("w-novo", "Obra Autora", 2020), "obra-autora-2020")

    def test_autoria_forcada_vence_mapa(self):
        reg = SlugRegistry(authors={"valter hugo mae": "valter-hugo-mae-antigo"})
        self.assertEqual(reg.author_slug("valter hugo mae", "x", forced="valter-hugo-mae"), "valter-hugo-mae")

    def test_salva_e_carrega(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config" / "slugs.json"
            reg = SlugRegistry()
            reg.work_slug("w2", "B", None)
            reg.work_slug("w1", "A", None)
            reg.author_slug("fulana", "Fulana")
            reg.save(path)
            loaded = SlugRegistry.load(path)
            self.assertEqual(loaded.works, {"w1": "a", "w2": "b"})
            self.assertEqual(list(loaded.to_json()["works"]), ["w1", "w2"])
            self.assertEqual(loaded.authors, {"fulana": "fulana"})

    def test_mapa_ausente_e_vazio(self):
        reg = SlugRegistry.load(Path("/nao/existe/slugs.json"))
        self.assertEqual(reg.works, {})


if __name__ == "__main__":
    unittest.main()

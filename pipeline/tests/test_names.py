import unittest

import helpers  # noqa: F401
from lib.names import AuthorGroup, choose_canonical, find_suspects, group_names, languages_for, unify_key

OVERRIDES = {"valter hugo mae": {"name": "valter hugo mãe", "slug": "valter-hugo-mae"}}


class UnifyTest(unittest.TestCase):
    def test_chave(self):
        self.assertEqual(unify_key("  Érico   Veríssimo "), "erico verissimo")

    def test_tres_casos_reais(self):
        counts = {
            "Luís Fernando Veríssimo": 2, "Luis Fernando Verissimo": 1,
            "Érico Veríssimo": 1, "Erico Veríssimo": 3,
            "valter hugo mãe": 1, "Valter Hugo Mãe": 1,
        }
        groups = group_names(counts, OVERRIDES)
        self.assertEqual(len(groups), 3)
        self.assertEqual(groups["luis fernando verissimo"].name, "Luís Fernando Veríssimo")
        self.assertEqual(groups["luis fernando verissimo"].aliases, ["Luis Fernando Verissimo"])
        # mais acentos vence frequência
        self.assertEqual(groups["erico verissimo"].name, "Érico Veríssimo")
        # exceção vence a regra (que escolheria a forma com maiúsculas)
        vhm = groups["valter hugo mae"]
        self.assertEqual(vhm.name, "valter hugo mãe")
        self.assertEqual(vhm.aliases, ["Valter Hugo Mãe"])
        self.assertEqual(vhm.forced_slug, "valter-hugo-mae")
        self.assertTrue(vhm.overridden)

    def test_sem_override_maiusculas_vencem(self):
        groups = group_names({"valter hugo mãe": 5, "Valter Hugo Mãe": 1})
        self.assertEqual(groups["valter hugo mae"].name, "Valter Hugo Mãe")


class CanonicalTest(unittest.TestCase):
    def test_particulas_nao_contam(self):
        self.assertEqual(choose_canonical({"Machado de Assis": 1, "machado de assis": 9}), "Machado de Assis")

    def test_frequencia_desempata(self):
        self.assertEqual(choose_canonical({"Jose Saramago": 1, "JOSE SARAMAGO": 3}), "JOSE SARAMAGO")

    def test_alfabetica_ultimo_desempate(self):
        self.assertEqual(choose_canonical({"Ana B": 1, "Ana A": 1}), "Ana A")


class LanguagesTest(unittest.TestCase):
    def test_frequencia(self):
        self.assertEqual(languages_for([("inglês", 10), ("português", 1), ("inglês", 20)]),
                         ["inglês", "português"])

    def test_empate_menor_sequence(self):
        self.assertEqual(languages_for([("francês", 30), ("espanhol", 12)]), ["espanhol", "francês"])

    def test_vazio(self):
        self.assertEqual(languages_for([]), [])


class SuspectsTest(unittest.TestCase):
    def test_luiz_e_luis_viram_suspeita_sem_unificar(self):
        groups = group_names({"Luiz Fernando Veríssimo": 1, "Luís Fernando Veríssimo": 1})
        self.assertEqual(len(groups), 2)
        self.assertEqual(find_suspects(groups.values()),
                         [("Luís Fernando Veríssimo", "Luiz Fernando Veríssimo")])

    def test_sobrenome_diferente_nao_e_suspeita(self):
        groups = [AuthorGroup("ana silva", "Ana Silva"), AuthorGroup("ana souza", "Ana Souza")]
        self.assertEqual(find_suspects(groups), [])


if __name__ == "__main__":
    unittest.main()

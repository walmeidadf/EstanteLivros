"""Temas canônicos: carga/validação do themes.json, aplicação do mapa e resumo."""

import json
import tempfile
import unittest
from pathlib import Path

import helpers  # noqa: F401  (ajusta o sys.path para o pipeline)
from lib import themes
from lib.themes import Applied, ThemeConfig, ThemeConfigError, apply, slugify_theme, theme_key


def config_dict(**over):
    data = {
        "version": 1,
        "targetSize": [1, 10],
        "taxonomy": ["família", "memória", "violência"],
        "map": {
            "família": ["família"],
            "memória": ["memória"],
            "tempo e memória": ["memória"],
            "violência doméstica": ["violência", "família"],
            "violência": ["violência"],
            "Nova York": [],
            "nordeste": [],
        },
    }
    data.update(over)
    return data


def load(**over) -> ThemeConfig:
    return ThemeConfig.from_dict(config_dict(**over))


class ChavesTest(unittest.TestCase):
    def test_chave_ignora_caixa_acento_e_espacos(self):
        self.assertEqual(theme_key("  Segunda  Guerra Mundial "), theme_key("segunda guerra mundial"))
        self.assertEqual(theme_key("Memória"), theme_key("memoria"))

    def test_slug_espelha_o_do_app(self):
        self.assertEqual(slugify_theme("Segunda Guerra Mundial"), "segunda-guerra-mundial")
        self.assertEqual(slugify_theme("condição feminina"), "condicao-feminina")
        self.assertEqual(slugify_theme("  --Nova York!  "), "nova-york")


class ApplyTest(unittest.TestCase):
    def setUp(self):
        self.cfg = load()

    def test_uniao_ordenada_sem_repeticao(self):
        out = apply(["tempo e memória", "memória", "família"], self.cfg)
        self.assertEqual(out.themes, ["memória", "família"])
        self.assertEqual(out.unmapped, [])

    def test_um_original_para_varios_destinos(self):
        out = apply(["violência doméstica"], self.cfg)
        self.assertEqual(out.themes, ["violência", "família"])

    def test_so_tag_nao_vira_tema_mas_fica_nas_tags(self):
        out = apply(["memória", "Nova York"], self.cfg)
        self.assertEqual(out.themes, ["memória"])
        self.assertEqual(out.tags, ["memória", "Nova York"])

    def test_variantes_de_caixa_e_acento_compartilham_a_entrada(self):
        out = apply(["Nordeste", "MEMORIA"], self.cfg)
        self.assertEqual(out.unmapped, [])
        self.assertEqual(out.themes, ["memória"])

    def test_tags_sem_perda_uma_por_chave_na_ordem_do_csv(self):
        out = apply(["Tempo e Memória", "tempo e memória", "Nova York", "família"], self.cfg)
        self.assertEqual(out.tags, ["Tempo e Memória", "Nova York", "família"])  # grafia do CSV

    def test_original_sem_entrada_e_listado_e_nao_derruba_os_outros(self):
        out = apply(["memória", "tema inventado"], self.cfg)
        self.assertEqual(out, Applied(["memória"], ["memória", "tema inventado"], ["tema inventado"]))

    def test_sem_originais(self):
        self.assertEqual(apply([], self.cfg), Applied([], [], []))

    def test_independe_de_estado_anterior(self):
        raw = ["tempo e memória", "violência doméstica"]
        self.assertEqual(apply(raw, self.cfg), apply(list(raw), load()))


class ValidacaoTest(unittest.TestCase):
    def assertInvalid(self, fragment, **over):
        with self.assertRaises(ThemeConfigError) as ctx:
            load(**over)
        self.assertIn(fragment, str(ctx.exception))

    def test_destino_fora_da_taxonomia(self):
        data = config_dict()
        data["map"]["Nova York"] = ["cidades"]
        with self.assertRaises(ThemeConfigError) as ctx:
            ThemeConfig.from_dict(data)
        self.assertIn("'cidades', que não está na taxonomia", str(ctx.exception))

    def test_taxonomia_sem_uso(self):
        self.assertInvalid("'luto' não é destino de nenhum original",
                           taxonomy=["família", "memória", "violência", "luto"])

    def test_chaves_do_mapa_repetidas_pela_chave_de_comparacao(self):
        data = config_dict()
        data["map"]["Memoria"] = ["memória"]
        with self.assertRaises(ThemeConfigError) as ctx:
            ThemeConfig.from_dict(data)
        self.assertIn("original repetido no mapa", str(ctx.exception))

    def test_taxonomia_repetida_e_slug_colidindo(self):
        self.assertInvalid("tema canônico repetido", taxonomy=["família", "familia", "memória", "violência"])
        self.assertInvalid("slug repetido em /tema/ex-ilio", taxonomy=["ex ilio", "ex-ilio", "memória", "família", "violência"])

    def test_fora_do_target_size(self):
        self.assertInvalid("tem 3 temas; o esperado é 40 a 60", targetSize=[40, 60])

    def test_tema_canonico_deve_ser_minusculo(self):
        self.assertInvalid("deve estar em minúsculas",
                           taxonomy=["Família", "memória", "violência"])

    def test_formato_basico(self):
        self.assertInvalid("version deve ser 1", version=2)
        self.assertInvalid("targetSize", targetSize=[10, 1])
        self.assertInvalid("map deve ser um objeto", map=[])

    def test_destino_repetido_na_mesma_entrada(self):
        data = config_dict()
        data["map"]["violência doméstica"] = ["violência", "violência"]
        with self.assertRaises(ThemeConfigError) as ctx:
            ThemeConfig.from_dict(data)
        self.assertIn("repete um destino", str(ctx.exception))

    def test_arquivo_ausente_e_json_quebrado(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "themes.json"
            with self.assertRaisesRegex(ThemeConfigError, "não existe"):
                ThemeConfig.load(path)
            path.write_text("{ quebrado", encoding="utf-8")
            with self.assertRaisesRegex(ThemeConfigError, "ilegível"):
                ThemeConfig.load(path)
            path.write_text(json.dumps(config_dict()), encoding="utf-8")
            self.assertEqual(ThemeConfig.load(path).taxonomy, ["família", "memória", "violência"])


class ResumoTest(unittest.TestCase):
    def test_contagens_e_piso(self):
        works = [{"themes": ["memória", "família"], "tags": ["a", "B"]} for _ in range(5)]
        works.append({"themes": ["violência"], "tags": ["c", "b"]})
        s = themes.summarize(works)
        self.assertEqual((s.canonical, s.single_theme_works), (3, 1))
        self.assertEqual(s.below_floor, [("violência", 1)])
        self.assertEqual(s.avg_per_work, 1.83)
        self.assertEqual((s.tags, s.originals), (12, 3))  # a, b, c (B e b são o mesmo original)


if __name__ == "__main__":
    unittest.main()

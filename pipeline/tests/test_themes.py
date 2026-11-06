"""Temas canônicos: carga/validação do themes.json, aplicação do mapa e resumo."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import helpers  # noqa: F401  (ajusta o sys.path para o pipeline)
from lib import themes
from lib.build import ThemeMappingError, build
from lib.legacy_reader import LegacyDataError, read_legacy, split_list
from lib.slugs import SlugRegistry
from lib.themes_review import ReviewWork, render_review
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


OVERRIDES = {"valter hugo mae": {"name": "valter hugo mãe", "slug": "valter-hugo-mae"}}


def run_build(cfg=None, existing=None, **legacy_kwargs):
    with tempfile.TemporaryDirectory() as tmp:
        legacy = read_legacy(helpers.write_legacy(Path(tmp), **legacy_kwargs))
    return build(legacy, SlugRegistry(), OVERRIDES, None, existing, cfg)


class BuildComTemasTest(unittest.TestCase):
    def test_sem_configuracao_o_comportamento_antigo(self):
        cat = run_build().catalog
        self.assertEqual(cat.works["a-vegetariana-han-kang"]["themes"], ["corpo", "família", "violência"])
        self.assertTrue(all("tags" not in w for w in cat.works.values()))

    def test_themes_canonicos_e_tags_sem_perda(self):
        cat = run_build(helpers.themes_config()).catalog
        veg = cat.works["a-vegetariana-han-kang"]
        self.assertEqual(veg["themes"], ["corpo", "violência"])             # "família" é só tag
        self.assertEqual(veg["tags"], ["corpo", "família", "violência"])    # ordem e grafia do CSV
        espioes = cat.works["os-espioes-luis-fernando-verissimo"]
        self.assertEqual((espioes["themes"], espioes["tags"]), (["identidade"], ["identidade", "segredo"]))
        belas = cat.works["belas-maldicoes-neil-gaiman"]
        self.assertEqual((belas["themes"], belas["tags"]), (["fim do mundo", "amizade"], ["apocalipse", "amizade"]))
        self.assertEqual(list(veg)[list(veg).index("themes") + 1], "tags")   # tags logo depois de themes

    def test_vocabulario_sao_os_canonicos_em_uso_em_ordem_alfabetica(self):
        cat = run_build(helpers.themes_config()).catalog
        self.assertEqual(cat.vocabularies["themes"],
                         ["amizade", "corpo", "escola", "fim do mundo", "identidade", "violência"])

    def test_resultado_nao_depende_de_themes_anterior(self):
        first = run_build(helpers.themes_config()).catalog
        stale = helpers.clone(first)
        for work in stale.works.values():
            work["themes"] = ["lixo"]
            work["tags"] = ["lixo"]
        again = run_build(helpers.themes_config(), existing=stale).catalog
        self.assertEqual(again.works, first.works)
        self.assertEqual(again.vocabularies, first.vocabularies)

    def test_erro_acumula_temas_sem_mapeamento_e_obras_sem_tema(self):
        cfg = helpers.themes_config()
        del cfg.mapping[theme_key("segredo")]
        del cfg.mapping[theme_key("escola")]
        for original in ("apocalipse", "amizade"):
            cfg.mapping[theme_key(original)] = []          # Belas Maldições ficaria sem tema
        with self.assertRaises(ThemeMappingError) as ctx:
            run_build(cfg)
        message = str(ctx.exception)
        self.assertIn("2 tema(s) sem mapeamento", message)
        self.assertIn("'escola' (Comédias para se Ler na Escola)", message)
        self.assertIn("'segredo' (Os Espiões)", message)
        self.assertIn("1 obra(s) ficariam sem tema canônico", message)
        self.assertIn("Belas Maldições: apocalipse, amizade", message)
        self.assertIsInstance(ctx.exception, LegacyDataError)  # a migração já trata como código 1

    def test_obra_sem_nenhum_tema_no_csv_tambem_e_erro(self):
        works = [dict(w) for w in helpers.WORKS]
        works[3]["themes"] = ""
        with self.assertRaisesRegex(ThemeMappingError, "Belas Maldições: \\(sem temas no CSV\\)"):
            run_build(helpers.themes_config(), works=works)

    def test_determinismo(self):
        a = run_build(helpers.themes_config()).files
        b = run_build(helpers.themes_config()).files
        self.assertEqual(json.dumps(a, sort_keys=False), json.dumps(b, sort_keys=False))


def review_works():
    return [ReviewWork(f"{w['title_pt_br']} ({split_list(w['authors'])[0]})", split_list(w["themes"]))
            for w in sorted(helpers.WORKS, key=lambda w: w["work_id"])]


class RevisaoTest(unittest.TestCase):
    def setUp(self):
        self.cfg = helpers.themes_config()

    def test_cobre_todos_os_originais_e_e_deterministico(self):
        text = render_review(review_works(), self.cfg)
        self.assertEqual(text, render_review(review_works(), helpers.themes_config()))
        for original in ("apocalipse", "amizade", "segredo", "família", "violência", "escola", "corpo", "identidade"):
            self.assertIn(original, text)
        self.assertIn("4 obras · 8 temas originais · 6 temas canônicos (alvo 1 a 10) · 6 abaixo do piso de 5 obras.", text)
        self.assertNotIn("## Pendências", text)

    def test_bloco_por_tema_com_originais_e_obras_so_com_ele(self):
        text = render_review(review_works(), self.cfg)
        self.assertIn("### identidade · 2 obra(s)", text)
        self.assertIn("Originais: identidade (2), segredo (1)", text)
        self.assertIn("Obras que ficam só com este tema (1): Os Espiões (Luís Fernando Veríssimo)", text)
        self.assertIn("| identidade ⚠ | 2 | 2 |", text)

    def test_so_tag_varios_destinos_e_unico_tema(self):
        self.cfg.mapping[theme_key("violência")] = ["violência", "corpo"]
        text = render_review(review_works(), self.cfg)
        self.assertIn("## Só tag (1)", text)
        self.assertIn("família (1)", text)
        self.assertIn("- violência → violência, corpo", text)
        self.assertIn("- Os Espiões (Luís Fernando Veríssimo): identidade", text)

    def test_original_sem_entrada_aparece_como_pendencia_em_destaque(self):
        del self.cfg.mapping[theme_key("segredo")]
        text = render_review(review_works(), self.cfg)
        self.assertIn("## Pendências", text)
        self.assertIn("- **segredo** (1 obra(s)): Os Espiões (Luís Fernando Veríssimo)", text)
        self.assertIn("segredo", text.split("## Resumo")[0])

    def test_obra_que_perde_mais_da_metade_dos_originais(self):
        for original in ("apocalipse", "amizade"):
            self.cfg.mapping[theme_key(original)] = []
        text = render_review(review_works(), self.cfg)
        self.assertIn("## Pendências", text)  # Belas Maldições ficaria sem tema
        self.assertIn("Belas Maldições (Neil Gaiman): apocalipse, amizade", text)
        self.assertIn("- Belas Maldições (Neil Gaiman): 2 de 2", text)


class RevisaoCliTest(unittest.TestCase):
    def setUp(self):
        import review_themes

        self.module = review_themes
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.legacy = helpers.write_legacy(self.root / "legacy")
        self.themes = helpers.write_themes_config(self.root / "cfg")
        self.out = self.root / "docs" / "revisao-temas.md"

    def tearDown(self):
        self.tmp.cleanup()

    def run_quiet(self, *args):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return self.module.run(*args)

    def test_gera_o_documento_sem_tocar_no_legado(self):
        before = helpers.tree_bytes(self.legacy)
        self.assertEqual(self.run_quiet(self.legacy, self.themes, self.out), 0)
        self.assertIn("# Revisão de temas", self.out.read_text(encoding="utf-8"))
        self.assertEqual(helpers.tree_bytes(self.legacy), before)
        first = self.out.read_bytes()
        self.run_quiet(self.legacy, self.themes, self.out)
        self.assertEqual(self.out.read_bytes(), first)

    def test_entrada_invalida_codigo_2(self):
        self.themes.write_text('{"version": 3}', encoding="utf-8")
        self.assertEqual(self.run_quiet(self.legacy, self.themes, self.out), 2)
        self.assertFalse(self.out.exists())
        self.assertEqual(self.run_quiet(self.root / "nao-existe", self.themes, self.out), 2)


class CatalogoRealTest(unittest.TestCase):
    """O catálogo e o themes.json versionados não podem divergir (R4.2, R4.4)."""

    def test_catalogo_real_passa_o_validador_com_a_taxonomia(self):
        from lib.checks import check_catalog, load_catalog, load_schemas

        root = helpers.ROOT
        cfg = ThemeConfig.load(root / "pipeline" / "config" / "themes.json")
        cat = load_catalog(root / "catalog")
        issues = check_catalog(cat, load_schemas(root / "catalog" / "schema"), themes_cfg=cfg)
        self.assertEqual([i.format() for i in issues], [])
        self.assertEqual(set(cat.vocabularies["themes"]), {t for w in cat.works.values() for t in w["themes"]})
        self.assertTrue(set(cat.vocabularies["themes"]) <= set(cfg.taxonomy))
        self.assertTrue(all(w.get("tags") for w in cat.works.values()))  # tags em todas as obras

    def test_piso_do_catalogo_real(self):
        from lib.checks import load_catalog

        summary = themes.summarize(load_catalog(helpers.ROOT / "catalog").works.values())
        self.assertEqual(summary.below_floor, [])


if __name__ == "__main__":
    unittest.main()

"""Capas de obras: etapas, escolhas e CLI de ponta a ponta, tudo offline."""

import contextlib
import html
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import helpers  # noqa: F401  (ajusta o sys.path para o pipeline)
import enrich_covers  # noqa: E402
import enrich_helpers as eh  # noqa: E402
from lib.checks import check_catalog, load_catalog, load_schemas
from lib.covers import apply as apply_step
from lib.covers import measure, report
from lib.covers.context import CoverError
from lib.env import Env
from lib.images import ImageInfo
from lib.jsonio import write_catalog

VEG = "a-vegetariana-han-kang"
TORTO = "torto-arado-itamar-vieira-junior"
RARO = "livro-raro-fulana-de-tal"
OL_URL = "https://covers.openlibrary.org/b/isbn/9786580309313-L.jpg"
PNG = {"content-type": "image/png"}


def quiet(fn, *args, **kw):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = fn(*args, **kw)
    return code, out.getvalue(), err.getvalue()


class MeasureTest(unittest.TestCase):
    CFG = {"goodMinSide": 400, "rejectBelow": 250, "aspectRange": [0.6, 0.72]}

    def test_classes_e_limites(self):
        classify = lambda side: measure.classify(self.CFG, ImageInfo("jpg", side, side * 2))  # noqa: E731
        self.assertEqual(classify(400), measure.GOOD)
        self.assertEqual(classify(399), measure.BORDERLINE)
        self.assertEqual(classify(250), measure.BORDERLINE)
        self.assertEqual(classify(249), measure.LOW)

    def test_proporcao_fora_de_2_3(self):
        far = lambda w, h: measure.far_from_cover_ratio(self.CFG, ImageInfo("jpg", w, h))  # noqa: E731
        self.assertFalse(far(600, 900))   # 0,667
        self.assertTrue(far(800, 800))    # quadrada
        self.assertTrue(far(500, 1000))   # muito alta


class ApplyUnitTest(unittest.TestCase):
    def test_build_cover_omite_campos_vazios(self):
        self.assertEqual(apply_step.build_cover("https://x.org/a.jpg", "literal"),
                         {"sourceUrl": "https://x.org/a.jpg", "source": "literal"})
        cover = apply_step.build_cover("https://x.org/a.jpg", "literal", file="covers/a.jpg", focus="top")
        self.assertEqual(list(cover), ["sourceUrl", "source", "file", "focus"])

    def test_migracao_reproduz_o_que_o_apply_grava(self):
        # A migração da F1 não pode reescrever (nem reordenar) uma capa já aplicada.
        from lib.build import merge_cover
        for cover in (
            apply_step.build_cover("https://x.org/a.jpg", "literal", file="covers/a.jpg", license="CC BY 4.0",
                                   credit="Fulana", focus="top"),
            apply_step.build_cover("https://x.org/a.jpg", "literal", display="typographic"),
            apply_step.build_cover("https://x.org/a.jpg", "literal"),
        ):
            self.assertEqual(list(merge_cover(cover["sourceUrl"], cover["source"], cover).items()),
                             list(cover.items()))

    def test_escolha_malformada(self):
        with self.assertRaises(CoverError):
            apply_step.validate_choice("x", {"url": "https://x.org/a.jpg", "typographic": True})
        with self.assertRaises(CoverError):
            apply_step.validate_choice("x", {})
        with self.assertRaises(CoverError):
            apply_step.validate_choice("x", {"url": "https://x.org/a.jpg", "focus": "left"})


class CoversCliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        cat = eh.catalog()
        cat.works[VEG]["cover"] = {"sourceUrl": "https://img.test/veg.png", "source": "literal"}
        cat.works[RARO]["cover"] = {"sourceUrl": "https://img.test/raro.png", "source": "literal"}
        catalog_dir = self.root / "catalog"
        shutil.copytree(helpers.SCHEMA_DIR, catalog_dir / "schema")
        files = {f"works/{s}.json": w for s, w in cat.works.items()}
        files.update({f"authors/{s}.json": a for s, a in cat.authors.items()})
        files.update({"readings.json": cat.readings, "summaries.json": cat.summaries,
                      "vocabularies.json": cat.vocabularies})
        write_catalog(files, catalog_dir)
        config = self.root / "pipeline" / "config"
        config.mkdir(parents=True)
        shutil.copy(eh.CONFIG / "enrich.json", config / "enrich.json")
        self.set_choices({})
        self.web = helpers.FakeTransport([
            ("GET", "img.test/veg.png", (200, helpers.tiny_png(600, 900), PNG)),
            ("GET", "img.test/raro.png", (200, helpers.tiny_png(200, 300), PNG)),
            ("GET", "covers.openlibrary.org/b/isbn/9786580309313", (200, helpers.tiny_png(500, 750), PNG)),
        ])
        self.paths = enrich_covers.Paths(self.root)
        self.undated = mock.patch("lib.checks.UNDATED_HEAD", 1)
        self.undated.start()

    def tearDown(self):
        self.undated.stop()
        self.tmp.cleanup()

    def set_choices(self, choices):
        (self.root / "pipeline" / "config" / "cover_choices.json").write_text(json.dumps(choices), encoding="utf-8")

    def run_cli(self, *argv):
        return quiet(enrich_covers.main, list(argv), paths=self.paths, transport=self.web,
                     env=Env({}), today=eh.TODAY, sleep=lambda s: None)

    def state(self):
        return json.loads((self.root / "pipeline" / "cache" / "cover_state.json").read_text(encoding="utf-8"))

    def work(self, slug):
        return json.loads((self.root / "catalog" / "works" / f"{slug}.json").read_text(encoding="utf-8"))

    def tree(self):
        skip = ("pipeline/cache", "docs/plans/capas-execucoes.md")
        return {k: v for k, v in helpers.tree_bytes(self.root).items() if not k.startswith(skip)}

    def media(self):
        folder = self.root / "catalog" / "media" / "covers"
        return sorted(p.name for p in folder.iterdir()) if folder.is_dir() else []

    # -- R1, R2 ------------------------------------------------------------

    def test_download_e_medicao(self):
        before = self.tree()
        code, _, err = self.run_cli("--steps", "download,measure")
        self.assertEqual(code, 0, err)
        state = self.state()
        veg = state[VEG]["candidates"][0]
        self.assertEqual((veg["origin"], veg["klass"], veg["width"], veg["height"], veg["checkFraming"]),
                         ("catalog", "good", 600, 900, False))
        self.assertEqual(state[RARO]["candidates"][0]["klass"], "low")
        self.assertNotIn(TORTO, state)  # sem sourceUrl: nada a baixar
        cache = self.root / "pipeline" / "cache" / "covers" / "candidates"
        self.assertTrue((cache / veg["file"]).is_file())
        self.assertEqual(self.media(), [])  # o mestre só entra no catálogo após a escolha
        self.assertEqual({k: v for k, v in self.tree().items() if k.startswith("catalog/")},
                         {k: v for k, v in before.items() if k.startswith("catalog/")})

    def test_nao_imagem_e_falha_registrada_sem_repetir(self):
        self.web.routes.insert(0, ("GET", "img.test/veg.png", (200, b"<html>nao sou imagem</html>", {})))
        code, _, err = self.run_cli("--steps", "download")
        self.assertEqual(code, 1)
        self.assertIn(f"FALHA {VEG} download", err)
        self.assertEqual(self.state()[VEG]["downloadError"]["url"], "https://img.test/veg.png")
        self.assertEqual(self.state()[RARO]["candidates"][0]["origin"], "catalog")  # as outras seguem
        calls = self.web.count("img.test/veg.png")
        self.run_cli("--steps", "download")
        self.assertEqual(self.web.count("img.test/veg.png"), calls)

    def test_erro_http_numa_obra_nao_para_as_outras(self):
        self.web.routes.insert(0, ("GET", "img.test/veg.png", (500, b"", {})))
        code, _, err = self.run_cli("--steps", "download")
        self.assertEqual(code, 1)
        self.assertIn(f"FALHA {VEG} download", err)
        self.assertEqual(len(self.state()[RARO]["candidates"]), 1)

    def test_extensao_pelo_conteudo_e_nao_pela_url(self):
        self.web.routes.insert(0, ("GET", "img.test/veg.png", (200, helpers.tiny_jpeg(500, 700), PNG)))
        self.run_cli("--steps", "download")
        self.assertEqual(self.state()[VEG]["candidates"][0]["ext"], "jpg")

    # -- R3 ----------------------------------------------------------------

    def test_busca_so_gratuita(self):
        code, _, err = self.run_cli("--steps", "download,measure,search")
        self.assertEqual(code, 0, err)
        state = self.state()
        ol = next(c for c in state[TORTO]["candidates"] if c["origin"] == "openlibrary")
        self.assertEqual((ol["url"], ol["klass"]), (OL_URL, "good"))
        self.assertTrue(any("9786580309313-L.jpg?default=false" in c["url"] for c in self.web.calls))
        self.assertTrue(state[RARO]["noFreeSource"])  # baixa e sem ISBN: backlog
        self.assertNotIn("searched", state[VEG])  # a capa boa do catálogo dispensa a busca
        self.assertEqual(self.web.count("serpapi") + self.web.count("tavily"), 0)
        backlog = (self.root / "docs" / "plans" / "capas-backlog.md").read_text(encoding="utf-8")
        self.assertIn(RARO, backlog)
        self.assertNotIn(TORTO, backlog)

    def test_limitrofe_tambem_busca_alternativa(self):
        # Capa do catálogo limítrofe (350×525) + ISBN: a Open Library oferece uma melhor ao lado.
        self.web.routes.insert(0, ("GET", "img.test/veg.png", (200, helpers.tiny_png(350, 525), PNG)))
        self.web.routes.insert(0, ("GET", "covers.openlibrary.org/b/isbn/9788588808294",
                                   (200, helpers.tiny_png(500, 750), PNG)))
        self.run_cli("--steps", "download,measure,search")
        veg = self.state()[VEG]
        self.assertEqual({(c["origin"], c["klass"]) for c in veg["candidates"]},
                         {("catalog", "borderline"), ("openlibrary", "good")})
        self.assertFalse(veg["noFreeSource"])
        backlog = (self.root / "docs" / "plans" / "capas-backlog.md").read_text(encoding="utf-8")
        self.assertNotIn(VEG, backlog)

    def test_limitrofe_sem_alternativa_continua_utilizavel_e_fora_do_backlog(self):
        self.web.routes.insert(0, ("GET", "img.test/veg.png", (200, helpers.tiny_png(350, 525), PNG)))
        self.web.routes.insert(0, ("GET", "covers.openlibrary.org/b/isbn/9788588808294", (404, b"", {})))
        self.run_cli("--steps", "download,measure,search")
        veg = self.state()[VEG]
        self.assertEqual([c["origin"] for c in veg["candidates"]], ["catalog"])
        self.assertFalse(veg["noFreeSource"])  # a limítrofe do catálogo ainda é utilizável
        self.assertNotIn(VEG, (self.root / "docs" / "plans" / "capas-backlog.md").read_text(encoding="utf-8"))

    def test_ol_sem_capa_404_e_placeholder_pequeno(self):
        self.web.routes.insert(0, ("GET", "covers.openlibrary.org", (404, b"", {})))
        self.run_cli("--steps", "download,measure,search")
        self.assertTrue(self.state()[TORTO]["noFreeSource"])
        self.web.routes.insert(0, ("GET", "covers.openlibrary.org", (200, helpers.tiny_png(1, 1), PNG)))
        self.run_cli("--steps", "search", "--refresh")
        state = self.state()[TORTO]
        self.assertTrue(state["noFreeSource"])
        self.assertEqual(state["candidates"], [])
        self.assertIn("descartada", state["searchNotes"][0])

    def test_isbn10_como_alternativa(self):
        cat = load_catalog(self.root / "catalog")
        torto = cat.works[TORTO]
        torto["edition"]["isbn13"], torto["edition"]["isbn10"] = None, "8535902775"
        (self.root / "catalog" / "works" / f"{TORTO}.json").write_text(json.dumps(torto), encoding="utf-8")
        self.web.routes.insert(0, ("GET", "covers.openlibrary.org/b/isbn/8535902775",
                                   (200, helpers.tiny_png(450, 700), PNG)))
        self.run_cli("--steps", "search", "--only", TORTO)
        self.assertEqual(self.state()[TORTO]["candidates"][0]["url"],
                         "https://covers.openlibrary.org/b/isbn/8535902775-L.jpg")

    # -- R4, R5, R6 --------------------------------------------------------

    def test_sem_decisao_o_catalogo_nao_muda(self):
        before = {k: v for k, v in self.tree().items() if k.startswith("catalog/")}
        self.run_cli()
        self.assertEqual({k: v for k, v in self.tree().items() if k.startswith("catalog/")}, before)
        self.assertEqual(self.media(), [])

    def test_aplica_capa_real_com_foco(self):
        self.set_choices({TORTO: {"url": OL_URL, "focus": "top"}})
        code, _, err = self.run_cli()
        self.assertEqual(code, 0, err)
        cover = self.work(TORTO)["cover"]
        self.assertEqual(cover, {"sourceUrl": OL_URL, "source": "openlibrary",
                                 "file": f"covers/{TORTO}.png", "focus": "top"})
        self.assertEqual(self.media(), [f"{TORTO}.png"])
        cat = load_catalog(self.root / "catalog")
        self.assertEqual(check_catalog(cat, load_schemas(self.root / "catalog" / "schema")), [])

    def test_decisao_manual_vence_a_classe_automatica(self):
        # Capa "baixa" aprovada é usada; capa "boa" marcada tipográfica cai na tipográfica.
        self.set_choices({RARO: {"url": "https://img.test/raro.png"}, VEG: {"typographic": True}})
        code, _, err = self.run_cli()
        self.assertEqual(code, 0, err)
        self.assertEqual(self.work(RARO)["cover"]["file"], f"covers/{RARO}.png")
        veg = self.work(VEG)["cover"]
        self.assertEqual((veg.get("display"), veg.get("file")), ("typographic", None))
        self.assertEqual(self.media(), [f"{RARO}.png"])

    def test_none_vai_ao_backlog_e_mantem_tipografica(self):
        self.set_choices({RARO: {"none": True}})
        code, _, err = self.run_cli()
        self.assertEqual(code, 0, err)
        self.assertNotIn("file", self.work(RARO)["cover"])
        self.assertIn(RARO, (self.root / "docs" / "plans" / "capas-backlog.md").read_text(encoding="utf-8"))

    def test_trocar_a_escolha_remove_o_mestre_antigo(self):
        self.set_choices({RARO: {"url": "https://img.test/raro.png"}})
        self.run_cli()
        self.assertEqual(self.media(), [f"{RARO}.png"])
        self.set_choices({RARO: {"typographic": True}})
        self.run_cli()
        self.assertEqual(self.media(), [])
        self.assertEqual(self.work(RARO)["cover"]["display"], "typographic")

    def test_so_a_escolhida_e_promovida(self):
        self.set_choices({TORTO: {"url": OL_URL}})
        self.run_cli()
        self.assertEqual(self.media(), [f"{TORTO}.png"])  # a candidata da Vegetariana não foi promovida

    def test_escolha_invalida_para_antes_de_tudo(self):
        self.set_choices({TORTO: {"url": OL_URL, "focus": "left"}})
        before = self.tree()
        code, _, err = self.run_cli()
        self.assertEqual(code, 2)
        self.assertIn("focus", err)
        self.assertEqual(self.tree(), before)
        self.set_choices({"obra-que-nao-existe": {"none": True}})
        code, _, err = self.run_cli()
        self.assertEqual(code, 2)
        self.assertIn("obra inexistente", err)

    def test_catalogo_resultante_invalido_nao_grava(self):
        self.set_choices({RARO: {"url": "https://img.test/raro.png"}})
        before = {k: v for k, v in self.tree().items() if k.startswith("catalog/")}
        real = apply_step.build_cover
        bad = lambda *a, **kw: dict(real(*a, **kw), file="covers/nao-existe.png")  # noqa: E731
        with mock.patch.object(apply_step, "build_cover", bad):
            code, _, err = self.run_cli()
        self.assertEqual(code, 1)
        self.assertIn("cover.file", err)
        self.assertEqual({k: v for k, v in self.tree().items() if k.startswith("catalog/")}, before)

    # -- R8 ----------------------------------------------------------------

    def test_dry_run_nao_baixa_nem_grava(self):
        before = helpers.tree_bytes(self.root)
        code, out, err = self.run_cli("--dry-run")
        self.assertEqual(code, 0, err)
        self.assertIn("--dry-run: nada foi gravado", out)
        self.assertRegex(out, r"images\s+\d+\s*\n?")
        self.assertIn("SerpApi e Tavily não são usados", out)
        self.assertEqual(self.web.calls, [])
        self.assertEqual(helpers.tree_bytes(self.root), before)

    def test_segunda_execucao_igual_e_sem_rede(self):
        self.set_choices({TORTO: {"url": OL_URL, "focus": "bottom"}, VEG: {"typographic": True}})
        self.run_cli()
        first = self.tree()
        calls = len(self.web.calls)
        code, _, err = self.run_cli()
        self.assertEqual(code, 0, err)
        self.assertEqual(self.tree(), first)
        self.assertEqual(len(self.web.calls), calls)

    def test_only_e_limit(self):
        self.run_cli("--steps", "download", "--only", VEG)
        self.assertEqual(list(self.state()), [VEG])
        code, _, err = self.run_cli("--only", "nao-existe")
        self.assertEqual(code, 2)
        self.assertIn("obras inexistentes", err)

    def test_etapas_invalidas(self):
        with self.assertRaises(SystemExit):
            quiet(enrich_covers.main, ["--steps", "voar"], paths=self.paths, transport=self.web, env=Env({}))

    # -- R4.1, R9 ----------------------------------------------------------

    def test_folha_de_revisao(self):
        self.run_cli("--steps", "download,measure,search")
        page = (self.root / "docs" / "plans" / "revisao-capas.html").read_text(encoding="utf-8")
        self.assertIn("../../pipeline/cache/covers/candidates/", page)
        self.assertNotIn("src=\"http", page)  # sem hotlink
        self.assertIn(f'"{TORTO}": {{ "typographic": true }}', page)
        self.assertIn('"url": "https://covers.openlibrary.org/b/isbn/9786580309313-L.jpg"', html.unescape(page))
        self.assertIn("boa", page)
        self.assertIn("baixa", page)

    def test_log_de_execucoes(self):
        self.run_cli("--steps", "download")
        log = (self.root / "docs" / "plans" / "capas-execucoes.md").read_text(encoding="utf-8")
        self.assertIn("## 2026-11-02 · download · 3 obras", log)
        self.assertIn("images 2", log)

    def test_cobertura_mostra_capas(self):
        self.set_choices({RARO: {"url": "https://img.test/raro.png"}, VEG: {"typographic": True}})
        self.run_cli()
        text = (self.root / "docs" / "plans" / "cobertura.md").read_text(encoding="utf-8")
        self.assertIn("| Capa local escolhida (mestre em `catalog/media/covers/`) | 1 | 3 |", text)
        self.assertIn("| Capa revisada: fica a tipográfica | 1 | 3 |", text)


class ReportUnitTest(unittest.TestCase):
    def test_cores_do_handoff(self):
        self.assertEqual(report.LANGUAGE_COLORS["coreano"], ("#E3A9B0", "#2A1418"))


if __name__ == "__main__":
    unittest.main()

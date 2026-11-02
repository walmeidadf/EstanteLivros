"""Ponta a ponta: enrich_authors.py e review_summaries.py, offline."""

import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import enrich_authors
import enrich_helpers as eh
import helpers
import review_summaries
from lib.authors import photo as photo_step
from lib.authors.context import CONFIG
from lib.checks import load_catalog
from lib.env import Env
from lib.jsonio import dumps_canonical, write_catalog

BIO_OK = {"insufficient": False, "source_index": 1,
          "text": "Han Kang é uma escritora sul-coreana. Sua prosa poética trata de violência, corpo e memória."}


def quiet(fn, *args, **kw):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = fn(*args, **kw)
    return code, out.getvalue(), err.getvalue()


class EnrichCliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        cat = eh.catalog()
        catalog_dir = self.root / "catalog"
        shutil.copytree(helpers.SCHEMA_DIR, catalog_dir / "schema")
        files = {f"works/{s}.json": w for s, w in cat.works.items()}
        files.update({f"authors/{s}.json": a for s, a in cat.authors.items()})
        files.update({"readings.json": cat.readings, "summaries.json": cat.summaries,
                      "vocabularies.json": cat.vocabularies})
        write_catalog(files, catalog_dir)
        shutil.copytree(CONFIG, self.root / "pipeline" / "config",
                        ignore=shutil.ignore_patterns("slugs.json"))
        (self.root / "pipeline" / "config" / "countries.json").write_text(dumps_canonical(eh.COUNTRIES), encoding="utf-8")
        for name in ("author_wikidata.json", "author_photos.json", "author_overrides.json"):
            (self.root / "pipeline" / "config" / name).write_text("{}\n", encoding="utf-8")
        (self.root / "pipeline" / "config" / "summary_rejections.json").write_text("[]\n", encoding="utf-8")
        self.web = eh.FakeWeb().han_kang()
        self.web.openai = [BIO_OK]
        self.paths = enrich_authors.Paths(self.root)
        # O catálogo de teste tem ano já na leitura 2 (o real só a partir da 54).
        self.undated = mock.patch("lib.checks.UNDATED_HEAD", 1)
        self.undated.start()

    def tearDown(self):
        self.undated.stop()
        self.tmp.cleanup()

    def run_cli(self, *argv, env=None):
        return quiet(enrich_authors.main, list(argv), paths=self.paths, transport=self.web.fake,
                     env=Env(env or eh.ENV), today=eh.TODAY, sleep=lambda s: None)

    def tree(self):
        return {k: v for k, v in helpers.tree_bytes(self.root).items()
                if not k.startswith("pipeline/cache") and not k.endswith("enriquecimento-execucoes.md")}

    def paid_calls(self):
        paid = ("api.openai.com", "serpapi.com/search", "api.tavily.com/search", "img.test")
        return [c["url"] for c in self.web.fake.calls if any(p in c["url"] for p in paid)]

    def test_dry_run_nao_grava_nem_chama_o_que_e_pago(self):
        before = {k: v for k, v in helpers.tree_bytes(self.root).items() if not k.startswith("pipeline/cache")}
        code, out, err = self.run_cli("--dry-run")
        self.assertEqual(code, 0, err)
        self.assertIn("--dry-run: nada foi gravado", out)
        self.assertRegex(out, r"openai\s+1 ")  # a bio da Han Kang (fontes grátis vieram da rede)
        self.assertRegex(out, r"images\s+1 ")  # a foto do Commons seria baixada
        self.assertEqual(self.paid_calls(), [])
        self.assertEqual({k: v for k, v in helpers.tree_bytes(self.root).items()
                          if not k.startswith("pipeline/cache")}, before)

    def test_execucao_completa(self):
        code, out, err = self.run_cli()
        self.assertEqual(code, 0, err + out)
        cat = load_catalog(self.root / "catalog")
        han = cat.authors["han-kang"]
        self.assertEqual((han["wikidata"]["status"], han["country"], han["photo"]["source"]),
                         ("confirmed", "KR", "commons"))
        self.assertTrue((self.root / "catalog" / "media" / "authors" / "han-kang.png").is_file())
        self.assertEqual(cat.vocabularies["countries"], [{"code": "KR", "name": "Coreia do Sul", "languages": ["coreano"]}])
        bio = cat.summaries["summaries"][0]
        self.assertEqual((bio["scope"], bio["approved"]), ("autoria:han-kang", False))
        self.assertEqual(cat.authors["fulana-de-tal"]["wikidata"]["status"], "not_found")
        plans = self.root / "docs" / "plans"
        review = (plans / "revisao-autorias.md").read_text(encoding="utf-8")
        self.assertIn("**Bio para aprovar**", review)
        self.assertIn("--approve", review)
        self.assertIn("## 2026-11-02 · todas as fontes · 3 autorias", (plans / "enriquecimento-execucoes.md").read_text(encoding="utf-8"))
        self.assertIn("Bio proposta", (plans / "cobertura.md").read_text(encoding="utf-8"))
        schemas = enrich_authors.load_schemas(self.root / "catalog" / "schema")
        self.assertEqual(enrich_authors.check_catalog(cat, schemas), [])

    def test_segunda_execucao_igual_e_sem_chamadas(self):
        self.run_cli()
        first = self.tree()
        calls = len(self.paid_calls())
        code, out, err = self.run_cli()
        self.assertEqual(code, 0, err)
        self.assertEqual(self.tree(), first)
        self.assertEqual(len(self.paid_calls()), calls)  # tudo do cache ou nada pendente

    def test_manutencao_igual_a_carga(self):
        code, _, err = self.run_cli("--only", "han-kang")
        self.assertEqual(code, 0, err)
        only = json.loads((self.root / "catalog" / "authors" / "han-kang.json").read_text(encoding="utf-8"))
        self.assertEqual(only["wikidata"]["status"], "confirmed")
        self.assertIsNone(json.loads((self.root / "catalog" / "authors" / "fulana-de-tal.json")
                                     .read_text(encoding="utf-8"))["wikidata"])

    def test_ondas(self):
        code, _, err = self.run_cli("--wave", "1")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.web.fake.count("openai") + self.web.fake.count("tavily.com/search")
                         + self.web.fake.count("serpapi.com/search"), 0)
        code, out, _ = self.run_cli("--wave", "2", "--dry-run")
        self.assertIn("openai", out)
        code, _, err = self.run_cli("--wave", "2")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.web.fake.count("openai"), 1)

    def test_resultado_invalido_nao_grava(self):
        before = self.tree()
        with mock.patch.object(photo_step, "download", return_value=("authors/han-kang.png", [])):
            code, _, err = self.run_cli("--only", "han-kang")
        self.assertEqual(code, 1)
        self.assertIn("photo.file", err)
        self.assertEqual({k: v for k, v in self.tree().items() if not k.startswith("docs/")},
                         {k: v for k, v in before.items() if not k.startswith("docs/")})

    def test_chave_ausente_e_catalogo_invalido(self):
        env = dict(eh.ENV)
        del env["OPENAI_API_KEY"]
        code, _, err = self.run_cli(env=env)
        self.assertEqual(code, 2)
        self.assertIn("OPENAI_API_KEY", err)
        self.assertNotIn("sk-teste", err)
        code, _, _ = self.run_cli("--wave", "1", env=env)  # onda 1 não usa OpenAI
        self.assertEqual(code, 0)
        path = self.root / "catalog" / "summaries.json"
        path.write_text('{"summaries": [{"scope": "x"}]}', encoding="utf-8")
        self.assertEqual(self.run_cli()[0], 2)


class ReviewCliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        cat = helpers.valid_catalog()
        cat.summaries["summaries"] = [helpers.summary("autoria:autor-b", "Bio B."),
                                      helpers.summary("autoria:autora-a", "Bio A.")]
        files = {f"works/{s}.json": w for s, w in cat.works.items()}
        files.update({f"authors/{s}.json": a for s, a in cat.authors.items()})
        files.update({"readings.json": cat.readings, "summaries.json": cat.summaries,
                      "vocabularies.json": cat.vocabularies})
        shutil.copytree(helpers.SCHEMA_DIR, self.root / "catalog" / "schema")
        write_catalog(files, self.root / "catalog")
        (self.root / "pipeline" / "config").mkdir(parents=True)
        self.undated = mock.patch("lib.checks.UNDATED_HEAD", 1)
        self.undated.start()

    def tearDown(self):
        self.undated.stop()
        self.tmp.cleanup()

    def cli(self, *argv):
        return quiet(review_summaries.main, list(argv), root=self.root)

    def summaries(self):
        return json.loads((self.root / "catalog" / "summaries.json").read_text(encoding="utf-8"))["summaries"]

    def test_aprovar_rejeitar_editar(self):
        code, out, err = self.cli("--approve", "autoria:autora-a")
        self.assertEqual(code, 0, err)
        self.assertEqual([s["approved"] for s in self.summaries()], [False, True])
        code, _, _ = self.cli("--reject", "autoria:autor-b")
        self.assertEqual([s["scope"] for s in self.summaries()], ["autoria:autora-a"])
        self.assertEqual(json.loads((self.root / "pipeline" / "config" / "summary_rejections.json").read_text()),
                         ["autoria:autor-b"])
        code, _, _ = self.cli("--edit", "autoria:autora-a", "--text", "Bio nova.", "--and-approve")
        item = self.summaries()[0]
        self.assertEqual((item["text"], item["editedBy"], item["approved"]), ("Bio nova.", "human", True))
        self.assertTrue((self.root / "docs" / "plans" / "cobertura.md").is_file())

    def test_approve_file_list_e_erro(self):
        listfile = self.root / "ok.txt"
        listfile.write_text("# aprovadas\nautoria:autora-a\nautoria:autor-b\n", encoding="utf-8")
        self.assertEqual(self.cli("--approve-file", str(listfile))[0], 0)
        code, out, _ = self.cli("--list", "--pending")
        self.assertIn("0 resumo(s)", out)
        before = (self.root / "catalog" / "summaries.json").read_bytes()
        code, _, err = self.cli("--approve", "autoria:ninguem")
        self.assertEqual(code, 1)
        self.assertEqual((self.root / "catalog" / "summaries.json").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()

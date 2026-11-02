"""Testes de env, http, budget e images (tarefas 3–6)."""

import datetime as dt
import json
import struct
import tempfile
import unittest
from pathlib import Path

import helpers
from lib.budget import Budget, BudgetExhausted
from lib.env import Env, MissingKey, parse_env_file
from lib.http import CacheMiss, Http, HttpError, safe_url
from lib.images import sniff


class EnvTest(unittest.TestCase):
    def test_parse(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_text('# comentário\nA=1\nB="com espaço"\nexport C=\'x\'\nD=valor # nota\nE=\nruim\n',
                            encoding="utf-8")
            self.assertEqual(parse_env_file(path), {"A": "1", "B": "com espaço", "C": "x", "D": "valor", "E": ""})
            env = Env.load(path, environ={"A": "do-ambiente"})
        self.assertEqual(env.get("A"), "do-ambiente")
        self.assertIsNone(env.get("E"))

    def test_require(self):
        env = Env({"WIKIMEDIA_USER_AGENT": "ua", "OPENAI_MODEL": "m"})
        self.assertEqual(env.require(["identify"]), [])
        warnings = env.require(["photo"])
        self.assertTrue(any("SERP_API_KEY" in w for w in warnings))
        with self.assertRaises(MissingKey) as ctx:
            env.require(["bio"])
        self.assertIn("OPENAI_API_KEY", str(ctx.exception))
        self.assertNotIn("ua", str(ctx.exception).replace("OPENAI", ""))


class HttpTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cache = Path(self.tmp.name)
        self.slept = []

    def tearDown(self):
        self.tmp.cleanup()

    def http(self, transport, **kw):
        return Http(self.cache, transport=transport, user_agent="UA-teste", sleep=self.slept.append, **kw)

    def test_cache_hit_e_refresh(self):
        fake = helpers.FakeTransport([("GET", "example.org", {"ok": 1})])
        http = self.http(fake)
        self.assertEqual(http.get_json("p", "https://example.org/a", {"q": "x"}).data, {"ok": 1})
        second = http.get_json("p", "https://example.org/a", {"q": "x"})
        self.assertTrue(second.from_cache)
        self.assertEqual(len(fake.calls), 1)
        self.http(fake, refresh=True).get_json("p", "https://example.org/a", {"q": "x"})
        self.assertEqual(len(fake.calls), 2)

    def test_offline_levanta_cache_miss(self):
        http = self.http(helpers.FakeTransport(), offline=True)
        with self.assertRaises(CacheMiss):
            http.get_json("tavily", "https://api.tavily.com/search")
        self.assertEqual(http.missed["tavily"], 1)

    def test_segredos_fora_do_cache_e_da_chave(self):
        fake = helpers.FakeTransport([("GET", "serpapi", {"r": 1})])
        http = self.http(fake)
        http.get_json("serpapi", "https://serpapi.com/search.json", {"q": "a", "api_key": "SEGREDO"},
                      secret_params=("api_key",))
        stored = "".join(p.read_text(encoding="utf-8") for p in self.cache.rglob("*.json"))
        self.assertNotIn("SEGREDO", stored)
        # outra chave, mesma consulta → mesmo cache
        http.get_json("serpapi", "https://serpapi.com/search.json", {"q": "a", "api_key": "OUTRA"},
                      secret_params=("api_key",))
        self.assertEqual(len(fake.calls), 1)
        self.assertEqual(safe_url("https://x.org/?q=a&api_key=S", ["api_key"]), "https://x.org/?q=a&api_key=%2A%2A%2A")

    def test_erro_sem_segredo_na_mensagem(self):
        fake = helpers.FakeTransport([("POST", "openai", (401, {"error": "bad key Bearer sk-SEGREDO"}))])
        with self.assertRaises(HttpError) as ctx:
            self.http(fake).post_json("openai", "https://api.openai.com/v1/responses", {"x": 1},
                                      headers={"Authorization": "Bearer sk-SEGREDO"})
        self.assertNotIn("sk-SEGREDO", str(ctx.exception))
        self.assertEqual(list(self.cache.rglob("*.json")), [])  # erro não vai para o cache

    def test_retries_com_retry_after(self):
        responses = [(429, {}, {"retry-after": "3"}), (503, {}), {"ok": True}]
        fake = helpers.FakeTransport([("GET", "x.org", lambda url, body: responses.pop(0))])
        self.assertEqual(self.http(fake).get_json("p", "https://x.org/").data, {"ok": True})
        self.assertEqual(self.slept, [3.0, 2])

    def test_retries_esgotados(self):
        fake = helpers.FakeTransport([("GET", "x.org", (503, {}))])
        with self.assertRaises(HttpError):
            self.http(fake).get_json("p", "https://x.org/")
        self.assertEqual(len(fake.calls), 5)

    def test_404_vai_para_o_cache(self):
        fake = helpers.FakeTransport()
        http = self.http(fake)
        self.assertEqual(http.get_json("p", "https://x.org/nada").status, 404)
        self.assertEqual(http.get_json("p", "https://x.org/nada").status, 404)
        self.assertEqual(len(fake.calls), 1)

    def test_user_agent_e_pausa(self):
        fake = helpers.FakeTransport([("GET", "wikidata", {"ok": 1})])
        clock = iter([0.0, 0.05, 0.2]).__next__  # 1ª chamada; 2ª chega em 0,05 s; depois da pausa
        http = Http(self.cache, transport=fake, user_agent="UA-teste", sleep=self.slept.append,
                    clock=clock, intervals={"wikidata": 0.2})
        http.get_json("wikidata", "https://www.wikidata.org/w/api.php", {"a": 1})
        http.get_json("wikidata", "https://www.wikidata.org/w/api.php", {"a": 2})
        self.assertEqual(fake.calls[0]["headers"]["User-Agent"], "UA-teste")
        self.assertAlmostEqual(self.slept[0], 0.15)

    def test_bytes(self):
        png = helpers.tiny_png()
        fake = helpers.FakeTransport([("GET", "img", (200, png, {"content-type": "image/png"}))])
        http = self.http(fake)
        self.assertEqual(http.get_bytes("commons", "https://img.org/a.png").content, png)
        again = http.get_bytes("commons", "https://img.org/a.png")
        self.assertTrue(again.from_cache)
        self.assertEqual(again.content, png)

    def test_orcamento_so_em_chamada_de_rede(self):
        with tempfile.TemporaryDirectory() as ledger:
            budget = Budget({"tavily": {"monthly": 10, "reserve": 0, "perRun": 1}}, Path(ledger))
            fake = helpers.FakeTransport([("POST", "tavily", {"r": []})])
            http = self.http(fake, budget=budget)
            http.post_json("tavily", "https://api.tavily.com/search", {"q": 1})
            http.post_json("tavily", "https://api.tavily.com/search", {"q": 1})  # cache: não gasta
            with self.assertRaises(BudgetExhausted):
                http.post_json("tavily", "https://api.tavily.com/search", {"q": 2})
            self.assertEqual(len(fake.calls), 1)


class BudgetTest(unittest.TestCase):
    LIMITS = {"serpapi": {"monthly": 250, "reserve": 40, "perRun": 120},
              "openai": {"maxUsdPerRun": 0.01}}

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.today = lambda: dt.date(2026, 11, 2)

    def tearDown(self):
        self.tmp.cleanup()

    def test_saldo_usa_maior_uso_e_reserva(self):
        (self.dir / "serpapi-2026-11.json").write_text('{"count": 50}', encoding="utf-8")
        b = Budget(self.LIMITS, self.dir, {"serpapi": 100}, today=self.today)
        self.assertEqual(b.used("serpapi"), 100)
        self.assertEqual(b.available("serpapi"), 110)  # 250 - 100 - 40
        self.assertEqual(Budget(self.LIMITS, self.dir, {"serpapi": 100}, use_reserve=True,
                                today=self.today).available("serpapi"), 120)  # teto por execução

    def test_gasto_atualiza_livro_razao_e_esgota(self):
        b = Budget({"tavily": {"monthly": 3, "reserve": 1}}, self.dir, today=self.today)
        b.spend("tavily")
        b.spend("tavily")
        self.assertEqual(b.local_used("tavily"), 2)
        with self.assertRaises(BudgetExhausted):
            b.spend("tavily")
        self.assertEqual(Budget({"tavily": {"monthly": 3, "reserve": 1}}, self.dir,
                                today=lambda: dt.date(2026, 12, 1)).used("tavily"), 0)

    def test_sem_cota_e_teto_openai(self):
        b = Budget(self.LIMITS, self.dir, today=self.today)
        self.assertIsNone(b.available("wikidata"))
        b.spend("wikidata")
        b.spend("openai")
        b.add_openai(1000, 100, 0.02)
        with self.assertRaises(BudgetExhausted):
            b.spend("openai")
        self.assertEqual(b.snapshot()["openai"]["input"], 1000)


class ImagesTest(unittest.TestCase):
    def test_png_jpeg_gif_webp(self):
        self.assertEqual(sniff(helpers.tiny_png(640, 480)), ("png", 640, 480))
        self.assertEqual(sniff(helpers.tiny_jpeg(500, 700)), ("jpg", 500, 700))
        self.assertEqual(sniff(b"GIF89a" + struct.pack("<HH", 30, 40) + b"\x00" * 10), ("gif", 30, 40))
        vp8x = b"RIFF\x00\x00\x00\x00WEBPVP8X" + b"\x0a\x00\x00\x00" + b"\x00" * 4 \
            + (799).to_bytes(3, "little") + (599).to_bytes(3, "little")
        self.assertEqual(sniff(vp8x), ("webp", 800, 600))
        info = sniff(helpers.tiny_png(300, 900))
        self.assertEqual(info.min_side, 300)

    def test_nao_imagem(self):
        self.assertIsNone(sniff(b"<html>nao sou imagem</html>"))
        self.assertIsNone(sniff(b""))
        self.assertIsNone(sniff(b"\xff\xd8\xff"))


if __name__ == "__main__":
    unittest.main()

import json
import tempfile
import unittest
from pathlib import Path

import helpers
from lib.build import build
from lib.checks import check_catalog, load_schemas
from lib.coverage import work_rows
from lib.legacy_reader import LegacyDataError, read_legacy
from lib.slugs import SlugRegistry
from lib.work_overrides import WorkOverride, WorkOverridesError, apply, load

VEG = "a-vegetariana-han-kang"


def write(tmp, data):
    path = Path(tmp) / "work_overrides.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def entry(**fields):
    return {"source": "teste", "date": "2026-11-06", **fields}


def run_build(overrides):
    with tempfile.TemporaryDirectory() as tmp:
        legacy = read_legacy(helpers.write_legacy(Path(tmp)))
    return build(legacy, SlugRegistry(), {}, work_overrides=overrides)


class LoadTest(unittest.TestCase):
    def load(self, data):
        with tempfile.TemporaryDirectory() as tmp:
            return load(write(tmp, data))

    def test_arquivo_ausente_nao_corrige_nada(self):
        self.assertEqual(load(Path("/nao/existe/work_overrides.json")), {})

    def test_le_campos_e_origem(self):
        got = self.load({"version": 1, "works": {"x": entry(originalTitleRomanized="Er", firstPublished=None)}})
        self.assertEqual(got["x"].values, {"originalTitleRomanized": "Er", "firstPublished": None})
        self.assertEqual(got["x"].source, "teste")

    def test_rejeita_sem_origem_campo_desconhecido_e_vazio(self):
        bad = [
            {"version": 1, "works": {"x": {"originalTitle": None}}},
            {"version": 1, "works": {"x": entry(title="outro")}},
            {"version": 1, "works": {"x": entry()}},
            {"version": 1, "works": {"x": entry(originalTitleRomanized="  ")}},
            {"version": 1, "works": {"x": entry(firstPublished="2011")}},
            {"version": 1, "works": {"x": entry(date="6/11/2026", firstPublished=2011)}},
            {"version": 2, "works": {}},
        ]
        for data in bad:
            with self.subTest(data=data), self.assertRaises(WorkOverridesError):
                self.load(data)


class ApplyTest(unittest.TestCase):
    def test_sem_correcao_devolve_o_csv(self):
        self.assertEqual(apply(None, "a", "b", 1), ("a", "b", 1, [], []))

    def test_aplica_e_aponta_redundancia(self):
        ov = WorkOverride({"originalTitleRomanized": "Er", "firstPublished": 2011}, "t", None)
        got = apply(ov, "ער", "Er", None)
        self.assertEqual(got, ("ער", "Er", 2011, ["originalTitleRomanized", "firstPublished"],
                               ["originalTitleRomanized"]))

    def test_null_intencional_nao_e_redundante(self):
        ov = WorkOverride({"originalTitle": None}, "t", None)
        self.assertEqual(apply(ov, None, None, 1943), (None, None, 1943, ["originalTitle"], []))


class BuildTest(unittest.TestCase):
    def test_correcao_vence_o_csv_e_registra_no_audit(self):
        ov = {VEG: WorkOverride({"originalTitleRomanized": "Chaesik-juuija", "firstPublished": 2008}, "t", None)}
        works = run_build(ov).catalog.works
        self.assertEqual(works[VEG]["originalTitleRomanized"], "Chaesik-juuija")
        self.assertEqual(works[VEG]["firstPublished"], 2008)
        self.assertEqual(works[VEG]["audit"]["overrides"], ["originalTitleRomanized", "firstPublished"])
        others = [w for s, w in works.items() if s != VEG]
        self.assertTrue(all("overrides" not in w["audit"] for w in others))

    def test_sem_correcao_o_catalogo_nao_muda(self):
        self.assertEqual(run_build({}).files, run_build(None).files)

    def test_obra_inexistente_interrompe(self):
        with self.assertRaises(LegacyDataError):
            run_build({"nao-existe": WorkOverride({"firstPublished": 1}, "t", None)})

    def test_modelo_valido_no_schema(self):
        ov = {VEG: WorkOverride({"originalTitleRomanized": "Chaesik-juuija"}, "t", None)}
        cat = run_build(ov).catalog
        self.assertEqual(check_catalog(cat, load_schemas(helpers.SCHEMA_DIR), work_overrides=ov), [])


class CheckTest(unittest.TestCase):
    def setUp(self):
        self.ov = {VEG: WorkOverride({"originalTitleRomanized": "Chaesik-juuija"}, "t", None)}
        self.cat = run_build(self.ov).catalog
        self.schemas = load_schemas(helpers.SCHEMA_DIR)

    def codes(self):
        return [i.code for i in check_catalog(self.cat, self.schemas, work_overrides=self.ov)]

    def test_deriva_quando_o_catalogo_foi_editado(self):
        self.cat.works[VEG]["originalTitleRomanized"] = "outra"
        self.assertEqual(self.codes(), ["work.override-drift"])

    def test_deriva_sem_registro_no_audit(self):
        del self.cat.works[VEG]["audit"]["overrides"]
        self.assertEqual(self.codes(), ["work.override-drift"])

    def test_correcao_de_obra_inexistente(self):
        self.ov["fantasma"] = WorkOverride({"firstPublished": 1}, "t", None)
        self.assertEqual(self.codes(), ["work.override-drift"])

    def test_romanizacao_exige_original_nao_latino(self):
        self.cat.works[VEG].update(originalTitle="Good Omens")
        self.assertEqual(self.codes(), ["work.romanization"])


class CoverageTest(unittest.TestCase):
    def test_ausencia_intencional_sai_do_denominador(self):
        ov = {VEG: WorkOverride({"originalTitle": None, "firstPublished": None}, "t", None)}
        cat = run_build(ov).catalog
        rows = {name: (f, t) for name, f, t in work_rows(list(cat.works.values()))}
        base = {name: (f, t) for name, f, t in work_rows(list(run_build({}).catalog.works.values()))}
        original = "Título original (obras não escritas em português)"
        year = "Ano de primeira publicação"
        self.assertEqual(rows[original][1], base[original][1] - 1)
        self.assertEqual(rows[original][0], base[original][0] - 1)
        self.assertEqual(rows[year], (base[year][0] - 1, base[year][1] - 1))


if __name__ == "__main__":
    unittest.main()

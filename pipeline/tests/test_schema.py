import json
import tempfile
import unittest
from pathlib import Path

import helpers
from lib.checks import SCHEMA_FILES, load_schemas
from lib.schema import SchemaError, check_schema, load_schema, validate


def errs(instance, schema):
    return validate(instance, check_schema(schema))


class KeywordTest(unittest.TestCase):
    def test_type_e_uniao(self):
        s = {"type": ["string", "null"]}
        self.assertEqual(errs("x", s), [])
        self.assertEqual(errs(None, s), [])
        self.assertEqual(len(errs(3, s)), 1)

    def test_bool_nao_e_integer(self):
        self.assertEqual(len(errs(True, {"type": "integer"})), 1)
        self.assertEqual(errs(3, {"type": "integer"}), [])

    def test_required_properties_additional(self):
        s = {"type": "object", "required": ["a"], "additionalProperties": False,
             "properties": {"a": {"type": "integer"}}}
        self.assertEqual(errs({"a": 1}, s), [])
        self.assertEqual(errs({}, s), [("a", "campo obrigatório ausente")])
        self.assertEqual(errs({"a": 1, "b": 2}, s), [("b", "campo não permitido")])

    def test_items_e_caminho_aninhado(self):
        s = {"type": "object", "properties": {"l": {"type": "array", "items": {
            "type": "object", "properties": {"x": {"type": "string"}}}}}}
        self.assertEqual(errs({"l": [{"x": "ok"}, {"x": 1}]}, s)[0][0], "l[1].x")

    def test_enum_const(self):
        self.assertEqual(errs("a", {"enum": ["a", "b"]}), [])
        self.assertEqual(len(errs("c", {"enum": ["a", "b"]})), 1)
        self.assertEqual(errs(1, {"const": 1}), [])
        self.assertEqual(len(errs(2, {"const": 1})), 1)

    def test_pattern_e_tamanho(self):
        s = {"type": "string", "pattern": "^[a-z]+$", "minLength": 2, "maxLength": 3}
        self.assertEqual(errs("ab", s), [])
        self.assertEqual(len(errs("a", s)), 1)
        self.assertEqual(len(errs("abcd", s)), 1)
        self.assertEqual(len(errs("A1", s)), 1)

    def test_minimo_maximo(self):
        s = {"type": "integer", "minimum": 1, "maximum": 3}
        self.assertEqual(errs(2, s), [])
        self.assertEqual(len(errs(0, s)), 1)
        self.assertEqual(len(errs(4, s)), 1)

    def test_min_items_unique(self):
        s = {"type": "array", "minItems": 1, "uniqueItems": True}
        self.assertEqual(errs(["a"], s), [])
        self.assertEqual(len(errs([], s)), 1)
        self.assertEqual(len(errs(["a", "a"], s)), 1)

    def test_ref_local(self):
        s = {"$defs": {"slug": {"type": "string", "pattern": "^[a-z]+$"}}, "$ref": "#/$defs/slug"}
        self.assertEqual(errs("abc", s), [])
        self.assertEqual(len(errs("ABC", s)), 1)

    def test_one_of_null_ou_objeto(self):
        s = {"oneOf": [{"type": "null"}, {"type": "object", "required": ["a"]}]}
        self.assertEqual(errs(None, s), [])
        self.assertEqual(errs({"a": 1}, s), [])
        self.assertEqual(len(errs({}, s)), 1)
        self.assertEqual(len(errs("x", s)), 1)

    def test_palavra_chave_desconhecida_falha(self):
        with self.assertRaises(SchemaError):
            check_schema({"type": "string", "format": "email"})
        with self.assertRaises(SchemaError):
            check_schema({"type": "object", "properties": {"a": {"anyOf": []}}})

    def test_load_schema_de_arquivo(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "s.json"
            path.write_text(json.dumps({"type": "string", "if": {}}), encoding="utf-8")
            with self.assertRaises(SchemaError):
                load_schema(path)


class CatalogSchemasTest(unittest.TestCase):
    """Os schemas reais carregam e os exemplos do design validam."""

    def setUp(self):
        self.schemas = load_schemas(helpers.SCHEMA_DIR)

    def test_todos_carregam(self):
        self.assertEqual(set(self.schemas), set(SCHEMA_FILES))

    def test_catalogo_minimo_valida(self):
        cat = helpers.valid_catalog()
        for w in cat.works.values():
            self.assertEqual(validate(w, self.schemas["work"]), [])
        for a in cat.authors.values():
            self.assertEqual(validate(a, self.schemas["author"]), [])
        self.assertEqual(validate(cat.readings, self.schemas["readings"]), [])
        self.assertEqual(validate(cat.summaries, self.schemas["summaries"]), [])
        self.assertEqual(validate(cat.vocabularies, self.schemas["vocabularies"]), [])

    def test_exemplo_de_obra_do_design(self):
        work = helpers.valid_catalog().works["obra-a"]
        work.update({
            "slug": "a-vegetariana-han-kang", "originalTitle": "채식주의자",
            "originalTitleRomanized": "Chaesikjuuija", "authors": ["han-kang"],
            "cover": {"sourceUrl": "https://assets.literal.club/3/x.jpg", "source": "literal"},
            "references": [{"provider": "web", "id": None, "url": "https://x.org", "fields": None}],
            "legacyId": "work-8a1409675d20",
        })
        self.assertEqual(validate(work, self.schemas["work"]), [])

    def test_wikidata_e_foto_como_objeto(self):
        author = helpers.valid_catalog().authors["autora-a"]
        author["wikidata"] = {"id": "Q5646626", "status": "confirmed", "evidence": "P50", "rulesVersion": 1}
        author["photo"] = {"file": "authors/autora-a.jpg", "license": "CC BY-SA 4.0", "author": None,
                           "sourceUrl": "https://commons.wikimedia.org/x", "source": "commons"}
        self.assertEqual(validate(author, self.schemas["author"]), [])
        author["wikidata"] = {"id": None, "status": "not_found", "evidence": None, "rulesVersion": 1}
        self.assertEqual(validate(author, self.schemas["author"]), [])
        author["photo"]["file"] = "../fora.jpg"
        self.assertNotEqual(validate(author, self.schemas["author"]), [])
        author["photo"]["file"] = "authors/autora-a.jpg"
        author["bio"] = None  # campo removido do schema
        self.assertIn(("bio", "campo não permitido"), validate(author, self.schemas["author"]))

    def test_string_vazia_e_isbn_invalidos(self):
        work = helpers.valid_catalog().works["obra-a"]
        work["catalogerNote"] = ""
        work["edition"]["isbn13"] = "123"
        paths = {p for p, _ in validate(work, self.schemas["work"])}
        self.assertIn("catalogerNote", paths)
        self.assertIn("edition.isbn13", paths)

    def test_escopo_de_resumo(self):
        ok = {"summaries": [helpers.summary("pais:PT", text="")]}
        self.assertEqual(validate(ok, self.schemas["summaries"]), [])
        ok["summaries"][0]["scope"] = "pais:portugal"
        self.assertNotEqual(validate(ok, self.schemas["summaries"]), [])


if __name__ == "__main__":
    unittest.main()

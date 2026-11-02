import tempfile
import unittest
from pathlib import Path

import helpers
from lib.legacy_reader import (Cell, LegacyDataError, LegacyInputError, integer, read_legacy,
                               split_list, text, yes_no)

CELL = Cell("obras.csv", 7, "first_publication_year")


class ReadLegacyTest(unittest.TestCase):
    def test_le_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = read_legacy(helpers.write_legacy(Path(tmp)))
        self.assertEqual((len(data.works), len(data.readings), len(data.sources)), (4, 5, 3))
        self.assertEqual(data.works[0]["__line__"], "2")

    def test_csv_ausente(self):
        with tempfile.TemporaryDirectory() as tmp:
            helpers.write_legacy(Path(tmp))
            (Path(tmp) / "fontes.csv").unlink()
            with self.assertRaises(LegacyInputError) as ctx:
                read_legacy(Path(tmp))
        self.assertIn("fontes.csv", str(ctx.exception))

    def test_coluna_ausente(self):
        with tempfile.TemporaryDirectory() as tmp:
            helpers.write_legacy(Path(tmp), drop_column="isbn13")
            with self.assertRaises(LegacyInputError) as ctx:
                read_legacy(Path(tmp))
        self.assertIn("isbn13", str(ctx.exception))


class ConversionTest(unittest.TestCase):
    def test_text(self):
        self.assertEqual(text("  a "), "a")
        self.assertIsNone(text("   "))
        self.assertIsNone(text(None))

    def test_integer(self):
        self.assertEqual(integer(" 2014 ", CELL), 2014)
        self.assertIsNone(integer("", CELL))
        with self.assertRaises(LegacyDataError) as ctx:
            integer("dois mil", CELL)
        self.assertIn("linha 7", str(ctx.exception))
        self.assertIn("first_publication_year", str(ctx.exception))

    def test_yes_no(self):
        self.assertTrue(yes_no("sim", CELL))
        self.assertFalse(yes_no("não", CELL))
        self.assertFalse(yes_no("", CELL))
        with self.assertRaises(LegacyDataError):
            yes_no("talvez", CELL)

    def test_split_list(self):
        self.assertEqual(split_list(" a;  ; b ;a; c"), ["a", "b", "c"])
        self.assertEqual(split_list(""), [])
        self.assertEqual(split_list(None), [])


if __name__ == "__main__":
    unittest.main()

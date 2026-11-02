"""Leitura dos CSVs validados do legado (`legacy/exports/`)."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

REQUIRED_COLUMNS: Dict[str, List[str]] = {
    "obras.csv": [
        "work_id", "title_pt_br", "original_title", "authors", "original_language",
        "first_publication_year", "work_type", "genres", "themes", "edition_match",
        "edition_title", "edition_language", "isbn10", "isbn13", "publisher",
        "edition_publication_year", "physical_format", "cover_url", "cover_source",
        "literal_book_id", "literal_work_id", "literal_url", "openlibrary_work_id",
        "openlibrary_edition_id", "openlibrary_url", "google_books_id",
        "google_books_url", "wikidata_id", "wikidata_url", "additional_reference_urls",
        "validation_status", "confidence", "decision_reason", "source_conflicts",
        "validated_at",
    ],
    "leituras.csv": [
        "reading_sequence", "read_year", "reread", "work_id", "original_entry",
        "reading_notes",
    ],
    "fontes.csv": ["work_id", "provider", "identifier", "url", "fields_supported"],
}

Row = Dict[str, str]


class LegacyInputError(Exception):
    """Entrada ausente ou com colunas faltando (código de saída 2)."""


class LegacyDataError(Exception):
    """Valor inválido num CSV (código de saída 1)."""


@dataclass
class Cell:
    """Localização de um valor, para mensagens de erro."""

    file: str
    line: int
    column: str

    def where(self) -> str:
        return f"{self.file}, linha {self.line}, coluna {self.column}"


@dataclass
class LegacyData:
    works: List[Row]
    readings: List[Row]
    sources: List[Row]


def read_legacy(legacy_dir: Path) -> LegacyData:
    """Confere todos os cabeçalhos antes de ler qualquer linha."""
    problems = []
    for name, required in REQUIRED_COLUMNS.items():
        path = legacy_dir / name
        if not path.is_file():
            problems.append(f"{path}: arquivo ausente")
            continue
        with open(path, encoding="utf-8", newline="") as fh:
            header = next(csv.reader(fh), [])
        missing = [c for c in required if c not in header]
        if missing:
            problems.append(f"{path}: colunas faltando: {', '.join(missing)}")
    if problems:
        raise LegacyInputError("\n".join(problems))

    def rows(name: str) -> List[Row]:
        with open(legacy_dir / name, encoding="utf-8", newline="") as fh:
            out = []
            for line, row in enumerate(csv.DictReader(fh), start=2):
                row = {k: (v or "") for k, v in row.items() if k is not None}
                row["__line__"] = str(line)
                out.append(row)
            return out

    return LegacyData(rows("obras.csv"), rows("leituras.csv"), rows("fontes.csv"))


# -- conversões -----------------------------------------------------------

def text(value: Optional[str]) -> Optional[str]:
    """String sem espaços nas pontas; vazio vira None."""
    value = (value or "").strip()
    return value or None


def integer(value: Optional[str], cell: Cell) -> Optional[int]:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        raise LegacyDataError(f"{cell.where()}: inteiro inválido {value!r}") from None


def yes_no(value: Optional[str], cell: Cell) -> bool:
    value = (value or "").strip().lower()
    if value in ("sim", "s", "true", "1"):
        return True
    if value in ("não", "nao", "n", "false", "0", ""):
        return False
    raise LegacyDataError(f"{cell.where()}: esperado sim/não, recebido {value!r}")


def split_list(value: Optional[str], sep: str = ";") -> List[str]:
    """Itens sem espaços, sem vazios, sem repetidos, na ordem original."""
    out: List[str] = []
    for item in (value or "").split(sep):
        item = item.strip()
        if item and item not in out:
            out.append(item)
    return out

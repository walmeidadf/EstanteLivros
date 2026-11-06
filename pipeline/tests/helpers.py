"""Utilitários de teste: caminhos e fixtures sintéticas (nunca usam legacy/)."""

from __future__ import annotations

import copy
import csv
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

PIPELINE = Path(__file__).resolve().parent.parent
ROOT = PIPELINE.parent
SCHEMA_DIR = ROOT / "catalog" / "schema"

if str(PIPELINE) not in sys.path:
    sys.path.insert(0, str(PIPELINE))

from lib.legacy_reader import REQUIRED_COLUMNS  # noqa: E402

# -- legado sintético -------------------------------------------------------

WORKS: List[Dict[str, str]] = [
    {
        "work_id": "work-0001", "title_pt_br": "Os Espiões", "authors": "Luís Fernando Veríssimo",
        "original_language": "português", "first_publication_year": "2009", "work_type": "romance",
        "genres": "humor; ficção literária", "themes": "identidade; segredo",
        "edition_match": "representative", "edition_title": "Os Espiões", "edition_language": "português",
        "isbn13": "978-8560281725", "publisher": "Alfaguara", "edition_publication_year": "2009",
        "physical_format": "brochura", "cover_url": "https://example.org/espioes.jpg",
        "cover_source": "literal", "literal_book_id": "lit-book-1", "literal_work_id": "lit-work-1",
        "validation_status": "validated", "confidence": "high", "decision_reason": "Consenso.",
        "validated_at": "2026-08-13",
    },
    {
        "work_id": "work-0002", "title_pt_br": "Comédias para se Ler na Escola",
        "authors": "Luis Fernando Verissimo", "original_language": "português",
        "first_publication_year": "2001", "work_type": "crônica", "genres": "humor",
        "themes": "escola; identidade", "edition_match": "exact", "edition_title": "Comédias",
        "edition_language": "português", "publisher": "Objetiva", "edition_publication_year": "2001",
        "physical_format": "desconhecido", "cover_url": "", "cover_source": "literal",
        "validation_status": "validated", "confidence": "medium", "decision_reason": "Edição exata.",
        "validated_at": "2026-08-13",
    },
    {
        "work_id": "work-0003", "title_pt_br": "A Vegetariana", "original_title": "채식주의자 (Chaesikjuuija)",
        "authors": "Han Kang", "original_language": "coreano", "first_publication_year": "2007",
        "work_type": "romance", "genres": "drama psicológico; ficção literária",
        "themes": "corpo; família; violência", "edition_match": "representative",
        "edition_title": "A Vegetariana", "edition_language": "português", "isbn13": "9788588808294",
        "publisher": "Todavia", "edition_publication_year": "2018", "physical_format": "brochura",
        "cover_url": "https://example.org/vegetariana.jpg", "cover_source": "literal",
        "openlibrary_work_id": "/works/OL1W", "openlibrary_url": "https://openlibrary.org/works/OL1W",
        "additional_reference_urls": "https://example.org/a; https://example.org/b",
        "validation_status": "validated", "confidence": "high", "decision_reason": "Consenso.",
        "source_conflicts": "Anos divergentes.", "validated_at": "2026-08-13",
    },
    {
        "work_id": "work-0004", "title_pt_br": "Belas Maldições", "original_title": "Good Omens",
        "authors": "Neil Gaiman; Terry Pratchett", "original_language": "inglês",
        "first_publication_year": "1990", "work_type": "romance", "genres": "fantasia; humor",
        "themes": "apocalipse;  ; amizade", "edition_match": "representative",
        "edition_title": "Belas Maldições", "edition_language": "português", "isbn10": "85-286-1234-x",
        "publisher": "Bertrand", "edition_publication_year": "2019", "physical_format": "desconhecido",
        "validation_status": "validated", "confidence": "high", "decision_reason": "Consenso.",
        "validated_at": "2026-08-13",
    },
]

READINGS: List[Dict[str, str]] = [
    {"reading_sequence": "1", "work_id": "work-0003", "reread": "não", "original_entry": "A vegetariana - Han Kang"},
    {"reading_sequence": "2", "work_id": "work-0001", "reread": "não", "original_entry": "Os espiões - Luiz Fernando Veríssimo"},
    {"reading_sequence": "3", "work_id": "work-0002", "reread": "não", "original_entry": "Comédias - Verissimo"},
    {"reading_sequence": "4", "work_id": "work-0004", "reread": "não", "original_entry": "Belas maldições"},
    {"reading_sequence": "5", "work_id": "work-0003", "reread": "sim", "original_entry": "A vegetariana (de novo)"},
]

SOURCES: List[Dict[str, str]] = [
    {"work_id": "work-0001", "provider": "literal", "identifier": "lit-book-1", "url": "",
     "fields_supported": "edição, ISBN, editora, capa"},
    {"work_id": "work-0003", "provider": "openlibrary", "identifier": "/works/OL1W",
     "url": "https://openlibrary.org/works/OL1W", "fields_supported": "obra"},
    {"work_id": "work-0003", "provider": "busca_web", "identifier": "", "url": "https://example.org/a",
     "fields_supported": "complementação"},
]


def write_csv(path: Path, columns: List[str], rows: List[Dict[str, str]]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c, "") for c in columns})


def write_legacy(directory: Path, works: Optional[List[Dict[str, str]]] = None,
                 readings: Optional[List[Dict[str, str]]] = None,
                 sources: Optional[List[Dict[str, str]]] = None,
                 drop_column: Optional[str] = None) -> Path:
    """Grava obras.csv, leituras.csv e fontes.csv com todas as colunas obrigatórias."""
    directory.mkdir(parents=True, exist_ok=True)
    data = {
        "obras.csv": WORKS if works is None else works,
        "leituras.csv": READINGS if readings is None else readings,
        "fontes.csv": SOURCES if sources is None else sources,
    }
    for name, rows in data.items():
        columns = [c for c in REQUIRED_COLUMNS[name] if c != drop_column]
        write_csv(directory / name, columns, rows)
    return directory


# -- temas canônicos (F2.3) -------------------------------------------------

# Cobre os temas do legado sintético: união (segredo → identidade), "só tag"
# (família), dois destinos não são necessários aqui (ver test_themes.py).
THEMES_CONFIG: Dict[str, Any] = {
    "version": 1,
    "targetSize": [1, 10],
    "taxonomy": ["amizade", "corpo", "escola", "fim do mundo", "identidade", "violência"],
    "map": {
        "identidade": ["identidade"],
        "segredo": ["identidade"],
        "escola": ["escola"],
        "corpo": ["corpo"],
        "família": [],
        "violência": ["violência"],
        "apocalipse": ["fim do mundo"],
        "amizade": ["amizade"],
    },
}


def themes_config():
    """ThemeConfig de teste (cópia independente)."""
    from lib.themes import ThemeConfig

    return ThemeConfig.from_dict(copy.deepcopy(THEMES_CONFIG))


def write_themes_config(config_dir: Path) -> Path:
    """Grava o themes.json de teste em `config_dir` (cria a pasta)."""
    import json

    config_dir.mkdir(parents=True, exist_ok=True)
    path = config_dir / "themes.json"
    path.write_text(json.dumps(THEMES_CONFIG, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def make_catalog_dir(directory: Path) -> Path:
    """Diretório de catálogo vazio com os schemas reais copiados."""
    shutil.copytree(SCHEMA_DIR, directory / "schema")
    return directory


# -- catálogo mínimo válido (em memória) ------------------------------------

def _work(slug: str, authors: List[str]) -> Dict[str, Any]:
    return {
        "slug": slug, "title": slug.replace("-", " ").title(), "originalTitle": None,
        "originalTitleRomanized": None, "authors": authors, "language": "português",
        "firstPublished": 2000, "type": "romance", "genres": ["humor"], "themes": ["memória"],
        "edition": {"title": None, "language": "português", "publisher": "Editora", "year": 2001,
                    "isbn13": "9788535900000", "isbn10": None, "format": None, "match": "representative"},
        "cover": None, "catalogerNote": None, "confidence": "high", "references": [],
        "legacyId": None,
        "audit": {"validationStatus": "validated", "sourceConflicts": None, "validatedAt": "2026-08-13"},
    }


def _author(slug: str) -> Dict[str, Any]:
    return {"slug": slug, "name": slug.replace("-", " ").title(), "aliases": [], "country": "BR",
            "countrySource": "wikidata-citizenship", "languages": ["português"],
            "primaryLanguage": "português", "wikidata": None, "photo": None, "references": []}


def summary(scope: str, text: str = "Texto.", approved: bool = False, **extra: Any) -> Dict[str, Any]:
    item = {"scope": scope, "text": text, "approved": approved, "updatedAt": "2026-11-01",
            "source": None, "sourceUrl": None, "sourceLanguage": None, "model": None,
            "promptVersion": None, "editedBy": None}
    item.update(extra)
    return item


def valid_catalog():
    """Catálogo pequeno e válido: 2 obras, 2 autorias, 3 leituras (1 releitura)."""
    from lib.checks import Catalog

    return Catalog(
        works={"obra-a": _work("obra-a", ["autora-a"]), "obra-b": _work("obra-b", ["autora-a", "autor-b"])},
        authors={"autora-a": _author("autora-a"), "autor-b": _author("autor-b")},
        readings={"readings": [
            {"sequence": 1, "year": None, "work": "obra-a", "reread": False, "originalEntry": "A", "notes": None},
            {"sequence": 2, "year": 2014, "work": "obra-b", "reread": False, "originalEntry": "B", "notes": None},
            {"sequence": 3, "year": 2015, "work": "obra-a", "reread": True, "originalEntry": "A de novo", "notes": None},
        ]},
        summaries={"summaries": []},
        vocabularies={"languages": ["português"], "workTypes": ["romance"], "genres": ["humor"],
                      "themes": ["memória"],
                      "countries": [{"code": "BR", "name": "Brasil", "languages": ["português"]}]},
    )


def clone(obj: Any) -> Any:
    return copy.deepcopy(obj)


def tree_bytes(directory: Path) -> Dict[str, bytes]:
    """Conteúdo de todos os arquivos sob `directory`, para comparar byte a byte."""
    return {str(p.relative_to(directory)): p.read_bytes()
            for p in sorted(directory.rglob("*")) if p.is_file()}


# -- HTTP simulado ------------------------------------------------------------

class FakeTransport:
    """Transporte HTTP falso: casa (método, trecho da URL) com respostas prontas.

    `routes` é uma lista de (método, trecho, resposta). A resposta pode ser um
    dict/list (JSON 200), uma tupla (status, corpo, headers) ou uma função
    (url, body) -> qualquer um dos anteriores. Rotas mais específicas devem vir
    primeiro. Toda chamada fica registrada em `calls`.
    """

    def __init__(self, routes=None):
        self.routes = list(routes or [])
        self.calls = []

    def add(self, method, fragment, response):
        self.routes.append((method, fragment, response))
        return self

    def __call__(self, method, url, headers, body, timeout):
        import json as _json

        self.calls.append({"method": method, "url": url, "headers": dict(headers),
                           "body": _json.loads(body) if body else None})
        for r_method, fragment, response in self.routes:
            if r_method == method and fragment in url:
                if callable(response):
                    response = response(url, _json.loads(body) if body else None)
                if isinstance(response, tuple):
                    status, payload, resp_headers = (list(response) + [{}])[:3]
                else:
                    status, payload, resp_headers = 200, response, {}
                if isinstance(payload, (bytes, bytearray)):
                    data = bytes(payload)
                else:
                    data = _json.dumps(payload).encode("utf-8")
                return status, dict(resp_headers), data
        return 404, {}, b'{"error": "rota nao simulada"}'

    def count(self, fragment):
        return sum(1 for c in self.calls if fragment in c["url"])


def tiny_png(width=600, height=800) -> bytes:
    import struct as _struct
    import zlib as _zlib

    def chunk(kind, data):
        return _struct.pack(">I", len(data)) + kind + data + _struct.pack(">I", _zlib.crc32(kind + data))

    ihdr = _struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", _zlib.compress(b"\x00\x00\x00\x00")) \
        + chunk(b"IEND", b"")


def tiny_jpeg(width=500, height=700) -> bytes:
    import struct as _struct

    app0 = b"\xff\xe0" + _struct.pack(">H", 16) + b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    sof = b"\xff\xc0" + _struct.pack(">HBHHB", 11, 8, height, width, 1) + b"\x01\x11\x00"
    return b"\xff\xd8" + app0 + sof + b"\xff\xda\x00\x08\x01\x01\x00\x00\x3f\x00" + b"\x00" * 10 + b"\xff\xd9"

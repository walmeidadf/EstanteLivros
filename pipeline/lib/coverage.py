"""Relatório de cobertura do catálogo (docs/plans/cobertura.md)."""

from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List, Tuple

from .checks import Catalog
from .names import AuthorGroup, find_suspects, unify_key
from .titles import has_non_latin

Row = Tuple[str, int, int]


def _pct(filled: int, total: int) -> str:
    if total == 0:
        return "—"
    return f"{100 * filled / total:.1f}%".replace(".", ",")


def _count(items: Iterable[Dict[str, Any]], pred: Callable[[Dict[str, Any]], bool]) -> int:
    return sum(1 for item in items if pred(item))


def work_rows(works: List[Dict[str, Any]]) -> List[Row]:
    translated = [w for w in works if w.get("language") != "português"]
    non_latin = [w for w in works if w.get("originalTitle") and has_non_latin(w["originalTitle"])]
    edition = lambda w, k: (w.get("edition") or {}).get(k)  # noqa: E731
    return [
        ("Capa", _count(works, lambda w: w.get("cover") is not None), len(works)),
        ("Título original (obras não escritas em português)",
         _count(translated, lambda w: bool(w.get("originalTitle"))), len(translated)),
        ("Romanização (títulos originais não latinos)",
         _count(non_latin, lambda w: bool(w.get("originalTitleRomanized"))), len(non_latin)),
        ("Ano de primeira publicação", _count(works, lambda w: w.get("firstPublished") is not None), len(works)),
        ("ISBN-13", _count(works, lambda w: edition(w, "isbn13") is not None), len(works)),
        ("Editora", _count(works, lambda w: edition(w, "publisher") is not None), len(works)),
    ]


def author_rows(authors: List[Dict[str, Any]]) -> List[Row]:
    return [
        ("País", _count(authors, lambda a: a.get("country") is not None), len(authors)),
        ("Bio", _count(authors, lambda a: a.get("bio") is not None), len(authors)),
        ("Foto", _count(authors, lambda a: a.get("photo") is not None), len(authors)),
    ]


def _table(rows: List[Row]) -> List[str]:
    lines = ["| Campo | Preenchidos | Total | % |", "|---|---:|---:|---:|"]
    lines += [f"| {name} | {filled} | {total} | {_pct(filled, total)} |" for name, filled, total in rows]
    return lines


def render_coverage(cat: Catalog) -> str:
    works = [w for _, w in sorted(cat.works.items()) if isinstance(w, dict)]
    authors = [a for _, a in sorted(cat.authors.items()) if isinstance(a, dict)]
    readings = cat.readings.get("readings", []) if isinstance(cat.readings, dict) else []

    lines = [
        "# Cobertura do catálogo",
        "",
        "Gerado por `python3 pipeline/validate_catalog.py`. Não editar à mão.",
        "",
        f"{len(works)} obras · {len(authors)} autorias · {len(readings)} leituras.",
        "",
        "## Obras",
        "",
        *_table(work_rows(works)),
        "",
        "## Autorias",
        "",
        *_table(author_rows(authors)),
        "",
        "## Autorias unificadas",
        "",
    ]
    unified = [a for a in authors if a.get("aliases")]
    if unified:
        lines += [f"- {a['name']} ← {', '.join(a['aliases'])}" for a in unified]
    else:
        lines.append("Nenhuma.")

    lines += ["", "## Suspeitas de autoria (não unificadas)", ""]
    groups = [AuthorGroup(unify_key(a["name"]), a["name"]) for a in authors if a.get("name")]
    suspects = find_suspects(groups)
    if suspects:
        lines.append("Mesmo sobrenome e mesmas iniciais. Unificar, se for o caso, em `pipeline/config/author_overrides.json`.")
        lines.append("")
        lines += [f"- {a} × {b}" for a, b in suspects]
    else:
        lines.append("Nenhuma.")

    dated = sum(1 for r in readings if r.get("year") is not None)
    rereads = sum(1 for r in readings if r.get("reread") is True)
    lines += [
        "",
        "## Leituras",
        "",
        "| Métrica | Valor |",
        "|---|---:|",
        f"| Total | {len(readings)} |",
        f"| Com ano | {dated} |",
        f"| Sem ano | {len(readings) - dated} |",
        f"| Releituras | {rereads} |",
        "",
    ]
    return "\n".join(lines)

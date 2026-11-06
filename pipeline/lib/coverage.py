"""Relatório de cobertura do catálogo (docs/plans/cobertura.md)."""

from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

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
    cover = lambda w, k: (w.get("cover") or {}).get(k)  # noqa: E731
    return [
        ("Capa com URL de origem", _count(works, lambda w: w.get("cover") is not None), len(works)),
        ("Capa local escolhida (mestre em `catalog/media/covers/`)",
         _count(works, lambda w: cover(w, "file") is not None), len(works)),
        ("Capa revisada: fica a tipográfica", _count(works, lambda w: cover(w, "display") == "typographic"),
         len(works)),
        ("Título original (obras não escritas em português)",
         _count(translated, lambda w: bool(w.get("originalTitle"))), len(translated)),
        ("Romanização (títulos originais não latinos)",
         _count(non_latin, lambda w: bool(w.get("originalTitleRomanized"))), len(non_latin)),
        ("Ano de primeira publicação", _count(works, lambda w: w.get("firstPublished") is not None), len(works)),
        ("ISBN-13", _count(works, lambda w: edition(w, "isbn13") is not None), len(works)),
        ("Editora", _count(works, lambda w: edition(w, "publisher") is not None), len(works)),
    ]


def author_rows(authors: List[Dict[str, Any]], bios: Optional[Dict[str, Dict[str, Any]]] = None) -> List[Row]:
    bios = bios or {}
    total = len(authors)
    photo = lambda a: a.get("photo") or {}  # noqa: E731
    wd = lambda a: (a.get("wikidata") or {}).get("status")  # noqa: E731
    return [
        ("Identificada no Wikidata (confirmada, provável ou manual)",
         _count(authors, lambda a: wd(a) in ("confirmed", "probable", "manual")), total),
        ("País", _count(authors, lambda a: a.get("country") is not None), total),
        ("Foto", _count(authors, lambda a: a.get("photo") is not None), total),
        ("Foto do Commons", _count(authors, lambda a: photo(a).get("source") == "commons"), total),
        ("Bio proposta (inclui aprovadas)", _count(authors, lambda a: a["slug"] in bios), total),
        ("Bio aprovada", _count(authors, lambda a: bios.get(a["slug"], {}).get("approved") is True), total),
    ]


def _status_table(authors: List[Dict[str, Any]]) -> List[str]:
    labels = [("confirmed", "confirmada por obra"), ("probable", "provável"), ("manual", "manual"),
              ("ambiguous", "ambígua"), ("not_found", "não encontrada"), ("none", "sem Wikidata (manual)"),
              (None, "não processada")]
    counts: Dict[Optional[str], int] = {}
    for a in authors:
        status = (a.get("wikidata") or {}).get("status")
        counts[status] = counts.get(status, 0) + 1
    lines = ["| Identificação | Autorias |", "|---|---:|"]
    lines += [f"| {label} | {counts.get(key, 0)} |" for key, label in labels if counts.get(key)]
    return lines


def _table(rows: List[Row]) -> List[str]:
    lines = ["| Campo | Preenchidos | Total | % |", "|---|---:|---:|---:|"]
    lines += [f"| {name} | {filled} | {total} | {_pct(filled, total)} |" for name, filled, total in rows]
    return lines


def render_coverage(cat: Catalog) -> str:
    works = [w for _, w in sorted(cat.works.items()) if isinstance(w, dict)]
    authors = [a for _, a in sorted(cat.authors.items()) if isinstance(a, dict)]
    readings = cat.readings.get("readings", []) if isinstance(cat.readings, dict) else []
    summary_items = cat.summaries.get("summaries", []) if isinstance(cat.summaries, dict) else []
    bios = {s["scope"].split(":", 1)[1]: s for s in summary_items
            if isinstance(s, dict) and str(s.get("scope", "")).startswith("autoria:")}
    used_media = {(a.get("photo") or {}).get("file") for a in authors}
    orphans = sorted(m for m in (cat.media or set()) if m.startswith("authors/") and m not in used_media)

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
        *_table(author_rows(authors, bios)),
        "",
        *_status_table(authors),
        "",
    ]
    by_status = lambda s: [a for a in authors if (a.get("wikidata") or {}).get("status") == s]  # noqa: E731
    pending_lists = [
        ("Identificação ambígua (fixar em `pipeline/config/author_wikidata.json`)", by_status("ambiguous")),
        ("Não encontradas no Wikidata", by_status("not_found")),
        ("Identificadas, sem país", [a for a in authors if (a.get("wikidata") or {}).get("id") and not a.get("country")]),
    ]
    for title, items in pending_lists:
        if items:
            lines += [f"### {title}", ""]
            lines += [f"- {a['name']} (`{a['slug']}`)" for a in items]
            lines.append("")
    if orphans:
        lines += ["### Fotos órfãs em `catalog/media/`", ""]
        lines += [f"- `{o}`" for o in orphans]
        lines.append("")
    lines += [
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

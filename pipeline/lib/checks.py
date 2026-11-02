"""Regras de integridade e invariantes do catálogo.

Usado tanto pela migração (sobre o modelo em memória) quanto pelo validador
(sobre os arquivos em disco). Todas as regras rodam até o fim.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .schema import load_schema, validate

# Leituras 1..UNDATED_HEAD do caderno não têm ano (o registro 54 inicia 2014).
UNDATED_HEAD = 53

SCHEMA_FILES = {
    "work": "work.schema.json",
    "author": "author.schema.json",
    "readings": "readings.schema.json",
    "summaries": "summaries.schema.json",
    "vocabularies": "vocabularies.schema.json",
}


@dataclass(frozen=True)
class Issue:
    file: str
    path: str
    code: str
    message: str

    def format(self) -> str:
        return f"{self.file}  {self.path}  {self.code}  {self.message}"


@dataclass
class Catalog:
    """Catálogo em memória. `works`/`authors` são indexados pelo nome do arquivo sem `.json`."""

    works: Dict[str, Any] = field(default_factory=dict)
    authors: Dict[str, Any] = field(default_factory=dict)
    readings: Any = None
    summaries: Any = None
    vocabularies: Any = None
    load_issues: List[Issue] = field(default_factory=list)
    # Arquivos disponíveis em catalog/media/ (caminhos relativos, ex.: "authors/x.jpg").
    # None = não conferir (catálogos montados em memória sem mídia).
    media: Optional[Set[str]] = None


def scan_media(media_dir: Path) -> Set[str]:
    if not media_dir.is_dir():
        return set()
    return {p.relative_to(media_dir).as_posix() for p in media_dir.rglob("*")
            if p.is_file() and not p.name.startswith(".")}


def _load_file(path: Path, rel: str, issues: List[Issue]) -> Any:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        issues.append(Issue(rel, "(arquivo)", "file.missing", "arquivo ausente"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        issues.append(Issue(rel, "(arquivo)", "file.json", f"JSON inválido: {exc}"))
    return None


def load_catalog(catalog_dir: Path) -> Catalog:
    cat = Catalog()
    for sub, target in (("works", cat.works), ("authors", cat.authors)):
        folder = catalog_dir / sub
        if not folder.is_dir():
            cat.load_issues.append(Issue(f"catalog/{sub}/", "(pasta)", "file.missing", "pasta ausente"))
            continue
        for path in sorted(folder.glob("*.json")):
            data = _load_file(path, f"catalog/{sub}/{path.name}", cat.load_issues)
            if data is not None:
                target[path.stem] = data
    cat.readings = _load_file(catalog_dir / "readings.json", "catalog/readings.json", cat.load_issues)
    cat.summaries = _load_file(catalog_dir / "summaries.json", "catalog/summaries.json", cat.load_issues)
    cat.vocabularies = _load_file(catalog_dir / "vocabularies.json", "catalog/vocabularies.json", cat.load_issues)
    cat.media = scan_media(catalog_dir / "media")
    return cat


def load_schemas(schema_dir: Path) -> Dict[str, Dict[str, Any]]:
    return {name: load_schema(schema_dir / fname) for name, fname in SCHEMA_FILES.items()}


# -- helpers ---------------------------------------------------------------

def _readings(cat: Catalog) -> List[Dict[str, Any]]:
    if isinstance(cat.readings, dict) and isinstance(cat.readings.get("readings"), list):
        return [r for r in cat.readings["readings"] if isinstance(r, dict)]
    return []


def _summaries(cat: Catalog) -> List[Dict[str, Any]]:
    if isinstance(cat.summaries, dict) and isinstance(cat.summaries.get("summaries"), list):
        return [s for s in cat.summaries["summaries"] if isinstance(s, dict)]
    return []


def _as_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


# -- regras ----------------------------------------------------------------

def check_schema_rule(cat: Catalog, schemas: Dict[str, Dict[str, Any]]) -> List[Issue]:
    issues = []
    for stem, data in sorted(cat.works.items()):
        for path, msg in validate(data, schemas["work"]):
            issues.append(Issue(f"catalog/works/{stem}.json", path, "schema", msg))
    for stem, data in sorted(cat.authors.items()):
        for path, msg in validate(data, schemas["author"]):
            issues.append(Issue(f"catalog/authors/{stem}.json", path, "schema", msg))
    for name in ("readings", "summaries", "vocabularies"):
        data = getattr(cat, name)
        if data is None:
            continue
        for path, msg in validate(data, schemas[name]):
            issues.append(Issue(f"catalog/{name}.json", path, "schema", msg))
    return issues


def check_file_slug(cat: Catalog) -> List[Issue]:
    issues = []
    for sub, items in (("works", cat.works), ("authors", cat.authors)):
        seen: Dict[str, str] = {}
        for stem, data in sorted(items.items()):
            slug = data.get("slug") if isinstance(data, dict) else None
            rel = f"catalog/{sub}/{stem}.json"
            if slug != stem:
                issues.append(Issue(rel, "slug", "file.slug", f"slug {slug!r} difere do nome do arquivo"))
            if isinstance(slug, str):
                if slug in seen:
                    issues.append(Issue(rel, "slug", "file.slug", f"slug duplicado (também em {seen[slug]})"))
                else:
                    seen[slug] = rel
    return issues


def check_references(cat: Catalog) -> List[Issue]:
    issues = []
    readings = _readings(cat)
    read_works = set()
    for i, r in enumerate(readings):
        work = r.get("work")
        read_works.add(work)
        if work not in cat.works:
            issues.append(Issue("catalog/readings.json", f"readings[{i}].work", "ref.reading-work",
                                f"obra {work!r} não existe (seq {r.get('sequence')})"))
    used_authors = set()
    for stem, data in sorted(cat.works.items()):
        for j, author in enumerate(_as_list(data.get("authors"))):
            used_authors.add(author)
            if author not in cat.authors:
                issues.append(Issue(f"catalog/works/{stem}.json", f"authors[{j}]", "ref.work-author",
                                    f"autoria {author!r} não existe"))
        if stem not in read_works:
            issues.append(Issue(f"catalog/works/{stem}.json", "(obra)", "orphan.work", "obra sem nenhuma leitura"))
    for stem in sorted(cat.authors):
        if stem not in used_authors:
            issues.append(Issue(f"catalog/authors/{stem}.json", "(autoria)", "orphan.author", "autoria sem nenhuma obra"))
    return issues


def check_sequence(cat: Catalog, undated_head: Optional[int] = None) -> List[Issue]:
    undated_head = UNDATED_HEAD if undated_head is None else undated_head
    issues = []
    rel = "catalog/readings.json"
    readings = _readings(cat)
    seqs = [r.get("sequence") for r in readings]
    ints = [s for s in seqs if isinstance(s, int) and not isinstance(s, bool)]
    if ints:
        counts: Dict[int, int] = defaultdict(int)
        for s in ints:
            counts[s] += 1
        for s in sorted(k for k, v in counts.items() if v > 1):
            issues.append(Issue(rel, "readings", "seq.contiguous", f"sequência {s} repetida"))
        missing = sorted(set(range(1, max(ints) + 1)) - set(ints))
        if missing:
            issues.append(Issue(rel, "readings", "seq.contiguous", f"sequências ausentes: {missing}"))
    if ints != sorted(ints):
        issues.append(Issue(rel, "readings", "seq.contiguous", "leituras fora de ordem de sequência"))

    ordered = sorted(((i, r) for i, r in enumerate(readings) if isinstance(r.get("sequence"), int)),
                     key=lambda item: item[1]["sequence"])
    last_year: Optional[int] = None
    last_seq: Optional[int] = None
    first_by_work: Dict[str, int] = {}
    for idx, r in ordered:
        seq, year = r["sequence"], r.get("year")
        if isinstance(year, int):
            if last_year is not None and year < last_year:
                issues.append(Issue(rel, f"readings[{idx}].year", "year.monotonic",
                                    f"{year} < {last_year} (seq {seq}, anterior seq {last_seq})"))
            else:
                last_year, last_seq = year, seq
        if seq <= undated_head and year is not None:
            issues.append(Issue(rel, f"readings[{idx}].year", "year.undated-head",
                                f"leituras 1–{undated_head} não têm ano (seq {seq} tem {year})"))
        work = r.get("work")
        is_first = work not in first_by_work
        first_by_work.setdefault(work, seq)
        if r.get("reread") is True and is_first:
            issues.append(Issue(rel, f"readings[{idx}].reread", "reread.order",
                                f"primeira leitura de {work!r} marcada como releitura (seq {seq})"))
        if r.get("reread") is False and not is_first:
            issues.append(Issue(rel, f"readings[{idx}].reread", "reread.order",
                                f"leitura repetida de {work!r} sem reread (seq {seq}, primeira {first_by_work[work]})"))
    return issues


def check_vocab(cat: Catalog) -> List[Issue]:
    issues: List[Issue] = []
    vocab = cat.vocabularies if isinstance(cat.vocabularies, dict) else {}
    langs = set(_as_list(vocab.get("languages")))
    types = set(_as_list(vocab.get("workTypes")))
    genres = set(_as_list(vocab.get("genres")))
    themes = set(_as_list(vocab.get("themes")))
    countries = {c.get("code") for c in _as_list(vocab.get("countries")) if isinstance(c, dict)}

    def need(value: Any, allowed: set, rel: str, path: str, what: str) -> None:
        if isinstance(value, str) and value not in allowed:
            issues.append(Issue(rel, path, "vocab", f"{what} {value!r} fora do vocabulário"))

    for stem, w in sorted(cat.works.items()):
        rel = f"catalog/works/{stem}.json"
        need(w.get("language"), langs, rel, "language", "idioma")
        need(w.get("type"), types, rel, "type", "tipo")
        for i, g in enumerate(_as_list(w.get("genres"))):
            need(g, genres, rel, f"genres[{i}]", "gênero")
        for i, t in enumerate(_as_list(w.get("themes"))):
            need(t, themes, rel, f"themes[{i}]", "tema")
    for stem, a in sorted(cat.authors.items()):
        rel = f"catalog/authors/{stem}.json"
        need(a.get("primaryLanguage"), langs, rel, "primaryLanguage", "idioma")
        for i, lang in enumerate(_as_list(a.get("languages"))):
            need(lang, langs, rel, f"languages[{i}]", "idioma")
        country = a.get("country")
        if isinstance(country, str) and country not in countries:
            issues.append(Issue(rel, "country", "vocab.country", f"país {country!r} fora de vocabularies.countries"))
    for i, c in enumerate(_as_list(vocab.get("countries"))):
        for j, lang in enumerate(_as_list(c.get("languages") if isinstance(c, dict) else None)):
            need(lang, langs, "catalog/vocabularies.json", f"countries[{i}].languages[{j}]", "idioma")
    return issues


def check_photos(cat: Catalog) -> List[Issue]:
    if cat.media is None:
        return []
    issues = []
    for stem, a in sorted(cat.authors.items()):
        photo = a.get("photo") if isinstance(a, dict) else None
        if isinstance(photo, dict) and isinstance(photo.get("file"), str) and photo["file"] not in cat.media:
            issues.append(Issue(f"catalog/authors/{stem}.json", "photo.file", "photo.file",
                                f"arquivo catalog/media/{photo['file']} não existe"))
    return issues


def check_summaries(cat: Catalog) -> List[Issue]:
    issues = []
    rel = "catalog/summaries.json"
    years = {r.get("year") for r in _readings(cat) if isinstance(r.get("year"), int)}
    countries = {a.get("country") for a in cat.authors.values() if isinstance(a, dict) and a.get("country")}
    seen_scopes: Dict[str, int] = {}
    for i, s in enumerate(_summaries(cat)):
        scope_key = s.get("scope")
        if isinstance(scope_key, str):
            if scope_key in seen_scopes:
                issues.append(Issue(rel, f"summaries[{i}].scope", "summary.scope-unique",
                                    f"escopo {scope_key!r} repetido (também em summaries[{seen_scopes[scope_key]}])"))
            else:
                seen_scopes[scope_key] = i
        if s.get("approved") is not True:
            continue
        path = f"summaries[{i}]"
        if not isinstance(s.get("text"), str) or not s["text"].strip():
            issues.append(Issue(rel, f"{path}.text", "summary.approved", "resumo aprovado sem texto"))
        scope = s.get("scope")
        if not isinstance(scope, str) or ":" not in scope:
            issues.append(Issue(rel, f"{path}.scope", "summary.approved", f"escopo inválido: {scope!r}"))
            continue
        kind, value = scope.split(":", 1)
        ok = {
            "autoria": lambda v: v in cat.authors,
            "ano": lambda v: v.isdigit() and int(v) in years,
            "pais": lambda v: v in countries,
        }.get(kind, lambda v: False)(value)
        if not ok:
            issues.append(Issue(rel, f"{path}.scope", "summary.approved", f"escopo {scope!r} não aponta para nada existente"))
    return issues


def check_catalog(cat: Catalog, schemas: Dict[str, Dict[str, Any]],
                  undated_head: Optional[int] = None) -> List[Issue]:
    issues = list(cat.load_issues)
    issues += check_schema_rule(cat, schemas)
    issues += check_file_slug(cat)
    issues += check_references(cat)
    issues += check_sequence(cat, undated_head)
    issues += check_vocab(cat)
    issues += check_photos(cat)
    issues += check_summaries(cat)
    return issues

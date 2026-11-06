"""Montagem do modelo canônico a partir dos CSVs do legado."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from .checks import Catalog
from .legacy_reader import Cell, LegacyData, LegacyDataError, integer, split_list, text, yes_no
from .names import AuthorGroup, find_suspects, group_names, languages_for, unify_key
from .slugs import SlugRegistry, strip_accents
from .themes import ThemeConfig, apply as apply_themes
from .titles import split_original
from .work_overrides import WorkOverride, apply as apply_work_override

PROVIDER_ALIASES = {"busca_web": "web"}
UNKNOWN_VALUES = {"desconhecido"}

# Colunas de obras.csv que viram referências: (coluna id, coluna url, provider, campos)
REFERENCE_COLUMNS = [
    ("literal_book_id", "literal_url", "literal", "edição"),
    ("literal_work_id", None, "literal", "obra"),
    ("openlibrary_work_id", "openlibrary_url", "openlibrary", "obra"),
    ("openlibrary_edition_id", None, "openlibrary", "edição"),
    ("google_books_id", "google_books_url", "google_books", "edição"),
    ("wikidata_id", "wikidata_url", "wikidata", "obra"),
]


class ThemeMappingError(LegacyDataError):
    """Tema original sem destino no themes.json, ou obra que ficaria sem tema."""


@dataclass
class BuildResult:
    catalog: Catalog
    files: Dict[str, Any]
    unified: List[AuthorGroup] = field(default_factory=list)
    suspects: List[Tuple[str, str]] = field(default_factory=list)
    # (slug, campo): correção de work_overrides.json que o CSV já traz igual
    redundant_overrides: List[Tuple[str, str]] = field(default_factory=list)


def vocab_sort_key(value: str) -> Tuple[str, str]:
    return strip_accents(value).lower(), value


def _cell(row: Mapping[str, str], file: str, column: str) -> Cell:
    return Cell(file, int(row.get("__line__", "0")), column)


def _isbn(value: Optional[str], allow_x: bool) -> Optional[str]:
    raw = text(value)
    if raw is None:
        return None
    pattern = r"[^0-9X]" if allow_x else r"[^0-9]"
    return re.sub(pattern, "", raw.upper()) or None


def _known(value: Optional[str]) -> Optional[str]:
    value = text(value)
    return None if value is None or value.lower() in UNKNOWN_VALUES else value


def _existing_countries(existing: Optional[Catalog]) -> List[Dict[str, Any]]:
    vocab = existing.vocabularies if existing is not None else None
    if isinstance(vocab, dict) and isinstance(vocab.get("countries"), list):
        return vocab["countries"]
    return []


_ENRICHED_COVER_FIELDS = ("file", "license", "credit", "focus", "display")


def merge_cover(cover_url: Optional[str], cover_source: Optional[str],
                previous: Optional[Mapping[str, Any]]) -> Optional[Dict[str, Any]]:
    """Recompõe a capa do CSV preservando os campos enriquecidos (F2 · capas).

    `sourceUrl`/`source` vêm do legado; `file`, `license`, `credit`, `focus` e
    `display` são mantidos do catálogo atual, mesmo quando o CSV deixa de trazer
    uma URL (a capa local escolhida não se perde)."""
    prev = previous if isinstance(previous, dict) else {}
    enriched = {k: prev[k] for k in _ENRICHED_COVER_FIELDS
                if isinstance(prev, dict) and prev.get(k) is not None}
    # O `file` e a proveniência dele andam juntos. Se a Lila escolheu uma imagem de
    # OUTRA origem que a do legado (ex.: Open Library no lugar da Literal), a
    # sourceUrl/source do arquivo são mantidas; senão o legado manda (inclusive
    # para corrigir uma `source` gravada errada).
    other_origin = bool(prev.get("file")) and prev.get("sourceUrl") not in (None, cover_url)
    if cover_url and not other_origin:
        return {"sourceUrl": cover_url, "source": cover_source, **enriched}
    # Sem URL no legado, ou arquivo de outra origem: só sobra capa se já havia
    # campo enriquecido, com a proveniência do catálogo atual — o schema exige
    # sourceUrl numa capa não nula.
    if not enriched or not prev.get("sourceUrl"):
        return None
    return {"sourceUrl": prev.get("sourceUrl"), "source": prev.get("source"), **enriched}


def _theme_problems(unmapped: Mapping[str, List[str]],
                    without_theme: List[Tuple[str, List[str]]]) -> str:
    lines: List[str] = []
    if unmapped:
        lines.append(f"{len(unmapped)} tema(s) sem mapeamento em pipeline/config/themes.json:")
        for original in sorted(unmapped, key=lambda s: (strip_accents(s).lower(), s)):
            titles = unmapped[original]
            shown = ", ".join(titles[:3]) + (f" e mais {len(titles) - 3}" if len(titles) > 3 else "")
            lines.append(f"  {original!r} ({shown})")
    if without_theme:
        lines.append(f"{len(without_theme)} obra(s) ficariam sem tema canônico:")
        for title, originals in without_theme:
            lines.append(f"  {title}: {', '.join(originals) or '(sem temas no CSV)'}")
    return "\n".join(lines)


def build_references(work_row: Mapping[str, str], sources: Iterable[Mapping[str, str]]) -> List[Dict[str, Any]]:
    refs: List[Dict[str, Any]] = []
    seen = set()

    def add(provider: str, ref_id: Optional[str], url: Optional[str], fields: Optional[str]) -> None:
        provider = PROVIDER_ALIASES.get(provider, provider)
        if ref_id is None and url is None:
            return
        key = (provider, ref_id, url)
        if key in seen:
            return
        seen.add(key)
        refs.append({"provider": provider, "id": ref_id, "url": url, "fields": fields})

    for src in sources:
        add(src["provider"].strip(), text(src.get("identifier")), text(src.get("url")),
            text(src.get("fields_supported")))
    for id_col, url_col, provider, fields in REFERENCE_COLUMNS:
        add(provider, text(work_row.get(id_col)), text(work_row.get(url_col)) if url_col else None, fields)
    for url in split_list(work_row.get("additional_reference_urls")):
        add("web", None, url, None)
    return refs


ENRICHED_AUTHOR_FIELDS = ("country", "countrySource", "wikidata", "photo")


def build(legacy: LegacyData, registry: SlugRegistry,
          overrides: Optional[Mapping[str, Mapping[str, str]]] = None,
          existing_summaries: Any = None,
          existing: Optional[Catalog] = None,
          themes: Optional[ThemeConfig] = None,
          work_overrides: Optional[Mapping[str, WorkOverride]] = None) -> BuildResult:
    """Monta o catálogo. `existing` é o catálogo atual: os campos enriquecidos
    das autorias e das capas (F2) e `vocabularies.countries` são preservados.

    `themes` (F2.3): com a configuração, cada obra recebe `themes` canônicos e
    `tags` (os originais); sem ela, `themes` fica como vem do CSV e não há `tags`
    (uso como biblioteca e fixtures antigas). A migração sempre a passa."""
    overrides = overrides or {}
    work_overrides = work_overrides or {}
    redundant_overrides: List[Tuple[str, str]] = []
    existing_authors = existing.authors if existing is not None else {}
    existing_works = existing.works if existing is not None else {}
    work_rows = sorted(legacy.works, key=lambda r: r["work_id"])
    work_ids = {r["work_id"] for r in work_rows}

    # -- leituras (primeiro, para saber a primeira sequence de cada obra) --
    reading_rows = []
    for row in legacy.readings:
        seq = integer(row["reading_sequence"], _cell(row, "leituras.csv", "reading_sequence"))
        if seq is None:
            raise LegacyDataError(f"{_cell(row, 'leituras.csv', 'reading_sequence').where()}: sequência vazia")
        if row["work_id"] not in work_ids:
            raise LegacyDataError(
                f"{_cell(row, 'leituras.csv', 'work_id').where()}: obra {row['work_id']!r} não existe em obras.csv")
        reading_rows.append((seq, row))
    reading_rows.sort(key=lambda item: item[0])
    first_seq: Dict[str, int] = {}
    for seq, row in reading_rows:
        first_seq.setdefault(row["work_id"], seq)

    # -- autorias --
    name_counts: Counter = Counter()
    for row in work_rows:
        for name in split_list(row["authors"]):
            name_counts[name] += 1
    groups = group_names(name_counts, overrides)
    for group in groups.values():
        if group.forced_slug:
            registry.reserve_author(group.forced_slug)
    author_slug: Dict[str, str] = {}  # chave de unificação -> slug
    for key, group in groups.items():
        author_slug[key] = registry.author_slug(key, group.name, group.forced_slug)

    # -- obras --
    works: Dict[str, Dict[str, Any]] = {}
    work_slug: Dict[str, str] = {}
    lang_occurrences: Dict[str, List[Tuple[str, int]]] = {}
    unmapped_themes: Dict[str, List[str]] = {}  # original -> títulos das obras
    works_without_theme: List[Tuple[str, List[str]]] = []
    for row in work_rows:
        file = "obras.csv"
        names = split_list(row["authors"])
        if not names:
            raise LegacyDataError(f"{_cell(row, file, 'authors').where()}: obra sem autoria")
        authors = []
        for name in names:
            slug = author_slug[unify_key(name)]
            if slug not in authors:
                authors.append(slug)
        title = text(row["title_pt_br"])
        if title is None:
            raise LegacyDataError(f"{_cell(row, file, 'title_pt_br').where()}: título vazio")
        first_published = integer(row["first_publication_year"], _cell(row, file, "first_publication_year"))
        first_name = groups[unify_key(names[0])].name
        slug = registry.work_slug(row["work_id"], f"{title} {first_name}", first_published)
        work_slug[row["work_id"]] = slug
        original, romanized = split_original(row["original_title"])
        original, romanized, first_published, corrected, redundant = apply_work_override(
            work_overrides.get(slug), original, romanized, first_published)
        redundant_overrides += [(slug, k) for k in redundant]
        language = text(row["original_language"])
        for a in authors:
            lang_occurrences.setdefault(a, []).append((language, first_seq.get(row["work_id"], 10**9)))
        cover_url = text(row["cover_url"])
        sources = [s for s in legacy.sources if s["work_id"] == row["work_id"]]
        raw_themes = split_list(row["themes"])
        theme_fields: Dict[str, Any] = {"themes": raw_themes}
        if themes is not None:
            applied = apply_themes(raw_themes, themes)
            for original in applied.unmapped:
                unmapped_themes.setdefault(original, []).append(title)
            if not applied.unmapped and not applied.themes:
                works_without_theme.append((title, raw_themes))
            theme_fields = {"themes": applied.themes, "tags": applied.tags}
        works[slug] = {
            "slug": slug,
            "title": title,
            "originalTitle": original,
            "originalTitleRomanized": romanized,
            "authors": authors,
            "language": language,
            "firstPublished": first_published,
            "type": text(row["work_type"]),
            "genres": split_list(row["genres"]),
            **theme_fields,
            "edition": {
                "title": text(row["edition_title"]),
                "language": text(row["edition_language"]),
                "publisher": text(row["publisher"]),
                "year": integer(row["edition_publication_year"], _cell(row, file, "edition_publication_year")),
                "isbn13": _isbn(row["isbn13"], allow_x=False),
                "isbn10": _isbn(row["isbn10"], allow_x=True),
                "format": _known(row["physical_format"]),
                "match": text(row["edition_match"]),
            },
            "cover": merge_cover(cover_url, text(row["cover_source"]),
                                 (existing_works.get(slug) or {}).get("cover")),
            "catalogerNote": text(row["decision_reason"]),
            "confidence": text(row["confidence"]),
            "references": build_references(row, sources),
            "legacyId": row["work_id"],
            "audit": {
                "validationStatus": text(row["validation_status"]),
                "sourceConflicts": text(row["source_conflicts"]),
                "validatedAt": text(row["validated_at"]),
                # Campos corrigidos em pipeline/config/work_overrides.json.
                **({"overrides": corrected} if corrected else {}),
            },
        }

    unknown_overrides = sorted(set(work_overrides) - set(works))
    if unknown_overrides:
        raise LegacyDataError(
            "work_overrides.json: obra(s) inexistente(s): " + ", ".join(unknown_overrides))
    if unmapped_themes or works_without_theme:
        raise ThemeMappingError(_theme_problems(unmapped_themes, works_without_theme))

    authors_out: Dict[str, Dict[str, Any]] = {}
    for key, group in groups.items():
        slug = author_slug[key]
        langs = [lang for lang in languages_for(lang_occurrences.get(slug, [])) if lang]
        previous = existing_authors.get(slug)
        previous = previous if isinstance(previous, dict) else {}
        authors_out[slug] = {
            "slug": slug,
            "name": group.name,
            "aliases": group.aliases,
            "country": previous.get("country"),
            "countrySource": previous.get("countrySource"),
            "languages": langs,
            "primaryLanguage": langs[0] if langs else None,
            "wikidata": previous.get("wikidata"),
            "photo": previous.get("photo"),
            # O legado não traz referências de autoria: tudo o que existe veio da F2.
            "references": list(previous.get("references") or []),
        }

    readings = []
    for seq, row in reading_rows:
        readings.append({
            "sequence": seq,
            "year": integer(row["read_year"], _cell(row, "leituras.csv", "read_year")),
            "work": work_slug[row["work_id"]],
            "reread": yes_no(row["reread"], _cell(row, "leituras.csv", "reread")),
            "originalEntry": text(row["original_entry"]),
            "notes": text(row["reading_notes"]),
        })

    def vocab(values: Iterable[Optional[str]]) -> List[str]:
        return sorted({v for v in values if v}, key=vocab_sort_key)

    vocabularies = {
        "languages": vocab(w["language"] for w in works.values()),
        "workTypes": vocab(w["type"] for w in works.values()),
        "genres": vocab(g for w in works.values() for g in w["genres"]),
        "themes": vocab(t for w in works.values() for t in w["themes"]),
        "countries": _existing_countries(existing),
    }
    summaries = existing_summaries if existing_summaries is not None else {"summaries": []}

    catalog = Catalog(
        works=dict(sorted(works.items())),
        authors=dict(sorted(authors_out.items())),
        readings={"readings": readings},
        summaries=summaries,
        vocabularies=vocabularies,
    )
    files: Dict[str, Any] = {f"works/{s}.json": w for s, w in catalog.works.items()}
    files.update({f"authors/{s}.json": a for s, a in catalog.authors.items()})
    files["readings.json"] = catalog.readings
    files["summaries.json"] = catalog.summaries
    files["vocabularies.json"] = catalog.vocabularies

    unified = [g for g in groups.values() if g.aliases or g.overridden]
    suspects = find_suspects(groups.values())
    return BuildResult(catalog, files, unified, suspects, sorted(redundant_overrides))

"""Temas canônicos: taxonomia, mapa dos originais e sua aplicação (F2.3).

`pipeline/config/themes.json` guarda a taxonomia (temas canônicos, ~40 a 60) e o
mapa de cada tema ORIGINAL do caderno para zero ou mais temas canônicos. Lista
vazia significa "só tag": o original não vira tema, mas fica em `tags`.

A migração (`lib/build.py`) aplica o mapa a cada obra; o validador reaplica o
mapa às `tags` do catálogo para detectar mapa editado sem migrar.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .names import unify_key

# Piso de obras para um tema valer uma página. Espelho de CLOUD_MIN_WORKS
# (app/src/lib/atlas.ts): mantenha os dois iguais. Só relatório, nunca bloqueia.
THEME_FLOOR = 5

SUPPORTED_VERSION = 1


class ThemeConfigError(Exception):
    """themes.json ausente ou inválido (a migração sai com código 2)."""


def theme_key(theme: str) -> str:
    """Chave de comparação: sem acento, minúsculo, espaços normalizados."""
    return unify_key(theme)


def slugify_theme(theme: str) -> str:
    """Espelho de `slugifyTheme` (app/src/lib/home.ts)."""
    text = unicodedata.normalize("NFD", theme)
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


@dataclass
class ThemeConfig:
    taxonomy: List[str]
    # chave de comparação do original -> temas canônicos
    mapping: Dict[str, List[str]]
    # grafia como escrita no arquivo, por chave (para mensagens e revisão)
    spelling: Dict[str, str] = field(default_factory=dict)
    target_size: Tuple[int, int] = (40, 60)
    version: int = SUPPORTED_VERSION

    @classmethod
    def load(cls, path: Path) -> "ThemeConfig":
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except FileNotFoundError:
            raise ThemeConfigError(f"{path} não existe (veja docs/specs/temas)") from None
        except (OSError, json.JSONDecodeError) as exc:
            raise ThemeConfigError(f"{path} ilegível: {exc}") from None
        return cls.from_dict(data, source=str(path))

    @classmethod
    def from_dict(cls, data: Any, source: str = "themes.json") -> "ThemeConfig":
        def fail(message: str) -> "ThemeConfigError":
            return ThemeConfigError(f"{source}: {message}")

        if not isinstance(data, dict):
            raise fail("o conteúdo deve ser um objeto")
        if data.get("version") != SUPPORTED_VERSION:
            raise fail(f"version deve ser {SUPPORTED_VERSION}")
        size = data.get("targetSize")
        if not (isinstance(size, list) and len(size) == 2 and all(isinstance(n, int) for n in size)
                and 1 <= size[0] <= size[1]):
            raise fail("targetSize deve ser [mínimo, máximo] de inteiros")
        taxonomy, raw_map = data.get("taxonomy"), data.get("map")
        if not (isinstance(taxonomy, list) and all(isinstance(t, str) and t.strip() for t in taxonomy)):
            raise fail("taxonomy deve ser uma lista de textos")
        if not isinstance(raw_map, dict):
            raise fail("map deve ser um objeto")

        problems: List[str] = []
        if not size[0] <= len(taxonomy) <= size[1]:
            problems.append(f"a taxonomia tem {len(taxonomy)} temas; o esperado é {size[0]} a {size[1]}")
        for theme in taxonomy:
            if theme != theme.lower():
                problems.append(f"tema canônico {theme!r} deve estar em minúsculas")
        seen_key: Dict[str, str] = {}
        seen_slug: Dict[str, str] = {}
        for theme in taxonomy:
            key, slug = theme_key(theme), slugify_theme(theme)
            if key in seen_key:
                problems.append(f"tema canônico repetido: {theme!r} e {seen_key[key]!r}")
            if slug in seen_slug and seen_slug[slug] != theme:
                problems.append(f"slug repetido em /tema/{slug}: {theme!r} e {seen_slug[slug]!r}")
            seen_key.setdefault(key, theme)
            seen_slug.setdefault(slug, theme)
        canonical = set(taxonomy)

        mapping: Dict[str, List[str]] = {}
        spelling: Dict[str, str] = {}
        reached: set = set()
        for original, targets in raw_map.items():
            key = theme_key(original)
            if not key:
                problems.append("o mapa tem uma chave vazia")
                continue
            if key in mapping:
                problems.append(f"original repetido no mapa: {original!r} e {spelling[key]!r}")
                continue
            if not (isinstance(targets, list) and all(isinstance(t, str) for t in targets)):
                problems.append(f"destino de {original!r} deve ser uma lista de temas")
                continue
            for target in targets:
                if target not in canonical:
                    problems.append(f"{original!r} aponta para {target!r}, que não está na taxonomia")
            if len(set(targets)) != len(targets):
                problems.append(f"{original!r} repete um destino")
            mapping[key], spelling[key] = list(targets), original
            reached.update(targets)
        for theme in taxonomy:
            if theme not in reached:
                problems.append(f"tema canônico {theme!r} não é destino de nenhum original")
        if problems:
            raise fail("\n  " + "\n  ".join(problems))
        return cls(list(taxonomy), mapping, spelling, (size[0], size[1]), data["version"])


@dataclass
class Applied:
    themes: List[str]
    tags: List[str]
    unmapped: List[str]


def apply(raw: Iterable[str], cfg: ThemeConfig) -> Applied:
    """Temas canônicos e tags de uma obra, a partir dos temas originais (ordem do CSV).

    `themes`: união dos destinos, sem repetição, na ordem de primeira aparição.
    `tags`: todos os originais, um por chave de comparação, com a grafia do CSV.
    """
    themes: List[str] = []
    tags: List[str] = []
    unmapped: List[str] = []
    seen = set()
    for original in raw:
        key = theme_key(original)
        if key not in seen:
            seen.add(key)
            tags.append(original)
        targets = cfg.mapping.get(key)
        if targets is None:
            unmapped.append(original)
            continue
        for target in targets:
            if target not in themes:
                themes.append(target)
    return Applied(themes, tags, unmapped)


@dataclass
class ThemeSummary:
    canonical: int
    originals: int
    below_floor: List[Tuple[str, int]]
    works_by_theme: Dict[str, int]
    single_theme_works: int
    avg_per_work: float
    tags: int


def summarize(works: Iterable[Mapping[str, Any]]) -> ThemeSummary:
    """Contagens a partir de obras já normalizadas (`themes` e `tags`)."""
    count: Counter = Counter()
    total = single = tags = n = 0
    originals = set()
    for work in works:
        n += 1
        themes = list(work.get("themes") or [])
        count.update(themes)
        total += len(themes)
        single += 1 if len(themes) == 1 else 0
        work_tags = work.get("tags") or []
        tags += len(work_tags)
        originals.update(theme_key(t) for t in work_tags)
    below = sorted(((t, c) for t, c in count.items() if c < THEME_FLOOR), key=lambda kv: (kv[1], kv[0]))
    return ThemeSummary(
        canonical=len(count), originals=len(originals), below_floor=below,
        works_by_theme=dict(count), single_theme_works=single,
        avg_per_work=round(total / n, 2) if n else 0.0, tags=tags)

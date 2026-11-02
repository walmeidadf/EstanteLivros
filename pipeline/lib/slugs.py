"""Geração de slugs estáveis e mapa persistente (pipeline/config/slugs.json)."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Dict, Optional, Set

MAX_SLUG_LENGTH = 80
_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def strip_accents(text: str) -> str:
    """Remove marcas combinantes (acentos) após decomposição NFKD."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def slugify(text: str) -> str:
    """ASCII minúsculo com hífens; caracteres não latinos somem."""
    ascii_text = strip_accents(text).encode("ascii", "ignore").decode("ascii").lower()
    return _NON_ALNUM.sub("-", ascii_text).strip("-")


def truncate(slug: str, limit: int = MAX_SLUG_LENGTH) -> str:
    """Corta no último hífen dentro do limite; sem hífen, corte seco."""
    if len(slug) <= limit:
        return slug
    head = slug[:limit]
    if slug[limit] == "-":
        return head
    cut = head.rfind("-")
    return head[:cut] if cut > 0 else head


class SlugRegistry:
    """Mapa persistente de slugs de obras e autorias.

    Os slugs já mapeados são reservados antes de gerar novos, para que um slug
    novo nunca roube um antigo. O mapa só ganha entradas.
    """

    def __init__(self, works: Optional[Dict[str, str]] = None,
                 authors: Optional[Dict[str, str]] = None) -> None:
        self.works: Dict[str, str] = dict(works or {})
        self.authors: Dict[str, str] = dict(authors or {})
        self._taken_works: Set[str] = set(self.works.values())
        self._taken_authors: Set[str] = set(self.authors.values())
        self.created = 0
        self.reused = 0
        self.truncated = 0

    @classmethod
    def load(cls, path: Path) -> "SlugRegistry":
        from .jsonio import read_json  # import tardio evita ciclo

        if not path.exists():
            return cls()
        data = read_json(path)
        return cls(data.get("works", {}), data.get("authors", {}))

    def to_json(self) -> dict:
        return {
            "works": dict(sorted(self.works.items())),
            "authors": dict(sorted(self.authors.items())),
        }

    def save(self, path: Path) -> None:
        from .jsonio import write_text_atomic, dumps_canonical

        path.parent.mkdir(parents=True, exist_ok=True)
        write_text_atomic(path, dumps_canonical(self.to_json()))

    # -- geração -----------------------------------------------------------

    def _new(self, base_text: str, taken: Set[str], year: Optional[int]) -> str:
        base = slugify(base_text)
        cut = truncate(base)
        if cut != base:
            self.truncated += 1
        candidates = [cut]
        if year is not None:
            candidates.append(truncate(f"{cut}-{year}"))
        for candidate in candidates:
            if candidate and candidate not in taken:
                return candidate
        root = candidates[-1] or "item"
        n = 2
        while True:
            suffix = f"-{n}"
            candidate = truncate(root, MAX_SLUG_LENGTH - len(suffix)) + suffix
            if candidate not in taken:
                return candidate
            n += 1

    def work_slug(self, legacy_id: str, base_text: str, year: Optional[int]) -> str:
        if legacy_id in self.works:
            self.reused += 1
            return self.works[legacy_id]
        slug = self._new(base_text, self._taken_works, year)
        self.works[legacy_id] = slug
        self._taken_works.add(slug)
        self.created += 1
        return slug

    def author_slug(self, key: str, name: str, forced: Optional[str] = None) -> str:
        """`forced` vem de author_overrides.json e vence o mapa."""
        if forced:
            self.authors[key] = forced
            self._taken_authors.add(forced)
            return forced
        if key in self.authors:
            self.reused += 1
            return self.authors[key]
        slug = self._new(name, self._taken_authors, None)
        self.authors[key] = slug
        self._taken_authors.add(slug)
        self.created += 1
        return slug

    def reserve_author(self, slug: str) -> None:
        self._taken_authors.add(slug)

"""Unificação de autorias e escolha do nome canônico."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .slugs import strip_accents

PARTICLES = {"de", "da", "do", "dos", "das", "e", "del", "della", "di", "van",
             "von", "y", "la", "le", "du"}


def unify_key(name: str) -> str:
    """Nome sem acentos, minúsculo, com espaços normalizados."""
    return re.sub(r"\s+", " ", strip_accents(name).lower()).strip()


def _title_cased(name: str) -> bool:
    words = [w for w in name.split() if w.lower() not in PARTICLES]
    return bool(words) and all(w[0].isupper() for w in words if w[0].isalpha())


def _accents(name: str) -> int:
    """Número de caracteres cuja forma sem acento difere."""
    return sum(1 for ch in name if strip_accents(ch) != ch)


@dataclass
class AuthorGroup:
    key: str
    name: str
    aliases: List[str] = field(default_factory=list)
    overridden: bool = False
    forced_slug: Optional[str] = None


def choose_canonical(variants: Mapping[str, int]) -> str:
    """Maior placar: iniciais maiúsculas → nº de acentos → frequência → alfabética."""
    return sorted(
        variants,
        key=lambda n: (not _title_cased(n), -_accents(n), -variants[n], n),
    )[0]


def group_names(counts: Mapping[str, int],
                overrides: Optional[Mapping[str, Mapping[str, str]]] = None
                ) -> Dict[str, AuthorGroup]:
    """Agrupa grafias pela chave de unificação. Devolve {chave: grupo}."""
    overrides = overrides or {}
    buckets: Dict[str, Dict[str, int]] = {}
    for name, count in counts.items():
        buckets.setdefault(unify_key(name), {})[name] = count
    groups: Dict[str, AuthorGroup] = {}
    for key in sorted(buckets):
        variants = buckets[key]
        override = overrides.get(key)
        # Overrides só de país (F2) não mexem no nome.
        if override and override.get("name"):
            canonical = override["name"]
            group = AuthorGroup(key, canonical, overridden=True,
                                forced_slug=override.get("slug"))
        else:
            canonical = choose_canonical(variants)
            group = AuthorGroup(key, canonical)
        group.aliases = sorted(v for v in variants if v != canonical)
        groups[key] = group
    return groups


def languages_for(occurrences: Sequence[Tuple[str, int]]) -> List[str]:
    """`occurrences` = [(idioma, sequence da primeira leitura da obra)].

    Ordena por frequência; empate pela menor sequence.
    """
    freq: Counter = Counter()
    first: Dict[str, int] = {}
    for lang, seq in occurrences:
        freq[lang] += 1
        first[lang] = min(seq, first.get(lang, seq))
    return sorted(freq, key=lambda lang: (-freq[lang], first[lang], lang))


def _initials_and_surname(key: str) -> Tuple[str, str]:
    words = [w for w in key.split() if w not in PARTICLES]
    if not words:
        return "", ""
    return "".join(w[0] for w in words), words[-1]


def find_suspects(groups: Iterable[AuthorGroup]) -> List[Tuple[str, str]]:
    """Pares não unificados com mesmo sobrenome e mesmas iniciais."""
    items = sorted(groups, key=lambda g: g.key)
    suspects = []
    for i, a in enumerate(items):
        for b in items[i + 1:]:
            if _initials_and_surname(a.key) == _initials_and_surname(b.key) \
                    and _initials_and_surname(a.key)[1]:
                suspects.append((a.name, b.name))
    return suspects

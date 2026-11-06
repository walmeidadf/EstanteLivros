"""Contexto compartilhado pelas etapas de enriquecimento de capas."""

from __future__ import annotations

import datetime as dt
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from ..checks import Catalog
from ..http import Http

STEPS = ["download", "measure", "search", "apply"]
FOCUS_VALUES = ("top", "center", "bottom")


class CoverError(Exception):
    """Falha numa obra (download inválido, escolha malformada...)."""


@dataclass
class CoverResult:
    """O que aconteceu com uma obra nesta execução (para o log e o relatório)."""

    slug: str
    done: Dict[str, str] = field(default_factory=dict)  # etapa -> resultado curto
    failed: Dict[str, str] = field(default_factory=dict)  # etapa -> erro


@dataclass
class CoverContext:
    catalog: Catalog
    http: Http
    config: Dict[str, Any]
    steps: List[str]
    state: Dict[str, Dict[str, Any]]
    staging: Path
    candidates_dir: Path
    choices: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    refresh: bool = False
    dry_run: bool = False
    today: Callable[[], dt.date] = dt.date.today
    covers_to_delete: List[str] = field(default_factory=list)  # ex.: "covers/x.jpg"
    needed: Counter = field(default_factory=Counter)  # dry-run: chamadas necessárias
    changed: bool = False  # o catálogo foi alterado nesta execução

    def __post_init__(self) -> None:
        self.reading_count: Counter = Counter()
        self.years_by_work: Dict[str, Set[int]] = defaultdict(set)
        for r in (self.catalog.readings or {}).get("readings", []):
            self.reading_count[r.get("work")] += 1
            if isinstance(r.get("year"), int):
                self.years_by_work[r.get("work")].add(r["year"])

    @property
    def cover_config(self) -> Dict[str, Any]:
        return self.config.get("cover", {})

    def work_state(self, slug: str) -> Dict[str, Any]:
        st = self.state.setdefault(slug, {})
        st.setdefault("candidates", [])
        return st

    def candidate_path(self, entry: Dict[str, Any]) -> Path:
        return self.candidates_dir / entry["file"]

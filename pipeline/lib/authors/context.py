"""Contexto compartilhado pelas etapas de enriquecimento de autorias."""

from __future__ import annotations

import datetime as dt
import json
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from ..budget import Budget
from ..checks import Catalog
from ..env import Env
from ..http import Http
from ..names import unify_key
from ..providers import wikidata

PIPELINE = Path(__file__).resolve().parents[2]
CONFIG = PIPELINE / "config"


def read_config(name: str, default: Any) -> Any:
    path = CONFIG / name
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else default


def normalize_title(text: Optional[str]) -> str:
    """Título comparável: sem acentos, sem pontuação, minúsculo (mantém não latinos)."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    # unify_key remove acentos via NFKD; o NFC recompõe sílabas como as do hangul.
    text = unicodedata.normalize("NFC", unify_key(text))
    text = "".join(" " if unicodedata.category(ch).startswith(("P", "S")) else ch for ch in text)
    return re.sub(r"\s+", " ", text).strip()


def title_variants(text: Optional[str]) -> Set[str]:
    """Título completo e título principal (antes de ':' ou ' - ')."""
    out = set()
    if text:
        out.add(normalize_title(text))
        main = re.split(r"\s*[:–—]\s*|\s+-\s+", text, maxsplit=1)[0]
        out.add(normalize_title(main))
    out.discard("")
    return out


@dataclass
class Waves:
    """Etapas e fontes permitidas. Sem onda (manutenção) = tudo."""

    steps: List[str]
    photo_sources: List[str]
    bio_sources: List[str]
    llm: bool

    @classmethod
    def for_wave(cls, wave: Optional[int], photo_order: List[str]) -> "Waves":
        all_steps = ["identify", "country", "photo", "bio"]
        if wave == 1:
            return cls(all_steps, ["commons", "wikipedia"], ["wikipedia"], llm=False)
        if wave == 2:
            return cls(["bio"], [], ["wikipedia"], llm=True)
        if wave == 3:
            return cls(["photo", "bio"], list(photo_order), ["wikipedia", "tavily"], llm=True)
        return cls(all_steps, list(photo_order), ["wikipedia", "tavily"], llm=True)


@dataclass
class AuthorResult:
    """O que aconteceu com uma autoria nesta execução (para o log e o relatório)."""

    slug: str
    done: Dict[str, str] = field(default_factory=dict)  # etapa -> resultado curto
    deferred: Dict[str, str] = field(default_factory=dict)  # etapa -> provedor sem cota
    failed: Dict[str, str] = field(default_factory=dict)  # etapa -> erro
    notes: List[str] = field(default_factory=list)


@dataclass
class Context:
    catalog: Catalog
    http: Http
    env: Env
    budget: Budget
    config: Dict[str, Any]
    waves: Waves
    state: Dict[str, Dict[str, Any]]
    staging: Path
    overrides: Dict[str, Any] = field(default_factory=dict)
    author_wikidata: Dict[str, Any] = field(default_factory=dict)
    author_photos: Dict[str, Any] = field(default_factory=dict)
    rejections: List[str] = field(default_factory=list)
    countries: Dict[str, Any] = field(default_factory=dict)
    languages: Dict[str, Dict[str, str]] = field(default_factory=dict)
    occupations: Dict[str, str] = field(default_factory=dict)
    prompts_dir: Path = CONFIG / "prompts"
    refresh: bool = False
    regenerate: bool = False
    regenerate_prompt: Optional[str] = None
    dry_run: bool = False
    today: Callable[[], dt.date] = dt.date.today
    entity_cache: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    photos_to_delete: List[Path] = field(default_factory=list)
    needed: Counter = field(default_factory=Counter)  # dry-run: chamadas necessárias
    estimated_usd: float = 0.0

    # -- dados derivados do catálogo ---------------------------------------

    def __post_init__(self) -> None:
        self.works_by_author: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for work in self.catalog.works.values():
            for slug in work.get("authors", []):
                self.works_by_author[slug].append(work)
        readings = (self.catalog.readings or {}).get("readings", [])
        self.first_sequence: Dict[str, int] = {}
        self.reading_count: Counter = Counter()
        self.years_by_author: Dict[str, Set[int]] = defaultdict(set)
        for r in readings:
            work = self.catalog.works.get(r.get("work"), {})
            self.first_sequence.setdefault(r.get("work"), r.get("sequence"))
            for slug in work.get("authors", []):
                self.reading_count[slug] += 1
                if isinstance(r.get("year"), int):
                    self.years_by_author[slug].add(r["year"])
        for slug in self.works_by_author:
            self.works_by_author[slug].sort(key=lambda w: self.first_sequence.get(w["slug"], 10**9))

    @property
    def rules_version(self) -> int:
        return int(self.config.get("rulesVersion", 1))

    def iso(self, language: Optional[str]) -> Optional[str]:
        return (self.languages.get(language or "") or {}).get("iso")

    def bio_languages(self) -> List[str]:
        env_value = self.env.get("BIO_SOURCE_LANGUAGES")
        if env_value:
            return [x.strip() for x in env_value.split(",") if x.strip()]
        return list(self.config.get("bioSourceLanguages", ["pt", "en"]))

    def override_for(self, author: Dict[str, Any]) -> Dict[str, Any]:
        return self.overrides.get(author["slug"]) or self.overrides.get(unify_key(author["name"])) or {}

    def author_state(self, slug: str) -> Dict[str, Any]:
        return self.state.setdefault(slug, {})

    def waves_providers(self) -> List[str]:
        """Provedores com cota que as etapas e fontes desta execução podem usar."""
        out = []
        photo = "photo" in self.waves.steps
        bio = "bio" in self.waves.steps and self.waves.llm
        if photo and "serpapi" in self.waves.photo_sources:
            out.append("serpapi")
        if (photo and "tavily" in self.waves.photo_sources) or (bio and "tavily" in self.waves.bio_sources):
            out.append("tavily")
        return out

    def entity(self, qid: str) -> Optional[Dict[str, Any]]:
        if qid not in self.entity_cache:
            self.entity_cache.update(wikidata.entities(self.http, [qid]))
        return self.entity_cache.get(qid)

"""Pendências e ordem de prioridade das obras (irmão de `lib/selection.py`)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from . import apply as apply_step
from . import download, search
from .context import CoverContext


def cover_pending(ctx: CoverContext, work: Dict[str, Any]) -> bool:
    """Sem decisão registrada, ou decisão ainda não refletida no catálogo."""
    choice = ctx.choices.get(work["slug"])
    if choice is None:
        return True
    return not apply_step.applied(work, choice)


def step_pending(ctx: CoverContext, step: str, work: Dict[str, Any]) -> bool:
    """A etapa tem algo a fazer nesta obra?"""
    decided = work["slug"] in ctx.choices
    if step == "download":
        return not decided and download.pending(ctx, work)
    if step == "measure":
        return not decided and any("klass" not in c or ctx.refresh
                                   for c in ctx.work_state(work["slug"])["candidates"])
    if step == "search":
        return not decided and search.pending(ctx, work)
    if step == "apply":
        choice = ctx.choices.get(work["slug"])
        return choice is not None and not apply_step.applied(work, choice)
    return False


def priority_key(ctx: CoverContext, slug: str):
    current_year = ctx.today().year
    return (-ctx.reading_count[slug], 0 if current_year in ctx.years_by_work[slug] else 1, slug)


def select(ctx: CoverContext, only: Optional[Sequence[str]] = None, limit: Optional[int] = None) -> List[str]:
    """Obras a processar, por prioridade. Com `only`, só essas (mesmas regras)."""
    if only:
        unknown = [s for s in only if s not in ctx.catalog.works]
        if unknown:
            raise KeyError(f"obras inexistentes: {', '.join(unknown)}")
        slugs = list(only)
    else:
        slugs = list(ctx.catalog.works)
    slugs.sort(key=lambda s: priority_key(ctx, s))
    if not only:
        slugs = [s for s in slugs if cover_pending(ctx, ctx.catalog.works[s])]
    return slugs[:limit] if limit else slugs

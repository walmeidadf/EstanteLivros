"""Pendências por etapa e ordem de prioridade das autorias."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from .authors.context import Context

DEFINITIVE = {"confirmed", "probable", "manual", "none"}


def identify_pending(ctx: Context, author: Dict[str, Any]) -> bool:
    if ctx.refresh:
        return True
    wd = author.get("wikidata")
    manual = ctx.author_wikidata.get(author["slug"])
    if manual is not None:
        want = ("none", None) if manual.get("none") else ("manual", manual.get("id"))
        return wd is None or (wd.get("status"), wd.get("id")) != want
    if wd is None:
        return True
    if wd.get("status") in DEFINITIVE:
        return False
    return int(wd.get("rulesVersion") or 0) < ctx.rules_version


def country_pending(ctx: Context, author: Dict[str, Any]) -> bool:
    override = ctx.override_for(author).get("country")
    if override:
        return author.get("country") != override or author.get("countrySource") != "override"
    if author.get("countrySource") == "override":
        return True  # override removido
    wd = author.get("wikidata") or {}
    if not wd.get("id"):
        return False
    return ctx.refresh or author.get("country") is None


def photo_pending(ctx: Context, author: Dict[str, Any]) -> bool:
    choice = ctx.author_photos.get(author["slug"])
    photo = author.get("photo")
    if choice is not None:
        if choice.get("none"):
            return photo is not None
        return photo is None or photo.get("sourceUrl") not in (choice.get("url"), choice.get("pageUrl"))
    if photo is not None:
        return ctx.refresh
    tried = set(ctx.author_state(author["slug"]).get("photoTried", []))
    candidates = ctx.author_state(author["slug"]).get("photoCandidates", [])
    max_candidates = int(ctx.config.get("photo", {}).get("maxCandidates", 3))
    untried = [s for s in ctx.waves.photo_sources if s not in tried]
    return bool(untried) and len(candidates) < max_candidates


def bio_pending(ctx: Context, author: Dict[str, Any]) -> bool:
    from . import summaries

    scope = f"autoria:{author['slug']}"
    current = summaries.get(ctx.catalog, scope)
    if current is not None:
        if current.get("approved"):
            return False
        if ctx.regenerate:
            return True
        return bool(ctx.regenerate_prompt) and current.get("promptVersion") == ctx.regenerate_prompt
    if scope in ctx.rejections and not ctx.regenerate:
        return False
    state = ctx.author_state(author["slug"])
    prompt = ctx.config.get("bio", {}).get("promptVersion")
    if state.get("bioInsufficient") == prompt and not ctx.regenerate:
        return False
    if not ctx.waves.llm:
        # Onda 1: só coleta fontes grátis, se ainda não coletou.
        return "wikipedia" not in state.get("bioTried", [])
    tried = set(state.get("bioTried", []))
    untried = [s for s in ctx.waves.bio_sources if s not in tried]
    return bool(untried) or bool(state.get("bioSource"))


PENDING = {
    "identify": identify_pending,
    "country": country_pending,
    "photo": photo_pending,
    "bio": bio_pending,
}


def priority_key(ctx: Context, slug: str):
    current_year = ctx.today().year
    return (-ctx.reading_count[slug], 0 if current_year in ctx.years_by_author[slug] else 1, slug)


def select(ctx: Context, only: Optional[Sequence[str]] = None, limit: Optional[int] = None) -> List[str]:
    """Autorias a processar, por prioridade. Com `only`, só essas (mesmas regras)."""
    if only:
        unknown = [s for s in only if s not in ctx.catalog.authors]
        if unknown:
            raise KeyError(f"autorias inexistentes: {', '.join(unknown)}")
        slugs = list(only)
    else:
        slugs = list(ctx.catalog.authors)
    slugs.sort(key=lambda s: priority_key(ctx, s))
    if not only:
        slugs = [s for s in slugs if any(PENDING[step](ctx, ctx.catalog.authors[s]) for step in ctx.waves.steps)]
    return slugs[:limit] if limit else slugs

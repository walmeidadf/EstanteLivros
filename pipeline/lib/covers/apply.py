"""Etapa `apply`: aplica `pipeline/config/cover_choices.json` ao catálogo (R4, R5, R6).

Escolhas possíveis, por obra:
- `{"url": ..., "source": ..., "focus": ..., "license": ..., "credit": ...}`:
  usa a capa real (promove o mestre para `catalog/media/covers/`);
- `{"typographic": true}`: revisada, fica a capa tipográfica
  (`cover.display = "typographic"`);
- `{"none": true}`: sem capa aceitável; segue tipográfica e vai ao backlog.

A decisão humana vence a classificação automática. Uma obra com `cover: null`
não tem onde gravar `display` (o schema exige `sourceUrl`); nesse caso a
decisão `typographic`/`none` vive só em `cover_choices.json`.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..images import sniff
from .context import FOCUS_VALUES, CoverContext, CoverError

ENRICHED = ("file", "license", "credit", "focus", "display")


def build_cover(source_url: str, source: Optional[str], file: Optional[str] = None,
                license: Optional[str] = None, credit: Optional[str] = None,
                focus: Optional[str] = None, display: Optional[str] = None) -> Dict[str, Any]:
    """Objeto `cover` só com os campos preenchidos (mesma forma que a migração preserva)."""
    cover: Dict[str, Any] = {"sourceUrl": source_url, "source": source}
    for key, value in (("file", file), ("license", license), ("credit", credit),
                       ("focus", focus), ("display", display)):
        if value is not None:
            cover[key] = value
    return cover


def guess_source(url: str) -> str:
    """Origem a registrar quando a escolha não informa `source`."""
    return "openlibrary" if "covers.openlibrary.org" in url else "manual"


def _has_enrichment(cover: Dict[str, Any]) -> bool:
    return any(cover.get(k) is not None for k in ENRICHED)


def applied(work: Dict[str, Any], choice: Dict[str, Any]) -> bool:
    """A escolha já está refletida no catálogo?"""
    cover = work.get("cover")
    if choice.get("typographic"):
        return cover is None or (cover.get("display") == "typographic" and cover.get("file") is None)
    if choice.get("none"):
        return cover is None or not _has_enrichment(cover)
    if not cover or not cover.get("file") or cover.get("sourceUrl") != choice.get("url"):
        return False
    return all(cover.get(k) == choice.get(k) for k in ("focus", "license", "credit"))


def validate_choice(slug: str, choice: Dict[str, Any]) -> None:
    kinds = [k for k in ("url", "typographic", "none") if choice.get(k)]
    if len(kinds) != 1:
        raise CoverError(f"escolha de {slug}: use exatamente um entre url, typographic, none")
    if choice.get("focus") is not None and choice["focus"] not in FOCUS_VALUES:
        raise CoverError(f"escolha de {slug}: focus deve ser {', '.join(FOCUS_VALUES)}")


def _drop_local(ctx: CoverContext, cover: Dict[str, Any]) -> None:
    if cover.get("file"):
        ctx.covers_to_delete.append(cover["file"])


def run(ctx: CoverContext, work: Dict[str, Any]) -> Optional[str]:
    slug = work["slug"]
    choice = ctx.choices.get(slug)
    if choice is None:
        return None
    validate_choice(slug, choice)
    if applied(work, choice):
        return None
    cover = work.get("cover")

    if choice.get("typographic"):
        _drop_local(ctx, cover)
        work["cover"] = build_cover(cover["sourceUrl"], cover.get("source"), display="typographic")
        ctx.changed = True
        return "fica tipográfica"

    if choice.get("none"):
        _drop_local(ctx, cover)
        work["cover"] = build_cover(cover["sourceUrl"], cover.get("source"))
        ctx.changed = True
        return "sem capa aceitável"

    url = choice["url"]
    st = ctx.work_state(slug)
    candidate = next((c for c in st["candidates"] if c["url"] == url), None)
    if cover and cover.get("file") and cover.get("sourceUrl") == url:
        rel = cover["file"]  # mesmo mestre: só muda foco/licença/crédito
    else:
        if candidate is not None and ctx.candidate_path(candidate).is_file():
            content = ctx.candidate_path(candidate).read_bytes()
        else:
            resp = ctx.http.get_bytes("images", url)
            if resp.status != 200 or not resp.content:
                raise CoverError(f"download falhou (HTTP {resp.status})")
            content = resp.content
        info = sniff(content)
        if info is None:
            raise CoverError("arquivo escolhido não é uma imagem reconhecida")
        rel = f"covers/{slug}.{info.ext}"
        ctx.staging.mkdir(parents=True, exist_ok=True)
        (ctx.staging / f"{slug}.{info.ext}").write_bytes(content)
        if cover and cover.get("file") and cover["file"] != rel:
            ctx.covers_to_delete.append(cover["file"])
    previous_source = (cover or {}).get("source") if (cover or {}).get("sourceUrl") == url else None
    origin = candidate["origin"] if candidate and candidate["origin"] != "catalog" else previous_source
    work["cover"] = build_cover(url, choice.get("source") or origin or guess_source(url), file=rel,
                                license=choice.get("license"), credit=choice.get("credit"),
                                focus=choice.get("focus"))
    ctx.changed = True
    return f"capa real ({work['cover']['source']})"

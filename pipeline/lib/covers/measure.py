"""Etapa `measure`: resolução e proporção dos mestres candidatos (R2)."""

from __future__ import annotations

from typing import Any, Dict

from ..images import ImageInfo, sniff
from .context import CoverContext, CoverError

GOOD, BORDERLINE, LOW = "good", "borderline", "low"
LABELS = {GOOD: "boa", BORDERLINE: "limítrofe", LOW: "baixa"}


def classify(cfg: Dict[str, Any], info: ImageInfo) -> str:
    """boa (lado menor ≥ goodMinSide), baixa (< rejectBelow) ou limítrofe."""
    if info.min_side >= int(cfg.get("goodMinSide", 400)):
        return GOOD
    if info.min_side < int(cfg.get("rejectBelow", 250)):
        return LOW
    return BORDERLINE


def far_from_cover_ratio(cfg: Dict[str, Any], info: ImageInfo) -> bool:
    """true quando largura/altura sai da faixa esperada de uma capa 2:3."""
    low, high = cfg.get("aspectRange", [0.60, 0.72])
    return not (float(low) <= info.width / info.height <= float(high))


def describe(cfg: Dict[str, Any], info: ImageInfo) -> Dict[str, Any]:
    return {"width": info.width, "height": info.height,
            "ratio": round(info.width / info.height, 3),
            "klass": classify(cfg, info),
            "checkFraming": far_from_cover_ratio(cfg, info)}


def run(ctx: CoverContext, work: Dict[str, Any]) -> str:
    st = ctx.work_state(work["slug"])
    cfg = ctx.cover_config
    counts: Dict[str, int] = {}
    for entry in st["candidates"]:
        path = ctx.candidate_path(entry)
        info = sniff(path.read_bytes()) if path.is_file() else None
        if info is None:
            raise CoverError(f"candidata ilegível: {entry['file']}")
        entry.update(describe(cfg, info))
        counts[entry["klass"]] = counts.get(entry["klass"], 0) + 1
    if not counts:
        return "sem candidatas"
    return " · ".join(f"{LABELS[k]} {v}" for k, v in sorted(counts.items()))

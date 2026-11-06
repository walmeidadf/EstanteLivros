"""Etapa `download`: baixa a `cover.sourceUrl` do catálogo como candidata (R1).

O arquivo vai para `pipeline/cache/covers/candidates/` (fora do git), no tamanho
original. A promoção para `catalog/media/covers/` só acontece na etapa `apply`,
depois de uma escolha humana.
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict

from ..images import sniff
from .context import CoverContext, CoverError


def store_candidate(ctx: CoverContext, slug: str, url: str, origin: str, content: bytes) -> Dict[str, Any]:
    """Grava os bytes como candidata e a registra no estado da obra."""
    info = sniff(content)
    if info is None:
        raise CoverError("arquivo baixado não é uma imagem reconhecida")
    name = f"{slug}--{hashlib.sha1(url.encode('utf-8')).hexdigest()[:8]}.{info.ext}"
    ctx.candidates_dir.mkdir(parents=True, exist_ok=True)
    (ctx.candidates_dir / name).write_bytes(content)
    entry = {"url": url, "origin": origin, "file": name, "ext": info.ext}
    st = ctx.work_state(slug)
    st["candidates"] = [c for c in st["candidates"] if c["url"] != url] + [entry]
    return entry


def pending(ctx: CoverContext, work: Dict[str, Any]) -> bool:
    cover = work.get("cover")
    if not cover or not cover.get("sourceUrl"):
        return False
    st = ctx.work_state(work["slug"])
    url = cover["sourceUrl"]
    if ctx.refresh:
        return True
    return not any(c["url"] == url for c in st["candidates"]) and st.get("downloadError", {}).get("url") != url


def run(ctx: CoverContext, work: Dict[str, Any]) -> str:
    slug = work["slug"]
    url = work["cover"]["sourceUrl"]
    st = ctx.work_state(slug)
    resp = ctx.http.get_bytes("images", url)
    if resp.status != 200 or not resp.content:
        # Definitivo (ex.: 404): não tenta de novo sem --refresh. Erros transitórios levantam HttpError.
        st["downloadError"] = {"url": url, "error": f"HTTP {resp.status}"}
        raise CoverError(f"download falhou (HTTP {resp.status})")
    try:
        store_candidate(ctx, slug, url, "catalog", resp.content)
    except CoverError as exc:
        st["downloadError"] = {"url": url, "error": str(exc)}
        raise
    st.pop("downloadError", None)
    return "baixada"

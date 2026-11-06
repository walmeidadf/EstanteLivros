"""Open Library Covers: capa por ISBN (gratuito, sem chave).

`?default=false` faz a API responder 404 quando não há capa, em vez de devolver
uma imagem em branco com 200. O 404 é cacheável no `Http`, então uma obra sem
capa na Open Library não repete a chamada.
"""

from __future__ import annotations

from typing import Optional

from ..http import Http

PROVIDER = "openlibrary"
BASE = "https://covers.openlibrary.org/b/isbn"


def cover_url(isbn: str, size: str = "L") -> str:
    """URL canônica da capa (a que fica no catálogo como proveniência)."""
    return f"{BASE}/{isbn}-{size}.jpg"


def fetch_cover(http: Http, isbn: str, size: str = "L") -> Optional[bytes]:
    """Bytes da capa, ou None quando a Open Library não tem capa para o ISBN."""
    resp = http.get_bytes(PROVIDER, cover_url(isbn, size) + "?default=false")
    return resp.content if resp.status == 200 and resp.content else None

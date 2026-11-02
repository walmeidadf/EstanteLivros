"""Wikipédia: introdução de verbete e imagem principal."""

from __future__ import annotations

import urllib.parse
from typing import Any, Dict, Optional

from ..http import Http

PROVIDER = "wikipedia"


def _api(lang: str) -> str:
    return f"https://{lang}.wikipedia.org/w/api.php"


def page_url(lang: str, title: str) -> str:
    return f"https://{lang}.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"


def _page(http: Http, lang: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    resp = http.get_json(PROVIDER, _api(lang), {
        "action": "query", "format": "json", "formatversion": 2, "redirects": 1, **params,
    })
    pages = ((resp.data or {}).get("query") or {}).get("pages") or []
    page = pages[0] if pages else None
    if not page or page.get("missing") or page.get("invalid"):
        return None
    return page


def intro(http: Http, lang: str, title: str) -> Optional[str]:
    """Introdução do verbete em texto puro, ou None."""
    page = _page(http, lang, {"prop": "extracts", "exintro": 1, "explaintext": 1, "titles": title})
    text = (page or {}).get("extract") or ""
    text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    return text or None


def page_image(http: Http, lang: str, title: str, width: int) -> Optional[Dict[str, Any]]:
    """Imagem principal do verbete: {url, width, height, name} ou None."""
    page = _page(http, lang, {"prop": "pageimages", "piprop": "thumbnail|name",
                              "pithumbsize": width, "titles": title})
    thumb = (page or {}).get("thumbnail")
    if not thumb or not thumb.get("source"):
        return None
    return {"url": thumb["source"], "width": thumb.get("width"), "height": thumb.get("height"),
            "name": page.get("pageimage")}

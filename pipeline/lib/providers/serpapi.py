"""SerpApi (Google Imagens). Plano gratuito: 250 buscas/mês."""

from __future__ import annotations

import urllib.parse
from typing import Any, Dict, Iterable, List, Optional

from ..http import Http

SEARCH = "https://serpapi.com/search.json"
ACCOUNT = "https://serpapi.com/account"
PROVIDER = "serpapi"


def _domain(url: str) -> str:
    host = urllib.parse.urlsplit(url).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def is_excluded(url: str, excluded: Iterable[str]) -> bool:
    host = _domain(url)
    return any(host == d or host.endswith("." + d) for d in excluded)


def images(http: Http, api_key: str, query: str, min_side: int, excluded: Iterable[str],
           hl: str = "pt-br", gl: str = "br") -> List[Dict[str, Any]]:
    resp = http.get_json(PROVIDER, SEARCH, {"engine": "google_images", "q": query, "hl": hl, "gl": gl,
                                            "api_key": api_key}, secret_params=("api_key",))
    out = []
    excluded = list(excluded)
    for item in (resp.data or {}).get("images_results", []) or []:
        url, link = item.get("original"), item.get("link") or ""
        width, height = item.get("original_width"), item.get("original_height")
        if not url or not url.startswith("http"):
            continue
        if is_excluded(url, excluded) or (link and is_excluded(link, excluded)):
            continue
        if isinstance(width, int) and isinstance(height, int) and min(width, height) < min_side:
            continue
        out.append({"url": url, "width": width, "height": height, "source": item.get("source"),
                    "title": item.get("title"), "pageUrl": link or None})
    return out


def month_usage(http: Http, api_key: str) -> Optional[int]:
    """Buscas usadas no mês (endpoint de conta: não consome cota, não usa cache)."""
    resp = http.get_json("serpapi-account", ACCOUNT, {"api_key": api_key},
                         secret_params=("api_key",), use_cache=False)
    value = (resp.data or {}).get("this_month_usage")
    return int(value) if isinstance(value, int) else None

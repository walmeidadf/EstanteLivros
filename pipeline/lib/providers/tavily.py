"""Tavily: busca de fontes e imagens. Plano gratuito: 1.000 créditos/mês."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from ..http import Http
from .serpapi import is_excluded

SEARCH = "https://api.tavily.com/search"
USAGE = "https://api.tavily.com/usage"
PROVIDER = "tavily"


def _auth(api_key: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {api_key}"}


def search(http: Http, api_key: str, query: str, excluded: Iterable[str],
           max_results: int = 5) -> Dict[str, List[Dict[str, Any]]]:
    """{"results": [{url, title, content}], "images": [{url, description}]} (1 crédito, busca básica)."""
    excluded = sorted(set(excluded))
    body = {"query": query, "max_results": max_results, "search_depth": "basic",
            "include_images": True, "include_image_descriptions": True, "exclude_domains": excluded}
    resp = http.post_json(PROVIDER, SEARCH, body, headers=_auth(api_key))
    data = resp.data or {}
    results = [{"url": r.get("url"), "title": r.get("title"), "content": r.get("content") or ""}
               for r in data.get("results", []) or [] if r.get("url") and not is_excluded(r["url"], excluded)]
    images = []
    for img in data.get("images", []) or []:
        url, desc = (img, None) if isinstance(img, str) else (img.get("url"), img.get("description"))
        if url and url.startswith("http") and not is_excluded(url, excluded):
            images.append({"url": url.split("?utm_", 1)[0], "description": desc})
    return {"results": results, "images": images}


def month_usage(http: Http, api_key: str) -> Optional[int]:
    """Créditos usados no plano (endpoint de uso: não consome cota, não usa cache)."""
    resp = http.get_json("tavily-usage", USAGE, headers=_auth(api_key), use_cache=False)
    value = ((resp.data or {}).get("account") or {}).get("plan_usage")
    return int(value) if isinstance(value, int) else None

"""Wikimedia Commons: URL, dimensões, licença e autoria de uma imagem."""

from __future__ import annotations

import html
import re
from html.parser import HTMLParser
from typing import Any, Dict, Optional

from ..http import Http

API = "https://commons.wikimedia.org/w/api.php"
PROVIDER = "commons"


class _TextOnly(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def strip_html(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    parser = _TextOnly()
    parser.feed(value)
    text = html.unescape("".join(parser.parts))
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def image_info(http: Http, filename: str, width: int) -> Optional[Dict[str, Any]]:
    """{url, width, height, license, author, pageUrl} da miniatura de `width` px."""
    title = filename if filename.startswith("File:") else f"File:{filename}"
    resp = http.get_json(PROVIDER, API, {
        "action": "query", "format": "json", "formatversion": 2, "titles": title,
        "prop": "imageinfo", "iiprop": "url|size|extmetadata", "iiurlwidth": width,
    })
    pages = ((resp.data or {}).get("query") or {}).get("pages") or []
    if not pages or pages[0].get("missing"):
        return None
    infos = pages[0].get("imageinfo") or []
    if not infos:
        return None
    info = infos[0]
    meta = info.get("extmetadata") or {}
    return {
        "url": info.get("thumburl") or info.get("url"),
        "width": info.get("thumbwidth") or info.get("width"),
        "height": info.get("thumbheight") or info.get("height"),
        "license": strip_html((meta.get("LicenseShortName") or {}).get("value")),
        "author": strip_html((meta.get("Artist") or {}).get("value")),
        "pageUrl": info.get("descriptionurl"),
    }

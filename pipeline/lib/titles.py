"""Separação de título original e romanização."""

from __future__ import annotations

import re
import unicodedata
from typing import Optional, Tuple

_TRAILING_PARENS = re.compile(r"^(.+?)\s*\(([^()]+)\)$")


def is_latin_letter(ch: str) -> bool:
    code = ord(ch)
    return code <= 0x024F or 0x1E00 <= code <= 0x1EFF


def has_non_latin(text: str) -> bool:
    """Verdadeiro se houver alguma letra fora dos blocos latinos."""
    return any(unicodedata.category(ch).startswith("L") and not is_latin_letter(ch)
               for ch in text)


def split_original(value: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """Devolve (originalTitle, originalTitleRomanized)."""
    text = (value or "").strip()
    if not text:
        return None, None
    match = _TRAILING_PARENS.match(text)
    if match and has_non_latin(match.group(1)):
        return match.group(1).strip(), match.group(2).strip()
    return text, None

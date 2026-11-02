"""Tipo e dimensões de imagens a partir dos bytes (JPEG, PNG, WebP, GIF)."""

from __future__ import annotations

import struct
from typing import NamedTuple, Optional


class ImageInfo(NamedTuple):
    ext: str
    width: int
    height: int

    @property
    def min_side(self) -> int:
        return min(self.width, self.height)


def sniff(data: bytes) -> Optional[ImageInfo]:
    """Devolve tipo e dimensões, ou None se não for imagem reconhecida."""
    try:
        if data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR":
            width, height = struct.unpack(">II", data[16:24])
            return ImageInfo("png", width, height)
        if data[:6] in (b"GIF87a", b"GIF89a"):
            width, height = struct.unpack("<HH", data[6:10])
            return ImageInfo("gif", width, height)
        if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            return _webp(data)
        if data[:2] == b"\xff\xd8":
            return _jpeg(data)
    except (struct.error, IndexError):
        return None
    return None


def _webp(data: bytes) -> Optional[ImageInfo]:
    chunk = data[12:16]
    if chunk == b"VP8 ":
        width, height = struct.unpack("<HH", data[26:30])
        return ImageInfo("webp", width & 0x3FFF, height & 0x3FFF)
    if chunk == b"VP8L":
        bits = int.from_bytes(data[21:25], "little")
        return ImageInfo("webp", (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1)
    if chunk == b"VP8X":
        width = int.from_bytes(data[24:27], "little") + 1
        height = int.from_bytes(data[27:30], "little") + 1
        return ImageInfo("webp", width, height)
    return None


_SOF_MARKERS = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}


def _jpeg(data: bytes) -> Optional[ImageInfo]:
    i = 2
    while i + 4 <= len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7 or marker == 0xFF:
            i += 1 if marker == 0xFF else 2
            continue
        length = struct.unpack(">H", data[i + 2:i + 4])[0]
        if marker in _SOF_MARKERS:
            height, width = struct.unpack(">HH", data[i + 5:i + 9])
            return ImageInfo("jpg", width, height)
        if marker == 0xDA:  # início dos dados comprimidos sem SOF antes
            return None
        i += 2 + length
    return None

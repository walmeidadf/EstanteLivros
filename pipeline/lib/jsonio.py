"""Leitura e escrita canônica de JSON e escrita atômica do catálogo."""

from __future__ import annotations

import json
import os
import shutil
import uuid
from pathlib import Path
from typing import Any, Dict

TMP_DIR_NAME = ".tmp-migrate"


def dumps_canonical(obj: Any) -> str:
    """UTF-8 legível, indentação 2, ordem de chaves da construção, `\\n` final."""
    return json.dumps(obj, ensure_ascii=False, indent=2) + "\n"


def read_json(path: Path) -> Any:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def write_text_atomic(path: Path, text: str) -> None:
    tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    os.replace(tmp, path)


def write_catalog(files: Dict[str, Any], catalog_dir: Path) -> None:
    """Grava o catálogo de forma atômica.

    `files` mapeia caminho relativo (ex.: `works/x.json`, `readings.json`) ao
    conteúdo. `works/` e `authors/` são substituídos por inteiro; arquivos soltos
    são trocados um a um. `schema/`, `source/` e `media/` nunca são tocados.
    """
    catalog_dir.mkdir(parents=True, exist_ok=True)
    tmp = catalog_dir / TMP_DIR_NAME
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir()
    try:
        for rel, content in sorted(files.items()):
            target = tmp / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(dumps_canonical(content))
        # Garante que diretórios vazios também sejam trocados.
        for sub in ("works", "authors"):
            (tmp / sub).mkdir(exist_ok=True)
        _swap(tmp, catalog_dir)
    finally:
        if tmp.exists():
            shutil.rmtree(tmp)


def _swap(tmp: Path, catalog_dir: Path) -> None:
    for sub in ("works", "authors"):
        current = catalog_dir / sub
        old = catalog_dir / f".{sub}.old"
        if old.exists():
            shutil.rmtree(old)
        if current.exists():
            os.replace(current, old)
        os.replace(tmp / sub, current)
        if old.exists():
            shutil.rmtree(old)
    for item in sorted(tmp.iterdir()):
        if item.is_file():
            os.replace(item, catalog_dir / item.name)

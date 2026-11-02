"""Resumos gerados (bio de autoria, ano, país): inserir, aprovar, rejeitar, editar."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .checks import Catalog
from .jsonio import dumps_canonical, write_text_atomic

FIELDS = ("scope", "text", "approved", "updatedAt", "source", "sourceUrl", "sourceLanguage",
          "model", "promptVersion", "editedBy")


class SummaryError(Exception):
    pass


def _items(cat: Catalog) -> List[Dict[str, Any]]:
    if not isinstance(cat.summaries, dict):
        cat.summaries = {"summaries": []}
    return cat.summaries.setdefault("summaries", [])


def _sort(cat: Catalog) -> None:
    _items(cat).sort(key=lambda s: s.get("scope", ""))


def get(cat: Catalog, scope: str) -> Optional[Dict[str, Any]]:
    return next((s for s in _items(cat) if s.get("scope") == scope), None)


def upsert(cat: Catalog, scope: str, text: str, today: Callable[[], dt.date] = dt.date.today,
           **fields: Any) -> Dict[str, Any]:
    """Insere ou atualiza um resumo NÃO aprovado. `updatedAt` só muda se algo mudar."""
    current = get(cat, scope)
    if current is not None and current.get("approved"):
        raise SummaryError(f"{scope}: resumo aprovado não é sobrescrito automaticamente")
    new = {k: None for k in FIELDS}
    new.update(scope=scope, text=text, approved=False, editedBy=None)
    new.update({k: v for k, v in fields.items() if k in FIELDS and k not in ("scope", "approved")})
    if current is not None:
        comparable = {k: v for k, v in new.items() if k != "updatedAt"}
        if all(current.get(k) == v for k, v in comparable.items()):
            return current
        _items(cat).remove(current)
    new["updatedAt"] = today().isoformat()
    ordered = {k: new[k] for k in FIELDS}
    _items(cat).append(ordered)
    _sort(cat)
    return ordered


def approve(cat: Catalog, scope: str) -> Dict[str, Any]:
    item = get(cat, scope)
    if item is None:
        raise SummaryError(f"{scope}: resumo não existe")
    if not (item.get("text") or "").strip():
        raise SummaryError(f"{scope}: resumo sem texto não pode ser aprovado")
    item["approved"] = True
    return item


def edit(cat: Catalog, scope: str, text: str, today: Callable[[], dt.date] = dt.date.today) -> Dict[str, Any]:
    item = get(cat, scope)
    if item is None:
        raise SummaryError(f"{scope}: resumo não existe")
    text = text.strip()
    if not text:
        raise SummaryError(f"{scope}: texto vazio")
    if item["text"] != text:
        item.update(text=text, editedBy="human", approved=False, updatedAt=today().isoformat())
    return item


def reject(cat: Catalog, scope: str, rejections: List[str]) -> None:
    item = get(cat, scope)
    if item is None:
        raise SummaryError(f"{scope}: resumo não existe")
    _items(cat).remove(item)
    if scope not in rejections:
        rejections.append(scope)
        rejections.sort()


def load_rejections(path: Path) -> List[str]:
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return sorted(set(data)) if isinstance(data, list) else []


def save_rejections(path: Path, rejections: List[str]) -> None:
    write_text_atomic(path, dumps_canonical(sorted(set(rejections))))

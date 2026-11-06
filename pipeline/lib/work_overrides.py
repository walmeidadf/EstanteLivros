"""Correções à mão dos dados das obras (título original, romanização, ano).

A migração recompõe `originalTitle`, `originalTitleRomanized` e `firstPublished`
a partir do CSV do legado a cada execução. Como o legado fica fora do git, uma
correção feita direto em `catalog/works/` seria desfeita. Por isso ela vive em
`pipeline/config/work_overrides.json`, versionada, com a origem de cada entrada,
e é aplicada pelo `lib/build.py` logo depois de ler o CSV.

Formato:

    {
      "version": 1,
      "works": {
        "slug-da-obra": {
          "originalTitleRomanized": "…",   // qualquer um dos campos abaixo
          "source": "de onde veio a correção",
          "date": "2026-11-06"
        }
      }
    }

`null` num campo é uma ausência intencional (ex.: coletânea sem título original):
o campo fica `null` e a cobertura deixa de contá-lo como lacuna.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

SUPPORTED_VERSION = 1
FIELDS = ("originalTitle", "originalTitleRomanized", "firstPublished")
_ISO_DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")


class WorkOverridesError(Exception):
    """work_overrides.json inválido (a migração sai com código 2)."""


@dataclass(frozen=True)
class WorkOverride:
    values: Dict[str, Any]  # só os campos presentes (inclusive os que valem null)
    source: str
    date: Optional[str]


def load(path: Path) -> Dict[str, WorkOverride]:
    """Lê e valida o arquivo. Arquivo ausente = sem correções."""
    path = Path(path)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise WorkOverridesError(f"JSON inválido: {exc}") from exc
    if not isinstance(data, dict) or data.get("version") != SUPPORTED_VERSION:
        raise WorkOverridesError(f"esperado um objeto com version {SUPPORTED_VERSION}")
    works = data.get("works")
    if not isinstance(works, dict):
        raise WorkOverridesError("`works` deve ser um objeto slug → correção")
    result: Dict[str, WorkOverride] = {}
    for slug, entry in works.items():
        where = f"works.{slug}"
        if not isinstance(entry, dict):
            raise WorkOverridesError(f"{where}: esperado um objeto")
        unknown = set(entry) - set(FIELDS) - {"source", "date"}
        if unknown:
            raise WorkOverridesError(f"{where}: campo(s) desconhecido(s): {', '.join(sorted(unknown))}")
        source = entry.get("source")
        if not isinstance(source, str) or not source.strip():
            raise WorkOverridesError(f"{where}: `source` é obrigatório (origem da correção)")
        date = entry.get("date")
        if date is not None and (not isinstance(date, str) or not _ISO_DATE.match(date)):
            raise WorkOverridesError(f"{where}: `date` deve ser AAAA-MM-DD")
        values = {k: entry[k] for k in FIELDS if k in entry}
        if not values:
            raise WorkOverridesError(f"{where}: nenhuma correção (use {', '.join(FIELDS)})")
        for key in ("originalTitle", "originalTitleRomanized"):
            if key in values and values[key] is not None and not (
                    isinstance(values[key], str) and values[key].strip()):
                raise WorkOverridesError(f"{where}.{key}: texto não vazio ou null")
        year = values.get("firstPublished")
        if "firstPublished" in values and year is not None and (
                not isinstance(year, int) or isinstance(year, bool)):
            raise WorkOverridesError(f"{where}.firstPublished: inteiro ou null")
        result[slug] = WorkOverride(values, source.strip(), date)
    return result


def apply(override: Optional[WorkOverride], original: Optional[str], romanized: Optional[str],
          first_published: Optional[int]) -> Tuple[Optional[str], Optional[str], Optional[int], List[str], List[str]]:
    """Aplica a correção aos valores do CSV.

    Devolve (originalTitle, romanizado, ano, campos aplicados, campos redundantes);
    redundante = o CSV já trazia o mesmo valor (a correção pode sair do arquivo)."""
    if override is None:
        return original, romanized, first_published, [], []
    current: Mapping[str, Any] = {
        "originalTitle": original,
        "originalTitleRomanized": romanized,
        "firstPublished": first_published,
    }
    applied: List[str] = []
    redundant: List[str] = []
    out = dict(current)
    for key in FIELDS:
        if key not in override.values:
            continue
        applied.append(key)
        # `null` é marca de ausência intencional (vale mesmo com o CSV vazio).
        if override.values[key] is not None and current[key] == override.values[key]:
            redundant.append(key)
        out[key] = override.values[key]
    return out["originalTitle"], out["originalTitleRomanized"], out["firstPublished"], applied, redundant

"""Leitura de configuração do ambiente (`.env` + variáveis de ambiente).

As variáveis de ambiente vencem o arquivo. Valores de chaves nunca são
impressos: só o nome da variável aparece em mensagens.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Mapping, Optional

ROOT = Path(__file__).resolve().parents[2]

# Chaves por etapa: (obrigatórias, opcionais)
STEP_KEYS: Dict[str, tuple] = {
    "identify": (["WIKIMEDIA_USER_AGENT"], []),
    "country": (["WIKIMEDIA_USER_AGENT"], []),
    "photo": (["WIKIMEDIA_USER_AGENT"], ["SERP_API_KEY", "TAVILY_API_KEY"]),
    "bio": (["WIKIMEDIA_USER_AGENT", "OPENAI_API_KEY", "OPENAI_MODEL"], ["TAVILY_API_KEY"]),
}


class MissingKey(Exception):
    """Chave obrigatória ausente (código de saída 2)."""


def parse_env_file(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not path.is_file():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        elif " #" in value:
            value = value.split(" #", 1)[0].rstrip()
        values[key] = value
    return values


class Env:
    def __init__(self, values: Mapping[str, str]) -> None:
        self._values = dict(values)

    @classmethod
    def load(cls, path: Optional[Path] = None, environ: Optional[Mapping[str, str]] = None) -> "Env":
        values = parse_env_file(path or ROOT / ".env")
        source = os.environ if environ is None else environ
        values.update({k: v for k, v in source.items() if v != ""})
        return cls(values)

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        value = self._values.get(key, "")
        return value if value.strip() else default

    def setdefault(self, key: str, value: str) -> bool:
        """Define um valor só se a chave estiver vazia. Devolve True se definiu."""
        if self.has(key):
            return False
        self._values[key] = value
        return True

    def has(self, key: str) -> bool:
        return self.get(key) is not None

    def require(self, steps: List[str]) -> List[str]:
        """Confere as obrigatórias; devolve avisos sobre as opcionais ausentes."""
        missing, warnings = [], []
        for step in steps:
            required, optional = STEP_KEYS.get(step, ([], []))
            missing += [k for k in required if not self.has(k) and k not in missing]
            warnings += [f"{k} ausente: a etapa {step} vai pular essa fonte"
                         for k in optional if not self.has(k)]
        if missing:
            raise MissingKey("defina " + ", ".join(missing) + " no .env (veja .env.example)")
        return sorted(set(warnings))

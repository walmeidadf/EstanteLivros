"""Orçamento dos planos gratuitos (SerpApi, Tavily) e teto de custo da OpenAI.

Uso do mês = max(livro-razão local, uso informado pela API). O livro-razão fica
em `pipeline/cache/usage/{provedor}-{AAAA-MM}.json` e é incrementado a cada
chamada de rede (hits de cache não gastam).
"""

from __future__ import annotations

import datetime as dt
import json
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional


class BudgetExhausted(Exception):
    def __init__(self, provider: str, detail: str) -> None:
        super().__init__(f"{provider}: {detail}")
        self.provider = provider


class Budget:
    def __init__(self, limits: Mapping[str, Mapping[str, Any]], ledger_dir: Path,
                 remote_usage: Optional[Mapping[str, int]] = None, use_reserve: bool = False,
                 today: Optional[Callable[[], dt.date]] = None) -> None:
        self.limits = {k: dict(v) for k, v in limits.items()}
        self.ledger_dir = ledger_dir
        self.remote_usage = dict(remote_usage or {})
        self.use_reserve = use_reserve
        self._today = today or dt.date.today
        self.run_used: Counter = Counter()
        self.openai_usd = 0.0
        self.openai_tokens = {"input": 0, "output": 0}

    # -- cotas --------------------------------------------------------------

    def is_quota(self, provider: str) -> bool:
        return "monthly" in self.limits.get(provider, {})

    @property
    def month(self) -> str:
        return self._today().strftime("%Y-%m")

    def _ledger_path(self, provider: str) -> Path:
        return self.ledger_dir / f"{provider}-{self.month}.json"

    def local_used(self, provider: str) -> int:
        path = self._ledger_path(provider)
        if not path.is_file():
            return 0
        return int(json.loads(path.read_text(encoding="utf-8")).get("count", 0))

    def used(self, provider: str) -> int:
        return max(self.local_used(provider), int(self.remote_usage.get(provider, 0)))

    def available(self, provider: str) -> Optional[int]:
        """Chamadas ainda permitidas nesta execução (None = sem cota)."""
        if not self.is_quota(provider):
            return None
        lim = self.limits[provider]
        reserve = 0 if self.use_reserve else int(lim.get("reserve", 0))
        monthly_left = int(lim["monthly"]) - self.used(provider) - reserve
        per_run_left = int(lim.get("perRun", lim["monthly"])) - self.run_used[provider]
        return max(0, min(monthly_left, per_run_left))

    def spend(self, provider: str) -> None:
        """Chamado pelo cliente HTTP antes de cada chamada de rede."""
        if provider == "openai":
            self._check_openai()
            return
        if not self.is_quota(provider):
            return
        if self.available(provider) <= 0:
            raise BudgetExhausted(provider, "sem saldo no plano gratuito deste mês"
                                  + ("" if self.use_reserve else " (reserva preservada; use --use-reserve)"))
        self.run_used[provider] += 1
        self.ledger_dir.mkdir(parents=True, exist_ok=True)
        path = self._ledger_path(provider)
        path.write_text(json.dumps({"count": self.local_used(provider) + 1}) + "\n", encoding="utf-8")

    # -- OpenAI -------------------------------------------------------------

    @property
    def openai_max_usd(self) -> float:
        return float(self.limits.get("openai", {}).get("maxUsdPerRun", float("inf")))

    def _check_openai(self) -> None:
        if self.openai_usd >= self.openai_max_usd:
            raise BudgetExhausted("openai", f"teto de US$ {self.openai_max_usd:.2f} por execução atingido")

    def add_openai(self, input_tokens: int, output_tokens: int, usd: float) -> None:
        self.openai_tokens["input"] += input_tokens
        self.openai_tokens["output"] += output_tokens
        self.openai_usd += usd

    def snapshot(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for provider in sorted(self.limits):
            if self.is_quota(provider):
                out[provider] = {"usedMonth": self.used(provider), "usedRun": self.run_used[provider],
                                 "available": self.available(provider)}
        out["openai"] = {"usd": round(self.openai_usd, 4), **self.openai_tokens}
        return out

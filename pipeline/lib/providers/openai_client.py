"""OpenAI Responses API com saída estruturada (JSON Schema estrito)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Tuple

from ..http import Http

RESPONSES = "https://api.openai.com/v1/responses"
PROVIDER = "openai"


class OpenAIError(Exception):
    """Recusa, resposta incompleta ou JSON fora do schema."""


@dataclass
class Usage:
    input_tokens: int
    output_tokens: int

    def cost(self, price_in_per_m: float, price_out_per_m: float) -> float:
        return (self.input_tokens * price_in_per_m + self.output_tokens * price_out_per_m) / 1_000_000


def respond_json(http: Http, api_key: str, model: str, instructions: str, user_input: str,
                 schema_name: str, schema: Dict[str, Any]) -> Tuple[Dict[str, Any], Usage, bool]:
    """Devolve (objeto, uso, veio_do_cache). Requisições idênticas vêm do cache."""
    body = {
        "model": model,
        "instructions": instructions,
        "input": user_input,
        "text": {"format": {"type": "json_schema", "name": schema_name, "strict": True, "schema": schema}},
    }
    resp = http.post_json(PROVIDER, RESPONSES, body, headers={"Authorization": f"Bearer {api_key}"})
    data = resp.data or {}
    usage_raw = data.get("usage") or {}
    usage = Usage(int(usage_raw.get("input_tokens", 0)), int(usage_raw.get("output_tokens", 0)))
    if data.get("status") not in (None, "completed"):
        raise OpenAIError(f"resposta {data.get('status')}: {data.get('incomplete_details')}")
    text = None
    for item in data.get("output", []) or []:
        for part in item.get("content", []) or []:
            if part.get("type") == "refusal":
                raise OpenAIError(f"recusa do modelo: {part.get('refusal')}")
            if part.get("type") == "output_text":
                text = part.get("text")
    if text is None:
        text = data.get("output_text")
    if not text:
        raise OpenAIError("resposta sem texto")
    try:
        obj = json.loads(text)
    except json.JSONDecodeError as exc:
        raise OpenAIError(f"JSON inválido: {exc}") from None
    missing = [k for k in schema.get("required", []) if k not in obj]
    if missing:
        raise OpenAIError(f"campos ausentes: {missing}")
    return obj, usage, resp.from_cache

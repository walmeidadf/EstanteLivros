"""Cliente HTTP único do pipeline: cache em disco, retries, pausa e segredos.

- Chave de cache: sha256 de método + URL + parâmetros + corpo, SEM segredos.
- Hit de cache não chama a rede nem gasta orçamento.
- `offline=True`: um miss levanta `CacheMiss` em vez de chamar a rede.
  `offline_providers` restringe isso a alguns provedores (o dry-run bloqueia só
  os pagos ou com cota e os downloads de imagem).
- Segredos (parâmetros e cabeçalhos marcados) nunca vão para cache, log ou erro.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Mapping, Optional, Tuple

TransportResult = Tuple[int, Dict[str, str], bytes]
Transport = Callable[[str, str, Dict[str, str], Optional[bytes], float], TransportResult]

RETRY_STATUSES = {429, 500, 502, 503, 504}
CACHEABLE_STATUSES = {200, 404}
DEFAULT_SECRET_HEADERS = ("authorization", "x-api-key")
RETRY_WAITS = (1, 2, 4, 8)


class CacheMiss(Exception):
    def __init__(self, provider: str) -> None:
        super().__init__(f"{provider}: resposta ausente do cache (modo offline)")
        self.provider = provider


class HttpError(Exception):
    def __init__(self, provider: str, status: int, url: str, detail: str = "") -> None:
        super().__init__(f"{provider}: HTTP {status} em {url} {detail}".strip())
        self.provider = provider
        self.status = status


@dataclass
class Response:
    status: int
    data: Any = None
    content: bytes = b""
    content_type: Optional[str] = None
    from_cache: bool = False

    @property
    def ok(self) -> bool:
        return self.status == 200


def urllib_transport(method: str, url: str, headers: Dict[str, str], body: Optional[bytes],
                     timeout: float) -> TransportResult:
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, {k.lower(): v for k, v in resp.headers.items()}, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, {k.lower(): v for k, v in (exc.headers or {}).items()}, exc.read() or b""


def _retry_after(headers: Mapping[str, str]) -> Optional[float]:
    value = headers.get("retry-after")
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        try:
            when = parsedate_to_datetime(value)
            return max(0.0, (when - dt.datetime.now(when.tzinfo)).total_seconds())
        except (TypeError, ValueError):
            return None


def safe_url(url: str, secret_params: Iterable[str] = ()) -> str:
    """URL sem os valores de parâmetros secretos."""
    parts = urllib.parse.urlsplit(url)
    secrets = set(secret_params)
    query = [(k, "***" if k in secrets else v) for k, v in urllib.parse.parse_qsl(parts.query)]
    return urllib.parse.urlunsplit(parts._replace(query=urllib.parse.urlencode(query)))


class Http:
    def __init__(self, cache_dir: Path, transport: Optional[Transport] = None,
                 user_agent: Optional[str] = None, refresh: bool = False, offline: bool = False,
                 intervals: Optional[Mapping[str, float]] = None, budget: Any = None,
                 offline_providers: Optional[Iterable[str]] = None,
                 sleep: Callable[[float], None] = time.sleep,
                 clock: Callable[[], float] = time.monotonic, timeout: float = 60.0) -> None:
        self.cache_dir = cache_dir
        self.transport = transport or urllib_transport
        self.user_agent = user_agent or "EstanteDaLila/0.1"
        self.refresh = refresh
        self.offline = offline
        self.offline_providers = set(offline_providers or ())
        self.intervals = dict(intervals or {})
        self.budget = budget
        self.sleep = sleep
        self.clock = clock
        self.timeout = timeout
        self._last: Dict[str, float] = {}
        self.network: Counter = Counter()
        self.cached: Counter = Counter()
        self.missed: Counter = Counter()

    # -- API pública -------------------------------------------------------

    def get_json(self, provider: str, url: str, params: Optional[Mapping[str, Any]] = None,
                 headers: Optional[Mapping[str, str]] = None, secret_params: Iterable[str] = (),
                 use_cache: bool = True) -> Response:
        return self.request(provider, "GET", url, params, headers, None, secret_params, False, use_cache)

    def post_json(self, provider: str, url: str, body: Any, headers: Optional[Mapping[str, str]] = None,
                  use_cache: bool = True) -> Response:
        return self.request(provider, "POST", url, None, headers, body, (), False, use_cache)

    def get_bytes(self, provider: str, url: str, headers: Optional[Mapping[str, str]] = None) -> Response:
        return self.request(provider, "GET", url, None, headers, None, (), True, True)

    # -- núcleo ------------------------------------------------------------

    def cache_key(self, method: str, url: str, params: Mapping[str, Any], body: Any,
                  secret_params: Iterable[str]) -> str:
        secrets = set(secret_params)
        public = sorted((str(k), str(v)) for k, v in params.items() if k not in secrets)
        raw = json.dumps({"m": method, "u": url, "p": public, "b": body}, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def request(self, provider: str, method: str, url: str, params: Optional[Mapping[str, Any]],
                headers: Optional[Mapping[str, str]], body: Any, secret_params: Iterable[str],
                binary: bool, use_cache: bool) -> Response:
        params = dict(params or {})
        secret_params = tuple(secret_params)
        key = self.cache_key(method, url, params, body, secret_params)
        meta_path = self.cache_dir / provider / f"{key}.json"

        if use_cache and not self.refresh and meta_path.is_file():
            cached = self._read_cache(meta_path, binary)
            if cached is not None:
                self.cached[provider] += 1
                return cached
        if self.offline or provider in self.offline_providers:
            self.missed[provider] += 1
            raise CacheMiss(provider)

        if self.budget is not None:
            self.budget.spend(provider)  # pode levantar BudgetExhausted

        full_url = url + ("?" + urllib.parse.urlencode(params) if params else "")
        shown_url = safe_url(full_url, secret_params)
        send_headers = {"User-Agent": self.user_agent, "Accept": "*/*" if binary else "application/json"}
        send_headers.update(headers or {})
        data = None
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            send_headers.setdefault("Content-Type", "application/json")

        status, resp_headers, payload = self._send(provider, method, full_url, send_headers, data, shown_url)
        self.network[provider] += 1

        if status not in CACHEABLE_STATUSES:
            detail = payload[:200].decode("utf-8", "replace") if not binary else ""
            raise HttpError(provider, status, shown_url, _scrub(detail, send_headers))

        content_type = resp_headers.get("content-type")
        response = Response(status=status, content_type=content_type)
        if binary:
            response.content = payload if status == 200 else b""
        elif status == 200:
            try:
                response.data = json.loads(payload.decode("utf-8")) if payload else None
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise HttpError(provider, status, shown_url, f"JSON inválido: {exc}") from None
        if use_cache:
            self._write_cache(meta_path, method, url, params, body, secret_params, response, binary)
        return response

    def _send(self, provider: str, method: str, url: str, headers: Dict[str, str],
              data: Optional[bytes], shown_url: str) -> TransportResult:
        attempt = 0
        while True:
            self._pace(provider)
            try:
                status, resp_headers, payload = self.transport(method, url, headers, data, self.timeout)
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
                status, resp_headers, payload = 599, {}, str(exc).encode()
            if status not in RETRY_STATUSES and status != 599:
                return status, resp_headers, payload
            if attempt >= len(RETRY_WAITS):
                if status == 599:
                    raise HttpError(provider, status, shown_url, "falha de rede")
                return status, resp_headers, payload
            wait = _retry_after(resp_headers)
            self.sleep(wait if wait is not None else RETRY_WAITS[attempt])
            attempt += 1

    def _pace(self, provider: str) -> None:
        interval = self.intervals.get(provider, 0.0)
        last = self._last.get(provider)
        now = self.clock()
        if last is not None and interval > 0 and now - last < interval:
            self.sleep(interval - (now - last))
            now = self.clock()
        self._last[provider] = now

    # -- cache -------------------------------------------------------------

    def _read_cache(self, meta_path: Path, binary: bool) -> Optional[Response]:
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        response = Response(status=meta["status"], content_type=meta.get("contentType"), from_cache=True)
        if binary:
            bin_path = meta_path.with_suffix(".bin")
            if meta["status"] == 200:
                if not bin_path.is_file():
                    return None
                response.content = bin_path.read_bytes()
        else:
            response.data = meta.get("body")
        return response

    def _write_cache(self, meta_path: Path, method: str, url: str, params: Mapping[str, Any], body: Any,
                     secret_params: Iterable[str], response: Response, binary: bool) -> None:
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        secrets = set(secret_params)
        meta = {
            "request": {"method": method, "url": url,
                        "params": {k: v for k, v in params.items() if k not in secrets}, "body": body},
            "status": response.status,
            "contentType": response.content_type,
            "retrievedAt": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        }
        if binary:
            if response.status == 200:
                meta_path.with_suffix(".bin").write_bytes(response.content)
        else:
            meta["body"] = response.data
        tmp = meta_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(meta, ensure_ascii=False) + "\n", encoding="utf-8")
        tmp.replace(meta_path)


def _scrub(text: str, headers: Mapping[str, str]) -> str:
    """Remove de mensagens qualquer valor de cabeçalho secreto."""
    for name, value in headers.items():
        if name.lower() in DEFAULT_SECRET_HEADERS and value:
            text = text.replace(value, "***")
            if value.lower().startswith("bearer "):
                text = text.replace(value[7:], "***")
    return text

#!/usr/bin/env python3
"""Enriquece autorias: Wikidata (QID), país, foto e bio (proposta).

Carga inicial (em ondas, com revisão entre elas):
    python3 pipeline/enrich_authors.py --wave 1        # grátis: Wikidata, Wikipédia, Commons
    python3 pipeline/enrich_authors.py --wave 2        # bios via OpenAI a partir da Wikipédia
    python3 pipeline/enrich_authors.py --wave 3        # cota: SerpApi e Tavily
Manutenção (autoria nova):
    python3 pipeline/enrich_authors.py --only nova-autora

Sempre conferir antes com --dry-run. Código de saída: 0 ok; 1 falhas ou
catálogo resultante inválido; 2 chave ausente ou catálogo de partida inválido.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import summaries  # noqa: E402
from lib.authors import bio as bio_step  # noqa: E402
from lib.authors import country as country_step  # noqa: E402
from lib.authors import identify as identify_step  # noqa: E402
from lib.authors import photo as photo_step  # noqa: E402
from lib.authors.context import AuthorResult, Context, Waves, read_config  # noqa: E402
from lib.authors.countries_builder import build_countries  # noqa: E402
from lib.budget import Budget, BudgetExhausted  # noqa: E402
from lib.checks import Issue, check_catalog, load_catalog, load_schemas  # noqa: E402
from lib.enrich_report import render_photos_html, render_review, render_run_entry  # noqa: E402
from lib.env import Env, MissingKey  # noqa: E402
from lib.http import CacheMiss, Http, HttpError  # noqa: E402
from lib.jsonio import dumps_canonical, write_catalog, write_text_atomic  # noqa: E402
from lib.providers import serpapi, tavily  # noqa: E402
from lib.providers.openai_client import OpenAIError  # noqa: E402
from lib.selection import PENDING, select  # noqa: E402
from validate_catalog import print_issues, write_report  # noqa: E402

# No dry-run, só o que custa (ou baixa imagens) fica bloqueado; Wikimedia responde e vai para o cache.
DRY_RUN_BLOCKED = {"openai", "serpapi", "tavily", "images"}

PIPELINE = Path(__file__).resolve().parent
ROOT = PIPELINE.parent
STEPS = ["identify", "country", "photo", "bio"]
# Valores de referência do .env.example (gpt-5.4-mini), usados se o .env não definir.
DEFAULT_PRICES = {"OPENAI_PRICE_INPUT_PER_M": "0.75", "OPENAI_PRICE_OUTPUT_PER_M": "4.50"}


class Paths:
    def __init__(self, root: Path = ROOT) -> None:
        self.root = root
        self.catalog = root / "catalog"
        self.config = root / "pipeline" / "config"
        self.cache = root / "pipeline" / "cache"
        self.plans = root / "docs" / "plans"

    @property
    def state(self) -> Path:
        return self.cache / "enrich_state.json"


def _read(path: Path, default: Any) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else default


def build_context(paths: Paths, env: Env, args: argparse.Namespace, transport=None,
                  today=dt.date.today, sleep=None) -> Context:
    cat = load_catalog(paths.catalog)
    config = _read(paths.config / "enrich.json", {})
    budget = Budget(_read(paths.config / "budgets.json", {}), paths.cache / "usage",
                    use_reserve=args.use_reserve, today=today)
    http_kwargs = {"sleep": sleep} if sleep else {}
    http = Http(paths.cache, transport=transport, user_agent=env.get("WIKIMEDIA_USER_AGENT"),
                refresh=args.refresh, offline_providers=DRY_RUN_BLOCKED if args.dry_run else None,
                intervals=config.get("minIntervalSeconds"),
                budget=budget, **http_kwargs)
    waves = Waves.for_wave(args.wave, config.get("photo", {}).get("order", ["commons"]))
    if args.steps:
        waves.steps = [s for s in waves.steps if s in args.steps] if args.wave else list(args.steps)
    staging = Path(tempfile.mkdtemp(prefix="enrich-photos-"))
    return Context(
        catalog=cat, http=http, env=env, budget=budget, config=config, waves=waves,
        state=_read(paths.state, {}), staging=staging,
        overrides=_read(paths.config / "author_overrides.json", {}),
        author_wikidata=_read(paths.config / "author_wikidata.json", {}),
        author_photos=_read(paths.config / "author_photos.json", {}),
        rejections=summaries.load_rejections(paths.config / "summary_rejections.json"),
        countries=_read(paths.config / "countries.json", {"countries": {}, "defunct": {}}),
        languages=_read(paths.config / "languages.json", {}),
        occupations=_read(paths.config / "writer_occupations.json", {}),
        prompts_dir=paths.config / "prompts",
        refresh=args.refresh, regenerate=args.regenerate, regenerate_prompt=args.regenerate_prompt,
        dry_run=args.dry_run, today=today,
    )


def fetch_remote_usage(ctx: Context) -> None:
    """Uso do mês informado pelas APIs (não consome cota). Falhas não bloqueiam."""
    blocked, ctx.http.offline_providers = ctx.http.offline_providers, set()
    try:
        for provider, key_name, fn in (("serpapi", "SERP_API_KEY", serpapi.month_usage),
                                       ("tavily", "TAVILY_API_KEY", tavily.month_usage)):
            key = ctx.env.get(key_name)
            if key and provider in ctx.waves_providers():
                try:
                    value = fn(ctx.http, key)
                    if value is not None:
                        ctx.budget.remote_usage[provider] = value
                except (HttpError, OSError) as exc:
                    print(f"aviso: não consegui ler o uso de {provider}: {exc}", file=sys.stderr)
    finally:
        ctx.http.offline_providers = blocked


def run_step(ctx: Context, step: str, author: Dict[str, Any], result: AuthorResult) -> None:
    state = ctx.author_state(author["slug"])
    if step == "identify":
        outcome = identify_step.identify(ctx, author)
        result.done[step] = identify_step.apply(ctx, author, outcome)
    elif step == "country":
        code, source, notes = country_step.choose_country(ctx, author)
        state["countryNotes"] = notes
        result.done[step] = country_step.apply(ctx, author, code, source)
    elif step == "photo":
        outcome, notes = photo_step.run(ctx, author)
        state["photoNotes"] = notes
        result.done[step] = outcome
    elif step == "bio":
        outcome, notes = bio_step.run(ctx, author)
        result.done[step] = outcome
        result.notes += notes


def process(ctx: Context, slugs: List[str]) -> List[AuthorResult]:
    results = []
    for i, slug in enumerate(slugs, start=1):
        author = ctx.catalog.authors[slug]
        result = AuthorResult(slug)
        for step in ctx.waves.steps:
            if not PENDING[step](ctx, author):
                continue
            try:
                run_step(ctx, step, author, result)
            except CacheMiss as miss:
                ctx.needed[miss.provider] += 1
                result.done[step] = f"precisa de {miss.provider}"
            except BudgetExhausted as exc:
                result.deferred[step] = exc.provider
            except (HttpError, OpenAIError, bio_step.BioError, photo_step.PhotoError,
                    summaries.SummaryError, KeyError, ValueError) as exc:
                result.failed[step] = str(exc)
        if not ctx.dry_run:
            print(f"[{i}/{len(slugs)}] {slug}: " + " · ".join(
                [f"{k}={v}" for k, v in result.done.items()]
                + [f"{k}=ADIADA({v})" for k, v in result.deferred.items()]
                + [f"{k}=FALHOU" for k in result.failed]), flush=True)
        results.append(result)
    return results


def update_country_vocab(ctx: Context) -> None:
    used = sorted({a["country"] for a in ctx.catalog.authors.values() if a.get("country")})
    known = ctx.countries.get("countries", {})
    existing = {c["code"]: c for c in (ctx.catalog.vocabularies or {}).get("countries", [])}
    entries = []
    for code in used:
        info = known.get(code) or existing.get(code) or {"name": code, "languages": []}
        entries.append({"code": code, "name": info.get("name") or code, "languages": list(info.get("languages", []))})
    entries.sort(key=lambda c: (c["name"].lower(), c["code"]))
    ctx.catalog.vocabularies["countries"] = entries


def catalog_files(cat) -> Dict[str, Any]:
    files: Dict[str, Any] = {f"works/{s}.json": w for s, w in sorted(cat.works.items())}
    files.update({f"authors/{s}.json": a for s, a in sorted(cat.authors.items())})
    files["readings.json"] = cat.readings
    files["summaries.json"] = cat.summaries
    files["vocabularies.json"] = cat.vocabularies
    return files


def commit(ctx: Context, paths: Paths, schemas) -> List[Issue]:
    """Valida o resultado; se válido, grava catálogo, fotos, estado e relatórios."""
    update_country_vocab(ctx)
    staged = {f"authors/{p.name}" for p in ctx.staging.iterdir()} if ctx.staging.exists() else set()
    deleted = {p.as_posix() for p in ctx.photos_to_delete}
    ctx.catalog.media = ((ctx.catalog.media or set()) - deleted) | staged
    issues = check_catalog(ctx.catalog, schemas)
    if issues:
        return issues
    write_catalog(catalog_files(ctx.catalog), paths.catalog)
    media = paths.catalog / "media" / "authors"
    media.mkdir(parents=True, exist_ok=True)
    for rel in deleted - staged:
        (paths.catalog / "media" / rel).unlink(missing_ok=True)
    for path in sorted(ctx.staging.iterdir()):
        shutil.move(str(path), str(media / path.name))
    return []


def save_state(ctx: Context, paths: Paths) -> None:
    paths.cache.mkdir(parents=True, exist_ok=True)
    write_text_atomic(paths.state, json.dumps(ctx.state, ensure_ascii=False, indent=1, sort_keys=True) + "\n")


def write_reports(ctx: Context, paths: Paths, results, label: str, failures: int) -> None:
    paths.plans.mkdir(parents=True, exist_ok=True)
    write_text_atomic(paths.plans / "revisao-autorias.md", render_review(ctx.catalog, ctx.state))
    write_text_atomic(paths.plans / "revisao-fotos.html", render_photos_html(ctx.catalog, ctx.state))
    log = paths.plans / "enriquecimento-execucoes.md"
    header = "# Execuções do enriquecimento de autorias\n\nUma entrada por execução real (mais recente no fim).\n\n"
    previous = log.read_text(encoding="utf-8") if log.is_file() else header
    entry = render_run_entry(ctx.today().isoformat(), label, results, ctx.http, ctx.budget, failures)
    write_text_atomic(log, previous.rstrip("\n") + "\n\n" + entry)
    reloaded = load_catalog(paths.catalog)
    write_report(reloaded, paths.plans / "cobertura.md")


def print_plan(ctx: Context, slugs: List[str]) -> None:
    print(f"autorias selecionadas: {len(slugs)} · etapas: {','.join(ctx.waves.steps)}")
    print(f"{'provedor':<10} {'necessárias':>11} {'saldo':>7}  cabe?")
    providers = sorted(set(ctx.needed) | {"serpapi", "tavily"} & set(ctx.waves_providers()))
    for p in providers:
        need = ctx.needed[p]
        avail = ctx.budget.available(p)
        if p == "openai":
            print(f"{p:<10} {need:>11} {'—':>7}  ~US$ {ctx.estimated_usd:.4f} (teto US$ {ctx.budget.openai_max_usd:.2f})")
        elif avail is None:
            print(f"{p:<10} {need:>11} {'—':>7}  sem cota")
        else:
            print(f"{p:<10} {need:>11} {avail:>7}  {'sim' if need <= avail else 'NÃO'}")


def main(argv: Optional[Sequence[str]] = None, paths: Optional[Paths] = None, transport=None,
         env: Optional[Env] = None, today=dt.date.today, sleep=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--steps", type=lambda s: [x for x in s.split(",") if x])
    parser.add_argument("--wave", type=int, choices=[1, 2, 3])
    parser.add_argument("--only", type=lambda s: [x for x in s.split(",") if x])
    parser.add_argument("--limit", type=int)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--regenerate", action="store_true")
    parser.add_argument("--regenerate-prompt")
    parser.add_argument("--use-reserve", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--build-countries", action="store_true")
    args = parser.parse_args(argv)
    paths = paths or Paths()
    env = env or Env.load(paths.root / ".env")

    if args.steps and any(s not in STEPS for s in args.steps):
        parser.error(f"etapas válidas: {','.join(STEPS)}")
    schemas = load_schemas(paths.catalog / "schema")
    ctx = build_context(paths, env, args, transport, today, sleep)
    try:
        if args.build_countries:
            env.require(["identify"])
            countries_path = paths.config / "countries.json"
            data = build_countries(ctx, _read(countries_path, {}))
            write_text_atomic(countries_path, dumps_canonical(data))
            print(f"{len(data['countries'])} países gravados em {countries_path}")
            return 0

        start_issues = check_catalog(ctx.catalog, schemas)
        if start_issues:
            print_issues(start_issues, out=sys.stderr)
            print("catálogo de partida inválido: corrija antes de enriquecer", file=sys.stderr)
            return 2
        steps_needing = ctx.waves.steps if ctx.waves.llm else [s for s in ctx.waves.steps if s != "bio"]
        try:
            for w in env.require(steps_needing):
                print("aviso:", w, file=sys.stderr)
        except MissingKey as exc:
            print(str(exc), file=sys.stderr)
            return 2
        if "bio" in ctx.waves.steps and ctx.waves.llm:
            for key, value in DEFAULT_PRICES.items():
                if env.setdefault(key, value):
                    print(f"aviso: {key} não definido no .env; usando {value} (veja .env.example)", file=sys.stderr)
        if "country" in ctx.waves.steps and not ctx.countries.get("countries"):
            print("pipeline/config/countries.json ausente: rode --build-countries antes", file=sys.stderr)
            return 2

        fetch_remote_usage(ctx)
        try:
            slugs = select(ctx, args.only, args.limit)
        except KeyError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        results = process(ctx, slugs)
        failures = sum(len(r.failed) for r in results)

        if args.dry_run:
            print_plan(ctx, slugs)
            print("--dry-run: nada foi gravado")
            return 0

        issues = commit(ctx, paths, schemas)
        save_state(ctx, paths)  # o estado (candidatas, fontes) vale mesmo se a gravação falhar
        if issues:
            print_issues(issues, out=sys.stderr)
            print("catálogo resultante inválido: nada foi gravado", file=sys.stderr)
            return 1
        label = f"onda {args.wave}" if args.wave else ("manutenção" if args.only else "todas as fontes")
        write_reports(ctx, paths, results, label, failures)
        for r in results:
            for step, err in r.failed.items():
                print(f"FALHA {r.slug} {step}: {err}", file=sys.stderr)
        snap = ctx.budget.snapshot()
        print(f"autorias: {len(results)} · falhas: {failures} · adiadas: "
              f"{sum(len(r.deferred) for r in results)} · OpenAI US$ {snap['openai']['usd']:.4f}")
        return 1 if failures else 0
    finally:
        shutil.rmtree(ctx.staging, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())

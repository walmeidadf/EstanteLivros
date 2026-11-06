#!/usr/bin/env python3
"""Enriquece capas de obras: baixa, mede, busca (só fontes gratuitas) e aplica escolhas.

Fluxo (a capa real nunca entra sozinha; a Lila escolhe por obra):
    python3 pipeline/enrich_covers.py --dry-run                 # plano, sem baixar nada
    python3 pipeline/enrich_covers.py --steps download,measure  # baixa e mede os mestres do catálogo
    python3 pipeline/enrich_covers.py --steps search            # Open Library por ISBN (grátis)
    # revisar docs/plans/revisao-capas.html e preencher pipeline/config/cover_choices.json
    python3 pipeline/enrich_covers.py --steps apply             # aplica as escolhas ao catálogo
Manutenção (obra nova):
    python3 pipeline/enrich_covers.py --only slug-da-obra

Código de saída: 0 ok; 1 falhas ou catálogo resultante inválido; 2 catálogo de
partida inválido ou entrada incorreta.
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

from lib.checks import check_catalog, load_catalog, load_schemas  # noqa: E402
from lib.covers import apply as apply_step  # noqa: E402
from lib.covers import download as download_step  # noqa: E402
from lib.covers import measure as measure_step  # noqa: E402
from lib.covers import report  # noqa: E402
from lib.covers import search as search_step  # noqa: E402
from lib.covers.context import STEPS, CoverContext, CoverError, CoverResult  # noqa: E402
from lib.covers.select import select, step_pending  # noqa: E402
from lib.env import Env  # noqa: E402
from lib.http import CacheMiss, Http, HttpError  # noqa: E402
from lib.jsonio import write_catalog, write_text_atomic  # noqa: E402
from validate_catalog import print_issues, write_report  # noqa: E402

# No dry-run nada é baixado: download de imagens e Open Library ficam bloqueados.
DRY_RUN_BLOCKED = {"images", "openlibrary"}

PIPELINE = Path(__file__).resolve().parent
ROOT = PIPELINE.parent

RUNNERS = {
    "download": download_step.run,
    "measure": measure_step.run,
    "search": search_step.run,
    "apply": apply_step.run,
}


class Paths:
    def __init__(self, root: Path = ROOT) -> None:
        self.root = root
        self.catalog = root / "catalog"
        self.config = root / "pipeline" / "config"
        self.cache = root / "pipeline" / "cache"
        self.plans = root / "docs" / "plans"

    @property
    def state(self) -> Path:
        return self.cache / "cover_state.json"

    @property
    def candidates(self) -> Path:
        return self.cache / "covers" / "candidates"


def _read(path: Path, default: Any) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else default


def build_context(paths: Paths, env: Env, args: argparse.Namespace, transport=None,
                  today=dt.date.today, sleep=None) -> CoverContext:
    config = _read(paths.config / "enrich.json", {})
    http_kwargs = {"sleep": sleep} if sleep else {}
    http = Http(paths.cache, transport=transport, user_agent=env.get("WIKIMEDIA_USER_AGENT"),
                refresh=args.refresh, offline_providers=DRY_RUN_BLOCKED if args.dry_run else None,
                intervals=config.get("minIntervalSeconds"), **http_kwargs)
    return CoverContext(
        catalog=load_catalog(paths.catalog), http=http, config=config,
        steps=[s for s in STEPS if not args.steps or s in args.steps],
        state=_read(paths.state, {}), staging=Path(tempfile.mkdtemp(prefix="enrich-covers-")),
        candidates_dir=paths.candidates, choices=_read(paths.config / "cover_choices.json", {}),
        refresh=args.refresh, dry_run=args.dry_run, today=today)


def process(ctx: CoverContext, slugs: List[str]) -> List[CoverResult]:
    results = []
    for i, slug in enumerate(slugs, start=1):
        work = ctx.catalog.works[slug]
        result = CoverResult(slug)
        for step in ctx.steps:
            if not step_pending(ctx, step, work):
                continue
            try:
                outcome = RUNNERS[step](ctx, work)
                if outcome:
                    result.done[step] = outcome
            except CacheMiss as miss:
                ctx.needed[miss.provider] += 1
                result.done[step] = f"precisa de {miss.provider}"
            except (HttpError, CoverError, OSError) as exc:
                result.failed[step] = str(exc)
        if not ctx.dry_run and (result.done or result.failed):
            print(f"[{i}/{len(slugs)}] {slug}: " + " · ".join(
                [f"{k}={v}" for k, v in result.done.items()] + [f"{k}=FALHOU" for k in result.failed]), flush=True)
        results.append(result)
    return results


def catalog_files(cat) -> Dict[str, Any]:
    files: Dict[str, Any] = {f"works/{s}.json": w for s, w in sorted(cat.works.items())}
    files.update({f"authors/{s}.json": a for s, a in sorted(cat.authors.items())})
    files["readings.json"] = cat.readings
    files["summaries.json"] = cat.summaries
    files["vocabularies.json"] = cat.vocabularies
    return files


def commit(ctx: CoverContext, paths: Paths, schemas) -> list:
    """Valida o resultado; se válido, grava catálogo e promove os mestres escolhidos."""
    staged = {f"covers/{p.name}" for p in ctx.staging.iterdir()} if ctx.staging.exists() else set()
    deleted = set(ctx.covers_to_delete)
    ctx.catalog.media = ((ctx.catalog.media or set()) - deleted) | staged
    issues = check_catalog(ctx.catalog, schemas)
    if issues:
        return issues
    if ctx.changed:
        write_catalog(catalog_files(ctx.catalog), paths.catalog)
    media = paths.catalog / "media" / "covers"
    media.mkdir(parents=True, exist_ok=True)
    for rel in deleted - staged:
        (paths.catalog / "media" / rel).unlink(missing_ok=True)
    for path in sorted(ctx.staging.iterdir()) if ctx.staging.exists() else []:
        shutil.move(str(path), str(media / path.name))
    return []


def save_state(ctx: CoverContext, paths: Paths) -> None:
    paths.cache.mkdir(parents=True, exist_ok=True)
    state = {slug: st for slug, st in ctx.state.items() if st != {"candidates": []}}  # sem entradas vazias
    write_text_atomic(paths.state, json.dumps(state, ensure_ascii=False, indent=1, sort_keys=True) + "\n")


def write_reports(ctx: CoverContext, paths: Paths, results, label: str, failures: int) -> None:
    paths.plans.mkdir(parents=True, exist_ok=True)
    write_text_atomic(paths.plans / "revisao-capas.html", report.render_review_html(ctx))
    write_text_atomic(paths.plans / "capas-backlog.md", report.render_backlog(ctx))
    log = paths.plans / "capas-execucoes.md"
    header = "# Execuções do enriquecimento de capas\n\nUma entrada por execução real (mais recente no fim).\n\n"
    previous = log.read_text(encoding="utf-8") if log.is_file() else header
    entry = report.render_run_entry(ctx.today().isoformat(), label, results, ctx.http, failures)
    write_text_atomic(log, previous.rstrip("\n") + "\n\n" + entry)
    write_report(load_catalog(paths.catalog), paths.plans / "cobertura.md")


def print_plan(ctx: CoverContext, slugs: List[str]) -> None:
    print(f"obras selecionadas: {len(slugs)} · etapas: {','.join(ctx.steps)}")
    print(f"{'provedor':<12} {'chamadas necessárias':>20}")
    for provider in ("images", "openlibrary"):
        print(f"{provider:<12} {ctx.needed[provider]:>20}")
    print("sem cota: SerpApi e Tavily não são usados nesta onda")


def main(argv: Optional[Sequence[str]] = None, paths: Optional[Paths] = None, transport=None,
         env: Optional[Env] = None, today=dt.date.today, sleep=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--steps", type=lambda s: [x for x in s.split(",") if x])
    parser.add_argument("--only", type=lambda s: [x for x in s.split(",") if x])
    parser.add_argument("--limit", type=int)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    paths = paths or Paths()
    env = env or Env.load(paths.root / ".env")
    if args.steps and any(s not in STEPS for s in args.steps):
        parser.error(f"etapas válidas: {','.join(STEPS)}")

    schemas = load_schemas(paths.catalog / "schema")
    ctx = build_context(paths, env, args, transport, today, sleep)
    try:
        start_issues = check_catalog(ctx.catalog, schemas)
        if start_issues:
            print_issues(start_issues, out=sys.stderr)
            print("catálogo de partida inválido: corrija antes de enriquecer", file=sys.stderr)
            return 2
        try:
            for slug, choice in ctx.choices.items():
                if slug not in ctx.catalog.works:
                    raise KeyError(f"cover_choices.json: obra inexistente: {slug}")
                apply_step.validate_choice(slug, choice)
            slugs = select(ctx, args.only, args.limit)
        except (KeyError, CoverError) as exc:
            print(str(exc.args[0]) if isinstance(exc, KeyError) else str(exc), file=sys.stderr)
            return 2
        results = process(ctx, slugs)
        failures = sum(len(r.failed) for r in results)

        if args.dry_run:
            print_plan(ctx, slugs)
            print("--dry-run: nada foi gravado")
            return 0

        issues = commit(ctx, paths, schemas)
        save_state(ctx, paths)  # candidatas e medições valem mesmo se a gravação falhar
        if issues:
            print_issues(issues, out=sys.stderr)
            print("catálogo resultante inválido: nada foi gravado", file=sys.stderr)
            return 1
        label = "manutenção" if args.only else (",".join(args.steps) if args.steps else "todas as etapas")
        write_reports(ctx, paths, results, label, failures)
        for r in results:
            for step, err in r.failed.items():
                print(f"FALHA {r.slug} {step}: {err}", file=sys.stderr)
        print(f"obras: {len(results)} · falhas: {failures}")
        return 1 if failures else 0
    finally:
        shutil.rmtree(ctx.staging, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())

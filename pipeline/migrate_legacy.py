#!/usr/bin/env python3
"""Migra os CSVs validados do legado para o catálogo canônico.

Uso:
    python3 pipeline/migrate_legacy.py [--legacy legacy/exports] [--catalog catalog] [--dry-run]

Código de saída: 0 ok; 1 dados inválidos; 2 entrada ausente ou colunas faltando.
Não faz chamadas de rede e não altera `legacy/` nem `catalog/source/`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.build import build  # noqa: E402
from lib.checks import check_catalog, load_catalog, load_schemas, scan_media  # noqa: E402
from lib.jsonio import read_json, write_catalog  # noqa: E402
from lib.legacy_reader import LegacyDataError, LegacyInputError, read_legacy  # noqa: E402
from lib.schema import SchemaError  # noqa: E402
from lib.slugs import SlugRegistry  # noqa: E402
from validate_catalog import print_issues, write_report  # noqa: E402

PIPELINE = Path(__file__).resolve().parent
ROOT = PIPELINE.parent


def run(legacy_dir: Path, catalog_dir: Path, config_dir: Path, report: Optional[Path],
        dry_run: bool) -> int:
    try:
        legacy = read_legacy(legacy_dir)
    except LegacyInputError as exc:
        print(f"entrada inválida:\n{exc}", file=sys.stderr)
        return 2

    slugs_path = config_dir / "slugs.json"
    overrides_path = config_dir / "author_overrides.json"
    registry = SlugRegistry.load(slugs_path)
    overrides = read_json(overrides_path) if overrides_path.exists() else {}
    summaries_path = catalog_dir / "summaries.json"
    existing_summaries = read_json(summaries_path) if summaries_path.exists() else None
    # Catálogo atual: preserva o que o enriquecimento (F2) já preencheu.
    existing = load_catalog(catalog_dir) if (catalog_dir / "authors").is_dir() else None

    try:
        result = build(legacy, registry, overrides, existing_summaries, existing)
        schemas = load_schemas(catalog_dir / "schema")
    except (LegacyDataError, SchemaError) as exc:
        print(f"dados inválidos: {exc}", file=sys.stderr)
        return 1

    result.catalog.media = scan_media(catalog_dir / "media")
    issues = check_catalog(result.catalog, schemas)
    cat = result.catalog
    readings = cat.readings["readings"]
    aliases = sum(len(g.aliases) for g in result.unified)
    print(f"obras: {len(cat.works)} · leituras: {len(readings)} · "
          f"autorias: {len(cat.authors)} ({aliases} unificadas) · "
          f"releituras: {sum(1 for r in readings if r['reread'])}")
    print(f"slugs novos: {registry.created} · reutilizados: {registry.reused} · truncados: {registry.truncated}")
    print(f"suspeitas de autoria: {len(result.suspects)} (ver docs/plans/cobertura.md)")

    if issues:
        print_issues(issues, out=sys.stderr)
        print("nada foi gravado", file=sys.stderr)
        return 1
    if dry_run:
        print("--dry-run: nada foi gravado")
        return 0

    write_catalog(result.files, catalog_dir)
    registry.save(slugs_path)
    if report is not None:
        write_report(cat, report)
    print(f"catálogo gravado em {catalog_dir}")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--legacy", type=Path, default=ROOT / "legacy" / "exports")
    parser.add_argument("--catalog", type=Path, default=ROOT / "catalog")
    parser.add_argument("--config", type=Path, default=PIPELINE / "config")
    parser.add_argument("--report", type=Path, default=ROOT / "docs" / "plans" / "cobertura.md")
    parser.add_argument("--no-report", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    return run(args.legacy, args.catalog, args.config,
               None if args.no_report else args.report, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())

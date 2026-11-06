#!/usr/bin/env python3
"""Valida o catálogo canônico e gera o relatório de cobertura.

Uso:
    python3 pipeline/validate_catalog.py [--catalog catalog] [--report docs/plans/cobertura.md] [--no-report]

Código de saída: 0 válido; 1 inválido.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.checks import Catalog, Issue, check_catalog, load_catalog, load_schemas  # noqa: E402
from lib.coverage import render_coverage  # noqa: E402
from lib.jsonio import write_text_atomic  # noqa: E402
from lib.schema import SchemaError  # noqa: E402
from lib.themes import ThemeConfig, ThemeConfigError  # noqa: E402
from lib.work_overrides import WorkOverridesError, load as load_work_overrides  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def print_issues(issues: List[Issue], out=None) -> None:
    out = out or sys.stdout
    for issue in issues:
        print(issue.format(), file=out)
    print(f"{len(issues)} erro{'s' if len(issues) != 1 else ''}", file=out)


def write_report(cat: Catalog, report: Path) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    write_text_atomic(report, render_coverage(cat))


def run(catalog_dir: Path, report: Optional[Path]) -> int:
    try:
        schemas = load_schemas(catalog_dir / "schema")
    except (SchemaError, OSError, ValueError) as exc:
        print(f"erro ao carregar schemas: {exc}", file=sys.stderr)
        return 1
    cat = load_catalog(catalog_dir)
    themes_cfg = None
    # themes.json fica em pipeline/config, ao lado de catalog/. Catálogos fora do
    # repositório (testes em pastas temporárias) não o têm: a regra é pulada.
    themes_path = catalog_dir.parent / "pipeline" / "config" / "themes.json"
    if themes_path.is_file():
        try:
            themes_cfg = ThemeConfig.load(themes_path)
        except ThemeConfigError as exc:
            print(f"themes.json inválido: {exc}", file=sys.stderr)
            return 1
    work_overrides = None
    overrides_path = catalog_dir.parent / "pipeline" / "config" / "work_overrides.json"
    if overrides_path.is_file():
        try:
            work_overrides = load_work_overrides(overrides_path)
        except WorkOverridesError as exc:
            print(f"work_overrides.json inválido: {exc}", file=sys.stderr)
            return 1
    issues = check_catalog(cat, schemas, themes_cfg=themes_cfg, work_overrides=work_overrides)
    if report is not None:
        write_report(cat, report)
    print_issues(issues)
    return 1 if issues else 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--catalog", type=Path, default=ROOT / "catalog")
    parser.add_argument("--report", type=Path, default=ROOT / "docs" / "plans" / "cobertura.md")
    parser.add_argument("--no-report", action="store_true")
    args = parser.parse_args(argv)
    return run(args.catalog, None if args.no_report else args.report)


if __name__ == "__main__":
    sys.exit(main())

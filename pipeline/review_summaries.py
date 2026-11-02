#!/usr/bin/env python3
"""Revisão de resumos gerados (bios de autoria; depois, ano e país).

Uso:
    python3 pipeline/review_summaries.py --list [--pending] [--scope-prefix autoria:]
    python3 pipeline/review_summaries.py --approve autoria:han-kang [autoria:…]
    python3 pipeline/review_summaries.py --approve-file aprovados.txt
    python3 pipeline/review_summaries.py --reject autoria:fulana
    python3 pipeline/review_summaries.py --edit autoria:han-kang --text "…" [--and-approve]

Toda alteração passa pelo validador antes de gravar.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import summaries  # noqa: E402
from lib.checks import check_catalog, load_catalog, load_schemas  # noqa: E402
from lib.jsonio import dumps_canonical, write_text_atomic  # noqa: E402
from validate_catalog import print_issues, write_report  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def main(argv: Optional[Sequence[str]] = None, root: Path = ROOT) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true")
    group.add_argument("--approve", nargs="+", metavar="ESCOPO")
    group.add_argument("--approve-file", type=Path)
    group.add_argument("--reject", nargs="+", metavar="ESCOPO")
    group.add_argument("--edit", metavar="ESCOPO")
    parser.add_argument("--pending", action="store_true")
    parser.add_argument("--scope-prefix", default="")
    parser.add_argument("--text")
    parser.add_argument("--and-approve", action="store_true", help="com --edit: aprova o texto editado")
    args = parser.parse_args(argv)

    catalog_dir = root / "catalog"
    cat = load_catalog(catalog_dir)
    rejections_path = root / "pipeline" / "config" / "summary_rejections.json"
    rejections = summaries.load_rejections(rejections_path)

    if args.list:
        items = [s for s in cat.summaries.get("summaries", []) if s["scope"].startswith(args.scope_prefix)]
        if args.pending:
            items = [s for s in items if not s.get("approved")]
        for s in items:
            mark = "✓" if s.get("approved") else "·"
            print(f"{mark} {s['scope']}  [{s.get('source') or '?'}]\n    {s['text']}\n")
        print(f"{len(items)} resumo(s)")
        return 0

    try:
        changed: List[str] = []
        if args.approve or args.approve_file:
            scopes = args.approve or [line.strip() for line in args.approve_file.read_text(encoding="utf-8").splitlines()
                                      if line.strip() and not line.startswith("#")]
            for scope in scopes:
                summaries.approve(cat, scope)
                changed.append(f"aprovado: {scope}")
        elif args.reject:
            for scope in args.reject:
                summaries.reject(cat, scope, rejections)
                changed.append(f"rejeitado: {scope}")
        elif args.edit:
            if not args.text:
                parser.error("--edit exige --text")
            summaries.edit(cat, args.edit, args.text)
            changed.append(f"editado: {args.edit}")
            if args.and_approve:
                summaries.approve(cat, args.edit)
                changed.append(f"aprovado: {args.edit}")
    except summaries.SummaryError as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 1

    issues = check_catalog(cat, load_schemas(catalog_dir / "schema"))
    if issues:
        print_issues(issues, out=sys.stderr)
        print("nada foi gravado", file=sys.stderr)
        return 1
    write_text_atomic(catalog_dir / "summaries.json", dumps_canonical(cat.summaries))
    if args.reject:
        write_text_atomic(rejections_path, dumps_canonical(sorted(set(rejections))))
    write_report(load_catalog(catalog_dir), root / "docs" / "plans" / "cobertura.md")
    print("\n".join(changed))
    return 0


if __name__ == "__main__":
    sys.exit(main())

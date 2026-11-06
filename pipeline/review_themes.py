#!/usr/bin/env python3
"""Gera docs/plans/revisao-temas.md a partir do CSV legado e do themes.json.

Uso:
    python3 pipeline/review_themes.py [--legacy legacy/exports] [--themes pipeline/config/themes.json]
                                      [--output docs/plans/revisao-temas.md]

Só lê: não grava no catálogo nem em legacy/. Use --themes para revisar um
rascunho (por exemplo, em temp/temas/) antes de ele entrar em pipeline/config/.

Código de saída: 0 ok; 2 entrada ausente ou themes.json inválido.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.jsonio import write_text_atomic  # noqa: E402
from lib.legacy_reader import LegacyInputError, read_legacy, split_list, text  # noqa: E402
from lib.themes import ThemeConfig, ThemeConfigError  # noqa: E402
from lib.themes_review import ReviewWork, render_review  # noqa: E402

PIPELINE = Path(__file__).resolve().parent
ROOT = PIPELINE.parent


def run(legacy_dir: Path, themes_path: Path, output: Path) -> int:
    try:
        legacy = read_legacy(legacy_dir)
    except LegacyInputError as exc:
        print(f"entrada inválida:\n{exc}", file=sys.stderr)
        return 2
    try:
        cfg = ThemeConfig.load(themes_path)
    except ThemeConfigError as exc:
        print(f"themes.json inválido: {exc}", file=sys.stderr)
        return 2

    works: List[ReviewWork] = []
    for row in sorted(legacy.works, key=lambda r: r["work_id"]):
        authors = split_list(row["authors"])
        label = f"{text(row['title_pt_br']) or row['work_id']}" + (f" ({authors[0]})" if authors else "")
        works.append(ReviewWork(label, split_list(row["themes"])))

    output.parent.mkdir(parents=True, exist_ok=True)
    write_text_atomic(output, render_review(works, cfg))
    print(f"{len(works)} obras · {len(cfg.taxonomy)} temas canônicos · revisão em {output}")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--legacy", type=Path, default=ROOT / "legacy" / "exports")
    parser.add_argument("--themes", type=Path, default=PIPELINE / "config" / "themes.json")
    parser.add_argument("--output", type=Path, default=ROOT / "docs" / "plans" / "revisao-temas.md")
    args = parser.parse_args(argv)
    return run(args.legacy, args.themes, args.output)


if __name__ == "__main__":
    sys.exit(main())

"""Documento de revisão dos temas (F2.3): `docs/plans/revisao-temas.md`.

Só lê (CSV legado + themes.json). A revisão acontece em sessão: a Lila pede
ajustes, o mapa é editado e o documento é gerado de novo. A saída é
determinística e cobre TODOS os temas originais; um original sem entrada no
mapa aparece em destaque na seção de pendências.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple

from .slugs import strip_accents
from .themes import THEME_FLOOR, ThemeConfig, apply, theme_key


@dataclass
class ReviewWork:
    """Uma obra do CSV, como a revisão a enxerga."""

    label: str            # "Título (Autoria)"
    originals: List[str]  # temas originais, ordem do CSV


def _sort_text(value: str) -> Tuple[str, str]:
    return strip_accents(value).lower(), value


def _by_count_then_text(items: Iterable[Tuple[str, int]]) -> List[Tuple[str, int]]:
    return sorted(items, key=lambda kv: (-kv[1], _sort_text(kv[0])))


def _join(items: Sequence[str]) -> str:
    return "; ".join(items)


def render_review(works: Sequence[ReviewWork], cfg: ThemeConfig) -> str:
    # -- contagens -----------------------------------------------------------
    original_works: Dict[str, List[str]] = defaultdict(list)     # chave -> obras
    original_spelling: Dict[str, str] = {}
    applied_by_work: List[Tuple[ReviewWork, List[str], List[str]]] = []  # obra, themes, unmapped
    canonical_works: Dict[str, List[str]] = defaultdict(list)
    only_with: Dict[str, List[str]] = defaultdict(list)
    members: Dict[str, List[str]] = defaultdict(list)            # canônico -> chaves de originais
    for key, targets in cfg.mapping.items():
        for target in targets:
            members[target].append(key)

    for work in works:
        result = apply(work.originals, cfg)
        for original in result.tags:
            key = theme_key(original)
            original_works[key].append(work.label)
            original_spelling.setdefault(key, cfg.spelling.get(key, original))
        applied_by_work.append((work, result.themes, result.unmapped))
        for theme in result.themes:
            canonical_works[theme].append(work.label)
        if len(result.themes) == 1:
            only_with[result.themes[0]].append(work.label)

    unmapped: Dict[str, List[str]] = defaultdict(list)
    without_theme: List[ReviewWork] = []
    for work, themes, missing in applied_by_work:
        for original in missing:
            unmapped[original].append(work.label)
        if not themes and not missing:
            without_theme.append(work)

    below = sorted(t for t in cfg.taxonomy if len(canonical_works.get(t, [])) < THEME_FLOOR)
    lines: List[str] = [
        "# Revisão de temas",
        "",
        "Gerado por `python3 pipeline/review_themes.py`. Não editar à mão: ajuste "
        "`pipeline/config/themes.json` e gere de novo.",
        "",
        f"{len(works)} obras · {len(original_works)} temas originais · "
        f"{len(cfg.taxonomy)} temas canônicos (alvo {cfg.target_size[0]} a {cfg.target_size[1]}) · "
        f"{len(below)} abaixo do piso de {THEME_FLOOR} obras.",
        "",
    ]

    # -- pendências ------------------------------------------------------------
    if unmapped or without_theme:
        lines += ["## Pendências", ""]
        if unmapped:
            lines += [f"**{len(unmapped)} tema(s) original(is) sem entrada no mapa:**", ""]
            for original in sorted(unmapped, key=_sort_text):
                titles = unmapped[original]
                lines.append(f"- **{original}** ({len(titles)} obra(s)): {_join(titles[:4])}"
                             + (f"; e mais {len(titles) - 4}" if len(titles) > 4 else ""))
            lines.append("")
        if without_theme:
            lines += [f"**{len(without_theme)} obra(s) ficariam sem tema canônico:**", ""]
            lines += [f"- {w.label}: {', '.join(w.originals) or '(sem temas no CSV)'}" for w in without_theme]
            lines.append("")

    # -- resumo ----------------------------------------------------------------
    ordered = sorted(cfg.taxonomy, key=lambda t: (-len(canonical_works.get(t, [])), _sort_text(t)))
    lines += ["## Resumo", "", "| Tema canônico | Obras | Originais que caem nele |", "|---|---:|---:|"]
    for theme in ordered:
        mark = " ⚠" if theme in below else ""
        lines.append(f"| {theme}{mark} | {len(canonical_works.get(theme, []))} | {len(members.get(theme, []))} |")
    lines += ["", f"⚠ = abaixo do piso de {THEME_FLOOR} obras (só relatório, não bloqueia).", ""]

    # -- um bloco por tema canônico ---------------------------------------------
    lines += ["## Temas canônicos", ""]
    for theme in ordered:
        n = len(canonical_works.get(theme, []))
        lines += [f"### {theme} · {n} obra(s)", ""]
        originals = _by_count_then_text(
            (cfg.spelling[k], len(original_works.get(k, []))) for k in members.get(theme, []))
        lines.append("Originais: " + ", ".join(f"{o} ({c})" for o, c in originals))
        alone = only_with.get(theme, [])
        if alone:
            lines.append("")
            lines.append(f"Obras que ficam só com este tema ({len(alone)}): {_join(sorted(alone, key=_sort_text))}")
        lines.append("")

    # -- só tag e vários destinos -------------------------------------------------
    only_tag = [(cfg.spelling[k], len(original_works.get(k, []))) for k, v in cfg.mapping.items() if not v]
    lines += [f"## Só tag ({len(only_tag)})", "",
              "Originais que não viram tema; ficam guardados em `tags`.", ""]
    lines.append(", ".join(f"{o} ({c})" for o, c in _by_count_then_text(only_tag)) or "Nenhum.")
    lines.append("")

    several = sorted(((cfg.spelling[k], v) for k, v in cfg.mapping.items() if len(v) > 1),
                     key=lambda kv: _sort_text(kv[0]))
    lines += [f"## Mapeados para mais de um tema ({len(several)})", ""]
    lines += [f"- {o} → {', '.join(v)}" for o, v in several] or ["Nenhum."]
    lines.append("")

    # -- atenção -------------------------------------------------------------------
    single = sorted(((w.label, themes[0]) for w, themes, _ in applied_by_work if len(themes) == 1),
                    key=lambda kv: _sort_text(kv[0]))
    lines += ["## Atenção", "", f"### Obras com um único tema ({len(single)})", ""]
    lines += [f"- {label}: {theme}" for label, theme in single] or ["Nenhuma."]
    lines.append("")

    lossy: List[Tuple[str, int, int]] = []
    tag_only_keys = {k for k, v in cfg.mapping.items() if not v}
    for work, _, _ in applied_by_work:
        keys = list(dict.fromkeys(theme_key(o) for o in work.originals))
        gone = sum(1 for k in keys if k in tag_only_keys)
        if keys and gone * 2 > len(keys):
            lossy.append((work.label, gone, len(keys)))
    lossy.sort(key=lambda x: _sort_text(x[0]))
    lines += [f"### Obras em que mais da metade dos originais ficou só como tag ({len(lossy)})", ""]
    lines += [f"- {label}: {gone} de {total}" for label, gone, total in lossy] or ["Nenhuma."]
    lines.append("")
    return "\n".join(lines)

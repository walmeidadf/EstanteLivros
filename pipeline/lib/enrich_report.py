"""Relatórios do enriquecimento: revisão (md), folha de fotos (html) e log de execuções."""

from __future__ import annotations

import html
import json
from typing import Any, Dict, List, Optional

from .checks import Catalog


def _bios(cat: Catalog) -> Dict[str, Dict[str, Any]]:
    items = (cat.summaries or {}).get("summaries", [])
    return {s["scope"].split(":", 1)[1]: s for s in items if str(s.get("scope", "")).startswith("autoria:")}


def pending_items(cat: Catalog, state: Dict[str, Dict[str, Any]], author: Dict[str, Any],
                  bio: Optional[Dict[str, Any]]) -> List[str]:
    st = state.get(author["slug"], {})
    wd = author.get("wikidata") or {}
    items: List[str] = []
    if wd.get("status") in ("ambiguous", "not_found"):
        cands = st.get("identifyCandidates") or []
        desc = "; ".join(f"{c['id']} ({c.get('description') or 'sem descrição'})" for c in cands[:5])
        items.append(f"**Identificação {wd['status']}**: {wd.get('evidence')}." + (f" Candidatos: {desc}." if desc else ""))
    elif wd.get("status") == "probable":
        items.append(f"Identificação provável: [{wd['id']}](https://www.wikidata.org/wiki/{wd['id']}) — {wd.get('evidence')}.")
    for note in st.get("countryNotes", []):
        items.append(f"País: {note}.")
    if wd.get("id") and not author.get("country"):
        items.append("**Sem país**: definir `country` em `pipeline/config/author_overrides.json`.")
    if author.get("photo") is None:
        n = len(st.get("photoCandidates") or [])
        items.append(f"**Sem foto**: {n} candidata(s) em `docs/plans/revisao-fotos.html`." if n
                     else "**Sem foto** e sem candidatas.")
    for note in st.get("photoNotes", []):
        items.append(f"Foto: {note}.")
    if bio and not bio.get("approved"):
        source = f"[{bio.get('source')}]({bio['sourceUrl']})" if bio.get("sourceUrl") else (bio.get("source") or "?")
        items.append(f"**Bio para aprovar** (fonte: {source}):\n\n  > {bio['text']}")
    elif bio is None:
        reason = "fontes insuficientes" if st.get("bioInsufficient") else (
            "sem fonte encontrada" if st.get("bioTried") and not st.get("bioSource") else "ainda não gerada")
        items.append(f"Sem bio: {reason}.")
    return items


def render_review(cat: Catalog, state: Dict[str, Dict[str, Any]]) -> str:
    bios = _bios(cat)
    lines = [
        "# Revisão de autorias",
        "",
        "Gerado por `python3 pipeline/enrich_authors.py`. Não editar à mão: as decisões",
        "vão em `pipeline/config/` (QIDs, fotos, países) ou pelo `review_summaries.py` (bios).",
        "",
    ]
    to_approve = []
    sections = 0
    skipped = 0
    for slug, author in sorted(cat.authors.items()):
        bio = bios.get(slug)
        if author.get("wikidata") is None and slug not in state and bio is None:
            skipped += 1  # ainda não processada: não é pendência de revisão
            continue
        items = pending_items(cat, state, author, bio)
        if bio and not bio.get("approved"):
            to_approve.append(f"autoria:{slug}")
        if not items:
            continue
        sections += 1
        lines += [f"## {author['name']} (`{slug}`)", ""]
        lines += [f"- {item}" for item in items]
        lines.append("")
    if sections == 0:
        lines += ["Nenhuma pendência.", ""]
    if skipped:
        lines += [f"_{skipped} autorias ainda não processadas (não listadas)._", ""]
    if to_approve:
        lines += [
            "## Aprovar bios",
            "",
            "Depois de ler, aprove todas de uma vez (remova antes as que não quiser):",
            "",
            "```bash",
            "python3 pipeline/review_summaries.py --approve \\",
            *[f"  {scope} \\" for scope in to_approve[:-1]],
            f"  {to_approve[-1]}",
            "```",
            "",
        ]
    return "\n".join(lines)


def render_photos_html(cat: Catalog, state: Dict[str, Dict[str, Any]]) -> str:
    cards = []
    for slug, author in sorted(cat.authors.items()):
        cands = (state.get(slug) or {}).get("photoCandidates") or []
        if author.get("photo") is not None or not cands:
            continue
        items = []
        for c in cands:
            choice = {slug: {k: c.get(k) for k in ("url", "source", "pageUrl") if c.get(k)}}
            dims = f"{c['width']}×{c['height']}" if c.get("width") else "tamanho ?"
            items.append(
                f'<figure><img src="{html.escape(c["url"])}" alt="" loading="lazy" referrerpolicy="no-referrer">'
                f'<figcaption>{html.escape(c.get("source") or "")} · {dims}<br>{html.escape(c.get("title") or "")}'
                f'<pre>{html.escape(json.dumps(choice, ensure_ascii=False, indent=2)[2:-2])}</pre></figcaption></figure>')
        cards.append(f'<section><h2>{html.escape(author["name"])} <small>{slug}</small></h2>'
                     f'<div class="row">{"".join(items)}</div>'
                     f'<pre class="none">"{slug}": {{ "none": true }}</pre></section>')
    body = "".join(cards) or "<p>Nenhuma foto aguardando revisão.</p>"
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><title>Revisão de fotos</title>
<style>
body{{font-family:system-ui,sans-serif;background:#0E1714;color:#EDE6D6;margin:24px}}
section{{border-top:1px solid #2D3E37;padding:16px 0}} h2 small{{color:#A9B5AE;font-weight:400}}
.row{{display:flex;gap:16px;flex-wrap:wrap}} figure{{margin:0;width:220px}}
img{{width:220px;height:300px;object-fit:cover;background:#15211D}}
figcaption{{font-size:12px;color:#BFC8C2}} pre{{white-space:pre-wrap;font-size:11px;background:#15211D;padding:6px}}
</style></head><body>
<h1>Revisão de fotos</h1>
<p>Copie o bloco da foto escolhida para <code>pipeline/config/author_photos.json</code>
(ou o bloco <code>none</code>) e rode <code>python3 pipeline/enrich_authors.py --steps photo</code>.</p>
{body}
</body></html>
"""


def render_run_entry(date: str, label: str, results: List[Any], http: Any, budget: Any, failures: int) -> str:
    from collections import Counter

    per_step: Dict[str, Counter] = {}
    deferred: Counter = Counter()
    for r in results:
        for step, outcome in r.done.items():
            key = outcome.split(" (")[0] if step != "country" else ("país" if len(outcome) == 2 else outcome)
            per_step.setdefault(step, Counter())[key] += 1
        for step, provider in r.deferred.items():
            deferred[f"{step}/{provider}"] += 1
    lines = [f"## {date} · {label} · {len(results)} autorias", "", "| Etapa | Resultado |", "|---|---|"]
    for step in ("identify", "country", "photo", "bio"):
        if step in per_step:
            summary = " · ".join(f"{k} {v}" for k, v in sorted(per_step[step].items(), key=lambda kv: (-kv[1], kv[0])))
            lines.append(f"| {step} | {summary} |")
    if deferred:
        lines.append("| adiadas por cota | " + " · ".join(f"{k} {v}" for k, v in sorted(deferred.items())) + " |")
    providers = sorted(set(http.network) | set(http.cached))
    calls = " · ".join(f"{p} {http.network[p]} (cache {http.cached[p]})" for p in providers) or "nenhuma"
    snap = budget.snapshot()
    oa = snap["openai"]
    lines += [
        "",
        f"Chamadas: {calls}",
        f"OpenAI: {oa['input']} tokens de entrada, {oa['output']} de saída, US$ {oa['usd']:.4f} · Falhas: {failures}",
    ]
    quotas = [f"{p} {v['usedMonth']} usadas no mês, saldo {v['available']}" for p, v in snap.items() if p != "openai"]
    if quotas:
        lines.append("Cotas: " + " · ".join(quotas))
    return "\n".join(lines) + "\n"

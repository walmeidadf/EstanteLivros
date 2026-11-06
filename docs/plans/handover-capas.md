# Handover — fim das capas (F2.2)

Escrito ao concluir a spec `capas-obras` (PR #10, mergeado). Visão geral dos
próximos passos: [`docs/ROADMAP.md`](../ROADMAP.md), seção "Próximos passos".

## Onde o projeto está

- **131 de 302 obras com capa real**; 171 na tipográfica. Mestres em
  `catalog/media/covers/` (8,8 MB). O app deriva 2:3 em AVIF no build.
- Números: 219 testes do pipeline, 156 do app, build com 1080 páginas,
  validador em 0 erros.

## O que as capas ensinaram

- **A fonte do catálogo é fraca:** das 207 capas da Literal que baixaram (16
  deram 404), só 24 têm lado menor ≥ 400 px; a mediana é 319 px. A Open Library
  por ISBN achou capa para 75 obras, quase todas limítrofes (1 boa).
- **Resolução não basta:** a revisão visual reprovou capas por outros motivos:
  página de rosto escaneada (Kafka, Incidente em Antares), capa de edição
  estrangeira (7 casos), imagem quadrada/3D que perde as laterais no corte 2:3
  (8 casos). A folha `revisao-capas.html` marca `⚠` nas fora de 2:3.
- Padrão: **estética primeiro**. Capa tipográfica é aceitável e estável.

## Como retomar as capas (melhoria contínua)

- **Obra nova:** `python3 pipeline/enrich_covers.py --only slug`, revisar, decidir
  em `pipeline/config/cover_choices.json`, `--steps apply`.
- **Backlog:** `docs/plans/capas-backlog.md` (171 obras, com ISBN). Uma 2ª onda
  paga reaproveita a mesma CLI com uma etapa `search` nova (SerpApi 250/mês e
  Tavily 1.000/mês; limites em `pipeline/config/budgets.json`).
- As 21 obras com candidata rejeitada têm `{"none": true}` em
  `cover_choices.json`. Para trocar de ideia, mude a escolha e rode `apply`.
- `cover.license` e `cover.credit` ficam `null`: a licença das capas de editora
  é desconhecida e o app não mostra crédito de capa.

## Pendências herdadas e novas (não bloqueiam)

- Renomear `photo.author` para `photo.credit` nas autorias (consistência com
  `cover.credit`). Mexe em schema, Zod, pipeline e `AuthorHeader`.
- Capa da Obra com 136 px (tamanho de destaque); pode crescer.
- As anteriores (CSS de grade repetido, `404.astro`, fonte coreana da capa
  tipográfica) seguem em `handover-s5-s6.md`.

## Armadilhas

- `enrich_covers.py` baixa para `pipeline/cache/covers/candidates/` (fora do
  git). Sem esse cache, a folha de revisão fica sem imagens: rode `download`.
- A migração da F1 preserva `cover.file/license/credit/focus/display`
  (`merge_cover`); uma capa escolhida sobrevive a `migrate_legacy.py`.
- Para checar mudança em componente compartilhado, compare o HTML contra um
  baseline em `temp/` e ignore a ordem dos blocos `<style>` (muda sem efeito).

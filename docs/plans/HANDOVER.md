# Handover — fim da F2.1, início da F3 (app)

Escrito ao fim da sessão que concluiu o enriquecimento de autorias. Serve para
retomar o projeto na próxima sessão, que começa a interface (F3).

## Onde o projeto está

- **F0, F1 e F2.1 concluídas.** O catálogo (`catalog/`) está validado, com 0
  erros, e tem conteúdo real suficiente para construir todas as telas do design.
- Tudo está commitado e publicado em `main` (`walmeidadf/EstanteLivros`).

### Números do catálogo

| | |
|---|---|
| Obras | 302 |
| Leituras | 309 (7 releituras; 53 sem ano) |
| Autorias | 215 — 206 identificadas no Wikidata, 202 com país, 174 com foto |
| Bios aprovadas | 209 (em `catalog/summaries.json`, `scope: autoria:{slug}`) |
| Fotos mestre | 174 em `catalog/media/authors/` |
| Idiomas | 15 · Países | 36 · Temas | 496 (ainda não normalizados) |

### Pendências que NÃO bloqueiam a F3

O design tem fallback para todas elas. Corrigir vendo o app, não antes.
- 40 autorias sem foto, com candidatas em `docs/plans/revisao-fotos.html`.
- 9 autorias sem Wikidata e 6 sem bio.
- Revisar o estilo de algumas bios (ocupações a mais, frases genéricas).
- Normalizar os 496 temas (F2, depois do app).
- Capas das obras (F2, depois do app): 223 têm `cover.sourceUrl`, 79 não.

## O que fazer na próxima sessão: F3, spec S1

Começar pela spec **`estante-fundacao`** (ver `docs/ROADMAP.md`, seção F3):
Astro com saída estática, tokens e fontes do design, a camada que lê o
`catalog/` e os componentes base (capa, capa tipográfica, lombada, avatar de
iniciais, prateleira). O app vive em `app/` e **só lê** `catalog/`.

Fonte de verdade do visual: **`design/DESIGN_HANDOFF.md`** (tokens de cor, cor
por idioma, tipografia, componentes, telas, rotas e estados). As telas de
referência estão em `design/telas/*.dc.html` (medidas e estrutura, não código).

Decisões de stack já tomadas (`docs/TECH.md`): Astro estático, ilhas pequenas
para interatividade, busca com índice próprio, validação do catálogo no build
com Zod, PWA com `@vite-pwa/astro`, imagens derivadas no build (nunca hotlink),
Satori + resvg para os cards de compartilhar.

Sugestão de primeira entrega visível: a tela Início com a estante e a busca
(S2), para a Lila testar no Samsung cedo. Combinar deploy (F4) logo após a S1.

## Como o catálogo se lê (resumo; detalhe em `docs/DATA_MODEL.md`)

- `catalog/works/{slug}.json` — obra. Sem dados de leitura.
- `catalog/authors/{slug}.json` — autoria. `photo.file` é relativo a
  `catalog/media/`. **Não há `bio` aqui**: a bio é um resumo.
- `catalog/readings.json` — leituras (ordem do caderno; só o ano).
- `catalog/summaries.json` — bios e (no futuro) resumos de ano/país. Mostrar só
  com `approved: true`.
- `catalog/vocabularies.json` — idiomas, tipos, gêneros, temas e países (com
  nome pt-BR e idioma, para a cor por idioma do design).

Invariantes e regras estão no validador (`pipeline/validate_catalog.py`).
Rodar depois de qualquer mudança no `catalog/`.

## Avisos

- O app não deve chamar APIs externas nem fazer hotlink de imagens: usa só o
  `catalog/` e gera os derivados das imagens no build.
- `legacy/` está fora do git e não pode entrar no caminho de build.
- Chaves de API ficam em `.env` (fora do git); só o pipeline as usa.
- As specs vivem em `docs/specs/` (`.kiro/specs` é link simbólico para lá).

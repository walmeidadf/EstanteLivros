# Tarefas — Capas de obras (F2 · frente 2)

Referências: [`requirements.md`](requirements.md) · [`design.md`](design.md).

Cada tarefa de código termina com os testes passando: no pipeline
`python3 -m unittest discover -s pipeline/tests` (offline); no app
`npm run check` e `node --test` em `app/`. As tarefas 1–11 são implementação; as
12–16 são a execução real, com pontos de revisão humana marcados **(revisão)**.

Dependências: 1 → 2 → 3 → {4, 5, 6} → 7 → 8 → {9, 10} → 11 → 12 → 13 (revisão) →
14 → 15 → 16. Tarefas na mesma chave podem ser feitas em paralelo.

## Fundação: schema e configuração

- [x] 1. Esquema aditivo da capa
  - [x] 1.1 `catalog/schema/work.schema.json`: `cover` ganha `file`, `license`, `credit`, `focus` (`"top"|"center"|"bottom"|null`), `display` (`"typographic"|null`), todos opcionais; `file` casa `^covers/[a-z0-9]+(-[a-z0-9]+)*\.(jpg|png|webp|gif)$`; `sourceUrl`/`source` seguem como estão.
    - _Requisitos: 5.1, 5.2, 6.2_
  - [x] 1.2 `app/src/lib/catalog/schema.ts`: espelhar os campos novos no `workSchema.cover` (Zod), opcionais/nuláveis, mantendo "o Zod espelha o JSON Schema".
    - _Requisitos: 5.3_
  - [x] 1.3 `docs/DATA_MODEL.md`: documentar o `cover` novo e os três estados (`file` → usa a real; `display:"typographic"` → revisada, fica tipográfica; ambos ausentes → não revisada).
    - _Requisitos: 5.3_
  - [x] 1.4 Atualizar fixtures/helpers do pipeline e dos testes do app para o `cover` novo; testes da F1 e do app verdes com o catálogo atual (campos novos ausentes = válido).
    - _Requisitos: 5.3, 10.1_

- [x] 2. Configuração nova
  - [x] 2.1 `pipeline/config/enrich.json`: bloco `cover` (`goodMinSide: 400`, `rejectBelow: 250`, `aspectRange: [0.60, 0.72]`, `openLibrarySize: "L"`) e `minIntervalSeconds.openlibrary`/`images`.
    - _Requisitos: 2.5, 3.4_
  - [x] 2.2 `pipeline/config/cover_choices.json` com `{}`.
    - _Requisitos: 4.2_

## Ajustes na F1

- [x] 3. Integridade e preservação
  - [x] 3.1 `lib/checks.py`: `check_covers` (espelho de `check_photos`) — todo `cover.file` referenciado existe em `catalog/media/covers/`; testes válido/inválido.
    - _Requisitos: 5.5, 10.1_
  - [x] 3.2 `migrate_legacy.py`/`build.py`: ao recompor `cover` do CSV, preservar `file`, `license`, `credit`, `focus` e `display` já presentes (mescla, não sobrescreve).
    - _Requisitos: 5.4_
  - [x] 3.3 Teste de migração com capa enriquecida: campos preservados e segunda execução byte a byte igual.
    - _Requisitos: 10.3_
  - [x] 3.4 Rodar migração + `validate_catalog.py` no catálogo real; conferir o diff (nenhuma capa existente perdida).
    - _Requisitos: 5.5_

## Pipeline: `enrich_covers.py`

- [x] 4. Contexto e seleção (`lib/covers/context.py`, `lib/covers/select.py`)
  - [x] 4.1 `CoverContext` + `Waves` (etapas `download,measure,search,apply`); carrega `enrich.json` (bloco `cover`), `cover_choices.json`, catálogo e estado; staging via `tempfile.mkdtemp`.
    - _Requisitos: 8.1_
  - [x] 4.2 `cover_pending` (obra sem decisão em `cover_choices.json` e sem mestre decidido) e `priority_key` por visibilidade da obra (nº de leituras → ano corrente → slug).
    - _Requisitos: 8.3, 4.5_
  - [x] 4.3 Testes de seleção/pendência (com `--only`, `--limit`, `--refresh`).
    - _Requisitos: 10.1_

- [x] 5. Etapa `download` (`lib/covers/download.py`)
  - Baixa `cover.sourceUrl` via `http.get_bytes("images", …)`; extensão pelo content-type real (fallback `sniff`); grava mestre em staging; bytes não-imagem → falha registrada, obra sem capa local; cache evita rebaixar.
  - Testes: content-type → extensão; não-imagem → falha; 2ª execução usa cache.
  - _Requisitos: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 6. Etapa `measure` (`lib/covers/measure.py`)
  - `lib.images.sniff` → classifica boa (`≥400`) / limítrofe (`250–399`) / baixa (`<250`); grava dimensão e proporção no estado; marca "verificar enquadramento" fora de `aspectRange`.
  - Testes: JPEG/PNG/WEBP mínimos; os três limiares; marca de proporção.
  - _Requisitos: 2.1, 2.2, 2.3, 2.4, 2.6_

- [x] 7. Etapa `search` — só gratuito (`lib/covers/search.py`, `lib/providers/openlibrary.py`)
  - [x] 7.1 Provedor `openlibrary`: `covers.openlibrary.org/b/isbn/{isbn}-L.jpg?default=false` por `isbn13` e, como alternativa, `isbn10`; 404 (sem capa) tratado e cacheado.
    - _Requisitos: 3.1, 3.4_
  - [x] 7.2 Fila: obras sem `sourceUrl` + as que não têm capa "boa" (baixas, limítrofes, download com erro); imagem recebida passa pela aferição do R2; placeholder/pequena descartada; sem fonte → backlog. **Sem SerpApi/Tavily.**
    - _Requisitos: 3.1, 3.2, 3.3_
  - [x] 7.3 User-Agent identificável e pausa `openlibrary` do `enrich.json`.
    - _Requisitos: 3.5_
  - [x] 7.4 Testes: `-L` por isbn13 e fallback isbn10; `?default=false` → 404; placeholder/pequena descartada; obra sem fonte → backlog.
    - _Requisitos: 10.1_

- [x] 8. Etapa `apply` (`lib/covers/apply.py`)
  - Lê `cover_choices.json`: `url` → promove o mestre + monta `cover` (com `focus`); `typographic:true` → `cover.display="typographic"`; `none:true` → segue tipográfica, vai ao backlog; decisão manual vence a classe automática; só a escolhida é promovida.
  - Testes: os três casos; precedência manual; `focus` no objeto.
  - _Requisitos: 4.2, 4.3, 4.4, 5.1, 5.2, 6.2_
  - _Como ficou:_ o `cover` só grava os campos preenchidos (sem `null`), na mesma ordem que a migração preserva. Obra com `cover: null` não tem onde gravar `display` (o schema exige `sourceUrl`): `typographic`/`none` dela vivem só em `cover_choices.json`.

- [x] 9. CLI, commit e dry-run (`pipeline/enrich_covers.py`)
  - [x] 9.1 `argparse` (`--steps`, `--only`, `--limit`, `--refresh`, `--dry-run`); `offline_providers={"images","openlibrary"}` no dry-run; códigos de saída 0/1/2.
    - _Requisitos: 8.1, 8.2, 8.4, 8.5_
  - [x] 9.2 `commit`: valida com `check_catalog`; se válido, grava catálogo e promove os mestres de staging para `catalog/media/covers/`; nada gravado se inválido.
    - _Requisitos: 5.5, 8.6_
  - [x] 9.3 Testes: dry-run não baixa nada; catálogo inválido → nada gravado; `check_covers` acusa `file` sem arquivo; idempotência byte a byte; falha numa obra não para as outras (saída 1).
    - _Requisitos: 8.5, 8.6, 10.1_

- [x] 10. Relatórios (`lib/enrich_report.py`, `lib/coverage.py`)
  - [x] 10.1 `render_covers_html` → `docs/plans/revisao-capas.html`: capa real candidata (2:3, corte central) ao lado da tipográfica, resolução, classe, origem e instrução de copiar o bloco para `cover_choices.json`.
    - _Requisitos: 4.1, 6.4_
  - [x] 10.2 `docs/plans/capas-backlog.md` (sem fonte gratuita) e linha de capas em `docs/plans/capas-execucoes.md` (fonte catálogo×OL, downloads rede×cache, falhas).
    - _Requisitos: 9.2, 9.3_
  - [x] 10.3 Seção de capas em `docs/plans/cobertura.md` (boa / limítrofe / só tipográfica / pendente / backlog).
    - _Requisitos: 9.1_
    - _Como ficou:_ o `cobertura.md` é calculado só a partir do catálogo, então mostra "com URL de origem", "capa local escolhida" e "revisada: fica tipográfica". A divisão boa/limítrofe/baixa e as pendências vivem na folha de revisão (`revisao-capas.html`), no `capas-backlog.md` e no `capas-execucoes.md`, que leem o estado das candidatas.

## App: derivar e mostrar

- [x] 11. Derivação e seleção
  - [x] 11.1 `app/src/lib/images.ts`: glob de `catalog/media/covers/*`, `deriveWorkCover(coverFile, focus, widths)` (2:3, AVIF, `object-position` = `focus`) e `hasWorkCover`; `buildSrcset` aceita `position`.
    - _Requisitos: 7.1, 7.2, 7.4_
  - [x] 11.2 `model.ts → WorkView`: `coverFile`, `coverFocus`, `coverDisplay` derivados de `w.cover` (`coverSourceUrl` segue como proveniência). Testes em `model.test.ts` (com/sem campos; `display:"typographic"` zera a seleção).
    - _Requisitos: 7.3, 10.2_
  - [x] 11.3 `CoverCaption.astro` e `WorkHeader.astro`: derivar quando `coverFile && coverDisplay !== "typographic"` e passar ao `Cover`; senão `null` → tipográfica. Selo "2×" e `loading="lazy"` intactos.
    - _Requisitos: 7.3, 7.5_
  - [x] 11.4 Diff de HTML contra a `main` (baseline em `temp/`, normalizando `data-astro-cid-*`) provando que obras sem capa não mudam; `route-integrity` verde.
    - _Requisitos: 7.6, 10.2_
    - _Como ficou:_ nas 1080 páginas o corpo do HTML e o conteúdo do CSS são idênticos ao baseline. Em 761 páginas dois blocos de CSS de componentes (escopos `data-astro-cid` distintos, sem `:global`) trocaram de ordem, porque `CoverCaption` passou a importar `images.ts`; isso não altera a cascata. Também verificado com um mestre de verdade (temporário, revertido): capa 2:3 de 408×612, `srcset` 104–408 px, `sizes` por tamanho e caminho local em `/_astro/`.
    - _Decisão de implementação:_ a regra "qual capa mostrar" ficou em `src/lib/cover-selection.ts` (pura, testada), com larguras próprias de capa (104/136/272/408) e `sizes` no `Cover`, para o navegador não baixar sempre a maior.

## Execução real

- [x] 12. Baixar e medir os 223 mestres
  - `python3 pipeline/enrich_covers.py --dry-run` e depois `--steps download,measure`; conferir classes e falhas na cobertura.
  - _Requisitos: 1.1, 2.1_
  - _Resultado (6/nov/2026):_ 207 baixadas e 16 com HTTP 404 (link quebrado na Literal). Melhor candidata por obra: 24 boas, 105 limítrofes, 78 baixas; 10 candidatas fora da faixa 2:3. Lado menor: mediana 319 px, mínimo 100 px, máximo 1763 px.

- [x] 13. **(revisão)** Escolher capas dos existentes
  - Abrir `docs/plans/revisao-capas.html`; preencher `cover_choices.json` (real / `typographic` / `none`) e marcar `focus` onde o centro corta mal; rodar `--steps apply`.
  - _Requisitos: 4.1, 4.2, 6.4_
  - _Decisão (6/nov/2026), tarefas 13 e 15 juntas:_ ficam só as capas que sustentam o padrão estético. Das 152 candidatas utilizáveis, 131 entram como capa real. 21 recebem `none` (tipográfica e backlog): 18 que a revisão visual reprovou (página de rosto escaneada, capa de edição estrangeira, proporção fora de 2:3 que perde as laterais no corte) e 3 com lado menor < 300 px. Nenhuma recebeu `focus`: o corte central serviu a todas as mantidas.

- [x] 14. Buscar as que faltam/baixas (gratuito)
  - `--steps search` (OL por ISBN); as resolvidas vão à revisão; o resto entra em `capas-backlog.md`.
  - _Requisitos: 3.1, 3.2_
  - _Resultado (6/nov/2026):_ 271 consultas à Open Library, 0 falhas. Achou capa para 75 obras, mas só 1 é boa (74 limítrofes), e nenhuma limítrofe/baixa do catálogo ganhou alternativa boa. 150 obras ficam sem capa utilizável (`capas-backlog.md`).

- [x] 15. **(revisão)** Escolher as novas e aplicar
  - Revisar as candidatas da OL em `revisao-capas.html`; completar `cover_choices.json`; `--steps apply`.
  - _Requisitos: 4.1, 4.3_
  - _Resultado:_ as candidatas da Open Library eram quase todas limítrofes e entraram na mesma revisão da tarefa 13. 171 obras seguem na tipográfica e em `capas-backlog.md` para a melhoria contínua (segunda onda).

- [ ] 16. Fechar a spec
  - [ ] 16.1 `validate_catalog.py` em código 0; `npm run check` + `node --test` + `npm run build` verdes (capas derivadas no build).
    - _Requisitos: 5.5, 7.6_
  - [ ] 16.2 Conferir `/styleguide` e uma grade real (desktop + celular); atualizar `ROADMAP.md` (F2 item 2) e escrever o handover, anotando o backlog da 2ª onda (paga) e o ponto futuro de renomear `photo.author` → `photo.credit`.
    - _Requisitos: 9.2_

# Tarefas — Obra e Autoria (S5)

Referências: [`requirements.md`](requirements.md) · [`design.md`](design.md).

Cada tarefa de código é incremental e termina **verde**: `npm run check`
(tipos) passa e, quando a tarefa tem testes, `npm test` (runner nativo do Node)
passa. Nada chama rede em build nem em teste; nenhuma tarefa escreve em
`catalog/`. Convenção mantida: regra em `src/lib` (imports relativos), páginas
`.astro` burras (alias `@/`), sem `<script>` nestas telas. Todo comando roda em
`app/`.

A entrega visível da S5 é `/obra/{slug}` (302) e `/autoria/{slug}` (215),
provadas no preview do Pages gerado pelo PR. Trabalho normal: branch
`feat/obra-autoria` → PR (preview) → merge em `main` (deploy de produção). A
documentação pode ir direto na `main`.

Lembretes de escopo:

- Sem botão/link/stub "Compartilhar" (S7); sem PWA/offline (S6).
- Capas reais, resumos e normalização de temas são frente de F2: a capa cai na
  tipográfica, a bio some sem summary aprovado; nada de "—" (handoff §8).
- Mudanças em `lib/catalog/model.ts` são **aditivas** (R13): nenhum campo
  removido ou renomeado; os testes atuais de `lib/catalog/` seguem verdes só
  com os fixtures ganhando os campos novos.
- `CoverCaption` e `WorkGrid` mudam de forma retrocompatível: **sem** a prop
  nova, o HTML das telas S4 (Idioma, País, Tema) é idêntico (diff contra a
  `main`, baseline em `temp/`).
- Artefatos descartáveis (HTML de baseline, capturas, dumps) vão em `temp/`,
  dentro do projeto; nunca em `/tmp`.

Dependências (tarefas na mesma chave podem ir em paralelo):

```
1 → 2 → {3, 4}                         (modelo, depois helpers de apresentação)
{2, 3} → 5 → 6                         (work-page; author-page depende de 5 por reuso)
{2} → 7                                (integridade de rotas)
{3, 4} → {8, 9}                        (ajustes retrocompatíveis em componentes)
{5, 6, 8, 9} → 10                      (componentes novos de layout)
{5, 10} → 11                           (página Obra)
{6, 10} → 12                           (página Autoria)
{11, 12, 7} → 13 → 14 → 15             (build/regressão → preview → PR)
```

## Preparação

- [ ] 1. Branch e baseline de regressão
  - [ ] 1.1 Criar a branch `feat/obra-autoria` a partir da `main` atualizada; confirmar worktree limpa. (`docs/specs/obra-autoria/` fica na `main`.)
  - [ ] 1.2 Rodar `npm run build` **antes de qualquer mudança de código** e copiar para `temp/baseline/` o HTML de `dist/idioma/portugues/index.html`, `dist/pais/brasil/index.html` e `dist/tema/memoria/index.html` (telas que usam `WorkGrid`/`CoverCaption`). Referência dos diffs das tarefas 8, 9 e 13.
    - _Requisitos: 1.2_
  - [ ] 1.3 Confirmar a linha de base: `npm run check` limpo e `npm test` com **108 verdes**.
    - _Requisitos: 14.3_

## Modelo de dados (aditivo, testável)

- [ ] 2. Acréscimos a `lib/catalog/model.ts` (design §"Acréscimos ao modelo") (R13)
  - [ ] 2.1 `ReadingView` ganha `originalEntry: string`, preenchido no laço de `readingsByWork` a partir de `raw.readings[].originalEntry` (já no schema). Ordenação por `sequence` inalterada.
    - _Requisitos: 13.1, 13.3_
  - [ ] 2.2 `PhotoView` ganha `author: string | null`, `license: string | null`, `sourceUrl: string | null`, vindos de `raw.author.photo`. `file` inalterado; `null` quando a autoria não tem foto.
    - _Requisitos: 13.2, 13.3_
  - [ ] 2.3 `AuthorView` ganha `bioSource: BioSource | null` (`{ label: string; url: string | null }`). No mesmo laço de summaries que já extrai a bio, guardar por slug a fonte (`summary.source` → `label`, `summary.sourceUrl` → `url`) **apenas para summaries aprovados**. `approvedSummaryByScope` e todos os agregados ficam inalterados.
    - _Requisitos: 13.2, 13.4, 13.5_
  - [ ] Fim: estender `model.test.ts` — `originalEntry` chega à leitura; crédito da foto (presente e nulo); `bioSource` presente com e sem `url`, e `null` quando a bio não é aprovada ou não existe; aprovação (`approvedSummaryByScope`) e agregados inalterados. Atualizar os fixtures de `model/load/aggregates/atlas/home/timeline.test.ts` com os três campos novos usando valores neutros, mantendo as expectativas atuais.
    - _Requisitos: 13.1, 13.2, 13.3, 13.4, 13.5_

## Helpers de apresentação (regra, testável)

- [ ] 3. Extrair `originalTitlePresentation` para `lib/text.ts` (design §"Camada de seleção", §Componentes) (R2)
  - [ ] 3.1 `originalTitlePresentation(language, title, original)` → `{ text, lang?, dir, font? } | null`: `null` quando `original` é vazio ou igual ao `title` por `fold()`; senão `lang` por `originalTitleLang`, `dir` por `scriptDir(detectScript(original))`, `font` pela regra de script (coreano → `--font-serif-kr`, demais CJK → `--font-serif-jp`, hebraico → `--font-serif-hebrew`, senão nenhuma). Puro.
    - _Requisitos: 2.4, 2.5, 2.6_
  - [ ] Fim: estender `text.test.ts` — igual ao pt-BR (ignora caixa/acento) → `null`; ausente → `null`; coreano/japonês/hebraico/árabe (`dir`/fonte corretos); latino sem `lang`; romanização tratada à parte pela página (sem `lang`).
    - _Requisitos: 2.4, 2.5, 2.6_

- [ ] 4. `isbn13` e rótulos de edição em `lib/text.ts` ou `work-page.ts` (design §"Camada de seleção") (R6)
  - [ ] 4.1 Helper de rótulo de edição: `exact` → "Edição lida"; `representative` com `edition.language === "português"` → "Edição brasileira de referência"; `representative` nos demais → "Edição de referência". ISBN usado como está (13 dígitos, sem hífen).
    - _Requisitos: 6.2, 6.3_
  - [ ] Fim: teste do rótulo nos três casos (coberto junto de `work-page.test.ts`, tarefa 5).
    - _Requisitos: 6.2, 6.3_

## Camada de seleção (regra, testável)

- [ ] 5. `src/lib/work-page.ts` (design §"Camada de seleção") (R2–R7)
  - [ ] 5.1 Tipos `WorkPage`, `OriginalTitle`, `Fact`, `ReadingLine`, `ThemeChip`, `EditionBox`, `NotebookEntry`. `buildWorkPage(catalog, slug)` resolve a `WorkView` por `worksBySlug` (lança se não existir).
    - _Requisitos: 1.1, 1.7_
  - [ ] 5.2 Topo: `original` via `originalTitlePresentation`; `romanized` (quando houver) numa linha à parte sem `lang`; `authors` com `authorHref`. Selo 2× vem de `work.reread` no componente.
    - _Requisitos: 2.1, 2.2, 2.4, 2.5, 2.6, 2.7_
  - [ ] 5.3 `facts` na ordem Idioma (`languageHref`), País (links `countryHref` por `work.countries`, resolvendo nome; some se vazio), Primeira publicação (some se nula), Tipo (`capitalizeFirst`, texto), Gêneros (`capitalizeFirst`, texto; some se vazio). Cada `Fact` sabe se é texto ou links; linha vazia não entra.
    - _Requisitos: 3.1, 3.2, 3.3, 3.4, 3.5, 1.9_
  - [ ] 5.4 `readings` por `sequence`: primeira da ordem = "primeira leitura", demais = "releitura" (pela posição, **não** por `reread`); `year` → `/ano/{ano}`, sem ano → "Entre os primeiros da lista" → `/ano/sem-data`; sempre "nº {sequence} da lista". `readingsHeading`: "Lido uma vez" / "Lido duas vezes" / "Lido N vezes".
    - _Requisitos: 4.1, 4.2, 4.3, 4.4, 4.5_
  - [ ] 5.5 `themes`: chips por slug do tema, ordenados por `worksByTheme` do slug (desc), empate pela ordem do caderno; contagem só quando o slug tem `≥ 5` obras (`CLOUD_MIN_WORKS`); `themeHref`; `capitalizeFirst`; `null` se a obra não tem tema.
    - _Requisitos: 5.1, 5.2, 5.3, 5.4, 5.5_
  - [ ] 5.6 `edition`: linhas Editora/Ano/ISBN presentes; rótulo pela tarefa 4; `null` se nenhuma linha. `catalogerNote` como está; `notebook` com uma entrada por leitura (`originalEntry` + identificação "em {ano}" ou "nº {N} da lista"). Nunca lê `confidence`.
    - _Requisitos: 6.1, 6.2, 6.3, 6.4, 7.1, 7.2, 7.3, 7.4_
  - [ ] Fim: `work-page.test.ts` (fixture no molde de `atlas.test.ts`): título original presente/igual/ausente/romanizado/RTL; ficha com e sem país/gêneros/ano; heading por 1/2/3 leituras; releitura por posição e não por `reread`; leitura sem ano; contagem de tema só a partir de 5; rótulo de edição por `match`/idioma; edição vazia → `null`; `notebook` por leitura; `catalogerNote` ausente → `null`.
    - _Requisitos: 2.4, 3.1, 4.4, 5.2, 6.1, 6.2, 7.2_

- [ ] 6. `src/lib/author-page.ts` (design §"Camada de seleção") (R8–R12)
  - [ ] 6.1 Tipos `AuthorPage`, `PhotoCredit`, `ContextLine`, `ThemeChip`. `buildAuthorPage(catalog, slug)` resolve por `authorsBySlug` (lança se não existir).
    - _Requisitos: 1.1, 1.7_
  - [ ] 6.2 `authorRank(catalog, slug)`: sobre `aggregates.readingsByAuthor`, `position = 1 + (autorias com contagem estritamente maior)`, `tied` = existe outra autoria com a mesma contagem. Pura, sem agregado novo.
    - _Requisitos: 9.3, 13.4_
  - [ ] 6.3 `numbers` (`BigNumber[]`): "livros lidos" = `author.works.length` ("1 livro lido" / "N livros lidos"); WHERE `authorRank.position ≤ 10` entra "{N}º" com rótulo "posição na estante" (ou "…(empatada)" se `tied`); senão entra "primeira leitura" = menor ano datado (omitida se não houver ano). Itens nulos não entram.
    - _Requisitos: 9.1, 9.2, 9.4, 9.5, 9.6, 9.7_
  - [ ] 6.4 `context`: "{País} · escreve em {idiomas}" com `countryHref` e `languageHref`; sem país → "Escreve em {idiomas}". `credit` dos campos novos da foto (nulos omitidos); `null` quando não há foto. `portrait` carrega só `{ ring: true, language: primaryLanguage }`.
    - _Requisitos: 8.1, 8.2, 8.4, 8.5_
  - [ ] 6.5 `bio`: `author.bio` + `author.bioSource`; `null` sem bio aprovada (a fonte nunca aparece sozinha).
    - _Requisitos: 10.1, 10.2, 10.3, 10.4_
  - [ ] 6.6 `works` = `author.works` em ordem do caderno (`toGridWork`); `captionFor(slug)` monta "lido em {ano}" juntando leituras ("lido em 2022 e 2025"; "nº {N} da lista" para sem data). `themes`: conta obras da autoria por slug, mantém `≥ 2`, top 10 desc (empate por nome), rótulo = variante mais frequente, `themeHref`; `null` se nenhum atinge 2.
    - _Requisitos: 11.1, 11.3, 11.4, 12.1, 12.2, 12.3, 12.4_
  - [ ] Fim: `author-page.test.ts`: posição (top 10, empate `tied`, fora do top some); números com/sem primeira leitura; plural de "livro(s)"; bio com/sem fonte e sem bio; legenda (um ano, dois anos, sem data); temas `≥ 2` e top 10; autoria de um livro só (sem bloco de temas); contexto com/sem país; crédito com/sem foto.
    - _Requisitos: 8.2, 8.4, 9.4, 10.2, 11.3, 12.2_

- [ ] 7. Integridade de rotas (`src/lib/route-integrity.ts` + teste) (R14)
  - [ ] 7.1 `allWorkAndAuthorLinks(catalog)`: coleta os `href` `/obra/…` e `/autoria/…` emitidos por `buildHome`, `buildTimeline` + `buildYear`/`buildUndated`, `buildAtlasByLanguage/Country`, `buildAtlasShared`, `buildLanguage/Country/ThemePages` e o índice de busca; devolve o conjunto com a origem de cada um (para a mensagem de erro).
    - _Requisitos: 14.2_
  - [ ] Fim: `route-integrity.test.ts` — contra um fixture, todo link `/obra/{slug}` existe em `worksBySlug` e todo `/autoria/{slug}` em `authorsBySlug`; um link órfão falha o teste com a origem no erro.
    - _Requisitos: 14.1, 14.2_

## Componentes: ajustes retrocompatíveis

- [ ] 8. `CoverCaption.astro` — legenda opcional (design §Componentes, decisão 3) (R11)
  - [ ] 8.1 Adicionar `<slot name="caption" />` após `.author`, só renderizado quando há conteúdo no slot. Nenhuma prop nova obrigatória. Estilo da legenda em `--font-ui`/`--faint`, à parte da autoria.
    - _Requisitos: 11.2, 11.3_
  - [ ] Fim: `npm run check` limpo; sem chamador do slot o markup é idêntico (confirmado na tarefa 13 pelo diff; aqui basta o build passar).
    - _Requisitos: 11.2_

- [ ] 9. `WorkGrid.astro` — `captionFor` opcional (design §Componentes, decisão 3) (R11)
  - [ ] 9.1 Prop `captionFor?: (slug: string) => string | null`. Quando presente e devolve texto, passar ao `CoverCaption` pelo slot `caption`. `sortable` segue independente; a grade mantém `repeat(3, minmax(0, 1fr))` e itens `min-width: 0`.
    - _Requisitos: 11.1, 11.2, 11.3, 1.8_
  - [ ] Fim: `npm run check` limpo. Sem `captionFor`, o HTML de Idioma/País/Tema é idêntico ao baseline (confirmado na tarefa 13).
    - _Requisitos: 11.2, 1.8_

## Componentes novos

- [ ] 10. `BackLink`, `WorkHeader`, `AuthorHeader`, `DescriptionList`, `FactLinks` (design §Componentes) (R1, R2, R8, R9, R15)
  - [ ] 10.1 `BackLink.astro`: `<a class="back" href="/">‹ Estante</a>`, alvo ≥ 44 px, foco visível (estilo promovido de `BrowseHeader`).
    - _Requisitos: 1.4, 15.1_
  - [ ] 10.2 `DescriptionList.astro`: `<dl>` de `{ label, value }`; pula item sem valor; `value` como texto ou slot indexado para linhas com links. Rótulos em `--font-ui` caixa alta `--faint`. `FactLinks.astro`: links separados por "·" (País com vários).
    - _Requisitos: 3.1, 3.3, 1.9_
  - [ ] 10.3 `WorkHeader.astro`: `Shelf` + `Cover size="hero"` (selo 2× por `work.reread`, `alt="Capa de {título}"`) + `h1` (título pt-BR Bodoni itálico) + título original (`lang`/`dir`/fonte) + romanização + `AuthorChip layout="row"` por autoria. Empilha no celular, grid 2 colunas ≥ 760 px. Prateleira/selo decorativos.
    - _Requisitos: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 15.3, 15.4_
  - [ ] 10.4 `AuthorHeader.astro`: retrato circular 132 px (foto 1:1 via `deriveAuthorPhoto` ou `InitialsAvatar ring`, `alt="{nome}"`) + `credit` discreto (`--faint`, link da fonte) quando houver foto + `h1` (nome Bodoni itálico) + `context` (país/idiomas com links; cor de idioma como texto via `onGround`) + `BigNumbers`.
    - _Requisitos: 8.1, 8.2, 8.3, 8.4, 8.5, 9.1, 15.2, 15.3_
  - [ ] Fim: `npm run check` limpo (componentes ainda sem página; a vitrine `/styleguide` pode ganhar uma seção opcional para conferir os dois cabeçalhos).
    - _Requisitos: 1.5_

## Montagem das telas

- [ ] 11. `src/pages/obra/[slug].astro` (design §Páginas) (R1–R7)
  - `getStaticPaths()` por `catalog.works` → `buildWorkPage`; `Base` (`{título} · A estante da Lila`) + `BackLink` + `WorkHeader`; `main`: ficha (`DescriptionList`), Leituras (`<ol>`, anos com link), Temas (chips 44 px `themeHref`), Edição (caixa, rótulo por `match`), "Nota do catalogador" e "Como estava no caderno" (`<blockquote>` por leitura, mais discretos). Blocos `null` não renderizam; sem "—"; sem `<script>`; margem/`max-width` como nas telas "ver todos".
  - _Requisitos: 1.1, 1.3, 1.4, 1.5, 1.6, 1.9, 2.1–2.7, 3.1–3.5, 4.1–4.5, 5.1–5.5, 6.1–6.4, 7.1–7.5, 15.1, 15.4_

- [ ] 12. `src/pages/autoria/[slug].astro` (design §Páginas) (R1, R8–R12)
  - `getStaticPaths()` por `catalog.authors` → `buildAuthorPage`; `Base` (`{nome} · A estante da Lila`) + `BackLink` + `AuthorHeader`; `main`: "Sobre" (bio + "Fonte: {label}" com link), "Na estante da Lila" (`WorkGrid` com `captionFor`, não ordenável), "Temas que mais aparecem" (chips `themeHref` com contagem). Blocos `null` somem; sem `<script>`.
  - _Requisitos: 1.1, 1.3, 1.4, 1.5, 1.6, 1.9, 8.1–8.5, 9.1–9.7, 10.1–10.4, 11.1–11.5, 12.1–12.4, 15.1, 15.4_

## Verificação de ponta a ponta

- [ ] 13. Build, testes e regressão (R1, R13, R14)
  - [ ] 13.1 `npm run check` limpo; `npm test` verde (108 anteriores + `work-page`, `author-page`, `route-integrity` + extensões de `model`/`text`).
    - _Requisitos: 14.3_
  - [ ] 13.2 `npm run build` contra o catálogo real: código 0; **517 páginas novas** (302 `obra` + 215 `autoria`), total 563 → 1080; nenhuma rede; nenhuma URL externa de imagem em `src`.
    - _Requisitos: 1.1, 14.3_
  - [ ] 13.3 Regressão: diff de `dist/idioma/portugues/`, `dist/pais/brasil/` e `dist/tema/memoria/` contra `temp/baseline/` (normalizando `data-astro-cid-*`): **idênticos** (prova que `CoverCaption`/`WorkGrid` sem `captionFor` não mudaram). Confirmar que nenhum `<script>` novo foi para essas telas.
    - _Requisitos: 1.5, 11.2_
  - [ ] 13.4 Conferir no HTML gerado de algumas obras e autorias: um `<h1>` por página; "‹ Estante" para `/`; capa tipográfica onde falta mestre; selo 2× nas 7 obras relidas; anos com link para `/ano/{ano}` e sem-data para `/ano/sem-data`; chips de tema para `/tema/{slug}`; nenhum "—", estrela, nota, dia ou mês; `lang`/`dir` nos títulos originais; crédito só com foto; bio só com summary aprovado.
    - _Requisitos: 1.9, 2.2, 4.3, 5.1, 7.4, 8.2, 10.3, 15.2, 15.3, 15.4_
  - [ ] 13.5 Conferir números de amostra: Elena Ferrante com posição "1º"; uma autoria do grupo de 3 leituras com "9º (empatada)"; uma autoria fora do top 10 sem posição; obra relida (ex.: `a-vegetariana-han-kang`) com "Lido duas vezes" e duas linhas; obra sem título original (ex.: uma em português) sem a linha original.
    - _Requisitos: 4.1, 4.4, 9.4, 9.5_

- [ ] 14. Prova no preview (desktop + celular), capturas em `temp/`
  - [ ] 14.1 `astro preview`: amostras de `/obra/*` (uma com romanização como `a-vegetariana-han-kang`, uma sem capa, uma com várias leituras, uma com duas autorias) e `/autoria/*` (Ferrante no top; uma com foto e crédito; uma sem bio; uma com um só livro) respondem **200**; a busca abre as páginas; capas/avatares de Idioma/País/Tema deixam de cair no Início.
    - _Requisitos: 1.1, 1.2, 14.1_
  - [ ] 14.2 Conferência visual: cabeçalho da Obra (capa + título + original/romanização + autoria); ficha, leituras, temas, edição e os blocos de registro; cabeçalho da Autoria (retrato 132 px com anel, crédito discreto, contexto com links, big numbers); grade "Na estante" com legenda "lido em {ano}"; temas da autoria; sem controles de ordenação; colunas iguais no celular (iframe 390 px no Chrome headless — o `--window-size` corta o lado direito por artefato). A conferência de celular real é no preview do Pages, num aparelho.
    - _Requisitos: 1.8, 2.1, 8.1, 11.3, 15.2_

## Fechamento

- [ ] 15. PR, merge e documentação
  - [ ] 15.1 Abrir o PR de `feat/obra-autoria` (título curto; descrição com resumo, o que foi testado e que a última dívida de rota foi quitada); conferir o preview do Pages e o portão de CI (check + test + build) verdes; merge em `main`; deploy de produção verde; `/obra/*` e `/autoria/*` respondem 200 em `liliane.prateleira.site`; capas, avatares e resultados de busca deixam de cair no Início.
    - _Requisitos: 1.1, 1.2, 14.3_
  - [ ] 15.2 Documentação (direto na `main`): `design/DESIGN_HANDOFF.md` §6.8/§6.9 anotando o que foi implementado e os desvios (país na ficha da Obra; "Nota do catalogador" e caderno visíveis; divergência entre posição e o corte do top 10 do Atlas; sem "Compartilhar"), e §12; `docs/ROADMAP.md` (S5 ✓, dívida de rota de `/obra` e `/autoria` quitada); `AGENTS.md` (estado atual: S5 concluída, número de testes e páginas; próximo da F3 encerrado, retomar F2); `docs/plans/handover-s5-s6.md` (o que a S5 entregou e reusa; o que ainda falta: capas reais, resumos, normalização de temas, `404.astro`, PWA/S6, retrospectiva/S7).
    - _Requisitos: nenhum específico (documentação)_
  - [ ] 15.3 Limpar `temp/` (baseline e capturas) e apagar a branch local `feat/obra-autoria` após o merge.
    - _Requisitos: 14.3_

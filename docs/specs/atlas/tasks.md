# Tarefas — Atlas (S4)

Referências: [`requirements.md`](requirements.md) · [`design.md`](design.md).

Cada tarefa de código é incremental e termina **verde**: `npm run check`
(tipos) passa e, quando a tarefa tem testes, `npm test` (runner nativo do Node)
passa. Nada chama rede em build nem em teste; nenhuma tarefa escreve em
`catalog/`. Convenção da S1–S3 mantida: imports relativos dentro de `src/lib`,
alias `@/` nos `.astro`. Todo comando roda em `app/`.

A entrega visível da S4 é `/atlas`, `/atlas/pais`, `/idioma/{slug}`,
`/pais/{slug}` e `/tema/{slug}`, provadas no preview do Pages gerado pelo PR.
Trabalho normal: branch `feat/atlas` → PR (preview) → merge em `main` (deploy de
produção). A documentação pode ir direto na `main`.

Lembretes de escopo:

- As grades e listas linkam `/obra/{slug}` e `/autoria/{slug}` (S5) no formato
  final: **404 temporário esperado** no preview.
- Sem botão "Compartilhar" (S7), sem PWA/offline (S6).
- Artefatos descartáveis (HTML de baseline, capturas, dumps) vão em `temp/`,
  dentro do projeto; nunca em `/tmp`.
- A camada `lib/catalog/`, `home.ts`, `timeline.ts` e `search.ts` **não mudam**.

Dependências (tarefas na mesma chave podem ir em paralelo):

```
1 → 2 → 3 → 4 → 5 → 6                (camada de seleção, em série)
2 → {7, 8, 9}                         (ajustes e extrações; independentes da cadeia acima)
{3, 7, 8, 9} → 10                     (componentes novos)
{6, 10} → {11, 12, 13, 14, 15} → 16 → 17 → 18
```

Obs.: a tarefa 4 usa `grid-sort.ts` (tarefa 3) em `toGridWork`, e a 6 usa
`onGround` (tarefa 2).

## Preparação

- [ ] 1. Branch e baseline de regressão
  - [ ] 1.1 Criar a branch `feat/atlas` a partir da `main` atualizada; confirmar worktree limpa. (`docs/specs/atlas/` fica na `main`.)
  - [ ] 1.2 Rodar `npm run build` **antes de qualquer mudança de código** e copiar para `temp/baseline/` o HTML de `dist/index.html`, `dist/linha-do-tempo/index.html`, `dist/ano/2024/index.html`, `dist/ano/sem-data/index.html` e `dist/styleguide/index.html`. É a referência dos diffs das tarefas 8, 9 e 16.
    - _Requisitos: 12.1_
  - [ ] 1.3 Confirmar a linha de base de qualidade: `npm run check` limpo e `npm test` com **69 verdes**.
    - _Requisitos: 12.7_

## Helpers de apoio (regra, testável)

- [ ] 2. `text.ts` e `language-color.ts` (design §4.1, §4.3)
  - [ ] 2.1 `text.ts`: `languageTag(language)` com o mapa fixo (pt, en, es, fr, it, ru, ja, de, he, ko, no, ca, cs, ar, nl); idioma desconhecido → `undefined`. `detectScript` passa a devolver `"arabic"` (`\u0600–\u06FF`) e `scriptDir("arabic")` = `"rtl"`. O tipo `Script` ganha `"arabic"`. Sem mudar o resultado para os demais alfabetos.
    - _Requisitos: 7.5, 7.6_
  - [ ] 2.2 `language-color.ts`: `contrastRatio(hexA, hexB)` (fórmula WCAG) e `onGround(hex, min = 4.5)`, que mistura a cor com `#F4EBD8` em passos de 5% até atingir `min` contra `#0E1714`, devolvendo a própria cor se já passa. Constantes dos dois hex no módulo, com comentário de que espelham `--ground` e `--title`.
    - _Requisitos: 8.3, 12.2_
  - [ ] Fim: estender `text.test.ts` (mapa de idiomas; árabe → `arabic`/`rtl`; hebraico segue `rtl`; latim inalterado) e `language-color.test.ts` (`contrastRatio` conhecido, `onGround` devolve a mesma cor para português/japonês/coreano, e para inglês/francês/russo/alemão/"outros" devolve cor com razão ≥ 4,5 e mesma matiz aproximada).
    - _Requisitos: 7.5, 8.3_

## Camada de seleção (regra, testável)

- [ ] 3. Comparador da ordenação (`src/lib/grid-sort.ts`) (design §7) (R10)
  - [ ] 3.1 Tipos `SortKey` (`"seq" | "title" | "author" | "year"`) e `SortData` (`seq`, `title`, `author` já dobrados, `year | null`); `compareBy(key)` devolvendo comparador total e estável: `seq` crescente; `title` (pt-BR) → `seq`; `author` (pt-BR) → `title` → `seq`; `year` crescente com `null` ao fim → `seq`.
    - _Requisitos: 10.3_
  - [ ] 3.2 `toDataset(d)` e `fromDataset(ds)` (ida e volta pelos `data-seq`, `data-title`, `data-author`, `data-year`; ano ausente = string vazia ↔ `null`). Puro, sem DOM (`fromDataset` recebe um objeto com chaves de string), para o mesmo módulo rodar no build e no navegador.
    - _Requisitos: 10.1, 10.4_
  - [ ] Fim: `grid-sort.test.ts` — cada chave; desempates; acentos e caixa (entrada já dobrada); sem ano por último; ida e volta do dataset; estabilidade em empate total.
    - _Requisitos: 10.3, 10.4_

- [ ] 4. `src/lib/atlas.ts`: base comum e Atlas por idioma/país (design §3.0–§3.2) (R2, R3, R11)
  - [ ] 4.1 Tipos `BandData`, `GridWork`, `OthersBlock`; reexportar `SortData` de `grid-sort.ts`. Importar `slugifyTheme`, `themeHref`, `DEFAULT_RAIL_CAP` e o tipo `AuthorPick` de `home.ts` (**sem duplicar** o slug nem o `themeHref`). Helpers `languageHref`, `countryHref`, `capitalizeFirst`, `readingsLabel(n)` ("1 leitura"/"N leituras"), `firstSequence(work)` (ordem do caderno; sem leitura → fim, desempate por slug) e `toGridWork(work)` (monta `href=/obra/{slug}` e o `SortData` com `fold` de `search.ts`, primeira autoria, `firstPublished`).
    - _Requisitos: 11.1, 11.2, 11.4_
  - [ ] 4.2 Índices memoizados por `Catalog` (`WeakMap`): `countryIndex` (código, nome vindo de `AuthorView.countryName`, obras, contagem por idioma, `dominant` com desempate pelo nome do idioma) e `themeIndex` (§6 abaixo, tarefa 6.1). Sem ler disco.
    - _Requisitos: 11.2, 11.7_
  - [ ] 4.3 `buildAtlasByLanguage(catalog)`: faixas por `worksByLanguageDesc`, uma lombada por **obra** no idioma, ordem do caderno, `label` capitalizado, `href=/idioma/{slug}`, contagem de obras; todos os idiomas, sem agrupar.
    - _Requisitos: 2.1, 2.2, 2.3, 2.4, 2.5_
  - [ ] 4.4 `buildAtlasByCountry(catalog)`: ordem por obras desc com desempate pelo **nome** do país (pt-BR); lombada por obra na cor do idioma **da obra**; `COUNTRY_BANDS = 10` faixas individuais; resto em `others` (`band` sem `href` com obras **distintas** + chips `{ name, href, count }` por quantidade desc); um único restante vira a 11ª faixa e `others` é `null`; ≤ 10 países → `others` `null`; obra sem país fora de tudo.
    - _Requisitos: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10_
  - [ ] Fim: início de `atlas.test.ts` (fixture no molde de `timeline.test.ts`): idiomas por quantidade e desempate por nome; lombada por obra; obra com duas autorias de países distintos contada e exibida nos dois; obra sem país ausente; corte 10 + "outros" com obras **distintas** (obra em dois países agrupados conta uma vez); um país restante vira faixa; ≤ 10 sem "outros"; desempate de países por nome.
    - _Requisitos: 2.1, 3.2, 3.5, 3.6, 3.7, 3.8, 3.9, 11.7_

- [ ] 5. `atlas.ts`: blocos compartilhados (design §3.3–§3.5) (R4, R5, R6)
  - [ ] 5.1 `topAuthors(catalog, limit = 10)`: de `readingsByAuthor`, leituras desc, desempate pelo **nome** (pt-BR), corte em 10; itens `AuthorPick` (`/autoria/{slug}`); `null` sem autorias.
    - _Requisitos: 4.1, 4.2, 4.3, 4.5_
  - [ ] 5.2 `themeCloud(catalog)`: sobre `themeIndex`; `CLOUD_MIN_WORKS = 5`, `CLOUD_LIMIT = 30`; `tier` 4/3/2/1 por razão ao maior (≥ 0,60 / ≥ 0,30 / ≥ 0,15 / resto); ordem de exibição alfabética pt-BR; `href` pelo `themeHref`; `null` se ninguém atinge o piso.
    - _Requisitos: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_
  - [ ] 5.3 `eras(catalog)`: épocas "antes de 1800" (só se > 0), séc. XIX, séc. XX, 2000s, 2010s, 2020s (aberto em ≥ 2020), por obra; obra sem ano ignorada; vazias ficam em 0 (exceto "antes de 1800"); `pct` relativo ao maior; `null` se nenhuma obra tem ano.
    - _Requisitos: 6.1, 6.2, 6.4, 6.5_
  - [ ] 5.4 `buildAtlasShared(catalog)` reúne `{ authors, cloud, eras }` (cada um possivelmente `null`) — o que as duas páginas do Atlas passam ao `AtlasInsights`.
    - _Requisitos: 4.5, 5.6, 6.1, 11.3_
  - [ ] Fim: estender `atlas.test.ts` — `topAuthors` (empate por nome, corte, vazio → `null`, singular/plural); nuvem (piso, tiers com valores de borda, ordem alfabética, variantes unificadas sem duplicar obra, vazio → `null`); épocas nas bordas 1799/1800/1899/1900/1999/2000/2009/2010/2019/2020, "antes de 1800" aparece só quando existe, obra sem ano ignorada, `pct`.
    - _Requisitos: 4.2, 5.2, 5.3, 6.1, 6.2, 6.4_

- [ ] 6. `atlas.ts`: páginas de Tema, Idioma e País (design §3.6–§3.8) (R7, R8, R9)
  - [ ] 6.1 `themeIndex` e `buildThemePages(catalog)`: agrupar por `slugifyTheme`; conjunto de obras sem duplicar; rótulo = variante com mais obras (empate: a minúscula; depois pt-BR); `name = capitalizeFirst(rótulo)`; `numbers` = obras · autorias distintas · idiomas distintos (singular/plural); `items` na ordem do caderno. Tema de uma obra gera página normal.
    - _Requisitos: 5.3, 9.1, 9.3, 9.6, 9.7_
  - [ ] 6.2 `buildLanguagePages(catalog)`: uma página por idioma com obra; slug por `slugifyTheme` do nome; **lança** em colisão; `color` de `languageColor`; `numbers` = obras · `% da estante` (`round`, `"<1%"` quando 0 com obras) · autorias distintas; `authors` = autorias do idioma por nº de obras no idioma (desc, nome), cortadas em `DEFAULT_RAIL_CAP`, `null` com 0 ou 1; `items` uma por **obra**.
    - _Requisitos: 7.1, 7.2, 7.3, 7.4, 7.5, 11.5_
  - [ ] 6.3 `buildCountryPages(catalog)`: uma página por país com obra; **lança** em colisão de slug; `dominantLanguage`; `nameColor = onGround(bg)` e `swatch = bg`; `sharing` (países com o mesmo `dominant`, quantidade desc, nome; `null` se nenhum); `summary` de `approvedSummaryByScope.get("pais:"+código)`; `numbers` = obras · autorias com `country === código`; `topAuthor` só com **máximo único e ≥ 2**; `items` = obras com `work.countries.includes(código)`. O código não vai para a tela.
    - _Requisitos: 8.1, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 11.5_
  - [ ] Fim: estender `atlas.test.ts` — Tema: "Segunda Guerra Mundial"/"segunda guerra mundial" viram um slug, rótulo pela variante mais frequente, obra com as duas variantes conta uma vez; Idioma: `%`, `<1%`, autorias, rail `null` com uma autoria, cap 20; País: dominante com empate, `sharing` presente/ausente, `topAuthor` único, em empate e com máximo 1, resumo aprovado/não aprovado/ausente; colisão de slug de idioma e de país lança; obra de dois países nas duas páginas.
    - _Requisitos: 5.3, 7.3, 7.4, 8.4, 8.5, 8.7, 8.8, 11.5, 11.7_

## Componentes: ajustes e extrações

- [ ] 7. Ajustes em componentes existentes (design §4, §5.1) (retrocompatíveis)
  - [ ] 7.1 `YearBand.astro`: `href?` opcional (sem `href` a raiz é `<div>` e a contagem sai como `N`, sem "›") e `shelfPerRow?: boolean` (padrão `false`). Com `shelfPerRow`: lombadas numa grade `repeat(auto-fill, 4px)` com `column-gap: 3px`, células de altura fixa (48 px + `--shelf-height`), lombadas apoiadas na base da célula e `repeating-linear-gradient` `--wood-top → --wood-bottom` desenhando uma prateleira por linha; o `<Shelf/>` separado não é renderizado nesse modo. Sem a prop, markup e CSS atuais **idênticos** (diff contra `temp/baseline/linha-do-tempo`).
    - _Requisitos: 2.6, 3.10, 12.2_
  - [ ] 7.2 `AuthorChip.astro`: `layout?: "stack" | "row"` (padrão `stack`, o Início não muda) e `meta?: string`. Em `row`: avatar à esquerda, nome e `meta` à direita, linha inteira com alvo ≥ 44 px; mesma derivação de foto.
    - _Requisitos: 4.1, 8.7_
  - [ ] 7.3 `CoverCaption.astro`: `showOriginal?: boolean` (padrão `false`). Ligado, mostra o título original em itálico, até 2 linhas, com `lang={languageTag(work.language)}`, `dir` e fonte Noto pelo script (`detectScript`/`scriptDir`); some se não houver original ou se for igual ao pt-BR.
    - _Requisitos: 7.5, 7.6, 9.4_
  - [ ] 7.4 `TypographicCover.astro`: trocar o `originalLang` próprio por `languageTag(language)` com fallback do script; manter a escolha de fonte e `dir` por `detectScript`/`scriptDir`. Efeito esperado e aceito: `lang`/`dir` a mais em títulos originais latinos e em árabe; nenhuma outra diferença.
    - _Requisitos: 7.5, 7.6_
  - [ ] Fim: `npm run check` limpo; build e diff do HTML contra `temp/baseline/`: Início, Ano e Linha do tempo **idênticos**, salvo os atributos `lang`/`dir` da capa tipográfica (listar as diferenças encontradas).
    - _Requisitos: 12.7_

- [ ] 8. Extrair `BigNumbers.astro` e usar na tela Ano (design §5.4)
  - [ ] 8.1 Componente `{ items: { value: string | number; label: string }[] }`; grade `repeat(items.length, 1fr)` até 3 itens, e 2 colunas no celular / `n` no desktop com 4; custom properties `--bn-bg`, `--bn-fg`, `--bn-muted`, `--bn-line` com padrão nos tokens atuais.
    - _Requisitos: 7.3, 8.6, 9.3_
  - [ ] 8.2 `ano/[year].astro` passa a usar `<BigNumbers>` (remover o CSS duplicado da página). O HTML gerado de `/ano/2024` deve ficar **idêntico** ao baseline.
    - _Requisitos: 12.7_
  - [ ] Fim: diff de `dist/ano/2024/index.html` contra `temp/baseline/` (ignorando apenas os hashes de classes escopadas do Astro, se mudarem); `npm run check` limpo.

- [ ] 9. Extrair `AuthorRail.astro` e usar no Início (design §5.5)
  - [ ] 9.1 Componente `{ title?: string }` + slot, com contêiner rolável, `scroll-snap`, `scroll-padding` e o cabeçalho `t-section-title` que hoje vivem em `index.astro`.
    - _Requisitos: 7.4_
  - [ ] 9.2 `index.astro` passa a usar `<AuthorRail title="Quem sempre volta">` com `AuthorChip`; remover o CSS duplicado. O HTML de `/` deve ficar **idêntico** ao baseline.
    - _Requisitos: 12.7_
  - [ ] Fim: diff de `dist/index.html` contra `temp/baseline/`; `npm run check` limpo.

## Componentes novos

- [ ] 10. `AtlasToggle`, `BrowseHeader`, `WorkGrid`, `AtlasInsights` (design §5.2, §5.3, §5.6, §5.7)
  - [ ] 10.1 `AtlasToggle.astro`: `<nav aria-label="Ver o Atlas por">` com dois `<a>` ("Idioma original" → `/atlas`, "País" → `/atlas/pais`), o atual com `aria-current="page"` e estilo de chip ativo (`--accent`/`--accent-ink`); alvos de 44 px, raio de pílula.
    - _Requisitos: 1.1, 1.2_
  - [ ] 10.2 `BrowseHeader.astro`: props `kicker`, `title`, `back`, `tone?`; slot para `BigNumbers`. Com `tone`: fundo e texto do par de §3.2; `h1` Bodoni itálico 500 `clamp(48px, 16vw, 78px)`, `line-height: .95`. Sem `tone`: `--surface` com borda `--line`. Um `<h1>`; kicker em `t-label`; voltar com alvo ≥ 44 px. Sobrescreve as custom properties do `BigNumbers` para a variante colorida.
    - _Requisitos: 7.2, 7.7, 9.2, 9.5, 12.2_
  - [ ] 10.3 `WorkGrid.astro`: props `items: GridWork[]` e `sortable?: boolean`. `<ol class="grid-3">` (3 colunas no celular; no desktop `auto-fill` de `--cover-hero-w`, sem esticar) com um `<li>` por obra, `data-*` de `toDataset`, `CoverCaption size="grid" showOriginal`. Com `sortable`: grupo de botões `hidden` com `aria-pressed` (Da lista · Título · Autoria · Ano de publicação), região `role="status"` visualmente oculta e o `<script>` vanilla: remove `hidden`; no clique reordena os `<li>` existentes com `compareBy`/`fromDataset` (sem recriar, sem rede, sem persistir), atualiza `aria-pressed` e anuncia "Ordenado por …". `sortable={false}` não emite controles, região nem script.
    - _Requisitos: 7.5, 7.9, 10.1, 10.2, 10.4, 10.5, 10.6, 12.1_
  - [ ] 10.4 `AtlasInsights.astro`: recebe `{ authors, cloud, eras }` (podem ser `null`) e renderiza, omitindo os nulos, (a) "Quem ela mais lê" — `<ol>` de `AuthorChip layout="row" meta=readingsLabel`; (b) "Temas que voltam" — links `inline-flex` com `min-height: 44px`, tiers 1–2 em Manrope 600 e 3–4 em Bodoni itálico `--accent`, tamanhos 14/17/24/32 px; (c) "Quando foram escritos" — linhas `[rótulo | barra | "N obras"]`, barra `aria-hidden` em `--bar-neutral` (a maior época em `--accent`). Cada bloco é `<section aria-labelledby>` com `<h2 class="t-section-title">`.
    - _Requisitos: 4.1, 4.3, 4.4, 5.2, 5.4, 6.3, 6.6, 6.7, 12.2_
  - [ ] Fim: `npm run check` limpo (os componentes ainda sem página; a vitrine `/styleguide` pode ganhar uma seção opcional para conferir tiers e cabeçalhos).

## Montagem das telas

- [ ] 11. `src/pages/atlas/index.astro` — Atlas por idioma (design §6.1) (R1, R2, R4–R6)
  - `Base` (`Atlas · A estante da Lila`) + `NavChips active="atlas"` + `h1` "Atlas" + `AtlasToggle active="idioma"`; `getCatalog()` uma vez; `buildAtlasByLanguage` → uma `YearBand` por idioma com `shelfPerRow`, `notes` vazio; `AtlasInsights` com `buildAtlasShared`. Margem lateral e `max-width` no desktop como o Início; legível sem JS.
  - _Requisitos: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 2.1–2.6, 4.1, 5.1, 6.1_

- [ ] 12. `src/pages/atlas/pais.astro` — Atlas por país (design §6.2) (R1, R3)
  - Mesmo esqueleto com `AtlasToggle active="pais"` e título "Atlas por país · A estante da Lila". `buildAtlasByCountry`: faixas com `shelfPerRow`; se `others`: `YearBand` sem `href` ("Outros países") e, abaixo, `<nav aria-label="Outros países">` com `<ul>` de chips (nome + contagem, ≥ 44 px, `/pais/{slug}`); depois `AtlasInsights`.
  - _Requisitos: 1.1, 1.2, 3.1–3.10, 4.1, 5.1, 6.1_

- [ ] 13. `src/pages/idioma/[slug].astro` (design §6.3) (R7)
  - `getStaticPaths()` a partir de `buildLanguagePages` (`params.slug`, `props.page`); `BrowseHeader` colorido (`kicker` "Idioma original", voltar `/atlas`) com `BigNumbers`; WHERE `authors` não for `null`, `AuthorRail title="Autorias"` com `AuthorChip`; `WorkGrid sortable`. Sem texto descritivo.
  - _Requisitos: 7.1–7.9_

- [ ] 14. `src/pages/pais/[slug].astro` (design §6.4) (R8)
  - `getStaticPaths()` a partir de `buildCountryPages`; voltar para `/atlas/pais`; WHERE `sharing`, `<nav aria-label="Países com o mesmo idioma">` com chips; `h1` Bodoni 700 com `color: nameColor` e filete de 4 px em `swatch`; WHERE `summary`, o parágrafo; `BigNumbers` (obras · autorias); WHERE `topAuthor`, seção "Quem ela mais lê aqui" com `AuthorChip layout="row"`; `WorkGrid` com `sortable={false}`. O código do país não é renderizado.
  - _Requisitos: 8.1–8.9_

- [ ] 15. `src/pages/tema/[slug].astro` (design §6.5) (R9)
  - `getStaticPaths()` a partir de `buildThemePages`; `BrowseHeader` sem `tone` (`kicker` "Tema", voltar `/atlas`) com três `BigNumbers`; `WorkGrid sortable`. Fecha o 404 dos carrosséis de tema do Início (slug do `themeHref`).
  - _Requisitos: 9.1–9.7, 12.6_

## Verificação de ponta a ponta

- [ ] 16. Build, testes e regressão (R11, R12)
  - [ ] 16.1 `npm run check` limpo; `npm test` verde (69 anteriores + `atlas`, `grid-sort`, `text`, `language-color`).
    - _Requisitos: 11.7, 12.7_
  - [ ] 16.2 `npm run build` contra o catálogo real: código 0; **546 páginas novas** (`/atlas`, `/atlas/pais`, 15 `idioma`, 36 `pais`, 493 `tema`); nenhuma rede; nenhum slug duplicado; conferir `dist/tema/segunda-guerra-mundial/` com as 7 obras.
    - _Requisitos: 8.1, 9.1, 11.5, 12.6_
  - [ ] 16.3 Regressão: diff de `dist/index.html`, `dist/linha-do-tempo/`, `dist/ano/2024/` e `dist/ano/sem-data/` contra `temp/baseline/`; só os atributos `lang`/`dir` da capa tipográfica podem diferir. Os demais `<script>` do Início (busca) inalterados; **o único `<script>` novo está em Idioma e Tema** (nenhum em Atlas e País).
    - _Requisitos: 12.1, 12.7_
  - [ ] 16.4 Conferir no HTML gerado: `aria-current` no alternador; `aria-hidden` nas lombadas e barras; `lang`/`dir` nos títulos originais; controles de ordenação com `hidden`; um `<h1>` por página; nenhum "—", estrela, nota, dia ou mês; nenhuma URL externa de imagem.
    - _Requisitos: 1.2, 6.7, 7.5, 10.1, 12.2, 12.3, 12.4_
  - [ ] 16.5 Conferir os números: 15 faixas de idioma em `/atlas`; 10 faixas + "Outros países" (26 chips) em `/atlas/pais`; 5 barras de época somando 301 (+1 sem ano ignorada); nuvem com 30 temas e piso 5; top 10 autorias com Ferrante em primeiro.
    - _Requisitos: 2.5, 3.5, 3.6, 4.1, 5.1, 6.1_

- [ ] 17. Prova no preview (desktop + celular), capturas em `temp/`
  - [ ] 17.1 `astro preview`: `/atlas`, `/atlas/pais`, `/idioma/portugues`, `/idioma/noruegues`, `/pais/brasil`, `/pais/estados-unidos`, `/pais/portugal`, `/tema/memoria`, `/tema/segunda-guerra-mundial` respondem **200**; `/atlas?por=pais` serve a vista de idioma; `/obra/*` e `/autoria/*` seguem 404 (S5, esperado).
    - _Requisitos: 1.5, 12.6_
  - [ ] 17.2 Conferência visual: alternar Idioma ↔ País; faixas de 115 e 95 lombadas com prateleira por linha (se não convencer, aplicar o fallback do design §5.1: quebra com prateleira única); chips de "Outros países"; nuvem, barras de época e lista de autorias; cabeçalho de Idioma colorido ("Norueguês" cabendo no celular); contraste do nome do país (inglês, francês, russo) com filete na cor pura; chips de idioma e destaque em País; Tema; ordenação por título/autoria/ano reordenando sem perder links; sem os controles quando o JS está desligado. Capturas headless a 390 px podem cortar o lado direito (artefato da ferramenta): a conferência de celular real é no preview do Pages, num aparelho.
    - _Requisitos: 2.6, 3.3, 7.2, 8.3, 10.1–10.4, 12.2_

## Fechamento

- [ ] 18. PR, merge e documentação
  - [ ] 18.1 Abrir o PR de `feat/atlas` (título curto; descrição com resumo, o que foi testado e o 404 temporário de `/obra` e `/autoria`); conferir o preview do Pages e o portão de CI (check + test + build) verdes; merge em `main`; deploy de produção verde; as rotas novas respondem 200 em `liliane.prateleira.site`; os links "Atlas" do cabeçalho e dos carrosséis de tema do Início deixam de levar a 404.
    - _Requisitos: 12.6, 12.7_
  - [ ] 18.2 Documentação (direto na `main`): `design/DESIGN_HANDOFF.md` §6.4/§6.5 anotando que o alternador usa `/atlas` e `/atlas/pais` (desvio da query string) e §6.11 deixando de ser "pendente" com o desenho adotado, além de §12 (pendências); `docs/ROADMAP.md` (S4 ✓, dívida de rota de `/atlas` e `/tema` quitada); `AGENTS.md` (estado atual: S4 concluída, próximo S5 `obra-autoria`, número de testes); `docs/plans/handover-s4-s5.md` (o que a S4 entrega e reusa na S5: `AuthorChip layout="row"`, `BigNumbers`, `AuthorRail`, `WorkGrid`, `languageTag`, `onGround`; destinos ainda em 404: `/obra` e `/autoria`; tarefa de pipeline: normalizar variantes de caixa dos temas; dívida: CSS de grade repetido em Ano, Sem data e `WorkGrid`).
    - _Requisitos: 12.8_
  - [ ] 18.3 Limpar `temp/` (baseline e capturas) e apagar a branch local `feat/atlas` após o merge.
    - _Requisitos: 12.7_

# Design — Obra e Autoria (S5)

## Visão geral

A S5 fecha a última dívida de rota do app, criando `/obra/{slug}` (302) e
`/autoria/{slug}` (215). Segue a arquitetura já consolidada nas S2–S4:

- **Regra em `src/lib`, página `.astro` burra.** Duas novas unidades puras —
  `work-page.ts` e `author-page.ts` — recebem o `Catalog` de `getCatalog()` e
  devolvem um `WorkPage` / `AuthorPage` com tudo pronto para posicionar: textos
  já formatados, links já montados, blocos ausentes já como `null`. Rodam sob
  `node --test`, sem DOM nem Astro.
- **Zero `<script>`.** Nenhuma das duas telas tem interação; são HTML estático.
  Isso mantém "funciona sem JS" (handoff §10) e não paga custo de ilha.
- **Reaproveita componentes.** `Cover`/`CoverCaption` (capa, selo 2×, título
  original com `lang`/`dir`), `WorkGrid` (grade 3 colunas), `AuthorChip`,
  `InitialsAvatar` (anel 132 px), `BigNumbers`, `Shelf`, `languageHref`,
  `countryHref`, `themeHref`, `onGround`, `slugifyTheme`.
- **Acréscimos ao modelo são aditivos** (R13): três campos novos, nenhum
  removido ou renomeado.

Mapa de navegação fechado pela S5 (as setas que hoje caem no Início):

```
Início / Ano / Idioma / País / Tema / Busca ─┬─ Obra ─┬─ Autoria
                                              │        ├─ Idioma
                                              │        ├─ País (da autoria)
                                              │        ├─ Ano (de cada leitura)
                                              │        └─ Tema
                                              └─ Autoria ─┬─ Obra
                                                          ├─ Idioma
                                                          ├─ País
                                                          └─ Tema
```

## Decisões de design

1. **Cabeçalhos próprios, não `BrowseHeader`.** O `BrowseHeader` da S4 embute
   `kicker` + `h1` + big numbers num bloco colorido de "ver todos"; Obra e
   Autoria têm anatomia diferente (capa ao lado do título; retrato circular com
   crédito). Em vez de parametrizar demais o `BrowseHeader`, a S5 monta o topo
   direto na página com `Shelf`/`Cover`/`InitialsAvatar`. O **link "‹ Estante"**
   fica num componente mínimo `BackLink.astro` (reuso nas duas telas), com o
   mesmo estilo de `.back` do `BrowseHeader` promovido para lá.
2. **Uma `DescriptionList` genérica para a ficha da Obra.** Lista rótulo/valor
   que já esconde a linha quando o valor é vazio (R1.9), sem conhecer o
   catálogo. A página passa itens `{ label, value }` onde `value` é texto ou um
   fragmento com links.
3. **Legenda do `WorkGrid` por `CoverCaption`, via slot nomeado.** `CoverCaption`
   ganha um `<slot name="caption">` opcional renderizado **abaixo** da autoria;
   `WorkGrid` ganha `captionFor?: (slug) => string | null`. Quando nenhum
   chamador passa `captionFor`, o HTML das telas S4 não muda (validado por diff
   contra a `main`, baseline em `temp/`). A legenda "lido em {ano}" é texto
   puro, sem link próprio (o link é a capa inteira).
4. **Retrato com crédito.** `deriveAuthorPhoto(file, "2:3")` já existe para
   retrato; a S5 usa 1:1 no `InitialsAvatar`/foto circular de 132 px (igual ao
   avatar do Atlas, com `ring`). O crédito (R8.2) vem dos campos novos da foto
   no modelo e é renderizado numa `<p class="credit">` discreta sob o retrato.
5. **Posição calculada na camada de seleção**, a partir de
   `aggregates.readingsByAuthor`, não de um agregado novo (R13.4). Função pura
   `authorRank(catalog, slug)` → `{ position, tied } | null`.
6. **Teste de integridade de rotas** roda em `src/lib`: reúne todos os `href`
   `/obra/…` e `/autoria/…` que `home`, `timeline`, `atlas` e o índice de busca
   emitem e confere contra os slugs do catálogo (R14.2). Pega qualquer link
   órfão no `node --test`, antes do build.

## Acréscimos ao modelo (`lib/catalog/model.ts`)

Aditivos, cobertos por extensão dos testes existentes (R13.3).

```ts
export type ReadingView = {
  // …campos atuais…
  originalEntry: string;        // novo: texto do caderno daquela leitura
};

export type PhotoView = {
  file: string;
  author: string | null;        // novo: crédito
  license: string | null;       // novo
  sourceUrl: string | null;     // novo
};

export type BioSource = { label: string; url: string | null };

export type AuthorView = {
  // …campos atuais…
  bio: string | null;
  bioSource: BioSource | null;  // novo: do mesmo summary aprovado
};
```

- **`originalEntry`** vem de `raw.readings[].originalEntry` (já no schema, hoje
  descartado). Preenchido no laço que monta `readingsByWork`.
- **crédito da foto** vem de `author.photo.{author,license,sourceUrl}` (já no
  schema). `file` segue igual.
- **`bioSource`** sai do mesmo `summary` aprovado que origina a bio: o `label`
  é `summary.source` (ex.: "Wikipédia (pt)") e a `url` é `summary.sourceUrl`.
  Para carregar isso, o laço de summaries passa a guardar, além do texto, a
  fonte por slug de autoria. `approvedSummaryByScope` **não muda** (R13.5).

Nenhum agregado muda (R13.4). Os fixtures de tens de teste ganham os três
campos com valores neutros (`originalEntry: "e{n}"`, `author/license/sourceUrl:
null`), o que mantém verdes as expectativas atuais.

## Camada de seleção

### `src/lib/work-page.ts`

```ts
export type WorkPage = {
  work: WorkView;                 // para Cover/selo/título
  original: OriginalTitle | null; // { text, lang?, dir, font? } — R2.4/2.5
  authors: { author: AuthorView; href: string }[];
  facts: Fact[];                  // ficha (R3), linhas vazias já removidas
  readings: ReadingLine[];        // R4
  readingsHeading: string;        // "Lido uma vez" | "Lido N vezes"
  themes: ThemeChip[] | null;     // R5
  edition: EditionBox | null;     // R6
  catalogerNote: string | null;   // R7.1
  notebook: NotebookEntry[];      // R7.2 (uma por leitura)
};
```

Regras aplicadas aqui:

- **Título original** (R2.4–2.6): só quando `originalTitle` existe e difere do
  pt-BR por `fold()` (sem caixa/acento). `lang` por `originalTitleLang`, `dir`
  por `scriptDir(detectScript())`, fonte Noto por script (mesma lógica de
  `CoverCaption`, extraída para `originalTitlePresentation(work)` em `text.ts`
  para não duplicar). `romanized` numa linha à parte, sem `lang`.
- **Ficha** (R3): na ordem Idioma, País, Primeira publicação, Tipo, Gêneros.
  Cada `Fact` carrega `kind: "text" | "links"`. País usa `work.countries`
  (ISO-2) resolvido para nome via vocabulário; some se vazio. Tipo/gêneros com
  `capitalizeFirst`.
- **Leituras** (R4): ordenadas por `sequence`. A **primeira da ordem** é
  "primeira leitura"; as demais, "releitura" (pela posição, não por `reread`).
  `year` → link `/ano/{ano}`; sem ano → "Entre os primeiros da lista" →
  `/ano/sem-data`. Sempre "nº {sequence} da lista". `readingsHeading` por
  contagem.
- **Temas** (R5): chips ordenados por `worksByTheme` do slug (desc), empate pela
  ordem do caderno. A contagem só aparece quando o slug tem `≥ CLOUD_MIN_WORKS`
  (5) obras — reaproveita a constante do Atlas. `null` se a obra não tem tema.
- **Edição** (R6): monta linhas Editora/Ano/ISBN presentes; `null` se nenhuma.
  Rótulo: `exact` → "Edição lida"; `representative` → "Edição brasileira de
  referência" quando `edition.language === "português"`, senão "Edição de
  referência". ISBN = `isbn13` como está (13 dígitos, sem hífen).
- **Registro** (R7): `catalogerNote` como está; `notebook` com uma entrada por
  leitura (`originalEntry` + identificação "em {ano}" ou "nº {N} da lista"). Sem
  sinal para `confidence` (R7.4: a página simplesmente nunca lê esse campo).

### `src/lib/author-page.ts`

```ts
export type AuthorPage = {
  author: AuthorView;
  portrait: { ring: true; language: string }; // foto derivada na página
  credit: PhotoCredit | null;                  // R8.2
  context: ContextLine;                        // país + idiomas, com links
  numbers: BigNumber[];                        // R9 (livros, [posição], [1ª])
  bio: { text: string; source: BioSource | null } | null; // R10
  works: GridWork[];                           // R11 (ordem do caderno)
  captionFor: (slug: string) => string;        // R11.3 legenda por obra
  themes: ThemeChip[] | null;                  // R12
};
```

Regras aplicadas aqui:

- **Contexto** (R8.4): "{País} · escreve em {idiomas}". País → `countryHref`;
  cada idioma → `languageHref`. Sem país, "Escreve em {idiomas}". A cor de
  idioma, se usada como texto, passa por `onGround(cor, 4.5)` (R8.5) — na
  prática os links usam a cor padrão de link; a cor de idioma fica no anel do
  retrato.
- **Números e posição** (R9): `livros lidos` = `author.works.length` com
  plural. `authorRank`: ordena por `readingsByAuthor` desc; `position = 1 +
  (nº de autorias com contagem estritamente maior)`; `tied` = existe outra
  autoria com a mesma contagem. Só entra em `numbers` se `position ≤ 10`
  ("{N}º", rótulo "posição na estante" / "…(empatada)"). Senão, entra a
  "primeira leitura" (menor ano datado), omitida se não houver ano. `BigNumbers`
  decide colunas pelo número de itens (1–3) — já suportado.
- **Bio** (R10): `author.bio` + `author.bioSource`. Sem bio, `null` → a seção
  some. A fonte vira "Fonte: {label}" com link se `url` existir.
- **Na estante** (R11): `author.works` em ordem do caderno (`firstSequence`),
  `toGridWork` para cada. `captionFor(slug)` monta "lido em {ano}" juntando
  as leituras ("lido em 2022 e 2025"; "nº {N} da lista" para sem data). Grade
  **não** ordenável (sem script).
- **Temas** (R12): conta obras da autoria por slug de tema; mantém só `≥ 2`;
  top 10 por contagem desc, empate por nome; `null` se nenhum atinge 2 (caso
  das 156 autorias com um livro). Rótulo = variante mais frequente; link
  `themeHref`.

### `src/lib/route-integrity.ts` (ou um teste dedicado)

Função `allWorkAndAuthorLinks(catalog)` que coleta os `href` emitidos por
`buildHome`, `buildTimeline`+anos, `buildAtlas*`, `buildLanguage/Country/
ThemePages` e o índice de busca, filtra `/obra/` e `/autoria/`, e um teste
compara o conjunto com `worksBySlug`/`authorsBySlug`. Falha no `node --test` se
algum link apontar para slug inexistente (R14.2).

## Componentes

### Novos

- **`BackLink.astro`** — `<a class="back" href="/">‹ Estante</a>`, alvo ≥ 44 px
  (R1.4). Estilo movido de `BrowseHeader`.
- **`WorkHeader.astro`** — topo da Obra: `Shelf` + `Cover size="hero"` (selo 2×)
  à esquerda, `h1` (título pt-BR, Bodoni itálico) + título original/romanizado +
  `AuthorChip layout="row"` à direita. Empilha no celular, lado a lado ≥ 760 px.
- **`AuthorHeader.astro`** — topo da Autoria: retrato circular 132 px (foto 1:1
  derivada ou `InitialsAvatar ring`), crédito discreto, `h1` (nome), linha de
  contexto, `BigNumbers`.
- **`DescriptionList.astro`** — `<dl>` de pares; pula item sem valor. Aceita
  `value` como string ou `Astro.slots` indexado; para linhas com links a página
  passa um array `{ text, href }`.
- **`FactLinks.astro`** (pequeno) — renderiza uma lista de links separados por
  "·" dentro de um valor da ficha (País, se vários).

### Alterados (mudança aditiva, HTML inalterado onde não usada)

- **`CoverCaption.astro`** — novo `<slot name="caption" />` após `.author`;
  `WorkGrid` injeta a legenda. Sem o slot, markup idêntico (diff contra `main`).
- **`WorkGrid.astro`** — prop `captionFor?: (slug: string) => string | null`;
  quando presente, passa a legenda ao `CoverCaption` via slot. `sortable`
  continua opcional e independente.
- **`model.ts`** — os três campos de R13 (ver acima).
- **`text.ts`** — extrai `originalTitlePresentation(language, title, original)`
  → `{ lang?, dir, font? }`, reutilizado por `CoverCaption` e pela Obra (sem
  mudar a saída atual).

## Páginas `.astro`

### `src/pages/obra/[slug].astro`

```ts
export function getStaticPaths() {
  const catalog = getCatalog();
  return catalog.works.map((w) => ({
    params: { slug: w.slug },
    props: { page: buildWorkPage(catalog, w.slug) },
  }));
}
```

Estrutura: `Base` (title = `{título} · A estante da Lila`) › `BackLink` ›
`WorkHeader` › `main`: ficha (`DescriptionList`) · Leituras · Temas (chips) ·
Edição (caixa) · "Nota do catalogador" · "Como estava no caderno"
(`<blockquote>` por leitura). Larguras e `--gutter` como nas telas S4.

### `src/pages/autoria/[slug].astro`

```ts
export function getStaticPaths() {
  const catalog = getCatalog();
  return catalog.authors.map((a) => ({
    params: { slug: a.slug },
    props: { page: buildAuthorPage(catalog, a.slug) },
  }));
}
```

Estrutura: `Base` › `BackLink` › `AuthorHeader` (retrato + crédito + contexto +
`BigNumbers`) › `main`: "Sobre" (bio + fonte) · "Na estante da Lila"
(`WorkGrid` com `captionFor`) · "Temas que mais aparecem" (chips). Blocos `null`
não renderizam.

## Layout e estilo

- **Mobile-first**, `--gutter` do handoff §3.4; conteúdo centralizado em
  `max-width: 960px` ≥ 760 px, como nas telas "ver todos".
- **WorkHeader**: capa `size="hero"` (`--cover-hero-w`), não estica. Empilhada
  no celular; grid 2 colunas (capa auto / texto 1fr) ≥ 760 px.
- **AuthorHeader**: retrato centralizado no celular; retrato à esquerda e texto
  à direita ≥ 760 px (mesma linguagem do Idioma).
- **Ficha / edição / registro**: tipografia de texto corrente (Manrope),
  rótulos em `--font-ui` caixa alta `--faint`, filetes `--line` entre blocos. A
  nota do catalogador e o caderno vêm por último, menores e em `--muted`
  (R7.5).
- **Chips de tema**: pílula 44 px (handoff §4), reusando o padrão de chip já no
  app (não o estado ativo `--accent`).
- **Grades**: `repeat(3, minmax(0, 1fr))` no celular; desktop herda o
  comportamento do `WorkGrid` (colunas `--cover-hero-w`).

## Acessibilidade (R15)

- `h1` única por página; seções em `h2`. Sem pular nível.
- Capa: `alt="Capa de {título}"`; retrato: `alt="{nome}"`; prateleira, anel e
  selo decorativos (`aria-hidden`/`alt=""`).
- Links reais (`<a href>`), foco visível (herdado do global), toque ≥ 44 px.
- Título original com `lang`/`dir` corretos; romanização sem `lang` de idioma
  não latino.
- Texto sobre fundo escuro ≥ 4,5:1; `onGround` onde a cor do idioma for texto.

## Testes

- **`work-page.test.ts`**: título original (presente/igual/ausente/romanizado/
  RTL), ficha com e sem país/gêneros/ano, heading por nº de leituras, releitura
  por posição e não por `reread`, leitura sem ano, contagem de tema só a partir
  de 5, rótulo de edição por `match`/idioma, edição vazia some, nota e caderno
  por leitura.
- **`author-page.test.ts`**: posição (top 10, empate "tied", fora do top some),
  números com/sem primeira leitura, plural de "livro(s)", bio com/sem fonte e
  sem bio, legenda da grade (um ano, dois anos, sem data), temas ≥ 2 e top 10,
  autoria de um livro só (sem bloco de temas), contexto com/sem país, crédito
  com/sem foto.
- **`route-integrity.test.ts`**: todo link `/obra/…` e `/autoria/…` existe.
- **`model.test.ts`** (extensão): `originalEntry`, crédito da foto e `bioSource`
  preenchidos a partir do cru; aprovação inalterada.
- **Diff de HTML** de Idioma/País/Tema contra a `main` (baseline em `temp/`,
  normalizando `data-astro-cid-*`): `CoverCaption`/`WorkGrid` sem `captionFor`
  não mudam.
- **Build real**: `npm run check` limpo e build do catálogo em código 0, com as
  517 páginas novas (563 → 1080).

## Fora do escopo (confirmando)

PWA/offline (S6); "Compartilhar"/retrospectiva (S7), sem botão nem stub; capas
reais, resumos, normalização de temas (F2); páginas de gênero/tipo; hifenização
de ISBN; `404.astro`; modo de revisão `medium`; "outras obras" na Obra.

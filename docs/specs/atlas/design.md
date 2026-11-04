# Design — Atlas (S4)

## Visão geral

A S4 cria cinco rotas — **Atlas por idioma** (`/atlas`), **Atlas por país**
(`/atlas/pais`), **Idioma** (`/idioma/{slug}`), **País** (`/pais/{slug}`) e
**Tema** (`/tema/{slug}`) — e fecha os 404 de `/atlas` e `/tema/{slug}` que a
S2 deixou. Como na S2 e na S3, o trabalho é sobretudo **composição** de peças
existentes (`YearBand`, `Spine`, `Shelf`, `CoverCaption`, `AuthorChip`,
`InitialsAvatar`) mais uma **camada de seleção** nova, `atlas.ts`, que concentra
toda a regra.

Três princípios, herdados:

- **Páginas burras, regra em `src/lib`.** Cada `.astro` chama `getCatalog()`,
  pede o recorte pronto a `atlas.ts` e só posiciona componentes.
- **Zero JS para ler.** O único JavaScript novo é a ilha de ordenação da grade
  (Idioma e Tema). O Atlas e a página País são estáticos puros.
- **Links no formato final, 404 temporário aceito** para `/obra/{slug}` e
  `/autoria/{slug}` (S5).

Esta spec aplica uma regra que a S3 deixou escrita: *"extrai-se um componente
quando houver o segundo uso"*. Big numbers e o carrossel de avatares agora têm
segundo uso, então são extraídos (§5), com verificação de que Início e Ano não
mudam.

> **Dependências:** a S4 **não adiciona nenhuma** (Astro 7.4.0, Zod 4.6.7, sharp
> 0.35.5, TypeScript 6.0.3, Node 22). A camada de dados da S1 **fica
> inalterada** (R11.6): tudo o que a S4 precisa já existe em `WorkView`,
> `AuthorView`, `aggregates` e `approvedSummaryByScope`.

### Mapa de requisitos → seção

| Requisito | Onde é atendido |
|---|---|
| R1 Atlas e alternador | §2, §4 (`AtlasToggle`), §6.1 |
| R2 Atlas · por idioma | §3.1, §5 (`YearBand`), §6.1 |
| R3 Atlas · por país | §3.2, §5 (`YearBand`), §6.2 |
| R4 Quem ela mais lê | §3.3, §5 (`AuthorChip` row), §6.1 |
| R5 Temas que voltam | §3.4, §5 (`AtlasInsights`) |
| R6 Quando foram escritos | §3.5, §5 (`AtlasInsights`) |
| R7 Idioma | §3.6, §6.3 |
| R8 País | §3.7, §6.4 |
| R9 Tema | §3.8, §6.5 |
| R10 Ordenação da grade | §7 |
| R11 Camada de seleção | §3 |
| R12 Estados, a11y, entrega | §8, §9 |

## 1. Arquivos que a S4 cria ou toca

```text
app/
  src/
    lib/
      atlas.ts              NOVO  toda a regra da S4 (seleção, slugs, páginas)
      atlas.test.ts         NOVO  testes
      grid-sort.ts          NOVO  comparador da ordenação (build + cliente)
      grid-sort.test.ts     NOVO  testes
      text.ts               MEXE  + languageTag(), arabic em detectScript/scriptDir
      text.test.ts          MEXE  casos novos
      language-color.ts     MEXE  + contrastRatio(), onGround()
      language-color.test.ts MEXE casos novos
    components/
      AtlasToggle.astro     NOVO  alternador Idioma | País (dois links)
      AtlasInsights.astro   NOVO  os 3 blocos: autorias, nuvem de temas, épocas
      BigNumbers.astro      NOVO  extraído da tela Ano (2º uso)
      AuthorRail.astro      NOVO  extraído do Início (2º uso)
      BrowseHeader.astro    NOVO  cabeçalho de Idioma (colorido) e Tema (escuro)
      WorkGrid.astro        NOVO  grade 3 col. + controles + ilha de ordenação
      YearBand.astro        MEXE  + prop shelfPerRow; href opcional (§5)
      AuthorChip.astro      MEXE  + layout="row" e meta
      CoverCaption.astro    MEXE  + showOriginal
      TypographicCover.astro MEXE usa languageTag()/detectScript (sem regra própria)
    pages/
      atlas/index.astro     NOVO  /atlas
      atlas/pais.astro      NOVO  /atlas/pais
      idioma/[slug].astro   NOVO  /idioma/{slug}
      pais/[slug].astro     NOVO  /pais/{slug}
      tema/[slug].astro     NOVO  /tema/{slug}
      index.astro           MEXE  usa <AuthorRail> (sem mudar o HTML gerado)
      ano/[year].astro      MEXE  usa <BigNumbers> (sem mudar o HTML gerado)
```

`lib/catalog/`, `home.ts`, `timeline.ts` e `search.ts` **não mudam**. `atlas.ts`
importa `slugifyTheme`/`themeHref` de `home.ts` (R11.4) e `fold` de `search.ts`.

### Rotas e geração estática

- `atlas/index.astro` → `/atlas`; `atlas/pais.astro` → `/atlas/pais`. O host
  estático ignora a query, então `/atlas?por=pais` serve a vista de idioma
  (R1.5). Nenhum script de redirecionamento.
- `idioma/[slug]`, `pais/[slug]`, `tema/[slug]`: `getStaticPaths()` chama
  `buildLanguagePages(catalog)` / `buildCountryPages(catalog)` /
  `buildThemePages(catalog)` e devolve `{ params: { slug }, props: { page } }`.
  A página não recalcula nada: usa `Astro.props.page`.
- **Colisão de slug.** Os builders de idioma e país **lançam erro** se dois
  nomes dão o mesmo slug (R8.1, R11.5). Hoje não há colisão (15 idiomas, 36
  países). Os temas **não lançam**: variantes que diferem só por caixa ou
  acento são agrupadas (§3.8).
- Formato de build `directory` (padrão do Astro, o mesmo de `/linha-do-tempo`):
  `dist/atlas/index.html`, `dist/atlas/pais/index.html`, etc.
- Contagem esperada de páginas novas: 2 + 15 + 36 + 493 = **546**.

## 2. Navegação

```text
Início ──[chip Atlas]──► /atlas  ◄──toggle──►  /atlas/pais
                           │                       │
                  faixa de idioma             faixa de país / chip "Outros"
                           ▼                       ▼
                  /idioma/{slug}              /pais/{slug}
                           │                       │
                    voltar → /atlas        voltar → /atlas/pais
Início/Atlas (nuvem) ──► /tema/{slug}  ── voltar → /atlas
Idioma/País/Tema ──► /obra/{slug} (S5)      Atlas/País/Idioma ──► /autoria/{slug} (S5)
```

- `NavChips active="atlas"` nas duas vistas do Atlas (o chip "Atlas" vira
  `aria-current`, sem link, como já faz). O alternador é um segundo controle,
  logo abaixo do título.
- Idioma, País e Tema não mostram `NavChips`; têm só o link "‹ Atlas" no topo.

## 3. Camada de seleção — `atlas.ts`

Módulo puro (sem Astro), testável sob `node --test`, com imports relativos.
Recebe o `Catalog` e devolve estruturas prontas; recortes sem conteúdo voltam
`null` (R11.3).

### 3.0 Tipos e peças comuns

```ts
import type { AuthorPick } from "./home.ts";          // { author, readings, href }
import type { WorkView, AuthorView } from "./catalog/model.ts";

/** Faixa pronta para o <YearBand>. */
export type BandData = {
  label: string;
  /** Ausente = faixa sem link (bloco "Outros países"). */
  href?: string;
  count: number;
  spines: { language: string }[];
};

/** Dados de ordenação embutidos em cada peça da grade (§7). */
export type SortData = { seq: number; title: string; author: string; year: number | null };

/** Uma peça da grade de obras (uma por OBRA). */
export type GridWork = { work: WorkView; href: string; sort: SortData };
```

Regras comuns:

- **Ordem do caderno de uma obra** = `sequence` da sua primeira leitura
  (`work.readings[0].sequence`, já ordenadas no modelo). Obra sem leitura (não
  ocorre no catálogo validado) cai no fim, com desempate por slug.
- `slugify` = o `slugifyTheme` de `home.ts` (sem acento, minúsculas, hífens).
  Os helpers `languageHref`, `countryHref` e `themeHref` (este reaproveitado de
  `home.ts`) são **as únicas fontes** dessas rotas (R11.4).
- `capitalizeFirst("segunda guerra")` → `"Segunda guerra"`; só exibição, não
  altera o dado. Idiomas ("português" → "Português") e temas usam isso.
- Índices internos **memoizados por `Catalog`** (`WeakMap`), porque várias
  funções precisam das mesmas obras agrupadas:
  - `countryIndex`: `Map<code, { code, name, works, languageCounts, dominant }>`.
    O **nome** vem de `AuthorView.countryName` (o `Catalog` não tem a lista de
    países). `dominant` = idioma com mais obras no país; empate pelo nome do
    idioma (pt-BR).
  - `themeIndex`: `Map<slug, { slug, label, works }>` (§3.8).

### 3.1 Atlas · por idioma (R2)

`buildAtlasByLanguage(catalog): BandData[]`

- Fonte: `aggregates.worksByLanguageDesc` (quantidade desc; o empate já é
  estável por nome em pt-BR).
- Por idioma: obras com `work.language === key`, ordenadas pelo caderno →
  `spines` (uma por **obra**, `{ language }`); `count` = nº de obras;
  `label` = `capitalizeFirst(language)`; `href` = `/idioma/{slug}`.
- Todos os idiomas aparecem (15), sem agrupar (R2.5); idiomas sem cor própria
  usam o fallback "outros" que `Spine` já aplica.

### 3.2 Atlas · por país (R3)

`buildAtlasByCountry(catalog): { bands: BandData[]; others: OthersBlock | null }`

```ts
type OthersBlock = {
  band: BandData;                                   // sem href
  countries: { name: string; href: string; count: number }[];
};
export const COUNTRY_BANDS = 10;
```

- Fonte: `aggregates.worksByCountryDesc`. Desempate por **nome do país**
  (pt-BR) no lugar do código, para builds reproduzíveis e coerentes com R3.1
  (o agregado desempata pelo código; `atlas.ts` reordena com o nome).
- País = país das autorias, e uma obra conta em cada país (R3.2) — o
  `WorkView.countries` já entrega isso sem repetição.
- Cada faixa: `label` = nome do país; `count` = nº de obras; `spines` = uma por
  obra, **cada uma com o idioma original da obra** (as cores variam na faixa),
  ordem do caderno; `href` = `/pais/{slug}`.
- **Corte:** as `COUNTRY_BANDS` (10) primeiras viram faixas. O resto vira
  `others`, **exceto** quando sobraria **um** país só: ele vira a 11ª faixa e
  `others` é `null` (R3.7). Com ≤ 10 países, `others` é `null` (R3.8).
- **Outros países:** `band` = `{ label: "Outros países", count, spines }` onde
  `spines` e `count` são calculados sobre as obras **distintas** da união dos
  países agrupados (R3.6); `countries` = um chip por país (nome, `/pais/{slug}`,
  contagem), em quantidade desc.
- Obras sem país não entram em nenhuma faixa nem em `others` (R3.9): saem
  naturalmente, pois `work.countries` é vazio.

### 3.3 Quem ela mais lê (R4)

`topAuthors(catalog, limit = TOP_AUTHORS /*10*/): AuthorPick[] | null`

- Fonte: `aggregates.readingsByAuthor`. Ordena por leituras desc e, no empate,
  pelo **nome** (pt-BR) — o agregado desempata por slug, então `atlas.ts`
  reordena (R4.2). Corta em 10. Cada item: `{ author, readings, href:
  /autoria/{slug} }`, o mesmo tipo `AuthorPick` do Início.
- `null` se não há nenhuma autoria. Menos de 10 → lista menor (R4.5).
- O texto "N leituras"/"1 leitura" é montado por `readingsLabel(n)` em
  `atlas.ts` (singular/plural, R4.4).

### 3.4 Temas que voltam (R5)

`themeCloud(catalog): ThemeCloudItem[] | null`

```ts
export const CLOUD_LIMIT = 30;
export const CLOUD_MIN_WORKS = 5;
type ThemeCloudItem = { label: string; href: string; count: number; tier: 1 | 2 | 3 | 4 };
```

- Fonte: `themeIndex` (temas **agrupados por slug**, contados por obra distinta).
  Filtra `count >= CLOUD_MIN_WORKS` (hoje 52 temas), ordena por contagem desc
  e fica com os `CLOUD_LIMIT` (30) primeiros.
- **Degrau (`tier`)** pela razão `count / maior`: `≥ 0,60` → 4; `≥ 0,30` → 3;
  `≥ 0,15` → 2; senão 1 (R5.2). Com os dados atuais (máx. 62) os quatro
  degraus aparecem.
- **Ordem de exibição**: alfabética por rótulo (pt-BR), determinística (R5.5).
  O tamanho carrega a frequência; a ordem não.
- `null` se nenhum tema atinge o piso (R5.6).

### 3.5 Quando foram escritos (R6)

`eras(catalog): EraBar[] | null`

```ts
type EraBar = { id: string; label: string; count: number; pct: number };
```

- Épocas fixas, por `firstPublished` da obra: `< 1800` ("antes de 1800", só se
  `count > 0`), `1800–1899` ("séc. XIX"), `1900–1999` ("séc. XX"),
  `2000–2009` ("2000s"), `2010–2019` ("2010s"), `>= 2020` ("2020s"). Cronológico.
- Contagem **por obra**; obra sem `firstPublished` é ignorada, sem aviso (R6.4).
- `pct` = `count / maior * 100` (largura da barra); épocas vazias mantêm
  `count: 0` e `pct: 0` (R6.5), exceto "antes de 1800" (R6.2).
- `null` se nenhuma obra tem ano.
- O limite superior aberto de "2020s" evita perder obras futuras sem criar
  época nova a cada década; quando 2030 chegar, é uma decisão consciente.

### 3.6 Idioma (R7)

`buildLanguagePages(catalog): LanguagePage[]` (uma por idioma com obra; lança em
colisão de slug).

```ts
type LanguagePage = {
  slug: string;
  name: string;            // "Português"
  language: string;        // chave do catálogo ("português"), para a cor e o lang
  color: { bg: string; ink: string };
  numbers: { value: string; label: string }[];   // obras · % da estante · autorias
  authors: AuthorPick[] | null;                   // carrossel de avatares
  items: GridWork[];                              // uma por obra, ordem do caderno
};
```

- `numbers`: **obras** (`items.length`), **% da estante** = `round(obras /
  total * 100)`, mostrado como `"38%"`; resultado `0` com obras > 0 vira
  `"<1%"` (R7.3); **autorias** = autorias distintas das obras do idioma. Rótulos
  com singular/plural ("obra"/"obras", "autoria"/"autorias").
- `authors`: autorias das obras do idioma, ordenadas pelo nº de obras delas
  **naquele idioma** (desc; empate por nome), cortadas em `DEFAULT_RAIL_CAP`
  (20, de `home.ts`). `null` quando há 0 ou 1 autoria (R7.4). O `AuthorPick`
  usa `readings` = obras da autoria no idioma (não exibido).
- `items`: uma peça por **obra** (releitura = uma capa com selo "2×", via
  `WorkView.reread`), na ordem do caderno, com `sort` calculado no build (§7).

### 3.7 País (R8)

`buildCountryPages(catalog): CountryPage[]` (uma por país com obra; lança em
colisão de slug).

```ts
type CountryPage = {
  slug: string;
  name: string;
  dominantLanguage: string;
  nameColor: string;                // cor legível sobre --ground (§4.3)
  swatch: string;                   // cor exata do idioma (filete)
  sharing: { name: string; href: string }[] | null;   // chips
  summary: string | null;           // pais:{código} aprovado
  numbers: { value: string; label: string }[];        // obras · autorias
  topAuthor: AuthorPick | null;     // destaque
  items: GridWork[];
};
```

- `sharing`: demais países de `countryIndex` com o **mesmo `dominant`**, em
  quantidade desc (empate por nome); `null` se não há nenhum (R8.4). Países com
  vários idiomas na grade (ex.: Canadá) ficam pelo idioma dominante nas obras,
  que é o critério declarado nos requisitos.
- `summary` = `approvedSummaryByScope.get("pais:" + code) ?? null`. O código só
  é usado aqui; não vai à tela (R8.9).
- `numbers`: obras do país · autorias com `country === code`.
- `topAuthor`: entre as autorias do país, a de **maior** `readingsByAuthor`.
  Só vale se **exatamente uma** tem o máximo **e** o máximo ≥ 2 (R8.7); senão
  `null`. Candidatas a destaque: Elena Ferrante (8 leituras, Itália) e José
  Saramago (6, Portugal); países em que o topo empata ou é 1 omitem o destaque.
  Os casos de borda ficam cobertos por teste.
- `items`: obras com `work.countries.includes(code)`, ordem do caderno.
  Uma obra de duas autorias de países distintos aparece nas duas páginas (R8.8).

### 3.8 Tema (R9) e agrupamento por slug

`buildThemePages(catalog): ThemePage[]`

```ts
type ThemePage = {
  slug: string;
  name: string;                     // capitalizeFirst do rótulo
  numbers: { value: string; label: string }[];   // obras · autorias · idiomas
  items: GridWork[];
};
```

- `themeIndex` percorre `catalog.works` e, para cada tema `t` de cada obra,
  agrupa em `slugifyTheme(t)`. Guarda o conjunto de obras (sem duplicar a obra
  que traga as duas variantes) e a contagem de obras por variante.
- **Rótulo**: a variante com mais obras; empate → a que já está em minúsculas;
  persistindo, ordem pt-BR (R5.3). Casos reais: "Segunda Guerra Mundial" (2) e
  "segunda guerra mundial" (5) → rótulo `segunda guerra mundial`, 7 obras
  distintas (verificado no catálogo); "Nordeste"/"nordeste" e "Guerra
  Fria"/"guerra fria" seguem a mesma regra.
- `numbers`: obras · autorias distintas · idiomas originais distintos (R9.3).
  `name` = `capitalizeFirst(rótulo)` (R9.7).
- Um tema com uma obra gera página normal (R9.6).
- **Consistência com o Início:** os carrosséis de tema da S2 usam
  `aggregates.worksByThemeDesc` (sem agrupar). Os quatro primeiros temas não
  são afetados pelos três pares duplicados, então os links batem; o `href` sai
  do mesmo `themeHref`.

## 4. Peças de apoio fora do Atlas

### 4.1 `text.ts`: idioma → `lang`, árabe

- `languageTag(language: string): string | undefined` — mapa fixo: português
  `pt`, inglês `en`, espanhol `es`, francês `fr`, italiano `it`, russo `ru`,
  japonês `ja`, alemão `de`, hebraico `he`, coreano `ko`, norueguês `no`,
  catalão `ca`, tcheco `cs`, árabe `ar`, holandês `nl`. Desconhecido →
  `undefined` (sem atributo `lang`, nunca um valor inventado).
- `detectScript` ganha `"arabic"` (`\u0600–\u06FF`); `scriptDir("arabic")` =
  `"rtl"` (R7.5 pede `dir="rtl"` para hebraico e árabe).
- O título original numa grade usa `lang = languageTag(work.language)`. Os
  alfabetos com Noto (CJK, hebraico) escolhem a fonte pelo **script**, como a
  capa tipográfica faz hoje.
- `TypographicCover` passa a usar esses dois helpers em vez do `originalLang`
  próprio. Efeito colateral aceito: a capa de uma obra em árabe ganha
  `lang="ar" dir="rtl"`, e títulos originais em alfabeto latino ganham `lang`.
  Os demais atributos não mudam.

### 4.2 `AuthorChip`, `CoverCaption`

- `AuthorChip` ganha `layout?: "stack" | "row"` (padrão `stack`, sem mudar o
  Início) e `meta?: string`. Em `row`: avatar à esquerda, nome e `meta` ("8
  leituras") em coluna à direita, linha inteira com alvo ≥ 44 px. Usa a mesma
  derivação de foto.
- `CoverCaption` ganha `showOriginal?: boolean` (padrão `false`). Ligado, abaixo
  do título pt-BR (e acima/abaixo da autoria, a decidir na implementação por
  leitura visual) aparece o título original em itálico, com `lang` (§4.1), `dir`
  e a fonte Noto do script, em até 2 linhas. Some se não houver título original
  ou se for igual ao pt-BR (R7.5).

### 4.3 Cor legível do nome do país (R8.3)

Medido contra `--ground` (#0E1714): só português (7,1), japonês (13,8) e coreano
(9,2) passam 4,5:1; italiano 3,6, hebraico 3,9, espanhol 3,0, francês 2,8,
inglês 2,8, alemão 2,6, "outros" 2,6, russo 1,9. Usar a cor pura falharia para a
maioria dos países (inclusive os maiores: Estados Unidos, França, Reino Unido).

Decisão: `language-color.ts` ganha duas funções puras e testadas:

- `contrastRatio(hexA, hexB): number` (fórmula WCAG).
- `onGround(hex, min = 4.5): string` — clareia a cor misturando-a com
  `--title` (#F4EBD8) em passos de 5% até atingir `min` contra `--ground`;
  devolve a própria cor se já passa.

O **nome do país** usa `onGround(bg)` (mesma matiz, mais clara) e, para manter a
identidade exata do idioma, um **filete de 4 px na cor pura** do idioma sob o
nome. O texto passa o contraste; a cor de marca continua visível. A mesma
técnica se aplica a qualquer texto futuro na cor do idioma sobre fundo escuro.

> Os requisitos 8.3 já preveem "variante/alternativa quando a cor do idioma não
> passar"; este é o desenho dessa alternativa.

## 5. Componentes

### 5.1 `YearBand` (mexe, retrocompatível)

Dois acréscimos opcionais, sem alterar o uso da Linha do tempo:

- **`href?`** — sem `href`, a raiz é um `<div>` em vez de `<a>` e a contagem
  aparece como `N` (sem "›"). Serve à faixa "Outros países" (R3.10).
- **`shelfPerRow?: boolean`** (padrão `false`) — o problema: o Atlas tem faixas
  com muitas lombadas (português 115, Brasil 95). Em 390 px cabem ~46 lombadas
  por linha, então essas faixas quebrariam em 2–3 linhas e a única prateleira
  ficaria só sob a última, deixando as de cima no ar. Com `shelfPerRow`, o
  contêiner das lombadas vira uma grade de células de altura fixa
  (`grid-template-columns: repeat(auto-fill, 4px)`, `column-gap: 3px`,
  `grid-auto-rows` = 48 px + `--shelf-height`), cada lombada apoiada no fundo da
  célula, e uma `repeating-linear-gradient` com `--wood-top → --wood-bottom`
  desenha **uma prateleira por linha**. O `<Shelf/>` separado não é renderizado
  nesse modo. Sem `shelfPerRow`, o markup e o CSS atuais ficam como estão
  (R2.6, risco de regressão da S3 = zero).
- Fallback se o resultado visual não convencer no preview: manter a quebra com
  uma prateleira só. O contrato do componente não muda.

### 5.2 `AtlasToggle`

Dois `<a>` dentro de `<nav aria-label="Ver o Atlas por">`: "Idioma original" →
`/atlas`, "País" → `/atlas/pais`. A vista atual é `aria-current="page"` e usa o
estilo de chip ativo (`--accent` / `--accent-ink`), e é um `<a>` também (o
destino é a própria página), o que mantém a estrutura igual nas duas vistas.
Alvos de 44 px, pílula de 22 px de raio (handoff §3.4). Prop: `active:
"idioma" | "pais"`.

### 5.3 `AtlasInsights`

Recebe `{ authors, cloud, eras }` (cada um possivelmente `null`) e renderiza os
três blocos nesta ordem, omitindo os nulos (R4.5, R5.6, R6):

1. **Quem ela mais lê** — `<ol>` de `AuthorChip layout="row"` com `meta`
   "N leituras".
2. **Temas que voltam** — `<ul>` de links (`<a>`) em `inline-flex`,
   `min-height: 44px`; `tier` 1–2 em Manrope 600 (`--muted` / `--text`), `tier`
   3–4 em Bodoni itálico `--accent`; tamanhos 14 / 17 / 24 / 32 px. O tamanho
   varia **e** o `--accent` só reforça (R5.2).
3. **Quando foram escritos** — `<ul>` de linhas `[rótulo | barra | contagem]`.
   A barra é decorativa (`aria-hidden`, largura = `pct`); o rótulo e "N obras"
   são texto visível, então a informação existe sem a barra (R6.3, R6.7). Barras
   na cor `--bar-neutral`; a época com mais obras usa `--accent`.

Cada bloco usa `<section aria-labelledby>` com `<h2 class="t-section-title">`.

### 5.4 `BigNumbers` (extraído de Ano)

`{ items: { value: string | number; label: string }[] }`. A grade é
`repeat(items.length, 1fr)` até 3 itens, e `2` colunas no celular / `n` no
desktop quando são 4. Cores por custom properties com padrão nos tokens atuais:
`--bn-bg` (padrão `--ground`), `--bn-fg` (`--title`), `--bn-muted` (`--faint`),
`--bn-line` (`--line-soft`). O cabeçalho de Idioma sobrescreve as quatro com
`--lang-ink` e a cor do idioma.
`ano/[year].astro` passa a usar o componente; o HTML renderizado precisa ficar
**idêntico** ao atual (verificado por diff, §9).

### 5.5 `AuthorRail` (extraído de Início)

`{ title?: string }` + slot. Reúne o contêiner rolável, o `scroll-snap` e o
título `t-section-title` que hoje vivem em `index.astro`. Início e Idioma
usam o mesmo componente. Diff do HTML do Início antes/depois (§9).

### 5.6 `BrowseHeader` (Idioma e Tema)

Props: `kicker` ("Idioma original" / "Tema"), `title`, `back: { href, label }`,
`tone?: { bg: string; ink: string }`. Slot para `BigNumbers`.

- Com `tone` (Idioma): bloco com `background: tone.bg`, texto `tone.ink`. O
  `h1` em Bodoni itálico 500, `clamp(48px, 16vw, 78px)` (78 px no desktop,
  encolhe no celular para "norueguês"/"holandês" caberem), `line-height: .95`.
- Sem `tone` (Tema): fundo `--surface` com borda `--line`, texto `--title`.
- Um `<h1>` por página; o `kicker` é um `<p>` (`t-label`). O link de voltar
  fica dentro do cabeçalho, acima do kicker, com 44 px de alvo (R7.7).

### 5.7 `WorkGrid`

Props: `items: GridWork[]`, `sortable?: boolean`.

```html
<div class="sort" hidden role="group" aria-label="Ordenar por">
  <button aria-pressed="true"  data-sort="seq">Da lista</button>
  <button aria-pressed="false" data-sort="title">Título</button>
  <button aria-pressed="false" data-sort="author">Autoria</button>
  <button aria-pressed="false" data-sort="year">Ano de publicação</button>
</div>
<p class="visually-hidden" role="status" aria-live="polite"></p>
<ol class="grid-3">
  <li data-seq=".." data-title=".." data-author=".." data-year=".."> <CoverCaption showOriginal …/> </li>
</ol>
```

- Mesma grade de Ano: 3 colunas no celular; no desktop `auto-fill` de
  `--cover-hero-w` (136 px), sem esticar.
- Os controles ficam `hidden` no HTML. Só o script os revela (R10.1).
- `sortable={false}` (País) não renderiza controles, região viva nem script.
- Ano e Sem data seguem com as suas próprias grades (sem tocar na S3); a cópia
  de CSS que sobra é dívida conhecida (§11).

## 6. Composição das páginas

### 6.1 Atlas (`/atlas`)

```text
<Base title="Atlas · A estante da Lila">
  <header>  <NavChips active="atlas"/>  h1 "Atlas"  <AtlasToggle active="idioma"/>
  <main>
    {bands.map(b => <YearBand {...b} shelfPerRow/>)}        ← R2
    <AtlasInsights {authors} {cloud} {eras}/>                ← R4–R6
```

### 6.2 Atlas · por país (`/atlas/pais`)

Mesmo esqueleto com `AtlasToggle active="pais"`. Depois das faixas, se
`others` existir: `<YearBand {...others.band} shelfPerRow />` (sem `href`) e,
logo abaixo, a lista de chips de país (nome + contagem, ≥ 44 px) em um
`<ul>` dentro de `<nav aria-label="Outros países">`. Fecha com `AtlasInsights`.
O `<title>` da página: "Atlas por país · A estante da Lila".

### 6.3 Idioma (`/idioma/{slug}`)

```text
<BrowseHeader kicker="Idioma original" title={name} tone={color} back="/atlas">
  <BigNumbers items={numbers}/>
</BrowseHeader>
<main>
  {authors && <AuthorRail title="Autorias"> AuthorChip… </AuthorRail>}
  <WorkGrid items sortable/>
```

Sem texto descritivo (handoff §6.6). O título da seção do carrossel é
"Autorias" (o handoff não dá rótulo; pode ser ajustado na revisão visual).

### 6.4 País (`/pais/{slug}`)

```text
<header> back "‹ Atlas"
  {sharing && <nav aria-label="Países com o mesmo idioma"> chips… </nav>}
  <h1 style="color: nameColor"> {name} </h1> + filete 4px swatch
  {summary && <p class="t-body">…</p>}
  <BigNumbers items={numbers}/>
  {topAuthor && <section> <AuthorChip layout="row" meta="N leituras"/> </section>}
<main> <WorkGrid items sortable={false}/>
```

Nome em Bodoni 700; título da seção do destaque: "Quem ela mais lê aqui".

### 6.5 Tema (`/tema/{slug}`)

Igual a Idioma, sem `tone`, sem carrossel de autorias, `kicker="Tema"`, três big
numbers, `WorkGrid sortable`.

## 7. Ilha de ordenação (R10)

**`grid-sort.ts`** (puro, roda no build e no navegador):

```ts
export type SortKey = "seq" | "title" | "author" | "year";
export type SortData = { seq: number; title: string; author: string; year: number | null };
export function compareBy(key: SortKey): (a: SortData, b: SortData) => number;
export function toDataset(d: SortData): Record<string, string>;   // para os data-*
export function fromDataset(ds: DOMStringMap): SortData;
```

- `title` e `author` já chegam **dobrados** (`fold` de `search.ts`: sem acento,
  minúsculas), calculados no build; o cliente só compara strings, sem `fold`.
- Comparadores: `seq` (crescente); `title` (pt-BR, depois `seq`); `author`
  (pt-BR, depois `title`, depois `seq`); `year` (crescente, **sem ano ao fim**,
  depois `seq`). Todos terminam em `seq`, então a ordenação é total e estável.
- Autoria = nome da **primeira** autoria da obra.

**Script em `WorkGrid.astro`** (bundled pelo Astro, vanilla):

1. Se há `.sort[hidden]`, remove `hidden` (os controles só existem com JS).
2. A cada clique: lê os `data-*` de cada `<li>`, ordena com `compareBy`, e
   reanexa os `<li>` existentes na nova ordem (`append`, sem recriar nem
   buscar nada). Atualiza `aria-pressed` e escreve "Ordenado por título" na
   região `role="status"`.
3. Sem rede, sem persistência, sem framework (R10.5).

O foco permanece no botão clicado; as peças são movidas, não recriadas, então o
estado dos links é preservado (R10.4).

## 8. Estados incompletos e acessibilidade (R12)

| Caso | Comportamento |
|---|---|
| Obra sem título original | A linha do original some na grade |
| Obra sem país | Não aparece em `/atlas/pais` nem em `/pais/*`; aparece em Idioma, Tema e blocos |
| Obra sem `firstPublished` | Fora das barras de época; "ano" ordena por último |
| Sem resumo `pais:` aprovado | O bloco de frase não existe (hoje, nenhum país tem) |
| País sem idioma em comum com outros | A linha de chips some |
| Autoria sem foto | `InitialsAvatar` (S1) |
| Nenhum tema ≥ 5 obras / sem autorias / sem anos | O bloco correspondente some (`null`) |
| Idioma sem cor própria | Fallback "outros" (§3.2 do handoff) |

- Navegação sempre por `<a href>`; ações (`ordenar`) por `<button>` com
  `aria-pressed`. Um `<h1>` por página, `<h2>` nos blocos.
- Decorativos com `aria-hidden`: fileira de lombadas, barras de época. A
  informação equivalente está em texto visível.
- Texto sobre cor de idioma usa o par `ink` de §3.2 do handoff (cabeçalho de
  Idioma); texto de país/tema sobre `--ground` passa 4,5:1 (§4.3).
- Nada mostra dia/mês, estrelas, notas, "—" ou "não informado". Sem hotlink.

## 9. Fluxo de build e verificação

- **`npm run check`** limpo; **`npm test`**: `atlas.test.ts`, `grid-sort.test.ts`
  e casos novos em `text.test.ts` e `language-color.test.ts`, somando aos 69
  atuais.
- **Testes de `atlas.ts`** (fixture no molde de `timeline.test.ts`):
  idiomas por quantidade com desempate por nome; país com obra de duas autorias
  de países distintos contada nos dois; obra sem país fora das faixas; corte de
  10 + "outros" com obras **distintas**; um único país restante vira faixa;
  ≤ 10 países sem "outros"; `topAuthors` com desempate por nome; nuvem com piso,
  tiers e ordem alfabética; temas com variantes de caixa unificados (rótulo e
  contagem de obras sem duplicar); épocas incluindo bordas 1799/1800/1899/1900/
  2019/2020, "antes de 1800" condicional e obra sem ano; páginas de Idioma
  (`%`, `<1%`, autorias), País (idioma dominante, `sharing`, `topAuthor` com
  empate e com máximo 1, resumo aprovado/não aprovado) e Tema; colisão de slug de
  idioma/país lança.
- **Regressão das extrações** (build real, antes × depois, em `temp/`): diff do
  HTML de `dist/index.html`, `dist/ano/2024/index.html` e
  `dist/linha-do-tempo/index.html`. Esperado: idêntico, salvo os atributos
  `lang`/`dir` que a capa tipográfica ganha (§4.1).
- **Build do catálogo real** em código 0 com **546 páginas novas**; conferir
  contagens (302 obras, 15, 36, 493) e que `/atlas`, `/atlas/pais`, uma página
  de cada tipo e `/tema/segunda-guerra-mundial` respondem 200 no `astro preview`.
- **Preview do Pages (PR)**, desktop e celular: alternar Idioma ↔ País; faixas
  de 115 e 95 lombadas (prateleira por linha); chips de "Outros países";
  nuvem; barras; Idioma (cabeçalho colorido, "norueguês" cabendo); País
  (contraste do nome, chips de idioma, destaque); Tema; ordenação. Capturas
  headless a 390 px podem cortar o lado direito por artefato da ferramenta; a
  conferência de celular é no preview, num aparelho.
- Sem rede em build nem em teste; nada escreve em `catalog/`.

## 10. Decisões e alternativas

| Decisão | Alternativa descartada | Porquê |
|---|---|---|
| Duas rotas estáticas para o alternador | Query string + JS | A query não chega ao HTML estático; JS duplicaria o DOM e quebraria "sem JS" |
| Regra toda em `atlas.ts`, páginas burras | Cálculo no `.astro` | Convenção S1–S3; testável sob `node --test` |
| `YearBand` + `shelfPerRow` opcional | Quebrar linhas com uma prateleira só | Faixas de 95–115 lombadas ficariam com fileiras flutuando no celular; o modo é opt-in e não toca a S3 |
| `href` opcional no `YearBand` | Componente novo para "Outros países" | A faixa é a mesma; só perde o link |
| Cor do nome do país clareada + filete na cor pura | Cor pura do idioma | 8 de 11 cores não passam 4,5:1 sobre `--ground` |
| Temas agrupados por slug na camada de seleção | Corrigir o catálogo antes | Evita colisão de rota já; a correção na origem é tarefa de pipeline, separada |
| Todos os temas ganham página | Só os frequentes | Obra (S5) vai linkar qualquer tema; 493 páginas estáticas pequenas são baratas |
| Ordenação reordena `<li>` existentes, dados em `data-*` pré-dobrados | 4 grades no HTML, ou recriar peças | Menos HTML, sem perder links/foco, sem `fold` no cliente |
| Extrair `BigNumbers` e `AuthorRail` agora | Copiar CSS pela 2ª vez | Regra da S3 (extrai no segundo uso); regressão coberta por diff de HTML |
| Idioma dominante do país para os chips | Ampliar o modelo com idiomas por país | Sem tocar a camada de dados; critério já declarado nos requisitos |
| `languageTag()` por nome de idioma | Detectar `lang` só pelo script | O script não distingue idiomas de alfabeto latino; o idioma da obra é conhecido |
| Nuvem em ordem alfabética | Por frequência | O tamanho já comunica a frequência; a ordem estável ajuda a achar um tema |
| Sem texto descritivo no cabeçalho de Idioma | Frase gerada | Decisão do handoff §6.6 |

## 11. Riscos e limites conhecidos

- **404 temporários.** `/obra/{slug}` e `/autoria/{slug}` até a S5. No preview,
  tocar numa capa ou autoria leva a 404; é esperado.
- **Visual da prateleira por linha.** É a parte mais frágil da S4: precisa de
  conferência no aparelho. O fallback (quebra com prateleira única) não muda o
  contrato do componente.
- **Cabeçalho de Idioma colorido.** Texto sobre a cor do idioma usa o par
  `ink` do handoff. "Outros" (norueguês, catalão, tcheco, árabe, holandês)
  tem cabeçalho cinza-esverdeado `#4B5E55`: legível, mas sem identidade própria
  até esses idiomas ganharem cor.
- **Peso do Tema.** 493 páginas aumentam o tempo de build de forma modesta; as
  de uma obra são quase só cabeçalho e uma capa. Se o build ficar lento, o
  limite é restringir a `count >= 2` (163 páginas) e remover o link dos temas
  de uma obra, o que exigiria acordo com a S5.
- **Temas duplicados no catálogo.** O agrupamento por slug cobre a S4; a nuvem
  e as páginas ficam corretas, mas o Início (S2) ainda soma por variante, e o
  vocabulário deve ser normalizado no pipeline.
- **Grade com CSS duplicado.** Ano, Sem data e `WorkGrid` repetem ~10 linhas de
  CSS de grade. Unificar é uma refatoração futura, fora da S4.
- **Países com idioma dominante diferente do esperado.** Um país com poucas
  obras pode ter dominante inesperado (ex.: uma autoria escrevendo em outro
  idioma). O chip reflete as obras da estante, não o idioma oficial; é o
  critério assumido (requisito 8.4).
- **"2020s" aberto.** Obras com ano ≥ 2030 caberiam em "2020s". Não existem
  hoje; fica anotado.

# Handover — fim da S4, início da S5

Escrito ao concluir a S4 (`atlas`). Serve para retomar a F3 na spec seguinte
(S5 `obra-autoria`).

## Onde o projeto está (resumo)

- **S1–S4 concluídas e no ar** (`liliane.prateleira.site`). A S4 foi o PR #5; o
  PR #6 corrigiu as colunas das grades no celular. Validada pela Lila no
  desktop e no celular.
- `main` sincronizada, worktree limpa. Pasta `temp/` (no `.gitignore`) para
  artefatos descartáveis, nunca `/tmp`.
- Números: **108 testes** verdes (69 da S3 + 39 da S4), `npm run check` limpo,
  build do catálogo real com **563 páginas** (17 anteriores + 546 da S4).

## O que a S4 entregou

- **Atlas por idioma (`/atlas`)** e **por país (`/atlas/pais`)**. O alternador
  são **duas rotas estáticas** (links com `aria-current`), não `?por=` (a query
  não chega ao HTML estático). `/atlas?por=pais` serve a vista de idioma.
  - Faixas (`YearBand`) por idioma (15) e por país (10 + bloco "Outros países"
    com 26 chips). Lombada por **obra**; no país, na cor do idioma de cada obra.
  - Três blocos nas duas vistas: Quem ela mais lê (top 10 por leituras),
    Temas que voltam (nuvem, piso 5 obras, teto 30, 4 degraus), Quando foram
    escritos (séc. XIX, séc. XX, 2000s, 2010s, 2020s).
- **Idioma (`/idioma/{slug}`, 15)**: cabeçalho na cor do idioma, big numbers
  (obras · % da estante · autorias), carrossel de autorias, grade ordenável.
- **País (`/pais/{slug}`, 36)**: nome na cor do idioma dominante, **clareada
  para passar 4,5:1** (`onGround`) com filete na cor exata; chips de países com
  o mesmo idioma dominante; resumo só se `pais:{código}` aprovado (hoje nenhum);
  destaque da autoria mais lida (máximo único e ≥ 2); sem ordenação.
- **Tema (`/tema/{slug}`, 493)**: cabeçalho escuro, três big numbers, grade
  ordenável. Variantes de caixa/acento agrupadas pelo slug.
- **Ordenação (Idioma e Tema)**: ilha vanilla em `WorkGridSort.astro`; os
  controles nascem `hidden` e a grade, sem JS, fica na ordem do caderno. Só
  essas duas telas levam `<script>`.

### Peças novas e reusáveis (a S5 deve reaproveitar)

- **`src/lib/atlas.ts`** (puro, testado): `buildAtlasByLanguage/Country`,
  `topAuthors`, `themeCloud`, `eras`, `buildLanguagePages/CountryPages/
  ThemePages`; helpers `languageHref`, `countryHref`, `capitalizeFirst`,
  `readingsLabel`, `toGridWork`, `firstSequence`. `themeHref` é de `home.ts`.
  A S5 vai precisar de hrefs para **idioma, país e tema** (use estes).
- **`grid-sort.ts`**: comparador + `toDataset`/`fromDataset`.
- **`BigNumbers`** (cores por `--bn-*`), **`AuthorRail`**, **`BrowseHeader`**
  (cabeçalho colorido ou escuro), **`WorkGrid`** (grade 3 colunas com título
  original e, opcionalmente, ordenação), **`AtlasToggle`**, **`AtlasInsights`**.
- **`AuthorChip layout="row"`** (avatar + nome + meta) e **`CoverCaption
  showOriginal`** (título original com `lang`/`dir`/fonte Noto).
- **`YearBand`**: `href` opcional e `shelfPerRow` (uma prateleira por linha).
- **`text.ts`**: `languageTag`, `originalTitleLang` (omite `lang` em
  romanização de idioma não latino), árabe `rtl`.
- **`language-color.ts`**: `contrastRatio`, `onGround(hex, min)`. Use `onGround`
  sempre que a cor do idioma for **texto** sobre o fundo escuro (8 das 11 cores
  não passam 4,5:1).

## Convenções reforçadas na S4 (seguir na S5)

- Regra só em `src/lib`; `.astro` burro; imports relativos em `lib`, `@/` nos
  `.astro`. Componentes genéricos não conhecem o catálogo.
- **Grades:** `grid-template-columns: repeat(3, minmax(0, 1fr))`, **nunca
  `1fr`** puro (um título com palavra longa alarga a coluna e estoura a tela no
  celular; foi o bug do PR #6). Item de grade com `min-width: 0`.
- Script de uma tela em **componente próprio** (como `WorkGridSort`), para só ir
  às telas que usam; um `<script>` dentro de um componente compartilhado vai a
  todas.
- Verificar refatoração de componentes com **diff do HTML contra a `main`**
  (baseline em `temp/`, normalizando os `data-astro-cid-*`).
- Medir layout de celular carregando a página num **iframe de 390 px** no Chrome
  headless (o `--window-size` corta o lado direito por artefato).

## Destinos que ainda dão "404" (dívida de rota)

| Rota | Quem linka | Fecha em |
|---|---|---|
| `/obra/{slug}` | grades de Ano, Sem data, Idioma, País, Tema; capas e busca | S5 |
| `/autoria/{slug}` | Quem ela mais lê, avatares de Idioma/País, "quem sempre volta", busca | S5 |

**Comportamento atual (esperado, só registrado):** não existe `404.astro`, então
o Cloudflare Pages serve o `index.html` para rotas desconhecidas. Clicar numa
autoria ou capa hoje **leva ao Início** (responde 200), em vez de mostrar erro.
Some quando a S5 criar as páginas. Uma `404.astro` simples ficou como opção
(não pedida).

## O que a S5 encontra pronto (para Obra e Autoria)

- Handoff **§6.8 (Autoria)** e **§6.9 (Obra)**, mais §8 (estados incompletos).
- Modelo: `AuthorView` (foto, bio só com summary `approved`, `works`, país,
  idiomas, `primaryLanguage`), `WorkView` (título original e romanizado,
  edição, `firstPublished`, gêneros, temas, leituras, `reread`).
- `readingsByAuthor` (ranking da autoria; só mostrar posição se estiver no top
  10, §6.8), `InitialsAvatar` grande com `ring` (132 px), `AuthorChip`.
- Links prontos para sair da Obra: autoria, **idioma** (`languageHref`), **ano**
  de cada leitura (`/ano/{ano}`), **temas** (`themeHref`), país da autoria
  (`countryHref`).
- Ainda **não existe** botão "Compartilhar" (fica para a S7; sem stub).

## Fora do escopo da S5 (confirmando o roadmap)

- PWA/offline → S6. Retrospectiva 9:16 e "Compartilhar" → S7.
- Capas de obra, resumos de ano/país, temas normalizados → frente de F2.

## Pendências herdadas (não bloqueiam a S5)

- **Capas de obra** ainda não existem: grades caem na capa tipográfica.
- **Resumos** de ano e de país ainda não existem: as seções somem.
- **Temas duplicados por caixa** no catálogo ("Segunda Guerra Mundial" /
  "segunda guerra mundial", "Nordeste", "Guerra Fria"): o app agrupa pelo slug;
  o Início (S2) ainda soma por variante. Normalizar o vocabulário no pipeline.
- **CSS de grade repetido** em Ano, Sem data e `WorkGrid` (~10 linhas): unificar
  quando conveniente.
- **Idioma de fonte da capa tipográfica coreana** usa `--font-serif-jp` (herança
  da S1); a grade (`CoverCaption`) já usa `--font-serif-kr`.
- Revisão contínua de autorias (fotos, Wikidata, bio) segue não bloqueante.

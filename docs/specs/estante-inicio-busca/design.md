# Design — Estante: Início e busca (S2)

## Visão geral

A S2 monta a primeira tela pública, `/`, e a busca. Quase tudo no Início é
**composição** de peças que a S1 já entregou (Capa, Capa tipográfica, Avatar,
Lombada, Prateleira) arrumadas em carrosséis e cartões; o trabalho novo de
verdade é **um componente Carrossel genérico** (que S3–S5 também reusam) e a
**busca** (índice estático gerado no build + uma ilha pequena no cliente).

Três princípios guiam as escolhas, em continuidade com a S1:

- **As páginas são burras; a regra vive em `lib/catalog`.** O Início lê de
  `getCatalog()` e só decide layout. Nenhuma contagem nova nasce na página:
  "ano atual", "3+ leituras", "4 temas mais frequentes" e "releituras" saem
  todos dos agregados que a S1 já expõe. Onde falta um recorte pronto, ele vai
  para uma camada fina de *seleção* (§4), não para dentro do `.astro`.
- **Zero JS para ler; JS só na ilha de busca.** Todo o conteúdo do Início é
  estático (SSG). A única ilha é a busca; o resto renderiza e navega sem
  JavaScript. As setas do carrossel são reforço progressivo sobre uma fileira
  que já rola por toque/teclado.
- **Links no formato final, 404 temporário aceito.** Os destinos (`/ano/…`,
  `/autoria/…`, `/tema/…`, `/obra/…`, `/atlas`, `/linha-do-tempo`) nascem em
  S3–S5, mas as URLs já estão fixadas no handoff e são emitidas agora. Até lá,
  esses links dão 404 em dev/preview — esperado, não um furo.

> Versões já fixadas na S1 e reusadas aqui: `astro@7.4.0`, `zod@4.6.7`,
> `sharp@0.35.5`, `typescript@6.0.3`, Node 22 LTS. A S2 **não adiciona
> dependência** nova: a busca é vanilla TS (ilha Astro com `<script>`), sem
> framework de UI (R7.4).

### Mapa de requisitos → seção

| Requisito | Onde é atendido |
|---|---|
| R1 Início substitui o placeholder | §2 Página `/`, §3 Composição |
| R2 Componente Carrossel | §5 Carrossel |
| R3 "Em {ano atual}" | §4 Seleção, §3.1 |
| R4 "Quem sempre volta" | §4 Seleção, §3.2 |
| R5 Carrosséis de tema | §4 Seleção, §3.3 |
| R6 "Lidos duas vezes" + cartão Linha do tempo | §4 Seleção, §3.4, §6 Mini-gráfico |
| R7 Busca (índice + ilha) | §7 Busca |
| R8 Navegação do cabeçalho | §8 Cabeçalho e chips |
| R9 Acessibilidade e desempenho | transversal; resumido em §9 |

## 1. Arquivos que a S2 cria ou toca

A S2 não mexe em `lib/catalog/` (a camada de dados da S1 fica intacta). Ela
adiciona uma camada fina de **seleção** (recortes do Início), **um** componente
de layout (Carrossel), os blocos de seção do Início, a página `/` e a busca.

```text
app/
  src/
    lib/
      home.ts              NOVO  recortes do Início a partir de getCatalog()
      search.ts            NOVO  normalização + tipo de entrada do índice (puro)
      search.test.ts       NOVO  testes da normalização e do match
      home.test.ts         NOVO  testes dos recortes (ano atual, 3+, 4 temas…)
    components/
      Carousel.astro       NOVO  carrossel genérico (R2); reusado por S3–S5
      CoverCaption.astro    NOVO  capa + título/autoria sob a capa (item de carrossel)
      AuthorChip.astro      NOVO  avatar + nome (item de "quem sempre volta")
      NavChips.astro       NOVO  chips Estante/Atlas/Linha do tempo (R8)
      SearchBox.astro      NOVO  campo + ilha de busca (R7)
      TimelineCard.astro   NOVO  cartão "Linha do tempo" com mini-gráfico (R6)
    pages/
      index.astro          REESCRITO  o Início de verdade (era placeholder)
      search-index.json.ts NOVO  endpoint estático: emite o índice de busca no build
```

Decisão de fronteira: **`home.ts` e `search.ts` são a regra; os `.astro` são
layout.** `home.ts` devolve estruturas já prontas ("a lista do ano atual", "as
4 seções de tema"); o `index.astro` só itera e posiciona. Isso mantém a regra
testável sob `node --test` (convenção da S1: imports relativos dentro de
`lib/`) e deixa a página sem lógica de negócio.

## 2. A página `/`

`index.astro` substitui o placeholder. Estrutura, de cima para baixo, na ordem
do handoff §6.1 (R1.5):

```text
<Base title="A estante da Lila">
  <header>
    h1 "A estante da Lila"
    <SearchBox/>                        ← ilha de busca (R7)
    <NavChips active="estante"/>        ← Estante · Atlas · Linha do tempo (R8)
  </header>
  <main>
    §3.1  Carousel "Em {ano atual}"     → /ano/{ano}        (omitido se vazio)
    §3.2  Carousel "Quem sempre volta"  → itens /autoria/…  (omitido se <1)
    §3.3  4× Carousel de tema           → /tema/{slug}      (quantos houver)
    §3.4  Carousel "Lidos duas vezes"   → itens /obra/…     (omitido se 0)
    §6    <TimelineCard/>               → /linha-do-tempo
  </main>
</Base>
```

- `getCatalog()` é chamado **uma vez** no frontmatter; `home.ts` recebe o
  catálogo e devolve todos os recortes de uma vez (R1.4).
- Cada seção é renderizada só se tiver conteúdo (R3.6, R4.5, R5.5, R6.3): a
  decisão "mostrar ou omitir" mora em `home.ts` (devolve lista vazia → a página
  não renderiza aquele bloco), não espalhada em condicionais no `.astro`.
- Mobile-first em 390px, `--gutter` lateral, alvos ≥ `--tap` (R1.6). O conteúdo
  ganha `max-width` no desktop como o styleguide já faz, com os carrosséis
  "sangrando" até a borda (o corte da última peça é parte do design, §5).

## 3. As seções do Início (composição)

Todas as seções de capa usam o mesmo item `CoverCaption` dentro do `Carousel`;
muda só a fonte de dados (o recorte vindo de `home.ts`) e o destino do título.

### 3.1 "Em {ano atual}" (R3)

- `home.ts` descobre o **ano atual** como `max(readingsByYear.keys())` — o ano
  mais recente **com leituras**, não `new Date()` (R3.2). Isso evita uma tela
  vazia em janeiro e casa com "a estante abre no presente" sem depender do
  relógio do build. (Ver §11, decisão.)
- As obras do ano: todas as `WorkView` com alguma `reading.year === anoAtual`,
  ordenadas pela `sequence` daquela leitura (ordem do caderno, R3.3).
- Item: `CoverCaption` com capa **hero** (136px) + título e autoria sob a capa.
- Título da seção e cartão "ver todos" → `/ano/{ano}`.

### 3.2 "Quem sempre volta" (R4)

- `home.ts` filtra `readingsByAuthorDesc` por `count >= 3` e resolve cada slug
  em `AuthorView` (para nome, foto/iniciais, cor). A ordem já vem decrescente e
  estável dos agregados (R4.3).
- Item: `AuthorChip` = `InitialsAvatar` (foto derivada quando houver, senão
  iniciais) + nome em texto → `/autoria/{slug}`.
- Seção omitida se a lista filtrada for vazia (R4.5).

### 3.3 Carrosséis de tema (R5)

- `home.ts` pega os **4 primeiros** de `worksByThemeDesc` (frequência
  decrescente, desempate estável — R5.4) e, para cada tema, a lista de obras que
  o contêm.
- Uma seção `Carousel` por tema, item `CoverCaption` (capa `rail`/`hero`), com
  teto de ~20 e cartão "ver todos (N)" (N = total de obras do tema) →
  `/tema/{slug}`.
- Se houver menos de 4 temas, mostra quantos existirem (R5.5).

### 3.4 "Lidos duas vezes" (R6.1–R6.3)

- `home.ts` devolve as `WorkView` com `reread === true` (uma peça por obra,
  nunca duplicada — R6.2), ordenadas por quantidade de leituras e depois por
  título (desempate estável).
- Item: `CoverCaption` com `rereadBadge` (o selo "2×" do componente Capa da S1).
- Seção omitida se não houver releitura (R6.3).

## 4. Camada de seleção — `home.ts`

Módulo puro que recebe o `Catalog` e devolve um objeto com todos os recortes do
Início, já prontos para o layout:

```ts
type Caption = {            // o que um item de capa precisa mostrar/linkar
  work: WorkView;
  href: string;             // /obra/{slug} (destino do item, S5)
};

type RailSection = {
  title: string;
  href: string;             // destino do título e do "ver todos"
  items: Caption[];         // já cortado ao teto; `total` guarda o N real
  total: number;
};

type HomeData = {
  currentYear: RailSection | null;     // §3.1 (null → seção omitida)
  recurringAuthors: AuthorPick[] | null; // §3.2
  themeRails: RailSection[];           // §3.3 (0..4)
  rereads: RailSection | null;         // §3.4
  yearBars: { year: number; count: number }[]; // §6 mini-gráfico
};

export function buildHome(catalog: Catalog, railCap = 20): HomeData { … }
```

- `railCap = 20` é o teto do handoff §9 (R2.5), parametrizável para ajuste
  futuro sem tocar a página.
- Devolver `null` (e não lista vazia) para seções que somem deixa a intenção
  explícita no tipo e a página trivial: `{data.rereads && <Carousel …/>}`.
- `yearBars` é a série por ano para o mini-gráfico, **só anos conhecidos** —
  leituras sem ano não entram aqui (R6.6); elas vivem em "Os primeiros da lista"
  na S3.

Testes (`home.test.ts`, com um catálogo de exemplo): ano atual é o maior ano
com leitura (não o relógio); corte de 3+ leituras inclui/exclui certo; no
máximo 4 temas, na ordem dos agregados; releitura aparece uma vez; seções vazias
viram `null`.

## 5. Componente Carrossel — `Carousel.astro` (R2)

Peça genérica e sem conhecimento do catálogo (R2.8). Recebe título, `href` do
"ver todos", total e o conteúdo dos itens via `<slot>`.

```
Props: {
  title: string;
  href: string;        // destino do título e do cartão "ver todos"
  total: number;       // N do "ver todos (N)"; some do rótulo se == itens visíveis
  labelAllPrefix?: string;  // ex.: "ver todos"
}
Slot: os itens (cada um idealmente um <a href> — CoverCaption/AuthorChip)
```

Estrutura e comportamento (handoff §9):

- Fileira com `display:flex; overflow-x:auto; scroll-snap-type: x mandatory;`
  e `scroll-snap-align: start` em cada item (R2.1). **A rolagem é nativa do
  navegador** — funciona sem JS (R2.7).
- A última peça visível fica **cortada**: a fileira sangra até a borda direita
  e o `padding-right` é menor que a largura de um item, então o próximo item
  aparece pela metade (R2.2). Isso sinaliza que rola, sem bolinhas nem barra
  (R2.6).
- Cartão final **tracejado** "ver todos (N)" (`--dashed`), um `<a href>` para a
  página completa (R2.3). O **título da seção é o mesmo link** (R2.4).
- Teto de ~20 itens é aplicado por quem preenche o slot (`home.ts`); o Carousel
  só exibe o que recebe e mostra o "ver todos" com o `total` real (R2.5).
- **Desktop:** setas ‹ › fora das capas, como `<button aria-label>` que
  chamam `scrollBy` (reforço progressivo via um `<script>` mínimo inline, não
  uma ilha de framework). Sem JS, as setas ficam ocultas (`:not(.enhanced)`)
  e a rolagem por toque/teclado continua (R2.6, R2.7). Navegação por teclado:
  a fileira é focável e rola com as setas do teclado; os itens são links
  tabuláveis.
- Decorativos (o corte, as setas) não carregam informação que falte em texto; o
  dado de cada item está no próprio item (R9).

`CoverCaption.astro` (item): embrulha `Cover` (S1) num `<a href>`, com título
(e autoria) em **texto sob a capa** (handoff §9 — nunca só na imagem), com
`line-clamp` de 2 linhas e reticências. `AuthorChip.astro`: `InitialsAvatar` +
nome, também num `<a>`.

## 6. Mini-gráfico e cartão "Linha do tempo" — `TimelineCard.astro` (R6.4–R6.6)

- Barras verticais, uma por ano conhecido, altura proporcional à contagem
  (`yearBars` de `home.ts`). Usa `--bar-neutral`; o ano atual pode destacar em
  `--accent` (coerência com §3.1).
- **Decorativo** (`aria-hidden`): o cartão é um `<a href="/linha-do-tempo">`
  com um rótulo em texto ("Linha do tempo") que carrega o significado; as
  barras são enfeite (R6.6). O dado real (anos e contagens) é a própria página
  de destino (S3).
- Nunca mostra dia/mês nem trata "sem data" como um ano (R6.6): `yearBars` já
  exclui as leituras sem ano.

## 7. Busca — índice estático + ilha (R7)

Duas metades que compartilham **uma** regra de normalização.

### 7.1 Módulo puro `search.ts` (R7.3)

Normalização tolerante a acento e o formato da entrada do índice, num módulo
sem dependências (roda sob `node --test`):

```ts
export type SearchEntry = {
  type: "work" | "author";
  slug: string;
  label: string;        // rótulo de exibição (título pt-BR ou nome)
  href: string;         // /obra/{slug} ou /autoria/{slug}
  keys: string;         // chaves normalizadas concatenadas (busca)
};

/** "José Saramago (Ensaio…)" → "jose saramago ensaio". Sem acento, minúsculo. */
export function fold(text: string): string {
  return text
    .normalize("NFD").replace(/[\u0300-\u036f]/g, "")  // tira diacríticos
    .toLowerCase()
    .replace(/[^\p{L}\p{N}]+/gu, " ")                   // pontuação → espaço
    .trim();
}

/** true se a consulta (já foldada) casa a entrada. */
export function matches(entry: SearchEntry, foldedQuery: string): boolean { … }
```

A mesma `fold()` é usada na **geração** do índice (chaves) e na **consulta** no
cliente (R7.3) — por isso ela é o coração testável da busca (`search.test.ts`:
"josé"→"jose", "SARAMAGO"→"saramago", acento no meio, título CJK preservado nos
seus code points, match por substring de palavra).

### 7.2 Endpoint estático `search-index.json.ts` (R7.1, R7.2, R7.9)

Uma rota de endpoint do Astro que **emite JSON no build** (não uma página):

```ts
export const GET: APIRoute = () => {
  const { works, authors } = getCatalog();
  const entries: SearchEntry[] = [
    ...works.map(w => ({
      type: "work", slug: w.slug, label: w.title, href: `/obra/${w.slug}`,
      keys: fold([w.title, w.originalTitle, w.originalTitleRomanized]
                  .filter(Boolean).join(" ")),
    })),
    ...authors.map(a => ({
      type: "author", slug: a.slug, label: a.name, href: `/autoria/${a.slug}`,
      keys: fold(a.name),
    })),
  ];
  return new Response(JSON.stringify(entries));
};
```

- Uma entrada por obra (chaves: título pt-BR + original + romanização) e uma
  por autoria (nome) — R7.1, R7.2. Cobre todo o catálogo e é regenerado a cada
  build, sem passo manual (R7.9).
- Sai como asset estático em `/search-index.json`; o navegador baixa só quando
  a busca é usada (§7.3).

### 7.3 Ilha de busca `SearchBox.astro` (R7.4–R7.8)

- Markup estático: um `<form role="search">` com `<label for>` e um `<input>`
  de ~52px com ícone de lupa (handoff §4), mais um `<ul>` vazio para resultados
  (R7.7). Sem JS, o campo aparece mas não filtra — e **nada no resto da página
  depende disso** (R7.8).
- Um `<script>` do próprio componente (ilha Astro, vanilla TS, sem framework —
  R7.4): no primeiro foco/teclada, faz `fetch('/search-index.json')` **uma
  vez**, guarda em memória, e a cada tecla filtra com `fold(input)` + `matches`
  e injeta os resultados como `<a href>` (R7.5, R7.6). Debounce leve; limite de
  resultados exibidos (ex.: 20) para não explodir a lista.
- Acessível: `<label>` associado, `aria-label` no botão de lupa se for só
  ícone, `aria-controls`/`role=listbox` opcional para a lista; navegável por
  teclado (R7.7, R9.1).
- Não chama API externa; só o próprio asset do site (R7.4).

## 8. Cabeçalho e chips — `NavChips.astro` (R8)

- `h1` "A estante da Lila" em `.t-screen-title`.
- Três chips de 44px (handoff §4): `Estante` **ativo** (`--accent` +
  `--accent-ink`), `Atlas` e `Linha do tempo` como chip secundário
  (`--border`). O ativo é a prop `active` (R8.2).
- `Atlas` → `/atlas`, `Linha do tempo` → `/linha-do-tempo`, ambos `<a href>`
  operáveis por teclado (R8.3, R8.4). 404 temporário até S3/S4.
- O chip ativo pode ser um `<span aria-current="page">` em vez de link (não
  navega para a própria tela).

## 9. Acessibilidade e desempenho (R9) — transversal

- Navegação com `<a href>`, ações com `<button aria-label>` (setas, lupa),
  campo com `<label>` (R9.1). Chip ativo com `aria-current`.
- Capas e avatares herdam da S1: `loading="lazy"`, dimensões fixas 2:3/1:1,
  `alt` significativo; barras e corte decorativos com `aria-hidden` e o dado em
  texto no item ou no destino (R9.2, R6.6).
- Títulos não latinos herdam `lang`/`dir` da `TypographicCover`/`Cover` (R9.3).
- Contraste: tokens de §3.1 sobre `--ground`; texto sobre cor de idioma usa o
  par de §3.2 (R9.4).
- Carrosséis rolam por toque e teclado sem depender das setas; sem rolagem
  automática (R9.5).
- **Orçamento de JS:** o único script enviado é a ilha de busca (e o
  `scrollBy` mínimo das setas). Nenhuma outra parte do Início exige JS para ler
  ou navegar (R9.6, R1.2). O `search-index.json` só é baixado quando a busca é
  usada, não no carregamento da página.

## 10. Fluxo de build e verificação

- `npm run check` (astro check + tsc) cobre os tipos novos; `home.ts` e
  `search.ts` são tipados a partir das views da S1.
- `npm test` (node --test) roda `home.test.ts` e `search.test.ts`, somando aos
  32 testes da S1.
- `npm run build` gera `/` e o asset `/search-index.json`; o portão de CI (F4)
  roda check + test + build antes de publicar, então Início ou índice quebrados
  não vão ao ar.
- Verificação visual: além do styleguide da S1, o próprio `/` passa a ser a
  prova da S2 (no preview do Pages gerado pelo PR).

## 11. Decisões e alternativas

| Decisão | Alternativa descartada | Porquê |
|---|---|---|
| "Ano atual" = maior ano **com leitura** | `new Date().getFullYear()` | não depende do relógio do build; nunca abre vazio em começo de ano; casa com "a estante abre no presente" |
| Recortes do Início em `home.ts` | condicionais e filtros no `index.astro` | mantém a página burra e a regra testável sob `node --test` (convenção S1) |
| Índice como endpoint `.json.ts` | gerar o JSON num passo externo ao Astro | fica dentro do build do Astro, regenera sozinho, sem passo manual (R7.9) |
| Busca vanilla (ilha Astro + `<script>`) | Preact/React island, Pagefind, Fuse.js | R7.4 proíbe framework pesado; o catálogo é pequeno (~300+215), `fold`+substring basta e não adiciona dependência |
| `fold()` compartilhada build+cliente | normalizar só no cliente | as duas pontas precisam da MESMA regra; uma função só evita divergência (R7.3) |
| Setas do carrossel como reforço | setas como única forma de rolar | a fileira já rola nativamente; sem JS continua usável (R2.7, R9.5) |
| Links no formato final (404 temporário) | texto não clicável até S3–S5 | URLs já fixadas no handoff; evita reescrever markup depois |
| Carousel genérico agora | um carrossel específico por seção | S3–S5 reusam a mesma peça; um componente só, testado uma vez |

## 12. Riscos e limites conhecidos

- **404 temporários.** Todos os destinos de navegação e de busca (exceto a
  própria `/`) só existem em S3–S5. No preview do PR da S2, clicar leva a 404.
  É esperado e está registrado nos requisitos; some conforme as specs seguintes
  entram.
- **Capas de obra ainda ausentes.** Os carrosséis mostram a capa tipográfica
  para toda obra (nenhuma capa de obra no catálogo ainda, frente de F2). Quando
  as capas entrarem, `Cover` já as usa sem mudança de contrato; o Início não
  muda.
- **4 temas é um chute calibrável.** O número e o visual dos carrosséis de tema
  podem não ficar bons; `home.ts` recebe isso como parâmetro, então ajustar é
  trocar um argumento, não reescrever a tela.
- **Índice de busca cresce com o catálogo.** Hoje ~517 entradas (302 obras +
  215 autorias), um JSON pequeno. Se um dia pesar, dá para comprimir ou partir;
  não é problema na escala atual.
- **Busca exige JS.** Decisão aprovada: busca é interação, não leitura. Com JS
  desligado o campo fica inerte e o resto da tela continua inteiro (R7.8).

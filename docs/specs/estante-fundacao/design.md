# Design — Estante: fundação (S1)

## Visão geral

A S1 monta o esqueleto do app e os tijolos visuais. Nenhuma tela pública nasce
aqui; o que nasce é a base que a S2 em diante vai compor. O design abaixo
descreve a estrutura do projeto Astro, o sistema de tokens e cor por idioma, a
camada de dados (ler → validar → modelar → agregar), a derivação de imagens, os
cinco componentes base e a vitrine de verificação.

Três princípios guiam as escolhas:

- **O catálogo é a verdade; o app só lê.** Toda a camada de dados é um caminho
  de mão única: `catalog/*.json` → Zod → modelo de domínio → páginas. Nada
  escreve em `catalog/`, nada chama rede.
- **A cor por idioma é o eixo visual.** Um único módulo decide a cor, e todo
  componente colorido (lombada, capa tipográfica, avatar) bebe dele.
- **Falha cedo e alto.** Catálogo inválido quebra o build com mensagem clara,
  em vez de gerar um site silenciosamente errado.

> Versões fixadas na implementação (estáveis em nov/2026): `astro@7.4.0`
> (casada com o Node 22.22 do ambiente; a 7.4.5 exige 22.23.4), `zod@4.6.7`,
> `sharp@0.35.5`, `typescript@6.0.3` (a 7.x ainda não é suportada pelo
> `@astrojs/check`). Node 22 LTS.

### Mapa de requisitos → seção

| Requisito | Onde é atendido |
|---|---|
| R1 Projeto Astro | §1 Estrutura, §2 Config |
| R2 Tokens e fontes | §3 Tokens, §4 Fontes |
| R3 Cor por idioma | §5 Cor por idioma |
| R4 Validação no build | §6 Camada de dados (loader + Zod) |
| R5 Modelo e agregados | §6 Camada de dados (modelo + agregados) |
| R6 Derivação de imagens | §7 Imagens |
| R7 Componentes base | §8 Componentes |
| R8 Vitrine | §9 Vitrine |
| R9 Acessibilidade/desempenho | transversal; resumido em §10 |

## 1. Estrutura de pastas

O app vive em `app/`. O `catalog/` fica um nível acima e é lido por caminho
relativo à raiz do repositório — nunca copiado para dentro de `app/`.

```text
app/
  astro.config.mjs        saída estática; alias; integração de imagem
  tsconfig.json           strict; paths
  package.json            scripts e versões fixadas
  src/
    styles/
      tokens.css          custom properties: cores §3.1, medidas §3.4
      type.css            papéis tipográficos §3.3 (classes utilitárias)
      fonts.css           @font-face auto-hospedado (§4)
      global.css          reset enxuto + fundo --ground
    lib/
      catalog/
        schema.ts         esquemas Zod espelhando catalog/schema/*.json
        load.ts           lê e valida os arquivos (build-time)
        model.ts          monta o modelo de domínio
        aggregates.ts     contagens por ano/idioma/país/autoria/tema
        index.ts          getCatalog(): fachada cacheada por build
        __tests__/        testes da camada de dados
      language-color.ts   cor por idioma §3.2 (mapa + fallback)
      images.ts           resolução e derivação de imagens (§7)
      text.ts             iniciais, detecção de alfabeto, dir/lang
    components/
      Cover.astro
      TypographicCover.astro
      Spine.astro
      InitialsAvatar.astro
      Shelf.astro
    layouts/
      Base.astro          <html lang="pt-BR">, <head>, tokens e fontes
    pages/
      __styleguide/
        index.astro       vitrine (§9), fora do sitemap
  public/
    fonts/                arquivos de fonte auto-hospedados (woff2)
  README.md               scripts e convenções do app
```

Decisão: `src/lib/catalog/` concentra **toda** a regra de negócio. Os
componentes e páginas são "burros" — recebem props já resolvidas. Isso mantém a
regra de negócio num lugar só (R5) e deixa os componentes testáveis por
inspeção visual na vitrine.

## 2. Configuração do projeto

- **Astro 7.x** (versão estável atual, sobre Vite 8/Rolldown), `output: "static"`. Sem adaptador de servidor.
- **TypeScript** com `astro/tsconfigs/strict`; sem `any` implícito.
- **Node** fixado por `.nvmrc`/`engines` para o build reproduzir igual no CI (F4).
- **Versões fixadas** em `package.json` (sem `^`/`~`), conforme R1.4 e a
  convenção do projeto. O `package-lock.json` é versionado.
- **Alias** `@` → `src/` e um alias `@catalog` que resolve a raiz do catálogo a
  partir de uma única constante (`CATALOG_DIR`), para não espalhar `../../`.
- Scripts: `dev`, `build`, `preview`, `check` (`astro check` + `tsc --noEmit`).
  `build` roda a validação do catálogo como primeira etapa (§6.2); se ela
  lançar, o build morre com código ≠ 0 (R1.8, R4.3).

Dependências previstas na S1 (todas fixadas):

| Pacote | Para quê |
|---|---|
| `astro` | framework e build estático |
| `zod` | validação do catálogo (R4) |
| `sharp` | derivação de imagens no build (R6); já é a engine de `astro:assets` |

Nada de framework de UI (React/Vue/etc.) na S1 — não há ilha ainda (R1.7). A
busca e os alternadores interativos chegam nas specs seguintes.

## 3. Tokens de cor e medidas

`src/styles/tokens.css` declara, no `:root`, **exatamente** os valores do
handoff. Fonte única: §3.1 e §3.4. Exemplo (abreviado):

```css
:root {
  /* §3.1 cores de interface */
  --ground: #0E1714;
  --surface: #15211D;
  --line-soft: #1F2D28;
  --line: #2D3E37;
  --border: #33443D;
  --border-input: #3A4C45;
  --dashed: #4A5C54;
  --text: #EDE6D6;
  --title: #F4EBD8;
  --muted: #BFC8C2;
  --faint: #A9B5AE;
  --accent: #E8C678;
  --accent-ink: #1A1408;
  --wood-top: #5B3E26;
  --wood-bottom: #3A2716;
  --bar-neutral: #4B5E55;

  /* §3.4 medidas */
  --gutter: 16px;
  --tap: 44px;
  --radius-pill: 22px;
  --cover-ratio: 2 / 3;
  --cover-shadow: 0 16px 22px -14px rgba(0,0,0,.8);
  --cover-hero-w: 136px;   /* destaque 136×204 */
  --cover-rail-w: 104px;   /* carrossel 104×156 */
  --grid-gap-x: 12px;
  --grid-gap-y: 20px;
}
```

`global.css` aplica `background: var(--ground)` e `color: var(--text)` no corpo
(R2.2). As medidas viram custom properties para os componentes consumirem sem
números mágicos.

### Tipografia (§3.3)

`type.css` expõe classes utilitárias, uma por papel da tabela do handoff, com
fonte, peso, tamanho, `line-height` e `letter-spacing`:

| Classe | Papel |
|---|---|
| `.t-screen-title` | Bodoni itálico 500, 46–50px, lh .95, ls −.02em |
| `.t-year-giant` | Bodoni 700, 132px, lh .84 |
| `.t-section-title` | Bodoni itálico 500, 24–28px |
| `.t-bignumber` | Bodoni 700, 40–48px |
| `.t-label` | Manrope 700, 11–12px, ls .14–.18em, caixa alta |
| `.t-body` | Manrope 400–600, 13–16px |

Os tamanhos com faixa (46–50, 24–28) usam `clamp()` para escalar entre mobile
(390px de referência) e desktop.

## 4. Fontes auto-hospedadas

A regra do projeto proíbe hotlink (R2.5). Em vez do `<link>` para o Google
Fonts que as telas de referência usam, as fontes vêm dos pacotes
[Fontsource](https://fontsource.org) (`@fontsource*`, versões fixadas), que
**empacotam os `.woff2` no build** — sem rede em runtime. `fonts.css` importa
os CSS desses pacotes:

- **Bodoni Moda Variable** (opsz 6–96, `wght` + `wght-italic`) — títulos e números.
- **Manrope Variable** (400–800) — interface e texto.
- **Noto Serif KR / JP / Hebrew** — títulos originais; importado apenas o
  subset do script no peso 400. Cada subset traz seu próprio `unicode-range`,
  então o navegador só baixa a fonte **sob demanda** (R2.5): a Noto JP só é
  baixada numa página que contenha japonês.

Decisão: Fontsource dá o auto-hospedado versionado sem um passo manual de
download, e o `unicode-range` de cada subset resolve o "sob demanda" sem
JavaScript — o próprio navegador evita baixar a Noto JP numa página sem
japonês. (Desvio em relação ao plano inicial de baixar à mão para
`public/fonts/`: Fontsource é mais simples e igualmente sem hotlink.)

Os nomes de família ("Bodoni Moda Variable", "Manrope Variable") vêm dos
pacotes e ficam atrás de tokens (`--font-display`, `--font-ui`,
`--font-serif-*`) em `tokens.css`, para não se espalharem pelo CSS.

## 5. Cor por idioma

`src/lib/language-color.ts` é o módulo central (R3). Mapa idioma → par de cores
de §3.2, com fallback "outros":

```ts
export type LanguageColor = { bg: string; ink: string };

const LANGUAGE_COLORS: Record<string, LanguageColor> = {
  "português": { bg: "#C89B3C", ink: "#1A1408" },
  "inglês":    { bg: "#2F5D9E", ink: "#F4EFE6" },
  "espanhol":  { bg: "#A8432C", ink: "#F7EDE6" },
  "francês":   { bg: "#6B4F9A", ink: "#F3EEF8" },
  "italiano":  { bg: "#3F7A5C", ink: "#F2F0E8" },
  "russo":     { bg: "#7E2433", ink: "#F6E9EB" },
  "japonês":   { bg: "#E8DFCB", ink: "#2A2418" },
  "alemão":    { bg: "#5A5A5A", ink: "#F2F2F2" },
  "hebraico":  { bg: "#2A7F86", ink: "#EEF7F7" },
  "coreano":   { bg: "#E3A9B0", ink: "#2A1418" },
};
const OTHER: LanguageColor = { bg: "#4B5E55", ink: "#EDE6D6" };

export function languageColor(language: string): LanguageColor {
  return LANGUAGE_COLORS[language] ?? OTHER;
}
```

- **Cobertura:** o `vocabularies.json` de hoje lista 15 idiomas; 10 têm cor
  própria, os demais (árabe, catalão, holandês, norueguês, tcheco) caem em
  "outros" por design, sem erro (R3.2, R3.4).
- **Duas formas de uso (R3.3):** em build, os componentes leem `bg`/`ink` para
  montar `style`; para compor em CSS, um helper emite as custom properties
  `--lang-bg`/`--lang-ink` num wrapper, e o CSS as consome.
- **Teste:** idioma conhecido devolve o par certo; idioma fora do mapa devolve
  "outros" (coberto em §6.6).

## 6. Camada de dados

Caminho de mão única, executado uma vez por build: **ler → validar → modelar →
agregar**, e uma fachada `getCatalog()` que memoiza o resultado para o build
inteiro (R5.7).

### 6.1 Esquemas Zod (R4.1)

`schema.ts` reescreve em Zod os cinco JSON Schema reais de `catalog/schema/`,
campo a campo, mantendo os mesmos nomes e restrições. Pontos que o design fixa
para não escorregar para o JSON "sugerido" do handoff (R4.5):

- `work.cover` é **objeto `{ sourceUrl, source }` ou `null`** — não string.
- `work.authors` é lista de slugs; `firstPublished` e `edition.year` podem ser
  `null`.
- `author.photo` é **objeto ou `null`**; `author.country` é ISO-2 ou `null`;
  **não há `bio` na autoria**.
- `reading.year` pode ser `null`; existe `sequence` e `reread`.
- A bio vive em `summaries.json`, com `scope: "autoria:{slug}"` e `approved`.

Os esquemas Zod são a fonte dos tipos TypeScript (via `z.infer`), então o
código a jusante é tipado a partir da validação, não à parte dela.

### 6.2 Loader (R4.2–R4.4, R4.6)

`load.ts`:

1. Resolve `CATALOG_DIR` a partir da raiz do repo (R4.6), sem presumir layout
   da máquina.
2. Lê `readings.json`, `summaries.json`, `vocabularies.json` e todos os
   `works/*.json` e `authors/*.json`.
3. Valida cada arquivo com o Zod correspondente. Em erro, lança com **o
   caminho do arquivo e o campo** na mensagem (R4.3), e o build cai.
4. Checa as invariantes de referência que o schema isolado não vê (R4.4):
   - toda `work.authors[]` existe em `authors/`;
   - toda `reading.work` existe em `works/`;
   - `author.primaryLanguage ∈ author.languages`;
   - `summary.scope` tem alvo coerente: `autoria:{slug}` existe; `ano:{aaaa}`
     tem ao menos uma leitura naquele ano; `pais:{XX}` existe em `vocabularies`.

Essas invariantes duplicam de propósito parte do que o `validate_catalog.py` já
faz. O validador Python é a porta de entrada no `catalog/`; o loader é a
segunda trava, no build do app, para o site nunca sair de dado inconsistente.

### 6.3 Modelo de domínio (R5.1–R5.4, R5.6)

`model.ts` transforma os dados crus em um grafo tipado e navegável:

```ts
type Reading = { sequence: number; year: number | null; reread: boolean };

type Work = {
  slug: string;
  title: string;
  originalTitle: string | null;
  originalTitleRomanized: string | null;
  language: string;                 // idioma original
  color: LanguageColor;             // derivado de language
  authors: Author[];                // resolvidos
  readings: Reading[];              // uma obra, várias leituras
  firstPublished: number | null;
  genres: string[];
  themes: string[];
  edition: Edition;
  coverSourceUrl: string | null;    // origem; NÃO usada como src (R6.4)
  // ...ficha, notas
};

type Author = {
  slug: string;
  name: string;
  country: string | null;           // ISO-2
  countryName: string | null;       // resolvido via vocabularies
  languages: string[];
  primaryLanguage: string;
  color: LanguageColor;             // cor do primaryLanguage (avatar)
  photo: AuthorPhoto | null;
  bio: string | null;               // só se summary approved (R5.4)
  works: Work[];
};
```

Regras aplicadas aqui, uma vez, para todas as telas:

- **Releitura (R5.2):** uma obra, várias `readings`; nunca duplicada. O selo
  "2×" é decisão do componente, a partir de `readings.length > 1`.
- **Só o ano (R5.3):** `Reading` tem só `year`. Leituras com `year === null`
  são marcadas como "sem data" e expõem a `sequence` (nº da lista). Nenhum
  dia/mês existe no modelo.
- **Bio (R5.4):** `author.bio` só é preenchida se houver `summary` com
  `scope === "autoria:{slug}"` e `approved === true`. Senão, `null` → a seção
  "Sobre" some na tela (sem "—").
- **País da obra (R5.6):** derivado do país das autorias. Uma obra com autorias
  de países diferentes pertence a cada país (relevante para os agregados).

### 6.4 Agregados (R5.5)

`aggregates.ts` calcula, uma vez por build, as contagens que quase toda tela
pede:

- por **ano** (quantas leituras, com releitura contando no ano de cada leitura);
- por **idioma original** (nº de obras), ordenável por frequência;
- por **país** da autoria (nº de obras; uma obra conta em cada país das suas
  autorias — R5.6);
- por **autoria** (nº de leituras — base de "quem sempre volta");
- por **tema** (frequência — base da nuvem de temas na S4).

Os agregados devolvem tanto o mapa quanto a lista já ordenada por quantidade,
porque o design pede idiomas e países "por quantidade" (handoff §6.4, §6.5).

### 6.5 Fachada (R5.7)

`index.ts` expõe `getCatalog()` que roda load → model → aggregate **uma vez** e
memoiza. As páginas (S2+) e a vitrine chamam `getCatalog()` sem reler disco.

### 6.6 Testes (R5.8)

`__tests__/` com dados de exemplo mínimos cobrindo:

- releitura conta nos dois anos;
- leitura sem `year` cai em "sem data" e expõe `sequence`;
- bio não aprovada → `author.bio === null`;
- idioma fora do mapa → cor "outros";
- invariante quebrada (autor inexistente, scope órfão) → o loader lança.

Runner: o test runner nativo do Node (`node --test`), sem dependência extra.

## 7. Imagens (R6)

### O problema

`astro:assets` (`<Image>`, `<Picture>`, `getImage()`) gera WebP/AVIF no build,
força `alt`, fixa dimensões e evita salto de layout — exatamente o que R6 e R9
pedem. Mas ele otimiza **imagens importadas** (dentro de `src/`) ou remotas
autorizadas. Nossos mestres ficam em `catalog/media/`, **fora de `app/src`**.

### A decisão

Tratar `catalog/media/` como fonte local de assets e usar `astro:assets` sobre
ela, sem copiar o diretório para dentro de `app/`:

- Um helper `images.ts` resolve o caminho do mestre de uma autoria
  (`catalog/media/authors/{slug}.{ext}`) e usa a API de imagem do Astro para
  gerar os derivados (WebP/AVIF, 2:3, corte central) e os tamanhos de `srcset`
  (R6.1–R6.3).
- A engine por baixo é o **sharp** (já é a default do `astro:assets`), listado
  explícito nas dependências para o build do CI ter a lib nativa.
- O `src` renderizado é **sempre** o derivado local. A `cover.sourceUrl` do
  catálogo é só proveniência; nunca vira `src` (R6.4).
- `loading="lazy"` e dimensões fixas 2:3 em toda renderização (R6.6, R9.3).

### Fallback (R6.5)

Se não há mestre local para uma obra (hoje, **nenhuma** capa de obra foi
baixada — é frente de F2 posterior), a `<Cover>` renderiza a `<TypographicCover>`
em vez da imagem, sem erro de build. Para autoria sem foto (ex.: `beatriz-leal`),
o `<InitialsAvatar>` mostra as iniciais.

> Escopo da S1: entregamos o **mecanismo** de derivação e o fallback, provados
> na vitrine com as fotos de autoria reais (174 existem) e com a capa
> tipográfica para toda obra (nenhuma capa de obra ainda). Quando as capas de
> obra entrarem no catálogo, elas passam pelo mesmo caminho sem mudança de
> componente.

## 8. Componentes base (R7)

Todos são componentes `.astro` puros (zero JavaScript, R7.6), com props
tipadas (R7.8) e sem acesso direto ao catálogo — recebem o que precisam.

### 8.1 `Shelf.astro` — Prateleira

Faixa de 6–9px com gradiente `--wood-top → --wood-bottom` e sombra embaixo.
Decorativa: `aria-hidden="true"`. Slot opcional para apoiar capas/lombadas
"em cima" dela.

### 8.2 `Spine.astro` — Lombada mini

Barra de 4px de largura; altura determinística entre 30 e 48px a partir de um
`index` (hash simples do índice → altura estável entre builds), na cor do
idioma (`languageColor(language).bg`). `aria-hidden="true"`; o dado (título,
ano) existe em texto no contexto que a usa (R7.3, R7.6).

```
Props: { language: string; index: number }
```

### 8.3 `Cover.astro` — Capa

Quadro 2:3 com `--cover-shadow`. Se recebe um mestre de imagem resolvível,
renderiza o derivado (`<Image>`/`<Picture>` via `images.ts`), `object-fit:
cover`, corte central, `loading="lazy"`, `alt` = título. Senão, delega para
`TypographicCover`. Selo de releitura "2×" opcional no canto quando
`rereadBadge`.

```
Props: {
  title: string; language: string;
  master?: ImageRef;            // mestre local, se houver
  originalTitle?: string | null;
  author?: string;
  rereadBadge?: boolean;
  size?: "hero" | "rail" | "grid";
}
```

### 8.4 `TypographicCover.astro` — Capa tipográfica

Fallback de capa (R7.2), fiel a `telas/Capas.dc.html` mas com as fontes e cores
de produção:

- Fundo = `languageColor(language).bg`; texto = `.ink`.
- Topo: título em **Bodoni itálico** (não o Instrument Serif do mock).
- Rodapé: título original (quando difere, com `lang` e `dir="rtl"` quando for o
  caso) e autoria em caixa alta, separados por um filete de 1px.
- **Encolhimento do título em até 3 passos** (R7.2): classes de tamanho
  decrescente escolhidas por faixas de comprimento do título (sem JS); títulos
  muito longos cortam, deixando o subtítulo para a página da obra.
- Alfabeto não latino no título original → fonte Noto correspondente via
  `text.ts` (detecção de faixa Unicode) e `lang`/`dir` (R7.7, R9.2).

### 8.5 `InitialsAvatar.astro` — Avatar de iniciais

Círculo na cor do `primaryLanguage` da autoria, iniciais em Bodoni itálico
(R7.4). Se há foto local, mostra o derivado da foto no lugar das iniciais, com
`alt` = nome. Tamanho parametrizável (ex.: 132px com anel na página de Autoria,
na S5).

```
Props: { name: string; language: string; photo?: ImageRef | null; size?: number }
```

### 8.6 Estados incompletos (R7.7) — resumo

| Caso | Componente | Comportamento |
|---|---|---|
| Sem capa | `Cover` | cai em `TypographicCover` |
| Sem foto | `InitialsAvatar` | mostra iniciais |
| Título longo | `TypographicCover` | encolhe em 3 passos; corta no subtítulo |
| Título não latino | `TypographicCover` | Noto + `lang`/`dir` |
| Releitura | `Cover` | selo "2×" |

## 9. Vitrine (`/__styleguide`) (R8)

Página estática que importa `getCatalog()` e renderiza:

1. **Tokens de cor** — amostras de cada token de §3.1 com nome e hex.
2. **Cor por idioma** — um cartão por idioma de §3.2 mostrando `bg`/`ink`, mais
   o caso "outros" (ex.: catalão, que existe no catálogo).
3. **Tipografia** — cada classe de `type.css` com um exemplo.
4. **Componentes em estados** (R8.2):
   - `Cover` com capa tipográfica real (toda obra hoje) e, se algum mestre
     existir, com imagem;
   - `InitialsAvatar` com foto real (ex.: `han-kang`) e sem foto (ex.:
     `beatriz-leal`);
   - `TypographicCover` com título curto (Torto Arado), longo (Emburrecimento
     Programado), cirílico (Crime e Castigo), hebraico RTL (De Amor e Trevas) e
     japonês (Kitchen);
   - `Spine` numa fileira determinística sobre a `Shelf`.

Exclusão do público (R8.3): a rota mora em `pages/__styleguide/` e é removida do
sitemap; nenhuma página pública linka para ela. (Na F4 dá para não publicá-la,
mas isso é deploy, não S1.) Funciona sem JS (R8.4) e usa dados reais (R8.5).

Decisão: a vitrine é a **verificação visual oficial da S1** e a tela que abre a
palestra — a fundação visível antes de qualquer página de leitura existir.

## 10. Acessibilidade e desempenho (R9) — transversal

- `Base.astro` fixa `<html lang="pt-BR">` e importa tokens/tipos/fontes.
- Navegação com `<a href>`, ações com `<button>`, campos com `<label>`;
  ícone-só com `aria-label` (R9.1). Na S1 há pouca navegação, mas o layout base
  já estabelece o padrão.
- Decorativos (`Shelf`, `Spine`, barras) com `aria-hidden`; dado equivalente em
  texto (R7.6).
- Imagens com `alt` significativo ou `alt=""` quando decorativas, e dimensões
  fixas 2:3 (R9.3).
- Tudo renderiza sem JS (R9.4). Contraste conforme tokens e pares de idioma
  (R9.5) — os pares de §3.2 já foram escolhidos para contrastar texto/fundo.

## 11. Decisões e alternativas

| Decisão | Alternativa descartada | Porquê |
|---|---|---|
| `astro:assets` sobre `catalog/media/` | script próprio de sharp fora do Astro | reusa o pipeline de imagem do Astro (srcset, formatos, sem salto) sem reinventar |
| Zod espelhando os JSON Schema | gerar Zod do JSON Schema automaticamente | o catálogo tem invariantes de referência que o schema isolado não cobre; escrever à mão deixa o loader e as invariantes no mesmo lugar |
| Regra de negócio só em `lib/catalog` | regra espalhada nos componentes | uma fonte de verdade; componentes viram burros e testáveis por inspeção |
| Fontes auto-hospedadas + `unicode-range` | `<link>` para Google Fonts | regra "nada de hotlink"; `unicode-range` dá o "sob demanda" sem JS |
| Vitrine dentro da S1 | deixar para depois | verificação visual + material de palestra; custo baixo |
| Cor por idioma como módulo tipado | CSS puro com classes por idioma | precisa ser legível em build (para montar `style` de componente) e em CSS; o módulo serve os dois |

## 12. Riscos e limites conhecidos

- **Capas de obra ausentes.** Hoje nenhuma capa de obra foi baixada; a S1 prova
  o caminho com a capa tipográfica e com as fotos de autoria. Isso é esperado
  (frente de F2 posterior), não um furo da S1.
- **Fontes grandes.** Bodoni Moda e Manrope variáveis mais três Noto podem
  pesar; `unicode-range` e `font-display: swap` mitigam, e o subsetting fica
  como ajuste posterior se o peso incomodar no Samsung.
- **Dupla validação (Python + Zod).** É proposital (duas travas), mas significa
  manter dois espelhos do schema. Se divergirem, o Zod do app é quem decide se
  o site sai.

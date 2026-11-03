# Design — Linha do tempo (S3)

## Visão geral

A S3 cria três telas — **Linha do tempo** (`/linha-do-tempo`), **Ano**
(`/ano/{ano}`) e **Sem data** (`/ano/sem-data`) — e **um componente novo**, a
**Faixa do ano** (handoff §4). Como na S2, quase tudo é **composição** de peças
que a S1 já entregou (Lombada mini, Prateleira, Capa/Capa tipográfica, selo
"2×"); o trabalho novo de verdade é a Faixa do ano e a **camada de seleção**
`timeline.ts`, que concentra toda a regra.

Os mesmos três princípios da S2 guiam as escolhas:

- **As páginas são burras; a regra vive em `src/lib`.** As três páginas chamam
  `getCatalog()` uma vez, pedem o recorte pronto a `timeline.ts` e só posicionam
  componentes. Nenhuma contagem, nota ou ordenação nasce no `.astro`.
- **Zero JS para ler.** As três telas são 100% estáticas (SSG). Não há ilha
  nesta spec — nem a Faixa do ano nem a navegação entre anos precisam de
  JavaScript. A leitura e a navegação funcionam sem JS (handoff §10).
- **Links no formato final, 404 temporário aceito.** As grades das telas Ano e
  Sem data linkam `/obra/{slug}` (rota da S5). Até a S5 existir, esses links dão
  404 — esperado, igual à S2.

> Versões fixadas na S1 e reusadas aqui: `astro@7.4.0`, `zod@4.6.7`,
> `sharp@0.35.5`, `typescript@6.0.3`, Node 22 LTS. **A S3 não adiciona
> dependência nova.** Nenhuma ilha, nenhum framework de UI.

### Mapa de requisitos → seção

| Requisito | Onde é atendido |
|---|---|
| R1 Componente Faixa do ano | §5 Faixa do ano |
| R2 Tela Linha do tempo | §2 Páginas, §3.1, §5 |
| R3 Notas automáticas | §4 Seleção (notas) |
| R4 Bloco "Os primeiros da lista" | §3.1, §4 |
| R5 Tela Ano | §3.2, §4, §6 (mix de idiomas), §7 (grade) |
| R6 Resumo do ano (só aprovado) | §4 (resumo), §8 |
| R7 Navegação entre anos | §4 (vizinhos), §3.2 |
| R8 Tela Sem data | §3.3, §4, §7 |
| R9 Camada de seleção | §4 `timeline.ts` |
| R10 Acessibilidade e desempenho | transversal; resumido em §9 |

## 1. Arquivos que a S3 cria ou toca

A S3 **não mexe em `lib/catalog/`** (a camada de dados da S1 fica intacta) nem
em `home.ts`. Ela adiciona a seleção da linha do tempo, **um** componente novo,
e três páginas.

```text
app/
  src/
    lib/
      timeline.ts          NOVO  recortes da linha do tempo, ano e sem-data
      timeline.test.ts     NOVO  testes (ordem, notas, vizinhos, mix, sem-data)
    components/
      YearBand.astro       NOVO  Faixa do ano (R1); reusada por S4 (país)
    pages/
      linha-do-tempo.astro NOVO  a tela Linha do tempo (R2–R4)
      ano/
        [year].astro       NOVO  a tela Ano, uma por ano com leitura (R5–R7)
        sem-data.astro     NOVO  "Os primeiros da lista" (R8)
```

Decisão de fronteira, igual à S2: **`timeline.ts` é a regra; os `.astro` são
layout.** `timeline.ts` devolve estruturas prontas ("as faixas da linha do
tempo", "os dados do ano X com vizinhos"); as páginas só iteram e posicionam.
Assim a regra roda sob `node --test` (imports relativos dentro de `lib/`) e as
páginas ficam sem lógica.

### Rotas e geração estática

- `linha-do-tempo.astro` → `/linha-do-tempo` (página única).
- `ano/[year].astro` → `/ano/{ano}`, com `getStaticPaths()` emitindo **um
  caminho por ano com ao menos uma leitura** (R5.1). Anos sem leitura não geram
  página. `getStaticPaths` lê os anos de `aggregates.readingsByYear`.
- `ano/sem-data.astro` → `/ano/sem-data`. Como é uma rota literal e `[year]` é
  dinâmica, `sem-data` **não colide** com `[year]` (uma rota estática tem
  precedência sobre a dinâmica no Astro). Mesmo assim, por garantia, nenhum ano
  é a string literal `sem-data`. WHERE não houver leitura sem ano, a página
  pode existir mas fica vazia — então §4 trata isso: `buildUndated` devolve
  `null` e a página aborta a geração com um retorno condicional (ver §3.3).

## 2. As páginas

### Linha do tempo (`/linha-do-tempo`)

```text
<Base title="Linha do tempo · A estante da Lila">
  <header>
    <NavChips active="linha-do-tempo"/>        ← reusa o chip da S2
    h1 "Linha do tempo"
  </header>
  <main>
    {timeline.bands.map(band => <YearBand .../>)}   ← uma faixa por ano (desc)
    {timeline.undated && <a class="undated-block" href="/ano/sem-data">…}
  </main>
</Base>
```

### Ano (`/ano/{ano}`)

```text
<Base title="{ano} · A estante da Lila">
  <header>
    <nav> ‹ {prev}  ·  Linha do tempo  ·  {next} ›     ← R7
  </header>
  <main>
    <h1 class="year-giant">{ano}</h1> + nota curta      ← R5.2, R5.3
    <BigNumbers> leituras · idiomas · autorias · releituras   ← R5.4
    <LanguageMix> barra proporcional (aria-hidden) + legenda  ← R5.5
    {year.summary && <section class="year-summary">…}   ← R6 (hoje some)
    <ol class="grid-3"> CoverCaption por leitura         ← R5.6, R5.7
  </main>
</Base>
```

### Sem data (`/ano/sem-data`)

```text
<Base title="Os primeiros da lista · A estante da Lila">
  <header>
    <nav> ‹ Linha do tempo                               ← só a volta (R8.4)
    <h1>Os primeiros da lista</h1>
  </header>
  <main>
    <ol class="grid-3"> CoverCaption + "nº N da lista"    ← R8.2, R8.3
  </main>
</Base>
```

As três páginas são mobile-first (390px de referência), com `--gutter` lateral
e, no desktop, `max-width` como o Início já faz.

## 3. Composição das telas

### 3.1 Linha do tempo (R2, R3, R4)

- Uma **Faixa do ano** (§5) por item de `timeline.bands`, já na ordem do mais
  recente ao mais antigo (R2.2). A página só itera; a ordem, as notas e a
  contagem vêm prontas de `timeline.ts`.
- Cada faixa recebe: o `year`, o `href` (`/ano/{ano}`), o `count` (leituras do
  ano), a lista de `{ language }` por lombada (já na ordem do caderno) e as
  `notes` (array de strings, possivelmente vazio).
- No fim, WHERE `timeline.undated` não for `null`, um **bloco tracejado** "Os
  primeiros da lista" — um `<a href="/ano/sem-data">` com a borda `--dashed`
  (mesma linguagem do cartão "ver todos" da S2, handoff §4). WHERE não houver
  leitura sem ano, `timeline.undated` é `null` e o bloco não é renderizado
  (R4.3).

### 3.2 Ano (R5, R6, R7)

- **Navegação** no topo: `year.prev` e `year.next` já vêm de `timeline.ts` como
  o ano-alvo ou `null`. Quando há alvo, `<a href="/ano/{alvo}">`; quando `null`
  (extremo), um `<span>` inerte sem link (R7.3, R7.4). O meio é sempre um
  `<a href="/linha-do-tempo">` de volta.
- **Ano gigante** em `--accent` (Bodoni 700, handoff §3.3), e a **nota** curta
  do ano logo abaixo (a primeira nota principal de `year.notes`, se houver —
  R5.3).
- **Big numbers** (reusa a linguagem do handoff §4): quatro números —
  `readings · languages · authors · rereads` — já calculados em `timeline.ts`.
  Como a S1/S2 não criaram um componente `BigNumbers` compartilhado, a S3 monta
  a grade **inline na página** com os tokens (não há peça a reusar ainda); se a
  S4 precisar da mesma grade, extrai-se um componente então (evitar abstração
  prematura).
- **Mix de idiomas** (§6): barra proporcional decorativa + legenda textual.
- **Resumo do ano**: WHERE `year.summary` existir (summary `approved` de scope
  `ano:{ano}`), renderiza o bloco; senão nada (R6). Hoje **nenhum** `ano:`
  existe no catálogo (verificado), então o bloco não aparece em produção.
- **Grade** de 3 colunas (§7), uma peça por leitura, na ordem do caderno.
- **Sem botão "Compartilhar"** nesta spec (R5.9): a página não emite link para
  a retrospectiva (que nasce na S7).

### 3.3 Sem data (R8)

- Reusa o esqueleto da tela Ano, mas em **modo "sem data"**: título "Os
  primeiros da lista", **sem** big numbers, **sem** mix de idiomas, **sem**
  navegação anterior/próximo — só a volta para a Linha do tempo (R8.4).
- A grade (§7) usa `timeline.undated.items`, cada item com o rótulo "nº N da
  lista" (a `sequence`) no lugar do ano (R8.3).
- A página começa com um retorno condicional: `const undated =
  buildUndated(catalog); if (!undated) return Astro.redirect?` — na prática,
  WHERE não houver leitura sem ano, a rota **não é gerada** (R8.6). Como
  `sem-data.astro` é uma página estática única (não usa `getStaticPaths`),
  garantimos isso envolvendo o corpo num `if (undated)`: sem dados, a página
  renderiza vazia; para cumprir R8.6 à risca, o build é condicionado — ver §10,
  nota sobre a geração. (No catálogo atual há leituras sem ano, então a página
  existe; a regra protege builds futuros.)

## 4. Camada de seleção — `timeline.ts` (R9)

Módulo puro que recebe o `Catalog` e devolve os recortes das três telas, já
prontos. Padrão idêntico ao `home.ts`: puro, sem Astro, testável sob
`node --test`; devolve `null` para o que some (R9.4).

```ts
/** Uma lombada da faixa: só o idioma (a cor sai dele no componente). */
type BandSpine = { language: string };

/** Uma Faixa do ano pronta para a Linha do tempo. */
type YearBandData = {
  year: number;
  href: string;          // /ano/{year}
  count: number;         // leituras do ano (releitura conta em cada ano)
  notes: string[];       // 0..2: principal (andamento|mais cheio) + "N releituras"
  spines: BandSpine[];   // uma por leitura, na ordem do caderno
};

/** Um item de grade (tela Ano e Sem data). */
type GridItem = {
  work: WorkView;
  href: string;          // /obra/{slug}
  /** Rótulo "nº N da lista" na tela Sem data; ausente na tela Ano. */
  undatedLabel?: string;
};

type LanguageSlice = { language: string; count: number; pct: number };

type YearData = {
  year: number;
  notes: string[];
  readings: number;      // big number
  languages: number;     // idiomas distintos
  authors: number;       // autorias distintas
  rereads: number;       // leituras que são releitura
  mix: LanguageSlice[];  // barra de idiomas (desc)
  summary: string | null;// resumo aprovado, ou null
  items: GridItem[];     // grade, ordem do caderno, uma peça por leitura
  prev: number | null;   // ano anterior existente, ou null
  next: number | null;   // próximo ano existente, ou null
};

type UndatedData = {
  items: GridItem[];     // ordem do caderno; cada um com undatedLabel
} | null;

export function buildTimeline(catalog: Catalog): YearBandData[] { … }
export function buildYear(catalog: Catalog, year: number): YearData { … }
export function buildUndated(catalog: Catalog): UndatedData { … }
```

### Como cada peça é calculada

- **Faixas (`buildTimeline`)**: parte de `aggregates.readingsByYear` para a
  lista de anos; ordena **decrescente** por ano (R2.2 — note que
  `readingsByYearDesc` ordena por *contagem*, não por ano; aqui queremos por
  ano, então ordenamos explicitamente). Para cada ano, varre as obras e coleta
  as leituras daquele ano como `{ work, sequence, reread, language }`, ordena
  por `sequence` (ordem do caderno) e vira `spines` (R2.3). `count` = número
  dessas leituras (R2.4).
- **Notas (`notes`) — R3**: derivadas, nunca fixadas por ano (R3.1). Regra:
  - `currentYear` = `max(readingsByYear.keys())` (mesma regra do `home.ts`; o
    maior ano com leitura, não o relógio).
  - `fullestYear` = ano com o maior `count`; empate pelo **ano mais recente**.
  - nota **principal**: se `year === currentYear` → `"em andamento"` (tem
    prioridade, R3.4); senão se `year === fullestYear` → `"o ano mais cheio da
    estante"`; senão nenhuma.
  - nota **complementar**: `rereadsInYear > 0` → `"{n} releitura"` /
    `"{n} releituras"` (plural correto em pt-BR).
  - `notes` concatena principal (se houver) + complementar (se houver); pode
    ter 0, 1 ou 2 entradas (R3.6, R3.7). As duas coexistem.
- **Dados do ano (`buildYear`) — R5**: filtra as leituras do ano; `readings` =
  nº de leituras; `rereads` = nº dessas leituras com `reread === true`;
  `languages` = idiomas originais distintos das obras; `authors` = slugs de
  autoria distintos; `mix` = contagem por idioma (desc), com `pct` arredondado
  para a barra; `items` = uma peça por leitura, ordenada por `sequence`
  (R5.6). `notes` reusa a mesma regra das faixas (R5.3).
- **Resumo (`summary`) — R6**: a S3 precisa dos summaries de ano, mas o
  `model.ts` da S1 só extrai bios (`autoria:`). Decisão: `timeline.ts`
  **não** relê disco; recebe os summaries via `Catalog`. Como `Catalog` hoje
  não expõe `summaries`, a S3 faz **uma adição mínima e retrocompatível** na
  camada de dados: `buildModel` passa a guardar um índice
  `approvedSummaryByScope: Map<string,string>` (ou expõe os summaries
  aprovados), e `timeline.ts` lê `ano:{year}` dele. Isso mantém a regra "app só
  lê o que `getCatalog()` entrega" (R9) e não duplica a lógica de aprovação
  (R6.3). Ver §4.1.
- **Vizinhos (`prev`/`next`) — R7**: a partir da lista ordenada de anos
  existentes, `prev` = maior ano `< year` (ou `null`); `next` = menor ano
  `> year` (ou `null`). Salta pelos anos que existem (R7.2), inerte nos
  extremos (R7.3).
- **Sem data (`buildUndated`) — R8**: as leituras com `year === null`,
  resolvidas à sua obra, ordenadas por `sequence`; cada item com
  `undatedLabel = "nº {sequence} da lista"`. WHERE não houver nenhuma, devolve
  `null` (R8.6, R9.4).

### 4.1 Pequena extensão da camada de dados (summaries de ano)

Hoje `model.ts` lê `summaries` só para a bio de autoria (`autoria:`), e
`index.ts` não expõe `summaries` no `Catalog`. Para o resumo de ano (R6) sem
quebrar a convenção "app só lê `getCatalog()`" nem reinventar a aprovação:

- `buildModel` passa a montar também um `Map` dos summaries **aprovados** por
  scope (reusando o mesmo laço que já lê `raw.summaries`), e o expõe no modelo
  (ex.: `approvedSummaryByScope`).
- `timeline.ts` consulta `approvedSummaryByScope.get("ano:" + year)`; `null`
  quando não há (R6.2).

Essa é a única mudança na camada de dados da S1, aditiva e coberta por teste. A
alternativa (ler `summaries.json` direto no `timeline.ts`) violaria R9 (relê
disco) e duplicaria a regra de aprovação — descartada.

## 5. Componente Faixa do ano — `YearBand.astro` (R1)

Peça genérica, **sem conhecimento do catálogo** (R1.5). Recebe tudo pronto de
quem a usa (na S3, a página da Linha do tempo; na S4, a prateleira por país).

```
Props: {
  label: string;          // o ano ("2024") na linha do tempo; nome do país na S4
  href: string;           // destino da linha inteira
  count: number;          // "N ›"
  notes?: string[];       // 0..n notas curtas (vazio na S4)
  spines: { language: string }[];  // uma lombada por item, na ordem recebida
}
```

Estrutura e comportamento (handoff §4):

- A **linha inteira é um único `<a href>`** (R1.4), com alvo de toque adequado
  (handoff §3.4). Dentro: o `label` em Bodoni, as `notes` (se houver) em texto
  secundário, e `count` + "›" em `--accent`.
- Abaixo, a **fileira de lombadas**: para cada `spine`, um `<Spine
  language index={i} />` (componente da S1 — altura determinística pelo índice,
  cor do idioma) apoiado numa `<Shelf/>` (R1.2, R1.3). A fileira é larga; se
  passar da largura, **quebra ou corta** sem rolagem (a faixa não é um
  carrossel) — decisão em §11.
- A fileira é **decorativa** (`aria-hidden`): o ano e a contagem já estão em
  texto no link (R1.6). As lombadas não carregam informação que falte em texto.
- Sem JS: é só um link com spans e as peças da S1; nada a hidratar (handoff
  §10).

`YearBand` não decide notas nem ordem — recebe tudo de `timeline.ts` (R1.5).
Isso é o que a torna reusável pela S4 (lá o `label` é o país e `notes` é
vazio).

## 6. Mix de idiomas (tela Ano) — R5.5

- Uma barra horizontal: um segmento por idioma de `year.mix`, largura =
  `pct`, cor = cor do idioma (reusa `languageColor` da S1). A barra é
  **decorativa** (`aria-hidden`).
- Logo abaixo (ou como `aria-label`/legenda em texto), a lista "idioma — N",
  para o dado existir fora da cor (R10.2). Montada inline na página com tokens;
  não é peça reusável ainda.

## 7. Grade de 3 colunas — telas Ano e Sem data (R5.6, R8.2)

- Um `<ol class="grid-3">` (`grid-template-columns: repeat(3, 1fr)` com
  `--grid-gap-x`/`--grid-gap-y` dos tokens), um `<li>` por `GridItem`, na ordem
  do caderno (R5.6).
- Cada item reusa **`CoverCaption`** (S1/S2) com `size="rail"`? Não: a grade
  pede `size="grid"` do `Cover`. `CoverCaption` hoje só aceita `hero|rail`.
  Decisão: **estender `CoverCaption` para aceitar `size="grid"`** (passa adiante
  ao `Cover`, que já suporta `grid`), mudança aditiva e retrocompatível; a
  grade fica com capas 2:3 na largura da coluna. Alternativa (novo componente
  de grade) descartada — evita duplicar o item de capa.
- O selo "2×" sai do `rereadBadge` que `CoverCaption` já repassa ao `Cover`
  (R5.7).
- Na tela **Sem data**, abaixo (ou no lugar) da legenda, o texto "nº N da
  lista" (`undatedLabel`) — a mesma peça de capa, com um rótulo a mais. Para não
  inchar `CoverCaption` com um caso só desta tela, o rótulo "nº N da lista" é
  renderizado **pela página**, ao lado do `CoverCaption`, dentro do `<li>`
  (R8.3). Ver §11.

## 8. Resumo do ano — R6

- WHERE `year.summary` existir, um bloco com o texto (serifa, largura de
  leitura confortável). WHERE `null`, nada é renderizado (R6.2) — a decisão de
  mostrar/omitir mora em `timeline.ts` (devolve `null`), não em condicional
  espalhada.
- Verificado: o catálogo **não tem** nenhum summary `ano:` hoje, então o bloco
  não aparece em produção; a regra protege o dia em que a frente de F2 criar
  resumos de ano.

## 9. Acessibilidade e desempenho (R10) — transversal

- Navegação com `<a href>`: faixas, itens da grade, setas de ano (quando há
  alvo), volta para a linha do tempo. Setas inertes nos extremos são `<span>`
  sem link (R7.3, R7.4). Nenhum controle só-ícone sem rótulo (R10.1).
- Decorativos com `aria-hidden`: a fileira de lombadas da faixa e a barra do mix
  de idiomas; o dado (ano, contagem, idioma—N) existe em texto ao lado
  (R10.2).
- Capas herdam da S1: `loading="lazy"`, dimensões fixas 2:3, capa tipográfica
  como fallback; `lang`/`dir` dos títulos não latinos (R10.3, R10.4).
- Contraste: tokens de §3.1 sobre `--ground`; texto sobre cor de idioma usa o
  par de §3.2 (R10.5).
- **Zero JS para ler ou navegar** (R10.6): nenhuma ilha nesta spec. As três
  telas são estáticas puras.

## 10. Fluxo de build e verificação

- `npm run check` (astro check + tsc) cobre os tipos novos de `timeline.ts`, a
  extensão de `CoverCaption` (`grid`) e a pequena adição ao modelo (summaries
  aprovados por scope).
- `npm test` (node --test) roda `timeline.test.ts` somando aos 54 testes atuais
  (32 S1 + 13 home + 9 search): ordem das faixas (ano desc), notas (andamento,
  mais cheio, releituras, prioridade e coexistência), vizinhos prev/next
  saltando buracos e inertes nos extremos, mix de idiomas, resumo aprovado
  presente/ausente, "sem data" por sequence e `null` quando não há.
- `npm run build` gera `/linha-do-tempo`, uma `/ano/{ano}` por ano com leitura
  e `/ano/sem-data`; o portão de CI (F4) roda check + test + build antes de
  publicar.
- **Geração de `/ano/sem-data` (R8.6):** como é página estática única, o corpo
  fica sob `if (undated)`. Se um dia não houver leitura sem ano, a página
  renderiza vazia — aceitável, pois a Linha do tempo também deixa de linká-la
  (o bloco some, §3.1). Para "a rota não existir" à risca sem `getStaticPaths`,
  a alternativa seria transformar `sem-data` num parâmetro de `[year]`; fica
  anotado como melhoria se algum dia o catálogo zerar os sem-ano (improvável:
  são os primeiros do caderno).
- Verificação visual: o preview do Pages gerado pelo PR (percorrer a linha do
  tempo → abrir um ano → navegar prev/next → chegar em sem-data), no desktop e
  no celular, como nas specs anteriores.

## 11. Decisões e alternativas

| Decisão | Alternativa descartada | Porquê |
|---|---|---|
| Faixa do ano genérica (`label`, `notes`, `spines`), sem catálogo | faixa que conhece `WorkView`/ano | S4 reusa a mesma peça para país; o componente só sabe desenhar |
| Regra toda em `timeline.ts`, páginas burras | filtros e notas no `.astro` | mantém a página burra e a regra testável sob `node --test` (convenção S1/S2) |
| Faixa ordenada por **ano** desc | reusar `readingsByYearDesc` (por contagem) | a linha do tempo é cronológica; `readingsByYearDesc` ordena por quantidade, serve para "ano mais cheio", não para o eixo |
| Uma lombada e uma peça **por leitura** | por obra | coerente com "releitura conta em cada ano" (modelo S1); o ano reflete o que foi lido nele |
| Navegação salta pelos anos existentes | `ano ± 1` | os anos têm buracos; `±1` cairia em 404; saltar reflete a estante real (R7.2) |
| Notas derivadas, principal + complementar | uma nota só, ou texto por ano | as regras do handoff §6.2 são todas automáticas; coexistir dá mais informação sem curadoria manual |
| Estender `CoverCaption` com `size="grid"` | novo componente de grade | `Cover` já suporta `grid`; evita duplicar o item de capa; mudança aditiva |
| Rótulo "nº N da lista" na página, não no `CoverCaption` | parâmetro novo no `CoverCaption` | é um caso exclusivo da tela Sem data; não inchar o item de capa compartilhado |
| Summaries aprovados por scope expostos pelo modelo | `timeline.ts` lê `summaries.json` | ler disco violaria R9 e duplicaria a regra de aprovação; a adição ao modelo é mínima e aditiva |
| Big numbers e mix inline na página (sem componente) | extrair `BigNumbers`/`LanguageMix` agora | S4 ainda não existe; evitar abstração prematura — extrai-se quando houver o segundo uso |
| Sem botão "Compartilhar {ano}" | stub desabilitado | a retrospectiva nasce na S7; link morto confunde (R5.9) |
| Zero JS (sem ilha) | setas/animações com JS | nada aqui precisa de interação; tudo é link estático (R10.6) |

## 12. Riscos e limites conhecidos

- **404 temporários.** As grades linkam `/obra/{slug}` (S5). No preview do PR,
  clicar numa capa leva a 404 — esperado, igual à S2; some quando a S5 entrar.
- **Capas de obra ainda ausentes.** A grade mostra a capa tipográfica para toda
  obra (frente de F2). Quando as capas entrarem, `Cover` as usa sem mudar
  contrato; a grade não muda.
- **Resumos de ano ainda ausentes.** Nenhum `ano:` no catálogo; o bloco de
  resumo some. A regra já está pronta para quando a F2 criar resumos.
- **Faixa larga em anos cheios.** Um ano com muitas leituras gera muitas
  lombadas; a faixa quebra em linha ou corta (§5/§11), nunca vira carrossel. Se
  ficar ruim visualmente, ajusta-se o layout da faixa sem mudar o contrato do
  componente.
- **`/ano/sem-data` como página estática única.** A rota é gerada enquanto
  houver leitura sem ano (há hoje). O caso "catálogo sem nenhum sem-ano" está
  tratado como página vazia + bloco omitido na linha do tempo; migrar para
  `getStaticPaths` fica anotado caso um dia seja preciso não gerar a rota.

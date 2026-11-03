# Tarefas — Linha do tempo (S3)

Referências: [`requirements.md`](requirements.md) · [`design.md`](design.md).

Cada tarefa de código é incremental e termina **verde**: `npm run check`
(tipos) passa e, quando a tarefa tem testes, `npm test` (runner nativo do Node)
passa. Nada chama rede em build nem em teste; nenhuma tarefa escreve em
`catalog/`. Convenção da S1/S2 mantida: imports relativos dentro de `src/lib`,
alias `@/` nos `.astro`.

A entrega visível da S3 é `/linha-do-tempo`, `/ano/{ano}` e `/ano/sem-data`,
provadas no preview do Pages gerado pelo PR. Trabalho normal: branch
(`feat/linha-do-tempo`, já criada) → PR (preview) → merge em `main` (deploy de
produção).

Lembrete de escopo: as grades linkam `/obra/{slug}` (S5) — `href` no formato
final, **404 temporário esperado** no preview. Sem botão "Compartilhar" (S7).
Nenhuma ilha: as três telas são estáticas puras.

Dependências (tarefas na mesma chave podem ir em paralelo):

```
1 → 2 → {3, 4} → {5, 6, 7} → {8, 9, 10} → 11 → 12
```

## Extensão mínima da camada de dados (aprovada no design §4.1)

- [x] 1. Summaries aprovados por scope no modelo (`src/lib/catalog/model.ts`, `index.ts`)
  - [x] 1.1 Em `buildModel`, reusar o laço que já lê `raw.summaries` para montar também `approvedSummaryByScope: Map<string,string>` (todo summary `approved`, chaveado pelo `scope` completo, ex.: `ano:2024`, `autoria:han-kang`). Expor o mapa no `CatalogModel`.
    - _Requisitos: 6.1, 6.3_
  - [x] 1.2 Garantir que a mudança é **aditiva**: a extração de bio (`autoria:`) existente continua igual; `getCatalog()`/`Catalog` passam a expor `approvedSummaryByScope` sem quebrar nada. _(O campo entra no `CatalogModel`, herdado pelo `Catalog`; bio intacta.)_
    - _Requisitos: 9.1_
  - [x] Fim: estender `src/lib/catalog/model.test.ts` cobrindo que um summary `ano:{ano}` `approved` entra no mapa, um não-aprovado fica de fora, e a bio de autoria segue intacta. _(2 testes novos; 56 verdes.)_
    - _Requisitos: 6.1, 6.2, 6.3_

## Camada de seleção (regra, testável)

- [x] 2. Recortes da linha do tempo (`src/lib/timeline.ts`) (design §4)
  - [x] 2.1 Tipos `BandSpine`, `YearBandData`, `GridItem`, `LanguageSlice`, `YearData`, `UndatedData`; três funções puras `buildTimeline`, `buildYear`, `buildUndated`. Sem dependências de Astro.
    - _Requisitos: 9.1, 9.2, 9.3_
  - [x] 2.2 `buildTimeline(catalog)`: anos de `readingsByYear`, ordenados por **ano desc** (não por contagem); por ano, as leituras `{ work, sequence, reread, language }` ordenadas por `sequence` → `spines`; `count` = nº de leituras; `href` = `/ano/{ano}`.
    - _Requisitos: 2.2, 2.3, 2.4, 2.5_
  - [x] 2.3 Notas automáticas: `currentYear` = `max(readingsByYear.keys())`; `fullestYear` = maior `count` (empate pelo ano mais recente); principal "em andamento" (prioridade) → senão "o ano mais cheio da estante"; complementar "{n} releitura(s)" quando houver releitura no ano; `notes` com 0..2 itens, as duas podem coexistir. Nenhum texto fixado por ano.
    - _Requisitos: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_
  - [x] 2.4 `buildYear(catalog, year)`: big numbers (`readings`, `languages` distintos, `authors` distintos, `rereads`); `mix` por idioma (desc, com `pct`); `items` uma peça por leitura em ordem de `sequence` com `href=/obra/{slug}`; `notes` pela mesma regra de 2.3; `summary` = `approvedSummaryByScope.get("ano:"+year) ?? null`.
    - _Requisitos: 5.3, 5.4, 5.5, 5.6, 5.7, 6.1, 6.2_
  - [x] 2.5 Vizinhos: `prev` = maior ano `< year` existente (ou `null`); `next` = menor ano `> year` existente (ou `null`). Salta pelos anos que existem; `null` nos extremos.
    - _Requisitos: 7.2, 7.3_
  - [x] 2.6 `buildUndated(catalog)`: leituras com `year === null`, resolvidas à obra, ordenadas por `sequence`; cada item com `undatedLabel = "nº {sequence} da lista"` e `href=/obra/{slug}`; devolve `null` quando não há nenhuma.
    - _Requisitos: 8.2, 8.3, 8.6, 9.4_
  - [x] Fim: `src/lib/timeline.test.ts` com catálogo de exemplo (13 testes verdes): faixas em ano desc; nota de andamento tem prioridade sobre "mais cheio"; "mais cheio" com empate pelo ano recente; "N releituras" no plural certo; coexistência das duas notas; prev/next saltando buracos e `null` nos extremos; `mix`/big numbers por leitura; `summary` presente só quando aprovado; "sem data" por sequence e `null` quando vazio.
    - _Requisitos: 2.2, 3.2, 3.3, 3.4, 3.5, 5.4, 6.2, 7.2, 7.3, 8.6_

## Componente novo e ajustes de componente

- [x] 3. `YearBand.astro` — Faixa do ano (design §5) (R1)
  - [x] 3.1 Props tipadas `{ label, href, count, notes?, spines }`; a linha inteira é um único `<a href>` com alvo de toque adequado; `label` em Bodoni, `notes` em texto secundário, `count`+"›" em `--accent`. Sem conhecimento do catálogo.
    - _Requisitos: 1.1, 1.4, 1.5_
  - [x] 3.2 Fileira de lombadas: um `<Spine language index={i} />` (S1) por `spine`, na ordem recebida, apoiado numa `<Shelf/>` (S1); cor pela do idioma. A fileira é `aria-hidden`; ano e contagem existem em texto no link.
    - _Requisitos: 1.2, 1.3, 1.6_
  - _Requisitos: 1.1–1.6_

- [x] 4. Estender `CoverCaption.astro` para `size="grid"` (design §7)
  - Aceitar `size: "hero" | "rail" | "grid"` e repassar ao `Cover` (que já suporta `grid`); mudança aditiva e retrocompatível (hero/rail inalterados). O selo "2×" segue vindo de `rereadBadge`. _(`.size-grid { width: 100% }` para preencher a coluna.)_
  - _Requisitos: 5.6, 5.7, 8.2, 8.5_

## Montagem das telas

- [x] 5. `src/pages/linha-do-tempo.astro` (design §2, §3.1) (R2–R4)
  - [x] 5.1 `Base` + `header` (`NavChips active="linha-do-tempo"`, `h1` "Linha do tempo"); `getCatalog()` uma vez + `buildTimeline()`. Uma `YearBand` por faixa, do mais recente ao mais antigo. _(HTML: 2026→2014.)_
    - _Requisitos: 2.1, 2.2, 2.6, 2.7_
  - [x] 5.2 Ao fim, WHERE `buildUndated` indicar que há leitura sem ano, um bloco tracejado (`--dashed`) `<a href="/ano/sem-data">` "Os primeiros da lista"; omitido quando não há sem-data.
    - _Requisitos: 4.1, 4.2, 4.3, 4.4_
  - [x] 5.3 Mobile-first 390px (`--gutter`, alvos `--tap`), `max-width` no desktop; legível sem JS. _(Mesmo padrão do Início da S2.)_
    - _Requisitos: 2.6, 10.6_
  - _Requisitos: 2.1–2.7, 4.1–4.4_

- [x] 6. `src/pages/ano/[year].astro` (design §2, §3.2, §6, §7, §8) (R5–R7)
  - [x] 6.1 `getStaticPaths()` emitindo um caminho por ano com leitura (de `readingsByYear`); `buildYear(catalog, year)` no corpo. _(13 anos: 2014–2026.)_
    - _Requisitos: 5.1_
  - [x] 6.2 Navegação no topo: `prev`/`next` como `<a href="/ano/{alvo}">` quando há alvo, `<span>` inerte quando `null`; meio `<a href="/linha-do-tempo">` de volta; operável por teclado. _(2014 sem prev, 2026 sem next, confirmado.)_
    - _Requisitos: 7.1, 7.3, 7.4_
  - [x] 6.3 Ano gigante em `--accent` (Bodoni 700) + nota curta (primeira nota principal, se houver).
    - _Requisitos: 5.2, 5.3_
  - [x] 6.4 Big numbers (leituras · idiomas · autorias · releituras) inline com tokens; mix de idiomas como barra proporcional `aria-hidden` + legenda "idioma — N" em texto.
    - _Requisitos: 5.4, 5.5, 10.2_
  - [x] 6.5 Bloco de resumo só WHERE `year.summary` não for `null` (hoje some); sem título vazio quando ausente. _(Nenhum `.summary` em dist — correto.)_
    - _Requisitos: 6.1, 6.2_
  - [x] 6.6 Grade de 3 colunas (`grid-3`), um `CoverCaption size="grid"` por leitura na ordem do caderno, `/obra/{slug}`, selo "2×" quando releitura. Sem botão "Compartilhar".
    - _Requisitos: 5.6, 5.7, 5.9_
  - _Requisitos: 5.1–5.9, 6.1–6.2, 7.1–7.4_

- [x] 7. `src/pages/ano/sem-data.astro` (design §3.3, §7) (R8)
  - [x] 7.1 Corpo sob `const undated = buildUndated(catalog); if (undated) { … }`; título "Os primeiros da lista"; só a volta para a Linha do tempo (sem prev/next, sem big numbers, sem mix).
    - _Requisitos: 8.1, 8.4, 7.5_
  - [x] 7.2 Grade de 3 colunas, `CoverCaption size="grid"` por leitura na ordem do caderno + rótulo "nº N da lista" renderizado pela página ao lado do item; `/obra/{slug}`; selo "2×" quando couber. _(nº 1…N em ordem de sequence.)_
    - _Requisitos: 8.2, 8.3, 8.5_
  - _Requisitos: 8.1–8.6_

## Verificação de ponta a ponta

- [x] 8. Acessibilidade e desempenho (R10) — conferir nas três telas
  - Controles reais (`<a href>` em faixas, itens, setas com alvo, volta; setas inertes como `<span>` com `aria-hidden`); decorativos `aria-hidden` (fileira da faixa e barra do mix — confirmado em dist) com o dado em texto ao lado; capas `lazy`/2:3; `lang`/`dir` dos títulos não latinos herdados da S1; contraste pelos tokens/§3.2; **zero `<script>`** nas três telas (confirmado em dist).
  - _Requisitos: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

- [x] 9. Build e testes
  - [x] 9.1 `npm run check` limpo com os tipos novos (`timeline.ts`, `CoverCaption` com `grid`, `approvedSummaryByScope`); `npm test` verde. _(0 erros; 69 testes verdes: 56 + 13 timeline.)_
    - _Requisitos: 9.3_
  - [x] 9.2 `npm run build` contra o catálogo real: código 0; `/linha-do-tempo` gerada; uma `/ano/{ano}` por ano com leitura (13: 2014–2026); `/ano/sem-data` gerada; nenhuma rede. _(17 páginas no total.)_
    - _Requisitos: 2.1, 5.1, 8.1_
  - [x] 9.3 Conferir que o resumo não aparece (nenhum `ano:` no catálogo) e que a linha do tempo abre com as faixas em ordem decrescente de ano. _(Nenhum `.summary` em dist; faixas 2026→2014.)_
    - _Requisitos: 6.2, 2.2_

- [x] 10. Prova no preview (desktop + celular)
  - `astro preview`: `/linha-do-tempo`, `/ano/2024`, `/ano/2026`, `/ano/2014`, `/ano/sem-data` todas **200**. Capturas conferidas: linha do tempo (faixas coloridas por idioma sobre a prateleira, notas, contagem "N ›" em --accent), Ano (ano gigante em --accent, big numbers, mix de idiomas com legenda, grade de 3 colunas) e Sem data ("nº N da lista" em sequence). 404 esperados de `/obra/{slug}` (S5) anotados.
  - _Requisitos: 2.1, 5.1, 7.1, 8.1_

## Fechamento

- [ ] 11. PR e merge
  - PR aberto da branch `feat/linha-do-tempo` (gera preview no Pages). Aguarda revisão/aprovação/teste da Lila; merge em `main` dispara o deploy de produção. _(Conferência de celular fica para o preview do Pages, num aparelho.)_
  - _Requisitos: 2.1_

- [x] 12. Documentação
  - `docs/ROADMAP.md` (S3 ✓, dívida de rota quitada), `AGENTS.md` (estado atual: S3 concluída, próximo S4) e `docs/plans/handover-s3-s4.md` (YearBand pronta para a prateleira por país; `approvedSummaryByScope` para o resumo de país; destinos ainda em 404 até S4/S5).

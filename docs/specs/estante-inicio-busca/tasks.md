# Tarefas — Estante: Início e busca (S2)

Referências: [`requirements.md`](requirements.md) · [`design.md`](design.md).

Cada tarefa de código é incremental e termina **verde**: `npm run check`
(tipos) passa e, quando a tarefa tem testes, `npm test` (runner nativo do Node)
passa. Nada chama rede em build nem em teste; nenhuma tarefa escreve em
`catalog/` nem toca `lib/catalog/` (a camada de dados da S1 fica intacta).
Convenção da S1 mantida: imports relativos dentro de `src/lib`, alias `@/` nos
`.astro`.

A entrega visível da S2 é a tela `/` (Início) com busca, provada no preview do
Pages gerado pelo PR. Trabalho normal: branch → PR (preview) → merge em `main`
(deploy de produção).

Lembrete de escopo: todos os destinos de navegação e de busca, exceto a própria
`/`, nascem em S3–S5 — os `href` são emitidos no formato final e **404
temporário é esperado** no preview.

Dependências (tarefas na mesma chave podem ir em paralelo):

```
1 → 2 → {3, 4} → 5 → 6 → {7, 8, 9, 10} → 11 → 12
         (busca: 3 → 13 → 14)
```

## Camada de seleção (regra, testável)

- [x] 1. Recortes do Início (`src/lib/home.ts`)
  - [x] 1.1 `buildHome(catalog, railCap = 20)` puro, devolvendo `HomeData` (design §4): `currentYear`, `recurringAuthors`, `themeRails`, `rereads`, `yearBars`. Seções que somem devolvem `null`.
    - _Requisitos: 1.4, 1.5_
  - [x] 1.2 "Em {ano atual}": ano = maior ano **com leitura** (`max(readingsByYear.keys())`, não o relógio); obras com leitura naquele ano, ordenadas por `sequence`; destino `/ano/{ano}`; `null` se o ano não tiver leitura.
    - _Requisitos: 3.1, 3.2, 3.3, 3.4, 3.6_
  - [x] 1.3 "Quem sempre volta": autorias com `count >= 3` de `readingsByAuthorDesc`, resolvidas em `AuthorView`, ordem decrescente estável; `null` se nenhuma atingir o corte.
    - _Requisitos: 4.1, 4.3, 4.5_
  - [x] 1.4 Temas: os 4 primeiros de `worksByThemeDesc` (0..4), cada um com suas obras (teto `railCap`, `total` real), destino `/tema/{slug}`.
    - _Requisitos: 5.1, 5.4, 5.5_
  - [x] 1.5 "Lidos duas vezes": obras com `reread === true`, uma por obra, ordenadas por nº de leituras e título; `null` se não houver releitura.
    - _Requisitos: 6.1, 6.2, 6.3_
  - [x] 1.6 `yearBars`: série por ano **só com anos conhecidos** (exclui "sem data"); ano atual marcável para destaque.
    - _Requisitos: 6.4, 6.6_
  - Fim: `src/lib/home.test.ts` com catálogo de exemplo cobrindo 1.2–1.6 (ano atual é o maior com leitura; corte de 3+; no máx. 4 temas na ordem dos agregados; releitura uma vez; seções vazias → `null`; `yearBars` sem "sem data").
    - _Requisitos: 3.2, 4.1, 5.1, 6.2, 6.6_

## Componente Carrossel

- [x] 2. `Carousel.astro` (design §5)
  - [x] 2.1 Fileira com `scroll-snap` nativo, última peça cortada (sangra até a borda; `padding-right` < largura de item), sem bolinhas/contador/barra; slot para os itens.
    - _Requisitos: 2.1, 2.2, 2.6_
  - [x] 2.2 Título-link e cartão final tracejado "ver todos (N)" (`--dashed`), ambos `<a href>` para a mesma página completa; `N` = `total`.
    - _Requisitos: 2.3, 2.4_
  - [x] 2.3 Desktop: setas ‹ › fora das capas como `<button aria-label>` com `scrollBy` (script mínimo inline, não ilha de framework); ocultas sem JS; rolagem por toque/teclado funciona sem JS.
    - _Requisitos: 2.6, 2.7_
  - [x] 2.4 Props tipadas (`title`, `href`, `total`, `labelAllPrefix?`); sem conhecimento do catálogo; teto aplicado por quem preenche o slot.
    - _Requisitos: 2.5, 2.8_
  - _Requisitos: 2.1–2.8_

## Itens de carrossel e cartões

- [x] 3. `CoverCaption.astro`
  - `Cover` (S1) dentro de `<a href>`, com título (e autoria) em **texto sob a capa**, `line-clamp` de 2 linhas; tamanho de capa parametrizável (hero/rail); herda capa tipográfica, selo "2×" e `lang`/`dir` da S1.
  - _Requisitos: 3.1, 3.5, 5.2, 6.1, 9.2, 9.3_

- [x] 4. `AuthorChip.astro`
  - `InitialsAvatar` (foto derivada quando houver, senão iniciais) + nome em texto, dentro de `<a href="/autoria/{slug}">`.
  - _Requisitos: 4.2, 4.4_

- [x] 5. `TimelineCard.astro` (design §6)
  - Cartão `<a href="/linha-do-tempo">` com rótulo "Linha do tempo" em texto e mini-gráfico de barras por ano (`yearBars`), `--bar-neutral` com ano atual em `--accent`; barras `aria-hidden`; sem dia/mês, sem "sem data" como ano.
  - _Requisitos: 6.4, 6.5, 6.6_

## Cabeçalho

- [x] 6. `NavChips.astro` (design §8)
  - `h1` "A estante da Lila" (`.t-screen-title`); chips de 44px: `Estante` ativo (`--accent`/`--accent-ink`, `aria-current`), `Atlas` → `/atlas`, `Linha do tempo` → `/linha-do-tempo` (`<a href>`, 404 temporário); operável por teclado.
  - _Requisitos: 8.1, 8.2, 8.3, 8.4_

## Busca

- [x] 13. Normalização e índice (`src/lib/search.ts`)
  - [x] 13.1 `fold(text)` (NFD → remove diacríticos → minúsculo → pontuação vira espaço) e `matches(entry, foldedQuery)`; tipo `SearchEntry`. Módulo puro, sem dependências. _(Acréscimo: `fold` recompõe em NFC para o Hangul voltar à forma canônica — ver nota no fim.)_
    - _Requisitos: 7.2, 7.3_
  - [x] 13.2 `src/lib/search.test.ts`: "josé"→"jose", "SARAMAGO"→"saramago", acento no meio, título CJK preservado, match por substring de palavra.
    - _Requisitos: 7.3, 7.5_

- [x] 14. Endpoint estático (`src/pages/search-index.json.ts`)
  - `GET` que lê `getCatalog()` e emite uma entrada por obra (chaves: título pt-BR + original + romanização) e por autoria (nome), via `fold`; sai como `/search-index.json`; regenera a cada build sem passo manual.
  - _Requisitos: 7.1, 7.2, 7.9_

- [x] 7. Ilha de busca (`src/components/SearchBox.astro`)
  - Markup estático: `<form role="search">`, `<label for>`, `<input>` de ~52px com ícone de lupa, `<ul>` de resultados vazio; `<script>` vanilla que faz `fetch('/search-index.json')` **uma vez** no primeiro foco, filtra com `fold`+`matches` a cada tecla (debounce leve, limite de ~20 resultados) e injeta `<a href>`; sem framework, sem API externa; `aria-label` no ícone; resto da página intacto sem JS.
  - _Requisitos: 7.4, 7.5, 7.6, 7.7, 7.8_

## Montagem do Início

- [x] 8. `index.astro` — a tela `/` (design §2, §3)
  - [x] 8.1 Substituir o placeholder: `Base` + `header` (`h1`, `SearchBox`, `NavChips`) + `main`; chamar `getCatalog()` uma vez e `buildHome()` para os recortes.
    - _Requisitos: 1.1, 1.3, 1.4, 1.5, 1.6_
  - [x] 8.2 Seções na ordem do §6.1, cada uma só se o recorte não for `null`: "Em {ano atual}" (hero), "Quem sempre volta" (AuthorChip), 4× tema (CoverCaption), "Lidos duas vezes" (CoverCaption com selo), `TimelineCard`.
    - _Requisitos: 1.5, 3.6, 4.5, 5.5, 6.3_
  - [x] 8.3 Mobile-first 390px: `--gutter`, alvos `--tap`, `max-width` no desktop com carrosséis sangrando até a borda; conteúdo legível sem JS.
    - _Requisitos: 1.2, 1.6, 9.6_
  - _Requisitos: 1.1–1.6_

## Verificação de ponta a ponta

- [ ] 11. Build e testes
  - [x] 11.1 `npm run check` limpo com os tipos novos; `npm test` verde (home + search somados aos 32 da S1). _(54 testes: 32 S1 + 13 home + 9 search.)_
    - _Requisitos: 1.2_
  - [x] 11.2 `npm run build` contra o catálogo real: código 0; `/` gerada; `/search-index.json` emitido com ~517 entradas (302 obras + 215 autorias); nenhuma rede. _(517 entradas confirmadas; preview serviu `/` 200 e `/search-index.json` 200 application/json.)_
    - _Requisitos: 7.1, 7.9, 1.2_
  - [x] 11.3 Acessibilidade/desempenho: só a busca carrega `<script>`; carrosséis rolam sem JS; capas `lazy`/2:3; decorativos `aria-hidden`; chip ativo `aria-current`; contraste pelos tokens/§3.2. _(Conferido no browser do desktop e do celular.)_
    - _Requisitos: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_
  - [x] 11.4 Busca sem JS: com JavaScript desligado, `/` continua legível e navegável e o campo não quebra a página.
    - _Requisitos: 7.8, 1.2_

- [x] 12. Fechamento
  - [x] 12.1 PR #2 (preview no Pages); Início conferido no preview e em produção (desktop + celular); 404 esperados dos destinos de S3–S5 anotados.
    - _Requisitos: 1.1_
  - [x] 12.2 Atualizar `docs/ROADMAP.md` (S2 concluída) e nota de handover para a S3 (`linha-do-tempo`), listando os destinos que a S2 já linka e esperam página.

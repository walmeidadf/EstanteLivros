# Handover — fim da S5, próximos passos

Escrito ao concluir a S5 (`obra-autoria`). Com ela, **todas as telas de leitura
da F3 estão no ar** e nenhuma rota do app cai mais no Início. O que resta da F3
é só PWA (S6) e compartilhar/retrospectiva (S7); o caminho recomendado agora é
voltar à **F2** (enriquecimento) corrigindo o que o app mostra.

## Onde o projeto está (resumo)

- **S1–S5 concluídas e no ar** (`liliane.prateleira.site`). A S5 foi mergeada em
  três PRs: #7 (páginas), #8 (alinhar cabeçalhos no desktop) e #9 (big numbers
  em faixa no cabeçalho de Autoria).
- `main` sincronizada, worktree limpa. Pasta `temp/` (no `.gitignore`) para
  artefatos descartáveis, nunca `/tmp`.
- Números: **151 testes** verdes, `npm run check` limpo, build do catálogo real
  com **1080 páginas** (563 da S4 + 517 da S5: 302 obra + 215 autoria).

## O que a S5 entregou

- **Obra (`/obra/{slug}`, 302)** e **Autoria (`/autoria/{slug}`, 215)**, os
  destinos de quase todos os links. Fecha a **última dívida de rota** (capas,
  avatares e busca abrem a página certa).
- Regra em `app/src/lib/work-page.ts` e `author-page.ts` (puros, testados);
  páginas `.astro` burras; **sem `<script>`** nas duas telas.
- **`route-integrity.ts`**: coleta todo `href` `/obra` e `/autoria` que home,
  timeline, atlas e a busca emitem e, no teste, confere contra os slugs do
  catálogo (0 órfãos nos 2878 links reais).

### Peças novas e reusáveis (para a S6/S7 e a F2)

- **`work-page.ts`** (`buildWorkPage`): título original (via
  `originalTitlePresentation`), ficha, leituras, temas, edição e registro.
  Helper `editionLabel(work)`.
- **`author-page.ts`** (`buildAuthorPage`): contexto, big numbers,
  `authorRank(catalog, slug)` (posição por leituras, com `tied`), bio+fonte,
  grade com `captionFor`, temas 2+.
- **Modelo (`lib/catalog/model.ts`) — 3 campos aditivos:** `ReadingView.
  originalEntry`; crédito da foto (`PhotoView.author/license/sourceUrl`);
  `AuthorView.bioSource` (`{ label, url }` do mesmo summary aprovado). Agregados
  e `approvedSummaryByScope` inalterados.
- **`text.ts`**: `originalTitlePresentation(language, title, original)` →
  `{ text, lang?, dir, font? } | null`, regra única de título original, reusada
  por `CoverCaption` e pela Obra.
- **Componentes novos:** `WorkHeader`, `AuthorHeader` (identidade no topo + big
  numbers em faixa), `BackLink` ("‹ Estante"), `DescriptionList`, `FactLinks`.
- **`CoverCaption`** ganhou `<slot name="caption">` e **`WorkGrid`** ganhou
  `captionFor?: (slug) => string | null` — retrocompatíveis (sem a prop, o HTML
  das telas S4 é idêntico).

## Convenções reforçadas na S5 (seguir adiante)

- Regra só em `src/lib`; `.astro` burro; imports relativos em `lib`, `@/` nos
  `.astro`. Páginas da S5 não levam `<script>`.
- **Comparação de título original é por `fold`** (sem caixa/acento). Efeito
  colateral aceito: some a linha de título original em 4 obras cujo original
  difere do pt-BR só por acento (`Jacarandá`, `Bonsai`, `Persépolis`,
  `Triste Tigre`). Registrado no handoff §6.9.
- **Cabeçalhos no desktop** centralizam no mesmo `max-width` do conteúdo da
  página (Obra 760 px, Autoria 960 px). Foi o bug dos PRs #8/#9.
- Diff do HTML contra a `main` (baseline em `temp/`, normalizando
  `data-astro-cid-*`) para provar que mudança em componente compartilhado não
  altera telas que não a usam.
- **Atenção ao fluxo de PR:** nesta sessão um PR foi mergeado cedo e os pushes
  seguintes foram para a branch depois do merge, sem entrar na `main`. Confira
  sempre se o PR não foi mergeado antes de continuar empurrando commits; se foi,
  abra um PR novo em cima da `main` atualizada.

## Decisões da S5 que afetam o resto

- **Posição da Autoria × top 10 do Atlas:** a posição é `1 + autorias com mais
  leituras` (empates compartilham, marcados "(empatada)"); só aparece no top 10.
  O Atlas corta o top 10 por nome no empate, então pode divergir da posição
  mostrada na Autoria. Aceito e documentado (handoff §6.8); não corrigir sem
  pedido.
- **Contagem de tema:** na Obra, a contagem só aparece em temas com 5+ obras na
  estante (piso da nuvem do Atlas). Na Autoria, "temas que mais aparecem" só
  lista temas em 2+ obras da autoria. Ambos agrupam variantes pelo slug.

## O que NÃO existe ainda (próximas frentes)

### F3 restante
- **S6 `pwa-offline`:** manifest, service worker, ícones, instalação, offline.
  Nada de PWA foi feito; o app é estático puro.
- **S7 `compartilhar`:** modo autenticado da Lila (Cloudflare Access já
  preparado na F4), retrospectiva 9:16 e card de livro. **Não há botão nem stub**
  de "Compartilhar" em lugar nenhum — criar do zero.

### F2 (enriquecimento) — recomendado antes da S6/S7
Agora dá para priorizar vendo o app no ar:
- **Capas de obra:** baixar as 223 existentes, trocar baixa resolução, buscar as
  ~79 que faltam. Hoje toda grade e a página de Obra caem na capa tipográfica.
  Quando as capas entrarem, `Cover`/`CoverCaption` já aceitam o derivado (o
  caminho de imagem do build é o de `images.ts`, hoje só para fotos de autoria —
  estender para capas de obra em `catalog/media/`).
- **Temas:** reduzir ~496 para ~40–60, revisado com a Lila (normaliza também as
  variantes de caixa/acento que hoje o app agrupa por slug). Afeta a nuvem do
  Atlas, os chips da Obra e os temas da Autoria.
- **Resumos de ano e país:** mesmo fluxo da bio (F2.1). Quando aprovados, as
  seções já existentes em Ano e País passam a aparecer (hoje somem).
- **Títulos originais / romanização e `first_publication_year`** que faltam.

### Revisão contínua de autorias (não bloqueante)
- ~40 fotos a escolher (`docs/plans/revisao-fotos.html`), 9 sem Wikidata, 6 sem
  bio. Olhar pelo app e corrigir no pipeline.

## Pendências herdadas (não bloqueiam)

- **CSS de grade repetido** em Ano, Sem data e `WorkGrid` (~10 linhas) — unificar
  quando conveniente. A Obra e a Autoria também repetem o chip de tema e a caixa
  de lista rótulo/valor; dá para extrair um componente de chip e um de "lista de
  dados" se outra tela precisar.
- **Sem `404.astro`:** rota desconhecida ainda serve o `index.html` no Pages
  (resposta 200). Com a S5, quase tudo tem página; um `404.astro` simples é
  opção (não pedido).
- **Idioma de fonte da capa tipográfica coreana** ainda usa `--font-serif-jp` na
  capa (herança da S1); a grade (`CoverCaption`) já usa `--font-serif-kr`.

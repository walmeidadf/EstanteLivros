# Handover — fim da S3, início da S4

Escrito ao concluir a S3 (`linha-do-tempo`). Serve para retomar a F3 na spec
seguinte (S4 `atlas`).

## Onde o projeto está (resumo)

- **S1 concluída**: fundação do app (ver `handover-s1-s2.md`).
- **S2 concluída — no ar**: Início e busca (`liliane.prateleira.site`).
- **S3 concluída — no ar**: Linha do tempo, Ano e Sem data. Quita a dívida de
  rota que a S2 deixou (`/linha-do-tempo` e `/ano/{ano}` davam 404). PRs #3 e
  #4 mergeados; validada em produção no desktop e no celular.
- `main` sincronizada, worktree limpa, branch de feature apagada.
- **Pasta `temp/`** (no `.gitignore`): artefatos descartáveis (screenshots,
  dumps, builds de verificação) vão lá, nunca em `/tmp`, para não pedir
  aprovação a cada escrita fora do workspace.

## O que a S3 entregou

Três telas, compostas com os componentes da S1/S2 e um componente novo:

- **Linha do tempo (`/linha-do-tempo`)**: uma **Faixa do ano** por ano, do mais
  recente ao mais antigo; lombadas na cor do idioma, uma por leitura, na ordem
  do caderno; notas automáticas ("em andamento", "o ano mais cheio da estante",
  "N releituras"); bloco tracejado "Os primeiros da lista" → `/ano/sem-data`.
- **Ano (`/ano/{ano}`)**: navegação anterior/próximo saltando pelos anos que
  existem (inerte nos extremos); ano gigante em `--accent`; big numbers
  (leituras · idiomas · autorias · releituras); barra de mix de idiomas com
  legenda; resumo só se houver summary `approved` (hoje nenhum, a seção some);
  grade na ordem do caderno: 3 colunas no celular; no desktop, colunas de
  largura fixa (`--cover-hero-w`, 136px, `auto-fill`), no mesmo tamanho de capa
  do Início. **Sem botão "Compartilhar"** (fica para a S7).
- **Sem data (`/ano/sem-data`)**: "Os primeiros da lista", cada item com
  "nº N da lista" (a `sequence`) no lugar do ano; sem big numbers nem nav.

### Peças novas e reusáveis

- **`YearBand.astro`** (Faixa do ano, handoff §4): genérica, não conhece o
  catálogo — recebe `label`, `href`, `count`, `notes[]`, `spines[]`. Reusa
  `Spine` (lombada mini) e `Shelf` (prateleira) da S1. **A S4 reusa essa peça
  na prateleira por país** (§6.5): lá o `label` é o nome do país e `notes` fica
  vazio.
- **`src/lib/timeline.ts`** (pura, testada): `buildTimeline`, `buildYear`,
  `buildUndated`. Padrão do `home.ts` — regra em `lib/`, páginas burras.
- **`CoverCaption`** ganhou `size="grid"` (preenche a coluna); hero/rail
  inalterados.

### Única mudança na camada de dados da S1

Para o resumo de ano, `buildModel` passa a expor
`approvedSummaryByScope: Map<string,string>` (todo summary `approved`, pelo
scope completo: `ano:2024`, `autoria:...`, `pais:PT`). Aditivo e
retrocompatível; a bio de autoria segue intacta (sai do mesmo laço). **A S4
pode usar esse mapa para o resumo de país** (`pais:{código}`), sem reler disco.

Verificação: `npm run check` limpo, `npm test` com **69 verdes** (54 da S2 + 13
de timeline + 2 de model). Build do catálogo real em código 0: 13 páginas de
ano (2014–2026) + linha do tempo + sem-data. **Zero JS** nas três telas.

## Convenções reforçadas na S3 (seguir na S4)

- **Regra só em `src/lib`** (`timeline.ts`); as páginas `.astro` chamam
  `getCatalog()` uma vez e só posicionam.
- Dentro de `src/lib`, **imports relativos**; alias `@/` nos `.astro`.
- Recortes que somem voltam como `null` da camada de seleção (handoff §8).
- **Links no formato final, 404 temporário aceito** até a página de destino
  existir.
- Componentes **genéricos** (como `YearBand`) não conhecem o catálogo: recebem
  dados prontos, para a spec seguinte reusar.

## Destinos que a S3 (e a S2) linkam e esperam página (dívida de rota)

| Rota | Quem linka | Fecha em |
|---|---|---|
| `/obra/{slug}` | grades de Ano e Sem data; capas e busca da S2 | S5 |
| `/autoria/{slug}` | "quem sempre volta" e busca da S2 | S5 |
| `/tema/{slug}` | carrosséis de tema da S2 | S4 |
| `/atlas` | chip do cabeçalho (S2) | S4 |
| `/idioma/{slug}`, `/pais/{slug}` | nascem na própria S4 | S4 |

`/linha-do-tempo`, `/ano/{ano}` e `/ano/sem-data` deixaram de ser 404 (S3).

## O que a S4 encontra pronto

- **`YearBand`** para a prateleira por país (§6.5), sem alteração.
- Da camada de dados: `worksByLanguageDesc`, `worksByCountryDesc`,
  `worksByThemeDesc`, o `countries`/`language`/`color` de cada obra,
  `countryName` da autoria, `firstPublished` (para "quando foram escritos") e
  `approvedSummaryByScope` (resumo de país).
- `Carousel` (S2) para os carrosséis de autoria do Idioma; `CoverCaption`
  (com `grid`) e `AuthorChip`/`InitialsAvatar` para grades e avatares.

## Fora do escopo da S4 (confirmando o roadmap)

- Obra e Autoria → S5 (destinos de muitos links).
- Retrospectiva 9:16 e "Compartilhar" → S7.

## Pendências herdadas (não bloqueiam a S4)

- Capas de obra ainda não existem (frente de F2): grades caem na capa
  tipográfica.
- Resumos de ano/país ainda não existem (frente de F2): a seção some.
- Revisão contínua de autorias (fotos, Wikidata, bio) segue não bloqueante.

## Nota de verificação visual (para quem retomar)

A S3 foi conferida por `astro preview` (todas as rotas 200) e capturas
headless. Atenção: capturas headless a 390px podem **parecer** cortar o lado
direito (o mesmo acontece com o Início da S2, que está correto em produção) —
é artefato da ferramenta de screenshot, não da página. A conferência real de
celular é no preview do Pages, num aparelho.

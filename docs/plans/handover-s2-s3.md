# Handover — fim da S2, início da S3

Escrito ao concluir a S2 (`estante-inicio-busca`). Serve para retomar a F3 na
spec seguinte (S3 `linha-do-tempo`).

## Onde o projeto está (resumo)

- **S1 concluída**: fundação do app em `app/` (ver `handover-s1-s2.md`).
- **S2 concluída — no ar**: tela Início (`/`) e busca, publicadas em
  `liliane.prateleira.site`. Validado em produção no desktop e no celular.
- `main` sincronizado, worktree limpa, branch de feature apagada (local e
  remota).

## O que a S2 entregou

A primeira tela pública, composta com os componentes da S1:

- **Início (`/`)**, na ordem do handoff §6.1: carrossel "Em {ano atual}",
  "Quem sempre volta" (autorias com 3+ leituras), 4 carrosséis de tema (os mais
  frequentes), "Lidos duas vezes" (releituras) e o cartão "Linha do tempo" com
  mini-gráfico de barras por ano.
- **Componente `Carousel`** genérico (`src/components/Carousel.astro`):
  scroll-snap nativo, última peça cortada, cartão tracejado "ver todos (N)",
  título-link e setas de desktop como reforço progressivo. **Reusável pela S3.**
- Itens e cartões: `CoverCaption`, `AuthorChip`, `TimelineCard`, `NavChips`.
- **Busca**: `src/lib/search.ts` (`fold` tolerante a acento + `matches`),
  endpoint estático `src/pages/search-index.json.ts` (517 entradas: 302 obras +
  215 autorias) e a ilha `src/components/SearchBox.astro` (vanilla, sem
  framework; baixa o índice no primeiro foco).
- **Camada de seleção** `src/lib/home.ts` (pura, testada): os recortes do
  Início. Padrão a seguir na S3 — regra em `lib/`, componentes/páginas burros.

Verificação: `npm run check` limpo, `npm test` com **54 verdes** (32 S1 + 13
home + 9 search), build do catálogo real em código 0, `/search-index.json` com
517 entradas. Deploy de produção verde.

## Convenções reforçadas na S2 (seguir na S3)

- **Regra de negócio só em `src/lib`** (ex.: `home.ts`); as páginas `.astro`
  chamam `getCatalog()` uma vez e só posicionam. Testável sob `node --test`.
- Dentro de `src/lib`, **imports relativos**; alias `@/` nos `.astro`.
- Seções que não têm conteúdo voltam como `null` da camada de seleção, para a
  página omiti-las sem espalhar condicionais (handoff §8: nada de "—").
- **`fold()` de `search.ts`** é a normalização tolerante a acento do projeto
  (inclui `slugifyTheme` em `home.ts`): reusar, não reinventar.
- Links no formato final mesmo quando a página de destino ainda não existe
  (404 temporário aceito). Ver abaixo os que a S2 já emite.

## Destinos que a S2 já linka e esperam página (dívida de rota)

A S2 emite estes `href` no formato final; hoje dão **404** em produção. A S3
quita os dois primeiros; os demais ficam para S4/S5.

| Rota | Quem linka na S2 | Fecha em |
|---|---|---|
| `/ano/{ano}` | título e "ver todos" de "Em {ano atual}" | **S3** |
| `/linha-do-tempo` | cartão "Linha do tempo"; chip do cabeçalho; "ver todos" de "Lidos duas vezes" | **S3** |
| `/ano/sem-data` | (ainda não linkada; nasce na própria S3) | **S3** |
| `/autoria/{slug}` | avatares de "Quem sempre volta"; resultados de busca | S5 |
| `/obra/{slug}` | capas dos carrosséis; resultados de busca | S5 |
| `/tema/{slug}` | título e "ver todos" dos carrosséis de tema | S4 |
| `/atlas` | chip do cabeçalho | S4 |

## O que fica para a S3 (`linha-do-tempo`)

Telas do handoff §6.2 e §6.3:

- **Linha do tempo** (`/linha-do-tempo`): uma **faixa do ano** por ano, do mais
  recente ao mais antigo; cada lombada é um livro na cor do idioma, na ordem do
  caderno (`reading_sequence`). Notas automáticas opcionais ("em andamento" no
  ano atual, "o ano mais cheio" no máximo, "N releituras"). No fim, o bloco
  tracejado "Os primeiros da lista" → `/ano/sem-data`.
- **Ano** (`/ano/{ano}`): navegação ano anterior/próximo; ano gigante; big
  numbers (leituras · idiomas · autorias · releituras); barra com o mix de
  idiomas do ano; **resumo do ano** só se houver summary `approved` (hoje não
  há nenhum — a seção some); grade de 3 colunas na ordem do caderno; botão de
  compartilhar leva à retrospectiva (S7).
- **Sem data** (`/ano/sem-data`): "Os primeiros da lista", sem big numbers de
  ano; cada item mostra "nº N da lista" (a `sequence`) no lugar do ano.

### O que a S3 encontra pronto

- **Componente novo da S1 que falta**: a **Faixa do ano** (handoff §4) ainda
  não existe — é o principal componente a construir na S3, reusando `Spine`
  (lombada mini) e `Shelf` (prateleira).
- Da camada de dados: `aggregates.readingsByYearDesc`, `undatedCount`, o
  `year`/`sequence`/`reread` de cada leitura e o `undated` do modelo já estão
  prontos (S1). A grade de 3 colunas pode reusar `Cover`/`CoverCaption`.
- `yearBars` de `home.ts` já exclui "sem data" — a S3 trata essas leituras na
  própria tela de Sem data, pela `sequence`.

### Fora do escopo da S3 (confirmando o roadmap)

- Atlas, Idioma, País, Tema → S4 `atlas`.
- Obra e Autoria → S5 `obra-autoria` (são os destinos de muitos links da S2/S3).
- Retrospectiva 9:16 e o botão "Compartilhar {ano}" → S7 `compartilhar`.

## Pendências herdadas (não bloqueiam a S3)

- Capas de obra ainda não existem no catálogo (frente de F2). Os carrosséis e a
  grade caem na capa tipográfica; quando as capas entrarem, passam pelo mesmo
  `images.ts` sem mudar componente.
- Resumos de ano ainda não existem (frente de F2). A seção de resumo da tela
  Ano só aparece com summary `approved` — por ora, some.
- Revisão contínua de autorias (fotos, Wikidata, bio) segue não bloqueante.

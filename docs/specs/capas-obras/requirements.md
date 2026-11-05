# Requisitos — Capas de obras (F2 · frente 2)

## Introdução

As 302 obras do catálogo têm hoje a capa só como **proveniência**: 223 guardam
uma `cover.sourceUrl` (de onde a capa poderia vir) e 79 têm `cover: null`.
Nenhuma obra tem capa local, e o app nunca usa a URL de origem como `src`
(regra R6.4 da S1). Por isso **toda grade, carrossel e a página de Obra caem
hoje na capa tipográfica**.

Esta spec traz as capas reais para a estante **sem hotlink**: baixa os mestres
para `catalog/media/covers/`, registra a proveniência e a licença, e estende a
derivação de imagem do build (`app/src/lib/images.ts`, hoje só para fotos de
autoria) para gerar os derivados 2:3 da capa. O componente `Cover` já aceita o
derivado; falta quem o produza e o ligue.

A capa real **não substitui automaticamente** a tipográfica. A tipográfica é um
fallback digno (decisão de design, §4/§8 do handoff) e permanece onde a capa
real não acrescenta. A escolha de mostrar a capa real é **por obra**, feita numa
revisão humana, igual ao fluxo de fotos de autoria da F2.1.

### Decisões já tomadas (nesta sessão)

- **Onda 100% gratuita.** As capas vêm só de fontes sem cota: a `cover.sourceUrl`
  já no catálogo e a Open Library por ISBN. SerpApi e Tavily **ficam fora desta
  onda**; obras sem capa boa seguem na tipográfica e entram num backlog para uma
  segunda onda (paga), decidida depois.
- **Resolução mínima.** Lado menor ≥ 400 px é "boa"; abaixo de 250 px é rejeitada.
  Entre 250 e 400 px, a capa entra na revisão como "baixa resolução" para a Lila
  decidir.
- **Enquadramento: corte central 2:3 por padrão (A), ajuste por obra sob demanda
  (B).** O build sempre corta no centro; o catálogo ganha um campo **opcional**
  de foco, usado só nas poucas obras em que o centro corta mal.
- **A escolha da capa é revisável por obra.** A capa tipográfica é o fallback e
  permanece onde a capa real não melhora a estante.
- Capas e fotos hospedadas pelo projeto, sem hotlink; derivados gerados no build
  (decisão do ROADMAP).

### Glossário

- **Mestre:** arquivo de capa baixado para `catalog/media/covers/{slug}.{ext}`,
  guardado no tamanho original, sem redimensionar nem recortar.
- **Derivado:** versão gerada no build do app (AVIF, tamanhos do `srcset`), a
  única que vira `src`.
- **Fonte gratuita:** origem de capa sem cota — a `cover.sourceUrl` do catálogo
  e a Open Library Covers por ISBN.
- **Cache:** respostas de rede gravadas em `pipeline/cache/`, fora do git.
- **Decisão manual:** arquivo versionado em `pipeline/config/` que fixa uma
  escolha humana (capa escolhida, "sem capa", enquadramento).
- **Capa tipográfica:** o fallback atual (`TypographicCover`), na cor do idioma.

## Requisitos

### Requisito 1 — Baixar os mestres existentes

**História:** Como mantenedor, quero as 223 capas que já têm URL baixadas para o
projeto, para que a estante pare de depender de um link externo.

#### Critérios de aceitação

1. O script SHALL baixar, para cada obra com `cover.sourceUrl`, o arquivo para `catalog/media/covers/{slug}.{ext}`, com a extensão derivada do tipo de conteúdo real da imagem (não da URL).
2. THE mestre SHALL ser gravado no tamanho original; o script SHALL NOT redimensionar nem recortar (os derivados são do build do app).
3. IF o download falhar ou o conteúdo não for uma imagem válida, THEN o script SHALL NOT gravar o mestre, SHALL deixar a obra sem capa local e SHALL listar o caso no relatório.
4. Toda resposta de rede SHALL ser guardada em cache em `pipeline/cache/covers/`, e uma nova execução SHALL reutilizá-la, salvo com `--refresh`.
5. THE script SHALL NOT fazer hotlink: o app usa só o arquivo local.

### Requisito 2 — Aferir resolução e qualidade

**História:** Como leitora, quero capas nítidas, para que a estante não pareça de
miniaturas borradas.

#### Critérios de aceitação

1. O script SHALL medir a largura e a altura de cada mestre baixado, lendo o cabeçalho do arquivo (sem dependência externa; JPEG, PNG, WEBP e GIF).
2. WHEN o lado menor for ≥ 400 px, THE capa SHALL ser classificada como "boa".
3. WHEN o lado menor for < 250 px, THE capa SHALL ser classificada como "baixa" e SHALL NOT ser oferecida como capa real sem uma substituição.
4. WHEN o lado menor estiver entre 250 e 400 px, THE capa SHALL ser classificada como "limítrofe" e SHALL ir à revisão para a Lila decidir.
5. THE limiares (400 e 250) SHALL ficar em configuração versionada (`pipeline/config/enrich.json`, bloco `cover`), não no código.
6. THE script SHALL registrar a proporção de cada mestre, para sinalizar na revisão as capas muito distantes de 2:3 (candidatas a ajuste de enquadramento, R6).

### Requisito 3 — Buscar as que faltam e substituir as de baixa resolução (só gratuito)

**História:** Como mantenedor, quero preencher as 79 obras sem capa e trocar as
de baixa resolução usando só fontes gratuitas, para não gastar cota nesta onda.

#### Critérios de aceitação

1. Para obras sem `cover.sourceUrl` e para as classificadas como "baixa", o script SHALL buscar uma capa **só em fontes gratuitas**, nesta ordem: (a) a própria `cover.sourceUrl`, quando existir; (b) a Open Library Covers por `isbn13`, e por `isbn10` como alternativa.
2. THE script SHALL NOT chamar SerpApi nem Tavily nesta spec. As obras que nenhuma fonte gratuita resolver SHALL ser registradas num backlog (`docs/plans/capas-backlog.md`) para uma segunda onda.
3. WHEN a Open Library devolver um placeholder (imagem "sem capa") ou uma imagem abaixo de 250 px, THE script SHALL descartá-la e tratar a obra como sem capa gratuita.
4. THE consulta por ISBN SHALL pedir o maior tamanho disponível da Open Library (sufixo `-L`), e a resposta SHALL passar pela aferição de resolução do R2.
5. THE busca gratuita SHALL respeitar limites de taxa (pausa entre chamadas, novas tentativas com espera crescente em 429/5xx) e SHALL enviar um `User-Agent` identificável à Open Library.

### Requisito 4 — Revisão e escolha por obra

**História:** Como Lila, quero ver a capa real ao lado da tipográfica e escolher,
sem mexer em JSON, para que a estante só troque onde fica melhor.

#### Critérios de aceitação

1. O pipeline SHALL gerar `docs/plans/revisao-capas.html` (fora do git) com, por obra pendente: título e autoria, a **capa real candidata** renderizada em 2:3 com corte central, a **capa tipográfica** ao lado para comparação, a resolução medida e a classificação (boa/limítrofe/baixa), e a origem.
2. A escolha SHALL ser registrada em `pipeline/config/cover_choices.json`: a capa real escolhida (com a URL/origem), ou `{ "typographic": true }` para manter a tipográfica, ou `{ "none": true }` quando não há capa aceitável e nem a tipográfica deve mudar.
3. THE decisão manual SHALL vencer a classificação automática: uma capa "limítrofe" ou "baixa" aprovada pela Lila SHALL ser usada; uma capa "boa" marcada como tipográfica SHALL cair na tipográfica.
4. O script SHALL baixar/promover a mestre só da capa escolhida.
5. WHILE uma obra não tiver decisão registrada, THE app SHALL continuar mostrando a capa tipográfica (padrão seguro, sem troca automática).
6. A revisão SHALL ser retomável: reexecutar o script SHALL manter as escolhas já feitas e listar só as pendências.

### Requisito 5 — Esquema e proveniência da capa

**História:** Como mantenedor, quero saber de onde veio cada capa e sob que
licença, igual às fotos de autoria.

#### Critérios de aceitação

1. THE objeto `cover` da obra SHALL ganhar, quando houver mestre local escolhido: `file` (`covers/{slug}.{ext}`), `license` (ou `null`), `author`/crédito (ou `null`) e `sourceUrl`, preservando `source`. A `sourceUrl` SHALL continuar sendo só proveniência (nunca `src`).
2. WHEN a decisão for manter a tipográfica, THE `cover` SHALL registrar essa escolha de forma explícita (ex.: `display: "typographic"`), para distinguir "ainda não revisada" de "revisada: fica tipográfica".
3. THE JSON Schema de obra (`catalog/schema/work.schema.json`), o loader/validador do app (`app/src/lib/catalog/schema.ts`) e `docs/DATA_MODEL.md` SHALL ser atualizados para os campos novos. Os campos novos SHALL ser **aditivos**: obras sem capa local continuam válidas.
4. A migração da F1 (`pipeline/migrate_legacy.py`) SHALL preservar `cover.file`, `license`, crédito, `display` e o enquadramento existentes, sem apagar o que foi enriquecido (mesma garantia do R8.3 das autorias).
5. A gravação no catálogo SHALL passar pelo validador da F1; se o resultado for inválido, nada é gravado.

### Requisito 6 — Enquadramento (corte central por padrão, ajuste por obra)

**História:** Como Lila, quero que o corte padrão sirva para a maioria e poder
ajustar as poucas capas em que o centro corta o título.

#### Critérios de aceitação

1. THE build SHALL cortar a capa em 2:3 no **centro** por padrão (`object-fit: cover`, `object-position: center`).
2. THE objeto `cover` SHALL aceitar um campo **opcional** de foco (ex.: `focus`: `"top" | "center" | "bottom"` ou uma porcentagem vertical), ausente na maioria das obras.
3. WHEN o foco estiver presente, THE build SHALL aplicá-lo ao `object-position` do derivado; WHEN ausente, THE build SHALL usar o centro.
4. THE folha de revisão SHALL permitir marcar o foco das capas sinalizadas como distantes de 2:3 (R2.6), e a escolha SHALL ser gravada junto da decisão da capa (R4.2).
5. THE enquadramento SHALL ser puramente de apresentação: o mestre NÃO é recortado; só o derivado do build muda.

### Requisito 7 — Derivação da capa no build do app

**História:** Como leitora, quero capas rápidas e nítidas em qualquer tela, sem
salto de layout nem hotlink.

#### Critérios de aceitação

1. `app/src/lib/images.ts` SHALL ganhar uma função de derivação de capa de obra (ex.: `deriveWorkCover`) que lê os mestres de `catalog/media/covers/*` via `import.meta.glob`, nos moldes de `deriveAuthorPhoto`, com proporção **2:3**.
2. THE derivado SHALL usar os tamanhos de capa já definidos (`COVER_WIDTHS`), gerar `srcset` e formato AVIF, e aplicar o `object-position` do foco (R6).
3. WHEN existir mestre local **e** a decisão for usar a capa real, THE `Cover`/`CoverCaption` SHALL renderizar o derivado; caso contrário, SHALL cair na capa tipográfica atual, sem mudança de comportamento.
4. THE `src` renderizado SHALL ser sempre o derivado local; a `sourceUrl` do catálogo SHALL NUNCA virar `src` (mantém R6.4 da S1).
5. THE imagem SHALL manter `loading="lazy"`, dimensões fixas 2:3 (sem salto de layout) e o selo "2×" de releitura, como hoje.
6. Telas que não usam capa (ou obras sem mestre) SHALL ter o HTML inalterado em relação à `main` (diffs de componente compartilhado não devem mexer em quem não usa a capa).

### Requisito 8 — Execução, cache e custo

**História:** Como mantenedor, quero rodar por partes e de novo, sem gastar e sem
refazer downloads.

#### Critérios de aceitação

1. O enriquecimento de capas SHALL ser uma CLI (`pipeline/enrich_covers.py`) com etapas selecionáveis (`--steps download,measure,search,apply`), filtro por obra (`--only slug,...`), limite (`--limit N`) e `--dry-run`.
2. THE `--dry-run` SHALL mostrar quantos downloads e consultas à Open Library seriam feitos (descontando o cache), e SHALL NOT baixar nada.
3. Por padrão, o script SHALL processar só as obras **pendentes** (sem decisão de capa registrada), na ordem de visibilidade (nº de leituras, depois presença no ano corrente, depois slug), igual à F2.1.
4. THE script SHALL usar só a biblioteca padrão do Python 3.9 (HTTP com `urllib`).
5. IF uma obra falhar, THEN o script SHALL seguir para as próximas e listar as falhas no fim (código de saída 1 quando houver falha).
6. Rodar duas vezes com o cache completo e as mesmas decisões SHALL produzir o mesmo catálogo, byte a byte.
7. Como esta onda não usa provedores com cota, THE script SHALL NOT consumir SerpApi/Tavily; a guarda de orçamento (`budgets.json`) SHALL permanecer válida para a segunda onda, sem bloquear esta.

### Requisito 9 — Relatórios e registro

**História:** Como mantenedor, quero ver o progresso das capas e o que sobrou
para a onda paga.

#### Critérios de aceitação

1. `docs/plans/cobertura.md` SHALL passar a mostrar, para obras: com capa local boa, limítrofe, só tipográfica (revisada), pendentes de revisão e sem capa gratuita (backlog).
2. `docs/plans/capas-backlog.md` SHALL listar as obras que nenhuma fonte gratuita resolveu, para a segunda onda (paga).
3. Cada execução real (não `--dry-run`) SHALL acrescentar uma entrada a `docs/plans/capas-execucoes.md` com data, seleção, etapas, obras processadas, resultado por fonte (catálogo × Open Library), downloads (rede × cache) e falhas.

### Requisito 10 — Testes

**História:** Como mantenedor, quero testar a lógica sem rede.

#### Critérios de aceitação

1. Os testes do pipeline SHALL rodar offline, com imagens e respostas simuladas (fixtures pequenas), cobrindo: extensão pelo tipo de conteúdo; leitura de dimensão de JPEG/PNG/WEBP; classificação boa/limítrofe/baixa; descarte de placeholder da Open Library; precedência da decisão manual; `display: typographic`; preservação na migração da F1; cache e `--dry-run`.
2. Os testes do app SHALL cobrir a seleção da capa (mestre + decisão → derivado; senão tipográfica) na camada `src/lib`, e `route-integrity`/HTML-diff SHALL garantir que telas sem capa não mudam.
3. A migração da F1 SHALL ter teste de preservação dos dados de capa enriquecidos.

## Fora do escopo

- **SerpApi/Tavily e qualquer capa paga** (segunda onda, decidida depois).
- **Temas, resumos de ano/país, títulos originais/romanização e
  `first_publication_year`** das obras (outras frentes da F2).
- **S6 `pwa-offline`** e **S7 `compartilhar`** (F3).
- **Revisão contínua de autorias** (40 fotos, 9 sem Wikidata, 6 sem bio).
- **Otimização/derivação de imagem** além do que o build do app já faz; o
  pipeline só baixa o mestre, sem redimensionar nem recortar.
- **Redesenho da capa tipográfica** — ela permanece como está, boa, servindo de
  fallback.

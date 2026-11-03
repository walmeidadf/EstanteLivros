# Requisitos — Linha do tempo (S3)

## Introdução

Esta é a terceira spec da F3 (o app) e fecha a **dívida de rota** que a S2
deixou: hoje `/ano/{ano}` e `/linha-do-tempo` são linkados pelo Início mas dão
404. A S3 cria essas telas e mais a de "sem data".

A S1 (`estante-fundacao`) deixou a fundação: tokens, fontes, cor por idioma, a
camada de dados (`getCatalog()`, com modelo e agregados) e os componentes base
(Capa, Capa tipográfica, Lombada mini, Avatar de iniciais, Prateleira). A S2
(`estante-inicio-busca`) entregou a tela Início e a busca, no ar em
`liliane.prateleira.site`, e firmou duas convenções que a S3 segue: o
**componente Carrossel** genérico e a regra de **pôr a seleção em `src/lib`**
(ex.: `home.ts`), deixando as páginas `.astro` burras.

A S3 entrega três telas e um componente novo:

1. **Linha do tempo** (`/linha-do-tempo`) — uma **faixa do ano** por ano, do
   mais recente ao mais antigo, com lombadas na cor do idioma na ordem do
   caderno, notas automáticas e, no fim, o bloco "Os primeiros da lista".
2. **Ano** (`/ano/{ano}`) — ano gigante, big numbers, mix de idiomas, resumo
   (só se aprovado) e grade de 3 colunas na ordem do caderno.
3. **Sem data** (`/ano/sem-data`) — "Os primeiros da lista", onde cada item
   mostra "nº N da lista" (a `sequence`) no lugar do ano.
4. O **componente novo Faixa do ano** (handoff §4), reusando a Lombada mini
   (`Spine`) e a Prateleira (`Shelf`) da S1. É o principal trabalho da S3.

Como nas telas anteriores, as telas são **compostas, não desenhadas do zero**:
seguem o handoff §6.2, §6.3, §4 e §8. O trabalho novo de verdade é a **Faixa do
ano** e a camada de seleção da linha do tempo.

### Decisões de escopo já tomadas

- **Notas automáticas nascem dos dados, nunca escritas por ano.** As três notas
  do handoff §6.2 são derivadas: "em andamento" (o ano atual), "o ano mais cheio
  da estante" (o ano com o máximo de leituras) e "N releituras" (quando o ano
  tem releitura). A seleção vive em `src/lib`, não há texto fixado por ano.
- **Uma faixa pode ter mais de uma nota.** A nota principal ("em andamento" tem
  prioridade sobre "o ano mais cheio") e, quando houver, a nota complementar
  "N releituras". As duas podem coexistir numa faixa.
- **Navegação anterior/próximo salta pelos anos que existem**, não por `ano ± 1`.
  Os anos de leitura não são contíguos; "‹ ano anterior" é o maior ano menor que
  o atual, e "próximo ano ›" o menor ano maior. Nos extremos, a seta fica
  inerte. `/ano/sem-data` fica fora desse encadeamento.
- **Uma lombada por leitura, não por obra.** Uma obra relida no mesmo ano
  aparece como duas lombadas naquela faixa, coerente com "releitura conta em
  cada ano" (modelo da S1). A grade da tela Ano segue a mesma contagem por
  leitura.
- **Links para rotas futuras no formato final, com 404 temporário aceito.** As
  grades e itens linkam `/obra/{slug}` (rota da S5); segue a mesma decisão da S2.
- **O botão "Compartilhar {ano}" fica fora da S3** (vai para a spec de
  compartilhamento, S7). A tela Ano não mostra stub nem link morto para a
  retrospectiva.

### Fora do escopo (fica para as specs seguintes)

- Atlas (idioma e país), Idioma, País, página de Tema e a prateleira por país
  que também usa a Faixa do ano → S4 `atlas`.
- Páginas Obra e Autoria (destinos dos links das grades) → S5 `obra-autoria`.
- Retrospectiva 9:16 e o botão "Compartilhar {ano}" → S7 `compartilhar`.
- Capas de obra (ainda não baixadas; frente de F2). A Capa já cai na capa
  tipográfica; quando as capas entrarem, as grades as mostram sem mudar
  contrato.
- Resumos de ano (ainda não existem; frente de F2). O bloco de resumo só aparece
  com summary `approved`; por ora, some.

### Glossário

- **Faixa do ano**: linha clicável com o ano (Bodoni), nota(s) opcional(is),
  contagem "N ›" em `--accent` e, embaixo, uma fileira de lombadas mini sobre a
  prateleira (handoff §4). Reusada pela S4 na prateleira por país.
- **Linha do tempo**: a tela `/linha-do-tempo`, uma faixa do ano por ano
  (handoff §6.2).
- **Lombada mini**: barra fina na cor do idioma, uma por leitura (componente
  `Spine` da S1).
- **Ordem do caderno**: a ordem original de leitura, dada pela `sequence` de
  cada leitura (termo da S1; "só o ano existe").
- **Ano atual**: o maior ano com ao menos uma leitura (não o relógio do build),
  mesma regra do Início (handoff §3.1/§11).
- **Ano mais cheio**: o ano com o maior número de leituras; empate resolve pelo
  ano mais recente.
- **Sem data / "Os primeiros da lista"**: as leituras sem ano, mostradas pela
  `sequence` (handoff §6.3, §8).
- **Big numbers**: grade de números em Bodoni com rótulo (handoff §4).
- **Resumo do ano**: texto gerado por IA e revisado; só aparece com summary
  `approved` de scope `ano:{ano}` (handoff §7.3, §8).
- **Handoff**: `design/DESIGN_HANDOFF.md`, fonte de verdade do visual. As
  seções citadas (§6.2, §4, …) referem-se a ele.
- **Catálogo / modelo / agregados**: termos da S1; a S3 consome o que
  `getCatalog()` já entrega e não altera a camada de dados do catálogo.

### Referências de design

Fonte de verdade visual: #[[file:design/DESIGN_HANDOFF.md]]
Contexto e dados do projeto: #[[file:design/DESIGN_BRIEF.md]]
Fundação que esta spec consome: #[[file:docs/specs/estante-fundacao/design.md]]
Handover que originou esta spec: #[[file:docs/plans/handover-s2-s3.md]]

## Requisitos

### Requisito 1 — Componente Faixa do ano

**História:** Como desenvolvedor das telas, quero uma faixa do ano genérica fiel
ao handoff §4, para montar a linha do tempo e reusá-la na prateleira por país
(S4) sem recriar a fileira de lombadas.

#### Critérios de aceitação

1. THE app SHALL prover um componente Faixa do ano com: um rótulo principal em Bodoni (o ano, na linha do tempo), zero ou mais notas, uma contagem "N ›" em `--accent` e, embaixo, uma fileira de lombadas mini sobre a prateleira (handoff §4).
2. THE Faixa do ano SHALL renderizar as lombadas com o componente Lombada mini (`Spine`) da S1 e apoiá-las na Prateleira (`Shelf`) da S1; SHALL NOT reimplementar lombada nem prateleira.
3. THE Faixa do ano SHALL colorir cada lombada pela cor do idioma original da obra correspondente, uma lombada por item recebido, na ordem em que os itens chegam.
4. THE linha inteira da Faixa do ano SHALL ser um único alvo clicável (`<a href>`) que leva ao destino recebido, com alvo de toque adequado (handoff §3.4).
5. THE Faixa do ano SHALL aceitar rótulo, notas, contagem, destino e a lista de itens (idioma por item) por props tipadas; SHALL NOT embutir conhecimento do catálogo nem decidir as notas por conta própria.
6. THE fileira de lombadas SHALL ser decorativa (`aria-hidden`), com o dado correspondente (ano e contagem) disponível em texto na própria faixa (handoff §10).

### Requisito 2 — Tela Linha do tempo

**História:** Como leitora, quero ver todos os anos de leitura de relance, do
mais recente ao mais antigo, para percorrer a estante pelo tempo.

#### Critérios de aceitação

1. THE app SHALL servir a tela Linha do tempo em `/linha-do-tempo`, fechando o 404 que a S2 deixou nessa rota.
2. THE Linha do tempo SHALL mostrar uma Faixa do ano (Requisito 1) por ano com ao menos uma leitura, ordenadas do ano mais recente ao mais antigo.
3. THE cada faixa SHALL mostrar as lombadas na ordem do caderno (`sequence`), uma lombada por leitura do ano, na cor do idioma de cada obra.
4. THE contagem "N" de cada faixa SHALL ser o número de leituras daquele ano (releitura conta em cada ano), coerente com os agregados da S1.
5. THE cada faixa SHALL levar a `/ano/{ano}` do seu ano.
6. THE Linha do tempo SHALL renderizar sem exigir JavaScript e SHALL ser mobile-first, com a margem lateral e os alvos de toque do handoff §3.4.
7. THE Linha do tempo SHALL consumir os dados por `getCatalog()`; SHALL NOT reler o catálogo do disco nem recalcular agregados que a S1 já expõe.

### Requisito 3 — Notas automáticas da linha do tempo

**História:** Como leitora, quero pequenas notas que expliquem o que cada ano
tem de especial, para que a linha do tempo conte algo além da contagem.

#### Critérios de aceitação

1. THE notas de cada ano SHALL ser derivadas dos dados pela camada de seleção; SHALL NOT existir texto de nota fixado por ano no código ou no catálogo.
2. WHERE um ano for o ano atual (o maior ano com leitura), THE faixa SHALL receber a nota "em andamento".
3. WHERE um ano for o ano mais cheio (máximo de leituras; empate pelo ano mais recente), THE faixa SHALL receber a nota "o ano mais cheio da estante".
4. WHEN um ano é ao mesmo tempo o atual e o mais cheio, THE nota principal "em andamento" SHALL ter prioridade sobre "o ano mais cheio".
5. WHERE um ano tiver ao menos uma releitura, THE faixa SHALL receber a nota complementar com a contagem de releituras daquele ano.
6. THE nota principal (atual/mais cheio) e a nota complementar de releituras SHALL poder coexistir na mesma faixa.
7. WHERE um ano não se qualificar para nenhuma nota, THE faixa SHALL aparecer sem nota, sem texto de preenchimento (handoff §8: nada de "—").

### Requisito 4 — Bloco "Os primeiros da lista" na linha do tempo

**História:** Como leitora, quero chegar às leituras antigas que não têm ano, a
partir do fim da linha do tempo, para não perder os primeiros livros do caderno.

#### Critérios de aceitação

1. WHERE houver ao menos uma leitura sem ano, THE Linha do tempo SHALL terminar com um bloco tracejado "Os primeiros da lista" que leva a `/ano/sem-data`.
2. THE bloco "Os primeiros da lista" SHALL usar o estilo tracejado do design (`--dashed`), coerente com o cartão "ver todos" da S2 (handoff §4).
3. WHERE não houver nenhuma leitura sem ano, THE bloco SHALL ser omitido inteiro, sem deixar título vazio.
4. THE bloco SHALL NOT tratar as leituras sem ano como se pertencessem a um ano; elas só aparecem em `/ano/sem-data` (handoff §1, §8).

### Requisito 5 — Tela Ano

**História:** Como leitora, quero abrir um ano e ver tudo o que li nele, com os
números e os livros, para mergulhar num ano específico.

#### Critérios de aceitação

1. THE app SHALL servir uma tela Ano em `/ano/{ano}` para cada ano com ao menos uma leitura, fechando o 404 que a S2 deixou em `/ano/{ano}`.
2. THE tela Ano SHALL mostrar o ano em tamanho gigante, em `--accent` (handoff §6.3).
3. WHERE o ano tiver nota automática (Requisito 3), THE tela Ano SHALL mostrar a mesma nota curta no topo.
4. THE tela Ano SHALL mostrar big numbers do ano: leituras · idiomas originais distintos · autorias distintas · releituras, a partir dos dados da S1.
5. THE tela Ano SHALL mostrar uma barra proporcional com o mix de idiomas originais do ano, decorativa (`aria-hidden`), com os idiomas e contagens disponíveis em texto (handoff §10).
6. THE tela Ano SHALL mostrar uma grade de 3 colunas com todas as leituras do ano, na ordem do caderno (`sequence`), reusando os componentes de capa da S1 (Capa/Capa tipográfica), uma peça por leitura.
7. THE cada item da grade SHALL levar a `/obra/{slug}` (rota da S5; 404 temporário aceito) e SHALL mostrar o selo "2×" quando a obra for releitura (componente da S1).
8. THE tela Ano SHALL renderizar sem exigir JavaScript, ser mobile-first e consumir os dados por `getCatalog()`.
9. THE tela Ano SHALL NOT mostrar o botão "Compartilhar {ano}" nesta spec (vai para a S7), e SHALL NOT deixar link morto para a retrospectiva.

### Requisito 6 — Resumo do ano (só quando aprovado)

**História:** Como leitora, quero ler um resumo do ano quando a Lila tiver
aprovado um, para ter o contexto em palavras além dos números.

#### Critérios de aceitação

1. WHERE existir um summary de scope `ano:{ano}` com `approved: true`, THE tela Ano SHALL mostrar o bloco de resumo com esse texto.
2. WHERE não existir resumo aprovado para o ano, THE bloco de resumo SHALL ser omitido inteiro, sem título vazio nem texto de preenchimento (handoff §8).
3. THE regra de "resumo aprovado" SHALL reusar o que o modelo da S1 já expõe; SHALL NOT reclassificar aprovação por conta própria.

### Requisito 7 — Navegação entre anos

**História:** Como leitora, quero ir do ano aberto para o anterior ou o próximo
e voltar à linha do tempo, para percorrer os anos sem passar pelo Início.

#### Critérios de aceitação

1. THE tela Ano SHALL oferecer navegação "‹ ano anterior · próximo ano ›" e um caminho de volta para a Linha do tempo.
2. THE "ano anterior" SHALL ser o maior ano de leitura menor que o ano atual, e o "próximo ano" o menor ano de leitura maior que o atual; a navegação SHALL saltar pelos anos que existem, não por `ano ± 1`.
3. WHERE o ano for o mais antigo com leitura, THE controle "ano anterior" SHALL ficar inerte (sem link); WHERE for o mais recente, THE controle "próximo ano" SHALL ficar inerte.
4. THE controles de navegação SHALL ser controles reais (`<a href>` quando levam a um ano, sem link quando inertes) e operáveis por teclado.
5. THE `/ano/sem-data` SHALL ficar fora do encadeamento anterior/próximo (sem setas de ano), mantendo apenas o caminho de volta para a Linha do tempo.

### Requisito 8 — Tela Sem data ("Os primeiros da lista")

**História:** Como leitora, quero ver os primeiros livros do caderno, que não
têm ano, identificados pela posição na lista, para conhecer o começo da estante.

#### Critérios de aceitação

1. THE app SHALL servir a tela Sem data em `/ano/sem-data`, com o título "Os primeiros da lista".
2. THE tela Sem data SHALL mostrar as leituras sem ano na ordem do caderno (`sequence`), reusando os componentes de capa da S1.
3. THE cada item SHALL mostrar "nº N da lista" (a `sequence`) no lugar do ano (handoff §6.3, §8).
4. THE tela Sem data SHALL NOT mostrar big numbers de ano nem navegação anterior/próximo; SHALL manter o caminho de volta para a Linha do tempo.
5. THE cada item SHALL levar a `/obra/{slug}` (rota da S5; 404 temporário aceito) e mostrar o selo "2×" quando couber.
6. WHERE não houver nenhuma leitura sem ano, THE rota `/ano/sem-data` SHALL NOT ser gerada (não há página vazia).

### Requisito 9 — Camada de seleção da linha do tempo

**História:** Como desenvolvedor das telas, quero toda a regra de seleção da
linha do tempo num módulo puro e testável, para manter as páginas burras e
seguir a convenção da S2.

#### Critérios de aceitação

1. THE app SHALL concentrar a seleção da linha do tempo, do ano e de "sem data" num módulo puro em `src/lib` (padrão do `home.ts`); as páginas `.astro` SHALL só chamar `getCatalog()` uma vez e posicionar os componentes.
2. THE módulo SHALL expor os recortes já prontos: as faixas por ano (ordenadas, com notas e contagem), os dados da tela Ano (big numbers, mix de idiomas, grade, nota, resumo e os vizinhos anterior/próximo) e a lista de "sem data" por `sequence`.
3. THE módulo SHALL ser puro e sem dependências de Astro, testável sob `node --test`, e SHALL reusar as normalizações já existentes do projeto onde fizer sentido (ex.: `slugifyTheme`/`fold`) em vez de reinventá-las.
4. WHERE um recorte não tiver conteúdo (ex.: sem leitura sem ano, sem resumo aprovado), THE módulo SHALL sinalizar ausência (ex.: `null`) para a página omitir a seção sem espalhar condicionais (handoff §8).

### Requisito 10 — Acessibilidade e desempenho

**História:** Como leitora, quero as telas da linha do tempo acessíveis e leves,
coerentes com a fundação, para que funcionem bem em celular e no teclado.

#### Critérios de aceitação

1. THE telas da S3 SHALL usar controles reais: `<a href>` para navegação (faixas, itens, setas de ano, volta); elementos só com ícone SHALL ter `aria-label`.
2. THE lombadas e barras decorativas (fileira da faixa, mix de idiomas) SHALL levar `aria-hidden`, com o dado correspondente disponível em texto no contexto (handoff §10).
3. THE capas das grades SHALL seguir as regras da S1: `loading="lazy"` e dimensões fixas 2:3 (sem salto de layout).
4. THE títulos de obra em alfabeto não latino SHALL herdar `lang` e `dir` corretos dos componentes da S1.
5. THE texto SHALL manter contraste de ao menos 4.5:1 sobre `--ground` e, sobre cor de idioma, usar o par fundo/texto do handoff §3.2.
6. THE telas da S3 SHALL ser legíveis e navegáveis sem JavaScript; nenhuma parte da leitura SHALL depender de JS.

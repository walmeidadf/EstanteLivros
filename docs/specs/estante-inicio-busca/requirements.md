# Requisitos — Estante: Início e busca (S2)

## Introdução

Esta é a segunda spec da F3 (o app) e a **primeira a entregar tela pública**. A
S1 (`estante-fundacao`) deixou pronta a fundação que esta spec consome: o
projeto Astro estático em `app/`, os tokens e fontes do design, a cor por
idioma, a camada de dados (`getCatalog()`, com modelo e agregados), os
componentes base (Capa, Capa tipográfica, Lombada, Avatar de iniciais,
Prateleira) e a vitrine interna `/styleguide`. A F4 (`infra-hospedagem`) pôs o
app no ar em `liliane.prateleira.site`, com deploy automático a cada push em
`main`.

A S2 entrega duas coisas:

1. a tela **Início** (`/`), substituindo o placeholder da S1;
2. a **busca** — um índice próprio gerado no build e uma ilha pequena de
   filtragem no cliente, tolerante a acento, cobrindo título pt-BR, título
   original e autoria.

O Início é composto, não desenhado do zero: ele arruma os componentes da S1 em
carrosséis e cartões, seguindo o handoff §6.1, §4 e §9. O trabalho novo de
verdade é o **componente Carrossel** (que S3/S4/S5 também vão reusar) e a
**busca** (índice estático + ilha), já que a S1 não montou índice nenhum.

### Decisões de escopo já tomadas

- **Links para rotas futuras são emitidos já no formato final.** Quase todos os
  destinos do Início (`/ano/{ano}`, `/autoria/{slug}`, `/tema/{slug}`,
  `/obra/{slug}`, `/atlas`, `/linha-do-tempo`) só nascem nas specs S3–S5. As
  URLs já estão definidas no handoff (§5, §6) e não vão mudar, então a S2 emite
  os `href` no formato final e **aceita 404 temporário** em dev/preview até as
  telas de destino existirem. Isso evita retrabalho de markup.
- **A busca pode exigir JavaScript.** O handoff §10 pede "leitura básica sem
  JS"; busca é interação, não leitura. A busca é uma ilha que só funciona com
  JS; o resto do Início é estático e funciona sem JS.
- **Quatro carrosséis de tema no Início**, os mais frequentes (handoff §12.4),
  com teto de ~20 itens por carrossel e cartão final "ver todos (N)". O número
  pode ser reajustado depois se não ficar bem.
- O **componente Carrossel** faz parte da S2: é peça nova e genérica, usada já
  no Início e reusada nas specs seguintes.

### Fora do escopo (fica para as specs seguintes)

- Linha do tempo, Ano, Sem data e a faixa do ano → S3 `linha-do-tempo`.
- Atlas (idioma e país), Idioma, País, página de Tema e nuvem de temas → S4
  `atlas`.
- Páginas Obra e Autoria (destinos dos links e dos resultados de busca) → S5
  `obra-autoria`.
- Manifest, service worker, instalação (PWA) → S6 `pwa-offline`.
- Modo da Lila, retrospectiva 9:16, cards de compartilhar → S7 `compartilhar`.
- Capas de obra (ainda não baixadas no catálogo; frente de F2). A Capa já cai na
  capa tipográfica; quando as capas entrarem, os carrosséis as mostram sem
  mudança de contrato.

### Glossário

- **Início**: a tela pública `/`, primeira porta da estante (handoff §6.1).
- **Carrossel**: fileira de rolagem horizontal com `scroll-snap`, última peça
  cortada e cartão final "ver todos (N)" (handoff §9).
- **Cartão "ver todos"**: peça tracejada no fim de um carrossel, que leva à
  página completa daquele recorte.
- **Quem sempre volta**: as autorias com 3 ou mais leituras (handoff §6.1).
- **Lidos duas vezes**: as obras com mais de uma leitura (releituras).
- **Índice de busca**: arquivo estático gerado no build, uma entrada por obra e
  por autoria, com as chaves de busca já normalizadas.
- **Normalização tolerante a acento**: dobra que remove acentos e caixa para
  comparar busca e conteúdo ("josé" casa "jose", "JOSE").
- **Ilha**: trecho interativo com JavaScript no cliente dentro de uma página
  estática (aqui, só a busca). Sem framework de UI pesado.
- **Handoff**: `design/DESIGN_HANDOFF.md`, fonte de verdade do visual. As
  seções citadas (§6.1, §9, …) referem-se a ele.
- **Catálogo / modelo / agregados**: termos da S1; a S2 consome o que
  `getCatalog()` já entrega e não altera a camada de dados do catálogo.

### Referências de design

Fonte de verdade visual: #[[file:design/DESIGN_HANDOFF.md]]
Contexto e dados do projeto: #[[file:design/DESIGN_BRIEF.md]]
Fundação que esta spec consome: #[[file:docs/specs/estante-fundacao/design.md]]

## Requisitos

### Requisito 1 — Tela Início substitui o placeholder

**História:** Como leitora, quero que `/` seja a estante de verdade, com os
livros arrumados por recortes que fazem sentido, para começar a navegar sem
precisar saber nada de antemão.

#### Critérios de aceitação

1. THE app SHALL servir a tela Início em `/`, substituindo o placeholder da S1.
2. THE Início SHALL renderizar seu conteúdo de leitura (cabeçalho, carrosséis e cartões) sem exigir JavaScript; só a busca (Requisito 7) depende de JS.
3. THE Início SHALL ser montado compondo os componentes da fundação (S1) e o componente Carrossel (Requisito 2); SHALL NOT reimplementar capa, avatar, lombada ou prateleira.
4. THE Início SHALL consumir os dados por `getCatalog()`; SHALL NOT reler o catálogo do disco por conta própria nem recalcular agregados que a S1 já expõe.
5. THE Início SHALL seguir a ordem de seções do handoff §6.1: cabeçalho e busca; "Em {ano atual}"; "Quem sempre volta"; carrosséis de tema; "Lidos duas vezes"; cartão "Linha do tempo".
6. THE Início SHALL ser mobile-first (largura de referência 390 px) e usar a margem lateral e os alvos de toque do handoff §3.4.

### Requisito 2 — Componente Carrossel

**História:** Como desenvolvedor das telas, quero um carrossel genérico fiel ao
handoff §9, para reusá-lo no Início e nas próximas telas sem recriar a rolagem.

#### Critérios de aceitação

1. THE app SHALL prover um componente Carrossel de rolagem horizontal com `scroll-snap` no início de cada item (handoff §9).
2. THE Carrossel SHALL deixar a última peça visível cortada, para sinalizar que a fileira rola.
3. THE Carrossel SHALL terminar num cartão tracejado "ver todos (N)", onde N é a contagem total do recorte, que leva à página completa correspondente.
4. THE Carrossel SHALL expor um título que também é link para a mesma página completa do cartão "ver todos".
5. THE Carrossel SHALL limitar a ~20 itens visíveis; WHEN o recorte tiver mais itens, THE excedente SHALL ficar só na página completa (alcançável pelo título e pelo cartão "ver todos").
6. THE Carrossel SHALL oferecer, no desktop, setas ‹ › posicionadas fora das capas e navegação por teclado; SHALL NOT exibir rolagem automática, bolinhas, contador ou barra de rolagem.
7. THE Carrossel SHALL usar controles reais (`<a href>` nos itens e no cartão "ver todos"; `<button>` com `aria-label` nas setas) e SHALL funcionar para leitura mesmo sem JavaScript (as setas são um reforço, não a única forma de rolar).
8. THE Carrossel SHALL aceitar qualquer conteúdo de item por slot/props tipadas (capa com legenda, avatar, etc.); SHALL NOT embutir conhecimento do catálogo.

### Requisito 3 — Carrossel "Em {ano atual}"

**História:** Como leitora, quero ver em destaque o que ando lendo neste ano,
para que a estante abra no presente.

#### Critérios de aceitação

1. THE Início SHALL mostrar um carrossel de destaque com as leituras do **ano atual**, com capas no tamanho de destaque (handoff §3.4) e título + autoria em texto sob a capa.
2. THE ano atual SHALL ser derivado dos dados (agregados de leituras por ano), não escrito fixo no código.
3. THE carrossel SHALL ordenar as obras pela ordem do caderno (`reading_sequence`) dentro do ano, coerente com a regra "só o ano existe" (handoff §1).
4. THE título da seção ("Em {ano atual}") e o cartão final "ver todos" SHALL levar a `/ano/{ano}` (rota da S3; 404 temporário aceito).
5. WHERE uma obra do ano não tiver capa local, THE carrossel SHALL mostrar a capa tipográfica (herdado do componente Capa da S1), sem erro.
6. WHERE não houver nenhuma leitura no ano atual, THE seção SHALL ser omitida inteira, sem deixar título vazio nem texto de preenchimento.

### Requisito 4 — "Quem sempre volta"

**História:** Como leitora, quero ver de relance as autorias a que sempre
retorno, para reencontrá-las a partir do Início.

#### Critérios de aceitação

1. THE Início SHALL mostrar um carrossel "Quem sempre volta" com as autorias de **3 ou mais leituras**, a partir dos agregados de leituras por autoria.
2. THE carrossel SHALL mostrar cada autoria como avatar (foto local quando houver, senão iniciais na cor do idioma principal — componente da S1), com o nome em texto.
3. THE carrossel SHALL ordenar as autorias por quantidade de leituras (decrescente), com desempate estável coerente com os agregados da S1.
4. THE cada avatar SHALL levar a `/autoria/{slug}` (rota da S5; 404 temporário aceito).
5. WHERE menos de uma autoria atingir o corte de 3 leituras, THE seção SHALL ser omitida inteira.

### Requisito 5 — Carrosséis de tema

**História:** Como leitora, quero carrosséis dos assuntos que mais leio, para
puxar um fio temático a partir do Início.

#### Critérios de aceitação

1. THE Início SHALL mostrar carrosséis para os **4 temas mais frequentes** (agregados de obras por tema), cada um com as obras daquele tema.
2. THE cada carrossel de tema SHALL mostrar as obras como capas com título + autoria em texto, com teto de ~20 itens e cartão final "ver todos (N)".
3. THE título de cada carrossel de tema e seu cartão "ver todos" SHALL levar a `/tema/{slug}` (rota da S4; 404 temporário aceito).
4. THE escolha e a ordem dos 4 temas SHALL vir dos agregados (frequência decrescente, desempate estável), não de lista escrita à mão.
5. WHERE houver menos de 4 temas no catálogo, THE Início SHALL mostrar quantos existirem, sem seção vazia.

### Requisito 6 — "Lidos duas vezes" e cartão "Linha do tempo"

**História:** Como leitora, quero ver o que reli e ter uma porta para a linha do
tempo, para fechar o Início com releituras e uma visão do todo.

#### Critérios de aceitação

1. THE Início SHALL mostrar um carrossel "Lidos duas vezes" com as obras lidas mais de uma vez (releituras), cada capa com o selo "2×" (componente da S1).
2. THE carrossel de releituras SHALL tratar cada obra relida como **uma** peça (nunca duplicada), coerente com o modelo da S1.
3. WHERE não houver nenhuma releitura, THE seção SHALL ser omitida inteira.
4. THE Início SHALL terminar com um cartão "Linha do tempo" com um mini-gráfico de barras por ano (a partir dos agregados de leituras por ano).
5. THE cartão "Linha do tempo" SHALL levar a `/linha-do-tempo` (rota da S3; 404 temporário aceito).
6. THE mini-gráfico SHALL ser decorativo (`aria-hidden`), com o dado correspondente disponível em texto no destino; SHALL NOT inventar dia/mês nem mostrar leituras sem ano como se fossem de um ano.

### Requisito 7 — Busca: índice estático e ilha de filtragem

**História:** Como leitora, quero achar um livro ou uma autoria digitando parte
do nome, mesmo com acento trocado, para chegar direto sem navegar pelos
recortes.

#### Critérios de aceitação

1. THE app SHALL gerar no build, a partir de `getCatalog()`, um **índice de busca estático** (asset do site), com uma entrada por obra e por autoria.
2. THE cada entrada SHALL conter o slug, um rótulo de exibição, o tipo (obra ou autoria) e as chaves de busca já **normalizadas** (sem acento, minúsculas) cobrindo, para obra, o título pt-BR e o título original; e, para autoria, o nome.
3. THE normalização tolerante a acento SHALL viver num módulo puro e testável (convenção da S1), usado **tanto** na geração do índice **quanto** na filtragem no cliente, para que as duas pontas usem exatamente a mesma regra.
4. THE busca no Início SHALL ser uma **ilha** que carrega o índice estático e filtra no cliente; SHALL NOT introduzir framework de UI pesado nem chamar nenhuma API externa.
5. WHEN a leitora digita, THE busca SHALL casar por acento-insensível e caixa-insensível contra título pt-BR, título original e nome da autoria, e mostrar os resultados como links.
6. THE cada resultado SHALL levar a `/obra/{slug}` ou `/autoria/{slug}` conforme o tipo (rotas da S5; 404 temporário aceito).
7. THE campo de busca SHALL ter ~52 px de altura com ícone de lupa (handoff §4), `<label>` associado e `aria-label` onde o rótulo for só ícone.
8. WHERE o JavaScript estiver desligado, THE resto do Início SHALL continuar legível e navegável; a busca pode ficar inerte, mas SHALL NOT quebrar a página nem esconder conteúdo estático.
9. THE índice de busca SHALL cobrir todas as obras e autorias do catálogo e SHALL ser regenerado a cada build, sem passo manual.

### Requisito 8 — Navegação do cabeçalho

**História:** Como leitora, quero os atalhos para os grandes modos da estante no
topo do Início, para saber que existem Atlas e Linha do tempo.

#### Critérios de aceitação

1. THE Início SHALL mostrar o título "A estante da Lila" e os chips de navegação `Estante` (ativa), `Atlas` e `Linha do tempo` (handoff §6.1).
2. THE chip ativo (`Estante`) SHALL usar `--accent` + `--accent-ink` e os demais o estilo de chip secundário (handoff §4), com alvo de toque ≥ 44 px.
3. THE chips `Atlas` e `Linha do tempo` SHALL ser `<a href>` para `/atlas` e `/linha-do-tempo` (rotas de S4 e S3; 404 temporário aceito).
4. THE chips SHALL usar controles reais e ser operáveis por teclado.

### Requisito 9 — Acessibilidade e desempenho do Início

**História:** Como leitora, quero o Início acessível e leve, coerente com a
fundação, para que a primeira tela já seja boa em celular e no teclado.

#### Critérios de aceitação

1. THE Início SHALL usar controles reais: `<a href>` para navegação, `<button>` para ações, `<label>` no campo de busca; elementos só com ícone SHALL ter `aria-label`.
2. THE capas, avatares e barras decorativas SHALL seguir as regras da S1: `loading="lazy"` e dimensões fixas 2:3 nas capas; barras e lombadas com `aria-hidden` e o dado em texto no contexto.
3. THE títulos de obra em alfabeto não latino SHALL herdar `lang` e `dir` corretos dos componentes da S1.
4. THE texto SHALL manter contraste de ao menos 4.5:1 sobre `--ground` e, sobre cor de idioma, usar o par fundo/texto do handoff §3.2.
5. THE carrosséis SHALL ser navegáveis por teclado e não depender de rolagem automática.
6. THE payload de JavaScript do Início SHALL se limitar à ilha de busca; nenhuma outra parte da tela SHALL exigir JS para ler ou navegar.

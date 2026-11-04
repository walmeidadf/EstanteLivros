# Requisitos — Obra e Autoria (S5)

## Introdução

Quinta spec da F3 (o app). Fecha a última **dívida de rota** das telas
anteriores: `/obra/{slug}` e `/autoria/{slug}`. Hoje quase todos os links do
app (capas das grades de Ano, Sem data, Idioma, País e Tema; avatares de
"Quem ela mais lê", de "quem sempre volta" e das páginas de Idioma e País; e
os resultados da busca) apontam para essas rotas e caem no Início, porque não
existe `404.astro` e o Cloudflare Pages serve o `index.html` para rotas
desconhecidas.

A S1 deixou a fundação (tokens, cor por idioma, `getCatalog()`, componentes
base). A S2 entregou Início e busca; a S3, Linha do tempo e Ano; a S4, Atlas,
Idioma, País e Tema. A convenção vigente é manter a regra de seleção em
`src/lib` e as páginas `.astro` burras.

### Escopo da S5

| Rota | Tela | Handoff | Páginas |
|---|---|---|---|
| `/obra/{slug}` | Obra | §6.9 | 302 |
| `/autoria/{slug}` | Autoria | §6.8 | 215 |

517 páginas novas, uma por entrada do índice de busca. Mais a camada de
seleção delas em `src/lib` (`work-page.ts` e `author-page.ts`, nomes a
confirmar no design) e três acréscimos aditivos ao modelo (Requisito 13).

### Decisões de escopo (aprovadas)

1. **Crédito da foto:** a foto do Commons leva uma linha de crédito bem
   discreta (autor, licença, link da fonte) sob o retrato.
2. **ISBN** em 13 dígitos, **sem hífens** (hifenizar certo exige tabela de
   faixas; errar parece erro de dado).
3. **Nota do catalogador** e **"Como estava no caderno"** ficam **visíveis**
   na página da Obra, sem `<details>`.
4. **Edição lida:** `edition.match = exact` usa o rótulo "Edição lida".
5. **Posição no ranking** com empate compartilhado, marcada como "empatada".
6. **Voltar** é um link fixo "‹ Estante" para `/`.

### Fora do escopo

- PWA e offline → S6. Retrospectiva e "Compartilhar" → S7. **Sem botão, link
  ou stub** de compartilhar em nenhuma das duas telas.
- Capas reais de obra, resumos de ano e país, normalização de temas → frente
  de F2. As telas funcionam sem eles (capa tipográfica; blocos somem).
- Páginas de gênero; hifenização de ISBN; `404.astro` (mudaria o
  comportamento atual do Pages; decisão à parte).
- Modo de revisão para `confidence = medium` (handoff §8).
- "Outras obras da autoria" dentro da página da Obra.
- Mudanças na ilha ou no formato do índice de busca.

### Glossário

- **Ordem do caderno:** `sequence` da primeira leitura da obra.
- **Leitura datada / sem data:** com ou sem `year` (só o ano existe; nunca dia
  ou mês).
- **Posição (da autoria):** `1 + número de autorias com estritamente mais
  leituras`. Empates compartilham a posição.
- **Handoff:** `design/DESIGN_HANDOFF.md`; as seções citadas referem-se a ele.

### Números do catálogo que embasam as decisões

302 obras · 215 autorias · 309 leituras (53 sem ano) · 185 obras com título
original (8 com romanização, 11 iguais ao título pt-BR) · ISBN em 290, editora
em 300, ano da edição em 298, primeira publicação em 301 · edições: 292
`representative` e 10 `exact`; idioma da edição: 300 português, 2 inglês · 7
obras lidas duas vezes · 1 obra com duas autorias · autorias por leituras: 8
(1), 7 (1), 6 (1), 4 (5), 3 (12), 2 (39), 1 (156) · 156 autorias com uma só
leitura · 41 sem foto · 13 sem país · 1 com mais de um idioma · 209 bios
aprovadas, todas com fonte e URL de fonte · `catalogerNote` nas 302 obras ·
nenhuma leitura com `notes`.

### Referências de design

Fonte de verdade visual: #[[file:design/DESIGN_HANDOFF.md]]
Contexto e dados: #[[file:design/DESIGN_BRIEF.md]]
Fundação: #[[file:docs/specs/estante-fundacao/design.md]]
Atlas (componentes reusados): #[[file:docs/specs/atlas/design.md]]
Handover que originou esta spec: #[[file:docs/plans/handover-s4-s5.md]]

## Requisitos

### Requisito 1 — Rotas, geração e navegação

**História:** Como leitora, quero que toda capa, avatar e resultado de busca
leve à página certa, para não cair no Início sem querer.

#### Critérios de aceitação

1. THE app SHALL gerar `/obra/{slug}` para cada obra do catálogo (hoje 302) e `/autoria/{slug}` para cada autoria (hoje 215), com o `slug` do próprio catálogo.
2. THE rotas SHALL usar o mesmo formato de `href` que as telas anteriores já emitem (`workHref` e `authorHref`); SHALL NOT ser alterado o destino de nenhum link existente.
3. THE cada página SHALL ter um `<title>` próprio (título da obra ou nome da autoria) e uma única `h1`.
4. THE cada página SHALL ter, no topo, o link "‹ Estante" para `/`, com alvo de toque ≥ 44 px (handoff §3.4).
5. THE páginas SHALL renderizar sem JavaScript, ser mobile-first e usar a margem lateral do handoff §3.4. THE S5 SHALL NOT adicionar nenhum `<script>`.
6. THE páginas SHALL consumir os dados por `getCatalog()`; SHALL NOT reler o catálogo do disco, chamar APIs externas ou fazer hotlink de imagens.
7. THE regra de seleção e formatação (o que mostrar, em que ordem, com que texto) SHALL ficar em `src/lib`, testada sem DOM; as páginas `.astro` SHALL só compor componentes.
8. THE grades SHALL usar `grid-template-columns: repeat(N, minmax(0, 1fr))` e itens com `min-width: 0`, para que um título com palavra longa não alargue a coluna no celular.
9. THE dado ausente SHALL fazer a linha ou o bloco correspondente sumir; SHALL NOT aparecer "—", "não informado" ou texto de erro (handoff §8).

### Requisito 2 — Obra · topo

**História:** Como leitora, quero ver a capa, o título e a autoria de um livro
logo ao abrir a página.

#### Critérios de aceitação

1. THE página SHALL mostrar a capa em tamanho grande apoiada na `Shelf`. WHERE a obra não tiver imagem local, THE capa SHALL ser a tipográfica (handoff §4/§8); a `cover.sourceUrl` SHALL NOT virar `src`.
2. WHERE a obra tiver mais de uma leitura, THE capa SHALL levar o selo "2×" (ou "N×").
3. THE título em pt-BR SHALL ser a `h1`, em Bodoni itálico, sem truncar (o limite de 2 linhas vale só para rótulos de grade).
4. WHERE a obra tiver `originalTitle` e ele for diferente do título pt-BR (comparação sem caixa e sem acento), THE página SHALL mostrar o título original abaixo do título, com `lang` (quando `languageTag` o conhecer), `dir="rtl"` para hebraico e árabe e a fonte Noto do alfabeto; a regra de `lang` é a de `originalTitleLang`.
5. WHERE a obra tiver `originalTitleRomanized`, THE página SHALL mostrá-lo numa linha menor logo abaixo do título original, sem `lang` de idioma não latino.
6. WHERE a obra não tiver título original (ou ele for igual ao pt-BR), THE linha SHALL sumir e nada a substitui.
7. THE autoria SHALL aparecer com `AuthorChip layout="row"` (avatar, nome), levando a `/autoria/{slug}`; WHERE a obra tiver mais de uma autoria, SHALL haver um chip por autoria, na ordem do catálogo.

### Requisito 3 — Obra · ficha

**História:** Como leitora, quero os dados básicos do livro em um bloco curto.

#### Critérios de aceitação

1. THE ficha SHALL ser uma lista de rótulo e valor com as linhas abaixo, na ordem: **Idioma original**, **País**, **Primeira publicação**, **Tipo**, **Gêneros**.
2. THE linha "Idioma original" SHALL ser um link para `languageHref(idioma)`.
3. THE linha "País" SHALL listar o país de cada autoria da obra (`countries`), cada um um link para `countryHref(nome)`; WHERE nenhuma autoria tiver país, THE linha SHALL sumir.
4. THE linha "Primeira publicação" SHALL mostrar o ano (`firstPublished`) e sumir quando for nulo.
5. THE "Tipo" e os "Gêneros" SHALL aparecer como texto com a primeira letra maiúscula (`capitalizeFirst`), não como links (não há páginas de tipo ou gênero). WHERE não houver gêneros, THE linha SHALL sumir.

### Requisito 4 — Obra · leituras

**História:** Como leitora, quero ver quando li cada livro e se foi releitura.

#### Critérios de aceitação

1. THE título da seção SHALL acompanhar a quantidade de leituras: "Lido uma vez", "Lido duas vezes", "Lido N vezes" (N ≥ 3).
2. THE seção SHALL ter uma linha por leitura, em ordem crescente de `sequence`.
3. WHERE a leitura tiver ano, THE linha SHALL mostrar o ano como link para `/ano/{ano}`; WHERE não tiver, THE linha SHALL mostrar "Entre os primeiros da lista" como link para `/ano/sem-data`. SHALL NOT aparecer dia ou mês.
4. THE cada linha SHALL mostrar "primeira leitura" (a primeira da ordem) ou "releitura" (as demais), definido pela posição na ordem e **não** pelo campo `reread`, e "nº {sequence} da lista".
5. THE obra de uma só leitura SHALL mostrar uma única linha, sem rótulo de releitura.

### Requisito 5 — Obra · temas

**História:** Como leitora, quero chegar a outros livros do mesmo tema.

#### Critérios de aceitação

1. THE seção "Temas" SHALL mostrar um chip por tema da obra, cada um um `<a href>` para `themeHref(tema)`, com alvo de toque ≥ 44 px e o rótulo com a primeira letra maiúscula.
2. THE temas da obra que, agrupados pelo slug (variantes de caixa e acento contam juntas), tiverem **5 ou mais obras** na estante SHALL mostrar a contagem junto ao rótulo; os demais SHALL NOT mostrar contagem.
3. THE ordem dos chips SHALL ser por contagem de obras decrescente e, no empate, pela ordem do catálogo; determinística entre builds.
4. WHERE a obra não tiver temas, THE seção SHALL sumir.
5. THE link de cada tema SHALL apontar para uma página existente (a S4 gera uma página por slug de tema).

### Requisito 6 — Obra · edição

**História:** Como leitora, quero saber qual edição serviu de referência.

#### Critérios de aceitação

1. THE caixa de edição SHALL mostrar, quando existirem: **Editora**, **Ano** (`edition.year`) e **ISBN** (`isbn13`, 13 dígitos, sem hífens). Cada linha sem dado SHALL sumir; WHERE nenhuma existir, THE caixa inteira SHALL sumir.
2. WHERE `edition.match = representative`, THE rótulo da caixa SHALL ser "Edição brasileira de referência" se o idioma da edição for português, e "Edição de referência" nos demais casos. O rótulo SHALL NOT afirmar que foi a edição que ela leu.
3. WHERE `edition.match = exact`, THE rótulo SHALL ser "Edição lida".
4. THE ISBN SHALL NOT ser link nem ter botão de copiar.

### Requisito 7 — Obra · registro do catálogo

**História:** Como leitora, quero ver a nota do catalogador e como o livro
estava no caderno.

#### Critérios de aceitação

1. WHERE a obra tiver `catalogerNote`, THE página SHALL mostrar o bloco "Nota do catalogador" com o texto, **visível** (sem `<details>`).
2. THE bloco "Como estava no caderno" SHALL mostrar o `originalEntry` de cada leitura, na ordem de `sequence`, como citação (`<blockquote>`); WHERE a obra tiver várias leituras, cada entrada SHALL ser identificada pela leitura (ano ou "nº N da lista").
3. THE textos SHALL ser mostrados como estão no catálogo, sem reescrever.
4. WHERE `confidence = medium`, THE página SHALL NOT mostrar nenhum sinal visual (handoff §8).
5. THE blocos SHALL vir depois de Leituras, Temas e Edição, com hierarquia visual mais discreta que o conteúdo principal.

### Requisito 8 — Autoria · cabeçalho

**História:** Como leitora, quero ver quem é a autoria, de onde vem e em que
língua escreve.

#### Critérios de aceitação

1. THE retrato SHALL ser a foto derivada em 1:1 quando houver mestre local, senão o `InitialsAvatar` de iniciais; nos dois casos com 132 px e **anel na cor do idioma principal** da autoria.
2. WHERE a foto for exibida e houver dados de crédito (`author`, `license`, `sourceUrl`), THE página SHALL mostrar, sob o retrato, uma linha de crédito discreta (texto pequeno, cor `--faint`) com autor, licença e um link para a fonte; campos nulos SHALL ser omitidos. WHERE o avatar de iniciais for exibido, SHALL NOT haver crédito.
3. THE nome SHALL ser a `h1`, em Bodoni itálico.
4. THE linha de contexto SHALL ser "{País} · escreve em {idiomas}", com o país como link para `countryHref(nome)` e cada idioma como link para `languageHref(idioma)`. WHERE a autoria não tiver país, THE linha SHALL ser só "Escreve em {idiomas}".
5. THE links de idioma SHALL usar a cor padrão de link do app; a cor do idioma como **texto** sobre o fundo escuro SHALL passar por `onGround` (contraste ≥ 4,5:1).

### Requisito 9 — Autoria · números e posição

**História:** Como leitora, quero ver o peso da autoria na minha estante.

#### Critérios de aceitação

1. THE bloco de números SHALL usar `BigNumbers`, com a ordem: **livros lidos**, **posição**, **primeira leitura**; os itens sem dado SHALL ser omitidos e o bloco usa tantas colunas quanto itens.
2. THE "livros lidos" SHALL ser o número de **obras distintas** da autoria, com singular e plural corretos ("1 livro lido" / "N livros lidos").
3. THE posição SHALL ser calculada por **leituras** (mesmo critério de `readingsByAuthor` e de "Quem ela mais lê"), como `1 + número de autorias com estritamente mais leituras`.
4. WHERE a posição for **10 ou menos**, THE bloco SHALL mostrar "{N}º" com o rótulo "posição na estante". WHERE outra autoria tiver a mesma contagem de leituras, THE rótulo SHALL ser "posição na estante (empatada)".
5. WHERE a posição for maior que 10, THE posição SHALL ser omitida e SHALL NOT ser substituída por texto.
6. THE "primeira leitura" SHALL mostrar o menor ano entre as leituras datadas da autoria e SHALL ser omitida quando todas as leituras forem sem data.
7. THE posição exibida SHALL poder diferir da ordem de "Quem ela mais lê" do Atlas dentro de um empate (o Atlas desempata por nome para cortar em 10). A diferença SHALL ser registrada na documentação do design, não corrigida na S5.

### Requisito 10 — Autoria · bio

**História:** Como leitora, quero uma apresentação curta da autoria, com a fonte.

#### Critérios de aceitação

1. WHERE a autoria tiver bio aprovada, THE página SHALL mostrar a seção "Sobre" com o texto da bio.
2. WHERE a bio tiver fonte, THE seção SHALL mostrar embaixo "Fonte: {rótulo}" (ex.: "Wikipédia (pt)"), como link para a URL da fonte quando ela existir.
3. WHERE a autoria não tiver bio aprovada, THE seção "Sobre" inteira SHALL sumir; a fonte SHALL NOT aparecer sozinha.
4. THE bio não aprovada SHALL NOT ser exibida em nenhuma circunstância.

### Requisito 11 — Autoria · "Na estante da Lila"

**História:** Como leitora, quero ver todos os livros da autoria que li e
quando.

#### Critérios de aceitação

1. THE seção "Na estante da Lila" SHALL mostrar uma grade de 3 colunas com todas as obras da autoria, na ordem do caderno, reaproveitando `WorkGrid`.
2. THE `WorkGrid` SHALL ganhar uma legenda opcional por item (sem alterar o HTML das telas que não a usam, verificado por diff contra a `main`).
3. THE legenda SHALL listar cada leitura: "lido em {ano}" para leitura datada e "nº {N} da lista" para sem data. WHERE houver várias leituras, THE legenda SHALL juntá-las em uma frase ("lido em 2022 e 2025").
4. THE cada item SHALL levar a `/obra/{slug}`; o selo "2×" SHALL aparecer em obras com mais de uma leitura.
5. THE grade SHALL NOT ter ordenação nem script.

### Requisito 12 — Autoria · temas que mais aparecem

**História:** Como leitora, quero ver os temas que mais se repetem nos livros
dessa autoria.

#### Critérios de aceitação

1. THE seção "Temas que mais aparecem" SHALL contar os temas por **obra** da autoria, agrupando variantes de caixa e acento pelo slug.
2. THE seção SHALL mostrar só temas presentes em **2 ou mais** obras da autoria, até **10**, por contagem decrescente e, no empate, pelo nome (pt-BR).
3. THE cada tema SHALL ser um chip para `themeHref(tema)` com a contagem de obras da autoria.
4. WHERE nenhum tema atingir o piso (caso de toda autoria com um só livro), THE seção SHALL sumir.

### Requisito 13 — Acréscimos ao modelo de dados

**História:** Como desenvolvedora, quero expor ao modelo só o que as páginas
precisam, sem mexer em nada do que já existe.

#### Critérios de aceitação

1. THE `ReadingView` SHALL ganhar `originalEntry` (texto do caderno daquela leitura).
2. THE `AuthorView` SHALL ganhar `bioSource` (`{ label, url }` do summary aprovado, ou `null`) e a foto SHALL expor também `author`, `license` e `sourceUrl`.
3. THE mudanças SHALL ser aditivas: SHALL NOT remover ou renomear campo, e os testes existentes de `lib/catalog/` SHALL continuar verdes sem alteração de expectativa.
4. THE agregados SHALL NOT mudar; a posição da autoria SHALL ser derivada de `readingsByAuthor` na camada de seleção.
5. THE `approvedSummaryByScope` SHALL continuar sendo a única fonte da aprovação; a fonte da bio SHALL vir do mesmo summary aprovado.

### Requisito 14 — Busca e integridade dos links

**História:** Como leitora, quero que cada resultado da busca abra a página
do livro ou da autoria.

#### Critérios de aceitação

1. THE índice de busca e a ilha SHALL permanecer inalterados; os resultados continuam mostrando rótulo e tipo ("Livro" ou "Autoria") e passam a abrir as páginas da S5.
2. THE conjunto de testes SHALL incluir uma verificação de integridade: todo `href` do índice e todo `href` `/obra/…` e `/autoria/…` emitido pelas camadas `home`, `timeline` e `atlas` SHALL corresponder a uma página gerada pela S5.
3. THE build do catálogo real SHALL sair com código 0 e gerar as 517 páginas novas (563 → 1080 no total).

### Requisito 15 — Acessibilidade e conteúdo

**História:** Como leitora (e visitante), quero páginas legíveis e navegáveis
por teclado e leitor de tela.

#### Critérios de aceitação

1. THE links e chips SHALL ter alvo de toque ≥ 44 px e foco visível; a navegação SHALL usar `<a href>` para destinos e nenhum `<button>` sem ação.
2. THE texto sobre fundo colorido ou escuro SHALL ter contraste ≥ 4,5:1 (`onGround` quando a cor do idioma for texto).
3. THE capas e retratos SHALL ter `alt` útil: a capa descreve "Capa de {título}" e o retrato "{nome}"; imagens decorativas (anel, prateleira) SHALL ter `alt=""` ou `aria-hidden`.
4. THE títulos de seção SHALL seguir a hierarquia `h1` > `h2`, sem pular nível.
5. THE texto da interface SHALL estar em pt-BR; identificadores de código SHALL estar em inglês.

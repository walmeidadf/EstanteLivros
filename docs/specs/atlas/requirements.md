# Requisitos — Atlas (S4)

## Introdução

Quarta spec da F3 (o app). Fecha duas **dívidas de rota** que a S2 deixou:
`/atlas` (chip do cabeçalho) e `/tema/{slug}` (carrosséis de tema do Início)
hoje dão 404. A S4 também cria as páginas que o Atlas alcança: Idioma e País.

A S1 deixou a fundação (tokens, cor por idioma, `getCatalog()` com modelo e
agregados, componentes base). A S2 entregou o Início e a busca; a S3, a Linha
do tempo, Ano e Sem data, incluindo o componente **`YearBand`** (Faixa do ano),
genérico e feito para ser reusado aqui. A convenção vigente é manter a regra de
seleção em `src/lib` (como `home.ts` e `timeline.ts`) e as páginas `.astro`
burras.

### Escopo da S4

Seis rotas estáticas e a camada de seleção delas:

| Rota | Tela | Handoff |
|---|---|---|
| `/atlas` | Atlas · por idioma (padrão) | §6.4 |
| `/atlas/pais` | Atlas · por país | §6.5 |
| `/idioma/{slug}` | Idioma (ver todos) — 15 páginas | §6.6 |
| `/pais/{slug}` | País (ver todos) — 36 páginas | §6.7 |
| `/tema/{slug}` | Tema (ver todos) — uma por tema | §6.11 |

Mais três blocos compartilhados pelas duas vistas do Atlas: **Quem ela mais
lê**, **Temas que voltam** e **Quando foram escritos**.

### Decisões de escopo propostas (a confirmar)

1. **Alternador Idioma | País = duas rotas estáticas, não query string.** O
   handoff diz `/atlas?por=idioma|pais`, mas o site é estático: a query não
   chega ao HTML, então um alternador por query exigiria JavaScript para
   esconder/mostrar blocos, duplicaria o DOM e quebraria "funciona sem JS"
   (handoff §10). Com rotas separadas (`/atlas` e `/atlas/pais`), o alternador
   é um par de links (`aria-current` na ativa), vale offline na PWA (S6), tem
   botão voltar correto e link compartilhável. **Desvio do handoff §6.4/§6.5**,
   registrado aqui e a ser anotado no handoff ao concluir.
2. **Os três blocos de baixo aparecem nas duas vistas.** Não dependem do
   alternador; repetir evita que a vista de país pareça incompleta.
3. **País com poucas obras:** as 10 maiores faixas de país aparecem sozinhas;
   o resto vira um bloco **"Outros países"** (faixa de lombadas + chips
   clicáveis), para que todos os 36 países continuem alcançáveis.
4. **Tema: todos os temas ganham página**, não só os mais frequentes. Há 496
   temas (333 com uma única obra); páginas pequenas são baratas e evitam que a
   página Obra (S5) linke temas que dão 404. A nuvem do Atlas e o Início
   mostram só os mais frequentes.
5. **Ordenação da grade (Idioma e Tema) é uma ilha vanilla mínima**, como a
   busca da S2. Sem JS a grade fica na ordem do caderno e os controles de
   ordenação não aparecem. Alternativa descartada: quatro grades no HTML.
6. **Obras sem país** (13 de 302: autorias sem país identificado) não entram
   na vista por país, sem aviso nem "—" (handoff §8). Continuam em Idioma, Tema
   e nos outros blocos.
7. **Países que "compartilham idioma"** (chips da página País) são os que têm
   o **mesmo idioma original dominante nas obras da estante** (ex.: Brasil ↔
   Portugal, Angola, Moçambique). Não depende de ampliar o modelo de dados.
8. **Variantes de caixa do mesmo tema** ("Segunda Guerra Mundial" /
   "segunda guerra mundial", "Nordeste", "Guerra Fria") hoje são temas
   distintos no catálogo e colidiriam no slug. A S4 agrupa por slug na camada
   de seleção. A correção na origem (vocabulário do catálogo) é tarefa de
   pipeline, fora da S4.

### Fora do escopo

- Obra e Autoria (`/obra/{slug}`, `/autoria/{slug}`) → S5. Os links saem no
  formato final e **dão 404 temporário**, como na S2/S3.
- PWA/offline → S6. Retrospectiva e "Compartilhar" → S7.
- Mapa-múndi ou qualquer visual geográfico (o handoff não pede).
- Capas de obra (frente de F2) e resumos de país (frente de F2): as telas
  funcionam sem eles (capa tipográfica; bloco de resumo some).
- Corrigir variantes de tema no catálogo (pipeline).
- Busca por tema/idioma/país no índice da S2.

### Glossário

- **Faixa**: instância do `YearBand` (S3) com rótulo, contagem "N ›", notas
  (vazias aqui) e fileira de lombadas sobre a prateleira.
- **Idioma dominante de um país**: o idioma original mais frequente entre as
  obras daquele país; empate pelo nome do idioma (pt-BR).
- **Época**: faixa de `firstPublished` do bloco "Quando foram escritos".
- **Ordem do caderno**: `sequence` da primeira leitura da obra.
- **Handoff**: `design/DESIGN_HANDOFF.md`; as seções citadas referem-se a ele.

### Números do catálogo que embasam as decisões

302 obras · 15 idiomas originais (português 115, inglês 81, espanhol 30,
francês 28, italiano 12, russo 9, japonês 6, coreano/hebraico/alemão 5,
norueguês 2, catalão/tcheco/árabe/holandês 1) · 36 países (BR 95, US 44, FR 23,
GB 18, IT 12, PT/ES 9, RU/CO 8, JP 6; os outros 26 têm ≤ 5) · 13 obras sem país
· 496 temas (52 com ≥ 5 obras) · `firstPublished`: 20 antes de 1900, 88 no séc.
XX, 48 nos 2000s, 94 nos 2010s, 51 nos 2020s, 1 sem ano.

### Referências de design

Fonte de verdade visual: #[[file:design/DESIGN_HANDOFF.md]]
Contexto e dados: #[[file:design/DESIGN_BRIEF.md]]
Fundação: #[[file:docs/specs/estante-fundacao/design.md]]
Componente reusado: #[[file:docs/specs/linha-do-tempo/design.md]]
Handover que originou esta spec: #[[file:docs/plans/handover-s3-s4.md]]

## Requisitos

### Requisito 1 — Atlas e alternador Idioma | País

**História:** Como leitora, quero abrir o Atlas e alternar entre ver a estante
por idioma e por país, para explorá-la por origem.

#### Critérios de aceitação

1. THE app SHALL servir o Atlas por idioma em `/atlas` e o Atlas por país em `/atlas/pais`, fechando o 404 de `/atlas` que a S2 deixou.
2. THE duas vistas SHALL mostrar o título da tela e um alternador "Idioma original | País" composto por dois `<a href>` (padrão: idioma), com a vista atual marcada por `aria-current="page"` e estilo ativo (`--accent`), alvos de toque ≥ 44 px (handoff §3.4).
3. THE Atlas SHALL renderizar sem JavaScript e SHALL ser mobile-first, com a margem lateral do handoff §3.4.
4. THE chip "Atlas" do cabeçalho (S2) SHALL levar a `/atlas` sem alteração de contrato.
5. IF a URL pedida for `/atlas?por=pais`, THEN THE app SHALL servir `/atlas` (a query é ignorada pelo host estático); SHALL NOT existir script de redirecionamento só para isso.
6. THE vistas SHALL consumir os dados por `getCatalog()`; SHALL NOT reler o catálogo do disco nem recalcular agregados que a S1 já expõe.

### Requisito 2 — Atlas · por idioma

**História:** Como leitora, quero ver quantas obras li em cada idioma original
e como elas se distribuem, para sentir o peso de cada língua.

#### Critérios de aceitação

1. THE vista por idioma SHALL mostrar uma Faixa (`YearBand`) por idioma original com ao menos uma obra, ordenadas por quantidade decrescente; empate pelo nome do idioma (pt-BR).
2. THE cada faixa SHALL ter como rótulo o nome do idioma (Bodoni), a contagem de **obras** "N ›" em `--accent` (não de leituras) e uma lombada mini por obra, na cor do idioma, na ordem do caderno.
3. THE cada faixa SHALL levar a `/idioma/{slug}`.
4. THE faixas SHALL NOT mostrar notas (lista de notas vazia).
5. THE vista SHALL listar todos os idiomas, sem agrupar; idiomas sem cor própria usam o fallback "outros" (handoff §3.2) sem erro.
6. WHERE uma faixa tiver mais lombadas do que cabem numa linha, THE fileira SHALL continuar legível dentro da largura da tela (quebra em linhas ou compressão), sem rolagem horizontal da página.

### Requisito 3 — Atlas · por país

**História:** Como leitora, quero ver de que países vêm os livros que li, na
mesma linguagem da Linha do tempo.

#### Critérios de aceitação

1. THE vista por país SHALL mostrar uma Faixa por país, ordenadas por quantidade de obras decrescente; empate pelo nome do país (pt-BR), para builds reproduzíveis.
2. THE país de uma obra SHALL ser o país da(s) **autoria(s)**; uma obra com autorias de países diferentes SHALL contar e aparecer em cada um deles (handoff §6.5).
3. THE cada faixa SHALL ter como rótulo o nome do país, a contagem "N ›" e uma lombada mini por obra, **na cor do idioma original de cada obra** (as cores podem variar dentro da faixa), na ordem do caderno.
4. THE cada faixa SHALL levar a `/pais/{slug}`.
5. THE vista SHALL mostrar individualmente as 10 maiores faixas; os países restantes SHALL ser reunidos no bloco "Outros países", depois delas.
6. THE bloco "Outros países" SHALL mostrar uma faixa com uma lombada por obra **distinta** dos países agrupados e a contagem de obras distintas, e abaixo dela um chip por país agrupado (nome e contagem), cada um levando a `/pais/{slug}`, em ordem decrescente de quantidade.
7. WHERE o agrupamento teria um único país, THE vista SHALL mostrá-lo como faixa individual, sem bloco "Outros países".
8. WHERE o catálogo tiver 10 países ou menos, THE bloco "Outros países" SHALL NOT aparecer.
9. THE obras sem país identificado SHALL NOT aparecer nesta vista nem ser sinalizadas com texto de erro ou "—" (handoff §8).
10. THE faixa "Outros países" em si SHALL NOT ser um link (não existe página que a represente); a navegação é pelos chips.

### Requisito 4 — Bloco "Quem ela mais lê"

**História:** Como leitora, quero ver as autorias que mais apareceram, para
lembrar quem eu sempre volto a ler.

#### Critérios de aceitação

1. THE Atlas SHALL mostrar, nas duas vistas, uma lista das 10 autorias com mais leituras, cada uma com avatar (foto, quando houver, senão iniciais na cor do idioma principal), nome e contagem de leituras.
2. THE ordem SHALL ser por leituras decrescente; empate estável por nome (pt-BR). A contagem SHALL ser a mesma de "quem sempre volta" (S2), isto é, `readingsByAuthor`.
3. THE cada item SHALL ser um `<a href>` para `/autoria/{slug}` (rota da S5; 404 temporário aceito).
4. THE texto da contagem SHALL usar o singular/plural corretos em pt-BR.
5. WHERE o catálogo tiver menos de 10 autorias, THE lista SHALL mostrar as que existirem; WHERE não houver nenhuma, THE bloco SHALL ser omitido.

### Requisito 5 — Bloco "Temas que voltam"

**História:** Como leitora, quero ver os temas mais recorrentes de relance, para
perceber o que me atrai.

#### Critérios de aceitação

1. THE Atlas SHALL mostrar, nas duas vistas, uma nuvem tipográfica com os temas mais frequentes (limite fixo na camada de seleção, definido no design) e piso mínimo de obras por tema.
2. THE tamanho de cada tema SHALL ser proporcional à frequência, em poucos degraus discretos; os degraus maiores SHALL usar itálico e `--accent` (handoff §6.4). A cor SHALL NOT ser o único indicador de ênfase (o tamanho também varia).
3. THE temas SHALL ser contados por **obra**, agrupando variantes que diferem só por caixa ou acento (mesmo slug); o rótulo exibido é a variante mais frequente (empate: a minúscula).
4. THE cada tema SHALL ser um `<a href>` para `/tema/{slug}` (Requisito 9), alvo de toque ≥ 44 px.
5. THE ordem de exibição na nuvem SHALL ser determinística entre builds.
6. WHERE nenhum tema atingir o piso, THE bloco SHALL ser omitido.

### Requisito 6 — Bloco "Quando foram escritos"

**História:** Como leitora, quero ver em que épocas foram escritos os livros que
li, para saber se leio mais o antigo ou o contemporâneo.

#### Critérios de aceitação

1. THE Atlas SHALL mostrar, nas duas vistas, barras por época calculadas por obra a partir de `firstPublished`: **séc. XIX** (de 1800 a 1899), **séc. XX** (1900–1999), **2000s**, **2010s**, **2020s**.
2. WHERE existirem obras anteriores a 1800, THE bloco SHALL incluir também a época "antes de 1800", antes de "séc. XIX"; WHERE não existirem, a época SHALL NOT aparecer.
3. THE barras SHALL ser proporcionais ao maior valor, em ordem cronológica, com a contagem em texto em cada barra; SHALL NOT depender só de cor ou de altura para transmitir o número.
4. THE obras sem `firstPublished` SHALL ser ignoradas nas barras, sem aviso na tela.
5. THE épocas sem obras SHALL aparecer com contagem 0 e barra vazia, para a escala cronológica não ter buracos, exceto "antes de 1800" (item 2).
6. THE barras SHALL NOT ser links (não há página de destino).
7. THE bloco SHALL ter alternativa textual acessível (lista ou tabela legível por leitor de tela), e a parte visual das barras SHALL ser decorativa (`aria-hidden`) quando duplicar essa informação.

### Requisito 7 — Tela Idioma

**História:** Como leitora, quero ver todas as obras de um idioma original, com
os números dele, para folhear a estante por língua.

#### Critérios de aceitação

1. THE app SHALL servir `/idioma/{slug}` para cada idioma original com ao menos uma obra (hoje 15), com `slug` derivado do nome do idioma sem acento e em minúsculas.
2. THE cabeçalho SHALL ser um bloco na **cor do idioma** (fundo e texto da tabela do handoff §3.2), com o rótulo "Idioma original" e o nome do idioma em Bodoni itálico (78 px no desktop; reduzindo no celular se não couber), e **sem texto descritivo** (handoff §6.6).
3. THE cabeçalho SHALL mostrar big numbers: **obras** (obras com o idioma) · **% da estante** (obras do idioma ÷ total de obras, inteiro arredondado; "<1%" quando maior que zero e menor que 1) · **autorias** (autorias distintas das obras do idioma).
4. THE tela SHALL mostrar um carrossel de avatares (`AuthorChip`) das autorias das obras do idioma, ordenadas pelo nº de obras delas naquele idioma (desc; empate por nome), com o teto de itens do handoff §9; WHERE houver uma única autoria ou nenhuma, o carrossel SHALL ser omitido.
5. THE tela SHALL mostrar a grade de 3 colunas com **uma peça por obra** (releitura = uma capa com selo "2×"), cada uma com título pt-BR e, abaixo, o **título original** em itálico com atributo `lang` do idioma (e `dir="rtl"` para hebraico e árabe); WHERE a obra não tiver título original, a linha SHALL sumir.
6. THE títulos originais em coreano, japonês ou hebraico SHALL usar a fonte Noto correspondente (handoff §8), carregada só quando o alfabeto aparecer.
7. THE tela SHALL oferecer a ordenação do Requisito 10 e um link de voltar para `/atlas`.
8. THE capas SHALL usar a Capa/Capa tipográfica da S1 (fallback quando não houver imagem); SHALL NOT fazer hotlink de imagens externas.
9. THE cada peça da grade SHALL levar a `/obra/{slug}` (S5; 404 temporário aceito).

### Requisito 8 — Tela País

**História:** Como leitora, quero ver todas as obras de autorias de um país, com
os números dele, para folhear a estante por origem.

#### Critérios de aceitação

1. THE app SHALL servir `/pais/{slug}` para cada país com ao menos uma obra (hoje 36), com `slug` derivado do nome do país em pt-BR sem acento, em minúsculas e com hífens; slugs duplicados SHALL falhar o build, não ser silenciados.
2. THE tela SHALL mostrar um link de voltar para `/atlas/pais`.
3. THE tela SHALL mostrar o nome do país em Bodoni 700, na cor do **idioma dominante** do país (Glossário), garantindo contraste legível sobre o fundo (≥ 4.5:1, ou variante/alternativa quando a cor do idioma não passar).
4. WHERE existirem outros países com obras e o mesmo idioma dominante, THE tela SHALL mostrar chips com esses países (nome e link para `/pais/{slug}`), em ordem decrescente de quantidade; caso contrário a linha SHALL ser omitida.
5. WHERE existir summary `approved` de scope `pais:{código}` (`approvedSummaryByScope`), THE tela SHALL mostrar a frase; caso contrário o bloco SHALL ser omitido, sem texto de preenchimento (handoff §8).
6. THE tela SHALL mostrar big numbers: **obras** · **autorias** (as do país).
7. WHERE uma única autoria do país tiver o maior número de leituras (valor ≥ 2), THE tela SHALL destacá-la (avatar, nome, contagem, link para `/autoria/{slug}`); em caso de empate no topo ou máximo igual a 1, o destaque SHALL ser omitido.
8. THE tela SHALL mostrar a grade de 3 colunas com uma peça por obra do país, na ordem do caderno, cada uma levando a `/obra/{slug}`; uma obra com autorias de países diferentes aparece em cada página de país correspondente.
9. THE tela SHALL usar o código do país apenas para consultar o resumo e SHALL NOT mostrá-lo ao visitante.

### Requisito 9 — Tela Tema

**História:** Como leitora, quero ver todas as obras de um tema, para seguir um
assunto que me interessa (e o link do carrossel do Início passa a funcionar).

#### Critérios de aceitação

1. THE app SHALL servir `/tema/{slug}` para cada tema (agrupado por slug, Requisito 5.3) com ao menos uma obra, fechando o 404 que a S2 deixou; o `slug` SHALL ser o mesmo que o Início e a nuvem já geram (`slugifyTheme`).
2. THE tela SHALL usar o template de Idioma (Requisito 7), com cabeçalho em fundo **escuro** (token de superfície do handoff §3.1) em vez de cor de idioma, o rótulo "Tema" e o nome do tema em Bodoni itálico.
3. THE cabeçalho SHALL mostrar big numbers: **obras** · **autorias** (distintas) · **idiomas** (originais distintos).
4. THE tela SHALL mostrar a grade de 3 colunas, uma peça por obra, com título pt-BR e título original como no Requisito 7.5, e a ordenação do Requisito 10.
5. THE tela SHALL mostrar um link de voltar para `/atlas`.
6. WHERE um tema tiver uma única obra, THE tela SHALL mostrar a grade normalmente, sem texto de preenchimento; os big numbers continuam coerentes (1 obra).
7. IF o nome exibido do tema vier em minúsculas do catálogo, THEN THE título SHALL capitalizar apenas a primeira letra na tela, sem alterar o dado.

### Requisito 10 — Ordenação da grade (Idioma e Tema)

**História:** Como leitora, quero reordenar a grade por lista, título, autoria
ou ano de publicação, para achar o que procuro.

#### Critérios de aceitação

1. THE grade SHALL ser entregue no HTML na **ordem do caderno** ("da lista"); sem JavaScript, ela SHALL ficar assim e os controles de ordenação SHALL NOT aparecer.
2. WHEN JavaScript estiver disponível, THE controles SHALL aparecer com as opções "Da lista" (padrão), "Título", "Autoria" e "Ano de publicação", como botões reais (`<button>`) com estado pressionado indicado (`aria-pressed`), alvos ≥ 44 px.
3. THE ordenações SHALL ser: lista = `sequence` da primeira leitura; título = título pt-BR (pt-BR, tolerante a acento); autoria = nome da primeira autoria (pt-BR), com título como desempate; ano = `firstPublished` crescente, com obras sem ano ao fim.
4. THE ordenação SHALL reordenar os elementos existentes (sem recriar peças nem buscar dados), preservar foco e estado dos links e SHALL ser estável.
5. THE ilha SHALL ser vanilla, mínima e SHALL NOT carregar framework nem rede; a escolha SHALL NOT ser persistida.
6. THE ordenação SHALL NOT existir na tela País (o handoff §6.7 não a pede) nem no Atlas.

### Requisito 11 — Camada de seleção (regra em `src/lib`)

**História:** Como desenvolvedor, quero a regra do Atlas isolada e testável, para
manter as páginas `.astro` burras, como em `home.ts` e `timeline.ts`.

#### Critérios de aceitação

1. THE app SHALL prover um módulo puro em `src/lib` (sem dependências de Astro, rodando sob `node --test`) com as funções que montam: as duas vistas do Atlas, os três blocos compartilhados, e os dados de Idioma, País e Tema.
2. THE módulo SHALL receber `getCatalog()` e SHALL NOT ler disco nem rede; SHALL NOT escrever em `catalog/`.
3. THE recortes sem conteúdo SHALL voltar como `null` (handoff §8), para a página omiti-los sem espalhar condicionais.
4. THE funções de slug e de href (idioma, país, tema) SHALL viver no módulo e ser as únicas fontes dessas rotas; o `slugifyTheme`/`themeHref` do Início SHALL ser reaproveitado, não duplicado.
5. THE geração das rotas estáticas (`getStaticPaths`) SHALL derivar de dados reais; SHALL falhar o build em colisão de slug de idioma ou país.
6. THE camada de dados da S1 SHALL permanecer inalterada, salvo extensão aditiva e retrocompatível justificada no design.
7. THE regras de contagem (obra por país, leitura por autoria, obra por idioma) SHALL ser coerentes com `aggregates.ts` e testadas contra o catálogo de exemplo, incluindo obra com duas autorias de países diferentes, tema com variantes de caixa, obra sem país e obra sem `firstPublished`.

### Requisito 12 — Estados, acessibilidade e entrega

**História:** Como leitora (Samsung Android) e como visitante, quero páginas
rápidas e legíveis, sem sinais de dado faltando.

#### Critérios de aceitação

1. THE telas SHALL ser estáticas; o único JavaScript novo SHALL ser a ilha de ordenação (Requisito 10), presente apenas em Idioma e Tema.
2. THE telas SHALL seguir o handoff §10: controles reais (`<a>`/`<button>`), um `<h1>` por página, hierarquia de títulos coerente, contraste ≥ 4.5:1 e texto sobre cor de idioma usando a coluna "Texto" de §3.2.
3. THE dados incompletos SHALL usar os fallbacks do design, nunca "—" nem "não informado" (handoff §8); só o **ano** de leitura existe, nunca dia ou mês.
4. THE telas SHALL NOT mostrar estrelas ou notas, e SHALL NOT fazer hotlink de imagens externas.
5. THE links para `/obra/{slug}` e `/autoria/{slug}` SHALL sair no formato final, aceitando o 404 temporário até a S5.
6. WHEN a S4 for publicada, `/atlas`, `/atlas/pais`, `/idioma/*`, `/pais/*` e `/tema/*` SHALL responder 200, e os links "Atlas" do cabeçalho e os carrosséis de tema do Início SHALL deixar de levar a 404.
7. THE entrega SHALL seguir o fluxo normal: branch, PR com preview no Pages, `npm run check`, `npm test` e build do catálogo real em código 0, e merge em `main`. Artefatos de verificação ficam em `temp/`.
8. THE documentação (handoff §6.4/§6.5 sobre a rota do alternador, `AGENTS.md`, roadmap e handover) SHALL ser atualizada ao concluir.

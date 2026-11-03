# Requisitos — Estante: fundação (S1)

## Introdução

Esta é a primeira spec da F3 (o app). O catálogo em `catalog/` está pronto e
validado (302 obras, 215 autorias, 309 leituras, 209 bios aprovadas). Ainda não
existe nenhuma linha de código em `app/`.

A S1 **não entrega nenhuma tela pública**. Ela entrega a fundação que todas as
telas seguintes (S2 em diante) vão consumir:

1. o projeto Astro estático em `app/`;
2. os tokens, as medidas e as fontes do design, como código;
3. a camada que lê, valida e modela o `catalog/` no build;
4. os componentes visuais base (capa, capa tipográfica, lombada, avatar de
   iniciais, prateleira) e a derivação de imagens;
5. uma vitrine interna que prova os quatro itens acima.

O objetivo é terminar a S1 com a certeza de que o catálogo entra no app com
segurança de tipos, de que o visual bate com o design e de que os tijolos das
próximas telas existem e funcionam — sem ter desenhado ainda o Início, o Atlas
ou qualquer página de leitura.

### Decisões de escopo já tomadas

- A vitrine de componentes (§Requisito 7) **faz parte da S1**: é verificação
  visual e material de apresentação.
- A derivação de imagens no build (§Requisito 6) **faz parte da S1**, porque a
  capa e o avatar dependem dela e ela prova a regra "nada de hotlink".
- Os agregados básicos (contagens por ano, idioma, país, autoria e tema)
  **fazem parte da S1** (§Requisito 5), para que a regra de negócio viva num
  lugar só, já que quase toda tela depende deles.

### Fora do escopo (fica para as specs seguintes)

- Tela Início, carrosséis e **o índice de busca** → S2 `estante-inicio-busca`.
- Linha do tempo, Ano, Sem data, faixa do ano → S3 `linha-do-tempo`.
- Atlas (idioma e país), Idioma, País, Tema, nuvem de temas → S4 `atlas`.
- Páginas Obra e Autoria → S5 `obra-autoria`.
- Manifest, service worker, instalação (PWA) → S6 `pwa-offline`.
- Modo da Lila, retrospectiva 9:16, cards de compartilhar → S7 `compartilhar`.
- Hospedagem e deploy → F4 `infra-hospedagem`.

### Glossário

- **Catálogo**: os dados canônicos em `catalog/` (obras, autorias, leituras,
  resumos, vocabulários). Fonte de verdade; o app só lê.
- **Loader**: o código que, no build, lê os arquivos do catálogo e os valida.
- **Modelo de domínio**: a forma tipada e derivada que o app consome, já com as
  regras de negócio aplicadas (ao contrário do JSON cru do catálogo).
- **Cor por idioma**: o sistema de cor central do design (§3.2 do handoff),
  onde cada idioma original tem um par fundo/texto.
- **Capa tipográfica**: o fallback de capa quando uma obra não tem imagem.
- **Derivado de imagem**: versão WebP/AVIF 2:3 gerada no build a partir de um
  mestre em `catalog/media/`.
- **Vitrine**: rota interna, fora do site público, que renderiza tokens e
  componentes em todos os seus estados.
- **Handoff**: `design/DESIGN_HANDOFF.md`, a fonte de verdade do visual. As
  seções citadas (§3.1, §3.2, …) referem-se a ele.

### Referências de design

Fonte de verdade visual: #[[file:design/DESIGN_HANDOFF.md]]
Contexto e dados do projeto: #[[file:design/DESIGN_BRIEF.md]]

## Requisitos

### Requisito 1 — Projeto Astro estático

**História:** Como mantenedor, quero um projeto Astro de saída estática em
`app/`, para gerar o site sem backend e sem JavaScript obrigatório.

#### Critérios de aceitação

1. THE projeto SHALL viver em `app/` e produzir saída estática (`output: "static"`), de modo que cada rota gere HTML que funcione sem JavaScript.
2. THE projeto SHALL usar TypeScript em modo estrito e falhar a checagem de tipos se houver erro.
3. THE projeto SHALL expor os scripts `dev`, `build`, `preview` e `check`, documentados no `README` do `app/`.
4. THE projeto SHALL fixar a versão de toda dependência (sem faixas `^`/`~`), coerente com a convenção do projeto.
5. THE `app/` SHALL apenas ler `catalog/`; SHALL NOT escrever em `catalog/` nem chamar APIs externas em tempo de build ou de execução.
6. THE `app/` SHALL NOT depender de nada em `legacy/`.
7. WHERE há interatividade (prevista só a partir da S2), THE projeto SHALL usar ilhas pequenas; a S1 SHALL NOT introduzir framework de UI pesado.
8. THE build SHALL completar com código de saída 0 quando o catálogo for válido e SHALL falhar com código ≠ 0 quando não for (ver Requisito 4).

### Requisito 2 — Tokens, medidas e fontes do design

**História:** Como desenvolvedor das próximas telas, quero os tokens do design
disponíveis como código, para construir qualquer tela sem reabrir o handoff a
cada cor ou medida.

#### Critérios de aceitação

1. THE app SHALL definir, como custom properties CSS globais, todos os tokens de cor da interface do handoff §3.1 (`--ground`, `--surface`, `--line-soft`, `--line`, `--border`, `--border-input`, `--dashed`, `--text`, `--title`, `--muted`, `--faint`, `--accent`, `--accent-ink`, `--wood-top`, `--wood-bottom`, `--bar-neutral`), com os valores exatos do handoff.
2. THE app SHALL aplicar `--ground` como fundo padrão de todas as páginas.
3. THE app SHALL registrar as medidas-chave do handoff §3.4 (margem lateral de 16 px, alvo de toque ≥ 44 px com raio 22 px, proporção de capa 2:3, sombra da capa, tamanhos de capa destaque/carrossel/grade) de forma reutilizável (custom properties e/ou utilidades).
4. THE app SHALL definir os papéis tipográficos do handoff §3.3 (título de tela, ano gigante, título de seção, big number, rótulo em caixa alta, texto corrente) com fonte, peso, tamanho, `line-height` e `letter-spacing` conforme a tabela.
5. THE app SHALL servir as fontes (Bodoni Moda, Manrope e Noto Serif KR/JP/Hebrew) a partir do próprio projeto, SHALL NOT fazer hotlink de serviços externos de fontes, e SHALL carregar as fontes Noto apenas quando houver texto no alfabeto correspondente.
6. THE texto SHALL manter contraste de ao menos 4.5:1 sobre `--ground` (os tokens de §3.1 já atendem) e, sobre cor de idioma, usar o par fundo/texto de §3.2.

### Requisito 3 — Cor por idioma

**História:** Como leitora, quero que a cor do idioma original seja consistente
em todo o app, porque é por ela que eu leio lombadas, capas e avatares.

#### Critérios de aceitação

1. THE app SHALL ter um módulo tipado que mapeie cada idioma original para o par `{ fundo, texto }` do handoff §3.2 (português, inglês, espanhol, francês, italiano, russo, japonês, alemão, hebraico, coreano).
2. WHEN um idioma não estiver no mapa, THE módulo SHALL retornar a cor "outros" do handoff §3.2, sem erro.
3. THE par de cores SHALL ser acessível tanto em build (para montar estilos) quanto como custom properties, para permitir compor com CSS.
4. THE módulo SHALL cobrir todos os idiomas presentes hoje em `catalog/vocabularies.json`, e idiomas novos SHALL cair em "outros" até ganharem cor própria.

### Requisito 4 — Validação do catálogo no build

**História:** Como mantenedor, quero que um catálogo inválido quebre o build,
para que o site publicado nunca saia de dados corrompidos.

#### Critérios de aceitação

1. THE app SHALL definir esquemas Zod que espelhem os JSON Schema reais do catálogo (`catalog/schema/*.json`): obra, autoria, leituras, resumos e vocabulários.
2. THE loader SHALL ler todos os arquivos do catálogo no build e validá-los com esses esquemas antes de qualquer página ser gerada.
3. IF qualquer arquivo violar o esquema, THEN THE build SHALL falhar com código ≠ 0 e uma mensagem que identifique o arquivo e o campo com problema.
4. THE loader SHALL validar invariantes de referência que o schema isolado não cobre: toda `work.authors[]` aponta para uma autoria existente; toda `reading.work` aponta para uma obra existente; `primaryLanguage` da autoria está em `languages`; o `scope` de cada resumo tem alvo coerente (uma `autoria:{slug}` existente, um `ano:{aaaa}` com leituras, um `pais:{XX}` existente).
5. THE loader SHALL tratar o modelo de dados **real** como fonte de verdade — `summaries.json` com `scope: autoria:{slug}` para a bio, só o campo `year` da leitura, `cover` como objeto ou `null`, `photo` como objeto ou `null` — e SHALL NOT assumir o JSON "sugerido" do handoff §7.3 (que ainda cita CSV e `bio` dentro da autoria).
6. THE loader SHALL parametrizar o caminho do `catalog/` (relativo à raiz do repositório), sem presumir estrutura de pastas do sistema de quem roda o build.

### Requisito 5 — Modelo de domínio e agregados

**História:** Como desenvolvedor das próximas telas, quero consumir um modelo
já derivado e com as regras de negócio aplicadas, para não reimplementar as
mesmas regras em cada tela.

#### Critérios de aceitação

1. THE app SHALL expor um modelo de domínio tipado que una as fontes cruas: cada obra com suas autorias resolvidas, suas leituras e sua cor de idioma; cada autoria com suas obras, sua bio aprovada (quando houver) e sua foto ou dados para o avatar.
2. THE modelo SHALL representar uma obra lida mais de uma vez como **uma** obra com várias leituras, nunca como obras duplicadas.
3. THE modelo SHALL expor, para cada leitura, apenas o **ano** (`year`); SHALL NOT expor nem inventar dia ou mês; leituras sem `year` SHALL ser identificáveis como "sem data" e manter a `sequence` (nº da lista).
4. THE modelo SHALL expor a bio de uma autoria **somente** quando existir um resumo com `scope: autoria:{slug}` e `approved: true`; caso contrário, a autoria SHALL se apresentar sem bio (a seção some, sem texto de preenchimento).
5. THE app SHALL calcular no build os agregados básicos: contagens por ano, por idioma original, por país da autoria, por autoria e por tema; e a lista ordenada por quantidade quando o design pedir (ex.: idiomas e países por frequência).
6. THE país de uma obra SHALL ser derivado do país da **autoria**; uma obra com autorias de países diferentes SHALL contar em cada país.
7. THE modelo e os agregados SHALL ser calculados uma vez por build e reutilizados, sem releitura de disco por página.
8. THE camada de dados SHALL ter testes que cubram as regras acima com dados de exemplo (releitura conta nos dois anos; sem `year` vai para "sem data"; bio não aprovada não aparece; idioma fora do mapa cai em "outros").

### Requisito 6 — Derivação de imagens no build

**História:** Como mantenedor, quero as imagens geradas a partir dos mestres no
build, para cumprir a regra de não fazer hotlink e manter a estante rápida.

#### Critérios de aceitação

1. THE app SHALL gerar, no build, derivados das imagens mestre de `catalog/media/` (hoje as fotos de autoria), em formato moderno (WebP e/ou AVIF).
2. THE derivado de capa e de foto SHALL ter proporção 2:3 com corte central, conforme o handoff §3.4.
3. THE app SHALL gerar os tamanhos necessários para `srcset` (miniaturas e dimensões fixas), de modo que as grades não sofram salto de layout.
4. THE app SHALL servir imagens apenas a partir de arquivos locais do projeto; SHALL NOT fazer hotlink de URLs externas em runtime, mesmo quando o catálogo guardar uma `sourceUrl`.
5. WHERE uma obra não tiver imagem local disponível no build, THE componente de capa SHALL recorrer à capa tipográfica (Requisito 7), sem erro de build.
6. THE imagens SHALL usar `loading="lazy"` e dimensões fixas 2:3 ao serem renderizadas pelos componentes.

> Nota de escopo: na S1, as capas de obra ainda não foram baixadas (frente de F2
> posterior). O Requisito 6 entrega o **mecanismo** de derivação e o caminho de
> fallback; a presença de cada capa específica é tratada quando as capas
> entrarem no catálogo.

### Requisito 7 — Componentes visuais base

**História:** Como desenvolvedor das próximas telas, quero os componentes base
prontos e fiéis ao design, para montar as telas da S2 em diante compondo peças.

#### Critérios de aceitação

1. THE app SHALL prover um componente **Capa**: imagem 2:3 com corte central; WHEN não houver imagem local, SHALL cair na Capa tipográfica.
2. THE app SHALL prover um componente **Capa tipográfica**: fundo na cor do idioma (§3.2), título em Bodoni itálico no topo, título original (quando houver, com `lang` e `dir` corretos) e autoria em caixa alta no rodapé separados por um filete; o título SHALL encolher em até 3 passos para caber.
3. THE app SHALL prover um componente **Lombada mini**: barra de 4 px de largura e altura variável (30–48 px) determinada pelo índice, na cor do idioma (§3.2).
4. THE app SHALL prover um componente **Avatar de iniciais**: círculo na cor do idioma principal da autoria com as iniciais em Bodoni itálico; WHEN a autoria tiver foto local, SHALL mostrar a foto no lugar.
5. THE app SHALL prover um componente **Prateleira**: faixa de 6–9 px com gradiente `--wood-top → --wood-bottom` e sombra, sobre a qual capas e lombadas se apoiam.
6. THE componentes decorativos (lombada, barras, prateleira) SHALL ter `aria-hidden` e o dado correspondente SHALL existir em texto no contexto de uso; os componentes SHALL NOT exigir JavaScript para renderizar.
7. THE componentes SHALL honrar os estados incompletos do handoff §8: sem capa → capa tipográfica; sem foto → avatar; título longo → reticências em até 2 linhas nos rótulos; título não latino → fonte Noto e `lang`/`dir` corretos.
8. THE componentes SHALL expor contratos de props tipados e SHALL NOT embutir dados do catálogo; recebem o que precisam de quem os usa.

### Requisito 8 — Vitrine de componentes

**História:** Como mantenedor (e apresentador), quero uma página interna que
mostre tokens e componentes em todos os seus estados, para verificar a S1 e
apresentar a fundação antes de qualquer tela existir.

#### Critérios de aceitação

1. THE app SHALL ter uma rota interna de vitrine (ex.: `/__styleguide`) que renderize os tokens de cor, a paleta de cor por idioma e cada componente base.
2. THE vitrine SHALL mostrar cada componente em seus estados relevantes: capa com imagem e capa tipográfica; avatar com foto e com iniciais; título curto e título longo; título latino e não latino; a cor de cada idioma de §3.2 mais o caso "outros".
3. THE vitrine SHALL ser excluída do site público: SHALL NOT aparecer no sitemap nem ser alcançável por navegação a partir das páginas públicas.
4. THE vitrine SHALL funcionar sem JavaScript, coerente com o resto da S1.
5. THE vitrine SHALL usar dados reais do catálogo sempre que possível (ex.: uma autoria com foto e uma sem, uma obra de idioma não latino), para que a verificação reflita o conteúdo de verdade.

### Requisito 9 — Acessibilidade e desempenho da fundação

**História:** Como leitora, quero uma estante acessível e leve desde a
fundação, para que isso não precise ser remendado tela a tela depois.

#### Critérios de aceitação

1. THE app SHALL usar controles reais: `<a href>` para navegação, `<button>` para ações e `<label>` em campos; elementos só com ícone SHALL ter `aria-label`.
2. THE títulos em alfabeto não latino SHALL ter `lang` e, para hebraico/árabe, `dir="rtl"`.
3. THE imagens renderizadas pelos componentes SHALL ter `alt` significativo (ou `alt=""` quando forem puramente decorativas) e dimensões fixas 2:3 para evitar salto de layout.
4. THE páginas geradas na S1 (incluindo a vitrine) SHALL ser legíveis sem JavaScript.
5. THE contraste de texto SHALL respeitar 4.5:1 conforme os tokens e os pares de cor por idioma do handoff.

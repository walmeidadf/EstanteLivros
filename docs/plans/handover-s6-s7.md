# Handover — da sessão F2 (capas e temas) para a próxima

Escrito em 6/nov/2026, ao fim da sessão que fez as capas (F2.2) e os temas (F2.3).
Este arquivo é o ponto de entrada; os detalhes ficam nos docs citados.

## Ordem decidida para a próxima sessão

O mantenedor quer fazer **primeiro**, nesta ordem:

1. **Dados das obras** (tarefa curta, sem spec).
2. **F2.6 Resumos de ano e país** (spec, no mesmo formato das anteriores).

**S6 (`pwa-offline`) e S7 (`compartilhar`)** ficam para a sessão seguinte; as seções
sobre elas mais abaixo continuam valendo e já têm fatos e perguntas.

### 1. Dados das obras (fatos de 6/nov/2026)

- Faltam: **13 romanizações** (título original não latino sem `originalTitleRomanized`),
  **2 títulos originais** (`essencial-franz-kafka-franz-kafka` e
  `o-gato-preto-e-outros-contos-de-terror-edgar-allan-poe`) e **1 ano de primeira
  publicação** (`essencial-franz-kafka-franz-kafka`). A lista das 13 sai de um
  script curto com `has_non_latin` (`pipeline/lib/titles.py`) sobre `catalog/works/`.
- Mais a fonte da capa tipográfica coreana: `TypographicCover` usa `--font-serif-jp`;
  a grade (`CoverCaption`) já usa `--font-serif-kr`.
- **Armadilha que torna a tarefa menos trivial:** `migrate_legacy.py` recompõe
  `originalTitle`, `originalTitleRomanized` e `firstPublished` a partir do CSV legado
  (`split_original` em `lib/titles.py`) a cada execução. Editar `catalog/works/*.json`
  direto seria desfeito pela próxima migração (o mesmo problema que os temas tiveram),
  e o CSV fica em `legacy/`, fora do git. Antes de corrigir, **decidir onde a
  correção vive**: por exemplo um override versionado em `pipeline/config/` aplicado no
  build, com a origem registrada (regra do AGENTS: o pipeline é o único que escreve no
  catálogo, com proveniência). As romanizações precisam de revisão humana.

### 2. F2.6 Resumos de ano e país (fatos de 6/nov/2026)

- **Infra pronta (da bio, F2.1):** `pipeline/lib/summaries.py`,
  `pipeline/review_summaries.py` (`--list --pending`, `--approve`, `--reject`, `--edit`),
  `pipeline/lib/providers/openai_client.py`, prompts em `pipeline/config/prompts/`
  (`author-bio-v1` a `v3`), `summary_rejections.json`, teto de custo em
  `budgets.json` (`openai.maxUsdPerRun` = 2,0) e `OPENAI_*` no `.env`
  (`gpt-5.4-mini`).
- **Escopos:** `ano:YYYY` (13 anos, 2014 a 2026) e `pais:XX` (36 países). O validador
  só aceita resumo aprovado cujo escopo aponte para algo que existe.
- **Hoje:** 209 resumos de `autoria:` aprovados e **nenhum** de ano ou país.
- **O app já está pronto:** a tela Ano lê `ano:{ano}` (`timeline.ts`) e a tela País lê
  `pais:{código}` (`atlas.ts`); sem resumo aprovado, o bloco some. Falta só gerar e
  aprovar. Resumo não aprovado nunca aparece.
- **Perguntas para os requisitos:** de que dados o prompt se alimenta (títulos,
  autorias, idiomas e os 58 temas canônicos, só do catálogo, sem fontes externas, ao
  contrário da bio); o que fazer com 2026, que está em andamento e ficaria
  desatualizado; tamanho e tom (handoff §6.3 e §6.7: texto curto, "frase curta" no
  país); regras duras: nada de nota ou estrela, nunca dia ou mês, nenhum fato que o
  catálogo não tenha; como a Lila revisa (em sessão, pela CLI, como na bio).

## Como retomar (leia nesta ordem)

1. [`AGENTS.md`](../../AGENTS.md): regras do projeto e estado atual.
2. [`docs/ROADMAP.md`](../ROADMAP.md): seção "Próximos passos".
3. Este arquivo.
4. [`docs/PRODUCT.md`](../PRODUCT.md), [`docs/TECH.md`](../TECH.md) e
   [`infra/README.md`](../../infra/README.md) (a parte do Cloudflare Access).
5. [`design/DESIGN_HANDOFF.md`](../../design/DESIGN_HANDOFF.md): §6.3 (Ano), §6.9
   (Obra), §6.10 (Retrospectiva), §10 (acessibilidade e desempenho).
6. Convenções do app: [`handover-s5-s6.md`](handover-s5-s6.md). Lições das duas
   últimas specs: [`handover-capas.md`](handover-capas.md) e
   [`handover-temas.md`](handover-temas.md).

## Estado em 6/nov/2026

- `main` = `origin/main` (`3be650f`), árvore limpa. No ar em
  `liliane.prateleira.site` (Cloudflare Pages), deploy automático a cada push em `main`.
- **646 páginas**; `dist` com 20,5 MB e 1600 arquivos. 272 testes do pipeline, 159 do app,
  `npm run check` limpo, validador do catálogo em 0 erros.
- Catálogo: 302 obras, 215 autorias, 309 leituras. 131 obras com capa real (171 na
  tipográfica), 58 temas canônicos, 209 bios aprovadas.
- Branches remotas `capas-obras` e `temas` já mergeadas e sem uso: podem ser apagadas
  (não apaguei sem o seu aval).
- **Nada de PWA existe**: sem `app/public/`, manifest, service worker, ícones nem
  `@vite-pwa/astro` nas dependências (hoje: `astro 7.4.0`, `sharp`, `zod` e fontes).

## O que esta sessão entregou

| Entrega | Resultado | Onde ler |
|---|---|---|
| **F2.2 Capas** (PR #10) | 131 de 302 obras com capa real, derivada no build (2:3, AVIF, `focus`). 171 seguem na tipográfica, no backlog para uma 2ª onda paga. Só entra capa de padrão estético alto. | `docs/specs/capas-obras/`, `handover-capas.md` |
| **F2.3 Temas** (PR #11) | 493 temas viraram 58 canônicos + `tags` (originais, só registro). `/tema` de 493 para 58 páginas. Nova `404.astro` (404 de verdade no Pages). | `docs/specs/temas/`, `handover-temas.md` |
| **ROADMAP corrigido** | "Dados das obras" estava quase pronto (era 21 romanizações; faltam 13, mais 2 títulos e 1 ano) e virou tarefa curta, sem spec. | `docs/ROADMAP.md` |

Lições que valem para qualquer migração: rode `git diff` nas obras depois dela e
investigue o que não devia mudar. Foi assim que apareceu o erro de proveniência de 43
capas (e o defeito do `merge_cover`).

## Como o mantenedor quer trabalhar (combinados da sessão)

- **Spec-driven com paradas:** propor o escopo e as decisões, esperar o OK, escrever os
  requisitos (EARS), parar; depois o design, parar; depois as tarefas, parar; só então
  executar. Cada spec em `docs/specs/{nome}/`.
- **Decisões com recomendação:** perguntas curtas, com a minha sugestão e o porquê.
- **Estética acima de cobertura.** A capa tipográfica e a falta de dado são aceitáveis;
  piorar o visual para "completar" não é.
- **Gratuito primeiro;** o pago fica para uma segunda onda, decidida depois.
- **Fluxo:** branch → PR (rascunho enquanto incompleto) → preview no Pages → **o
  mantenedor mergeia**. Docs vão direto na `main`. Nunca mergear sem pedir.
- **Verificar de verdade:** build, testes, diff de HTML contra um baseline em `temp/`,
  capturas de tela (desktop e celular). Dizer o que foi e o que não foi conferido.
- **Registrar no `tasks.md`** o que realmente aconteceu, inclusive desvios e erros.
- Resposta em pt-BR, direta, sem alarde; assumir o próprio erro quando aparecer.
- Escrever só em `temp/` para o que for descartável. Python (pipeline) tem testes e
  validador **locais**; o CI só roda o gate do app (check, test, build).

## S6 `pwa-offline`

**Escopo no ROADMAP:** manifest, service worker, ícones, instalação, offline.
O público principal é a Lila, num Samsung Android (PRODUCT.md).

### Fatos verificados

- `TECH.md` prevê `@vite-pwa/astro`. **Não foi checado** se ele é compatível com
  Astro 7.4.0: confirmar antes de decidir a ferramenta (a alternativa é um service
  worker escrito à mão).
- `astro.config.mjs` já fixa `site` e deixa `base` na raiz "para links, imagens,
  service worker (S6) e manifest viverem na raiz".
- Peso do build, para dimensionar o cache: 20,5 MB no total; HTML 9,4 MB (646
  páginas); AVIF 3,7 MB (931 arquivos); **fontes 7,3 MB** (19 arquivos; os 3
  `.woff` somam 4,5 MB; o `TECH.md` prevê Noto Serif KR, JP e Hebraico sob demanda, mas
  não conferi quais arquivos são esses); índice de busca 83 KB. Pré-cachear tudo seria
  pesado num celular, as fontes maiores em especial.
- Já existe `404.astro` estática: pode servir de base para a página de offline.
- Os deploys de PR saem em `head.prateleira-liliane.pages.dev` (alias único: o último
  PR vence) e em um endereço com hash por deploy. Teste de instalação e de service
  worker precisa de HTTPS: o preview serve.

### Pontos de partida (sugestões, a confirmar nos requisitos)

- Manifest: `name` "A estante da Lila", `lang` pt-BR, `display: standalone`,
  `start_url: "/"`, cores do tema (`--ground` `#0E1714`), ícones 192 e 512 com versão
  maskable. O ícone precisa de decisão de design (ver abaixo).
- Cache em duas camadas: pré-cachear o essencial (Início, Atlas, Linha do tempo,
  CSS, fontes latinas, índice de busca) e cachear o resto ao visitar
  (páginas e imagens sob demanda, com limite). Evitar pré-cache de 20 MB.
- `_headers` do Pages: o service worker e o manifest não podem ficar com cache longo.

### Perguntas para a fase de requisitos

1. O que precisa funcionar offline? Só o que a Lila já abriu, ou a estante inteira?
2. Como o app avisa que há versão nova (atualizar sozinho ou perguntar)?
3. Instalação: só o menu do navegador, ou um convite na própria tela? (Visitantes
   também veem; PRODUCT.md quer "sem login e poucos toques".)
4. Ícone: não há arte. Usar as iniciais, a lombada colorida, ou pedir um desenho?
5. Fontes: o que fica no pré-cache e o que só sob demanda.
6. Impacto na S7: se a área da Lila ficar em outro hostname, o service worker e o
   escopo da instalação ficam por origem (ver S7).

## S7 `compartilhar`

**Escopo no ROADMAP:** modo autenticado da Lila, retrospectiva 9:16, card de livro.
**Nenhum botão nem stub existe hoje**, nem na tela Ano nem na Obra.

### Fatos verificados

- **Só a Lila compartilha:** o botão aparece só no modo autenticado dela; visitantes
  não o veem (PRODUCT.md).
- **Onde ficam os botões (handoff):** "Compartilhar {ano}" na tela Ano (§6.3) e
  "Compartilhar" na Obra (§6.9), que gera o card do livro.
- **A peça (§6.10):** story 9:16, referência 540×960, exportar **1080×1920 PNG**.
  Conteúdo: período, total de leituras, barras por ano, mix de idiomas, autoria mais
  lida, **3 temas que voltam**, rodapé com @ e o endereço da estante. Uma versão por
  ano e uma "de sempre". Card do livro em 1:1 ou 4:5. Referência visual em
  `design/telas/Retro.dc.html`.
- **Tecnologia prevista (TECH.md):** Satori + resvg no build (PNG), entregue pela Web
  Share API. O handoff admite também `html-to-image` no navegador.
- **Cloudflare Access:** o `infra/README.md` o descreve como preparação, "não agora":
  protegeria "por hostname/rota (ex.: `admin.liliane.prateleira.site`), sem código na
  aplicação". A estante pública fica aberta. Nada foi configurado.
- Os 3 temas da retrospectiva agora são os **canônicos** (58), não os 493 de antes.
- "Ano fechado": `latestYearWithReading` (em `home.ts`) já identifica o ano em
  andamento (2026 hoje). Os anos 2014 a 2025 são os fechados.

### A decisão estrutural (resolver antes dos requisitos)

O app é 100% estático. **Como ele sabe que é a Lila?** Opções, nenhuma verificada
ainda:

| Opção | Como | Prós | Contras |
|---|---|---|---|
| **A. Hostname separado** | Um segundo hostname atrás do Access (ex. `admin.…`) serve uma variante do build com os botões | Alinhado ao `infra/README.md`; sem código de login; público intacto | Segundo deploy ou projeto no Pages; duas origens (instalação do PWA, cache, service worker por origem) |
| **B. Rota protegida** | Mesmo hostname, uma área (ex. `/lila/*`) protegida pelo Access por caminho | Uma origem só | Precisa espelhar páginas ou redirecionar; verificar se o Access cobre caminho no plano gratuito |
| **C. Detecção no cliente** | Ler o cookie do Access no navegador para mostrar o botão | Sem build extra | Provavelmente não funciona (cookie pode ser HttpOnly) e não protege nada; só esconde o botão |

Recomendo começar por **testar o Access de verdade** (uma hora de experimento)
antes de escrever os requisitos: o que ele protege e o que o app consegue ler.

### Perguntas para a fase de requisitos

1. Qual é o @ (Instagram) do rodapé? Não há no repositório.
2. Os PNGs gerados ficam em URLs públicas ou só na área da Lila? "Só ela compartilha"
   não quer dizer que a imagem seja secreta, mas é decisão de produto.
3. A retrospectiva "de sempre" e a de cada ano: um PNG por ano no build (13 + 1) ou
   gerados sob demanda no navegador?
4. As fontes do Satori: pelo que sei, ele lê TTF, OTF e WOFF, mas não WOFF2 (confirmar
   na documentação). O app usa pacotes Fontsource (woff/woff2): verificar qual arquivo
   serve para Bodoni Moda e Manrope.
5. Web Share com arquivo (`navigator.share({files})`) funciona no Chrome do Android,
   sob gesto do usuário e em HTTPS; é preciso um plano B (baixar a imagem).
6. A S7 aproveita o resumo do ano (F2.6)? Se sim, vale fazer a F2.6 antes.

## Outras frentes pendentes (independentes entre si)

| Frente | Tamanho | Observação |
|---|---|---|
| **Dados das obras** | Tarefa curta, sem spec | 13 romanizações, 2 títulos originais, 1 ano; fonte da capa tipográfica coreana |
| **F2.6 Resumos de ano e país** | Spec | ~49 textos (13 anos e 36 países); reaproveita o fluxo da bio; as seções em Ano e País hoje somem |
| **Polimento do desktop** | Mini-spec | Mais colunas na grade, setas nos carrosséis, CSS de grade repetido, capa da Obra com 136 px |
| **`photo.author` para `photo.credit`** | Tarefa isolada | 215 autorias, schema e pipeline |
| **Capas, 2ª onda** | Paga, sem prazo | 171 obras no backlog (`capas-backlog.md`) |
| **Autorias** | Contínuo | 40 fotos, 9 sem Wikidata, 6 sem bio |

## Armadilhas

- **zsh:** `path` é amarrada ao `PATH`. Nunca use `path` como nome de variável de
  laço no shell: quebra `curl`, `grep` etc. e a quebra persiste na sessão.
- **Capturas headless:** a janela mínima do Chrome headless é 500 px; use 500 para
  "celular". Não leia a captura antes de ela terminar (o arquivo ainda não existe).
- **Diff de HTML:** compare corpo e conjunto de regras CSS; a **ordem** dos blocos
  `<style>` muda sem efeito quando um componente passa a importar outro módulo.
- **Pages:** só existe 404 de verdade porque há `404.html`; `/404.html` responde 308
  para `/404`. Rotas de tema antigas dão 404.
- **Preview:** o alias `head.prateleira-liliane.pages.dev` é compartilhado entre PRs.

## Sugestão de abertura para a sessão da S6 e da S7 (a seguinte)

> Estante da Lila. Antes de propor qualquer coisa, leia `docs/plans/handover-s6-s7.md`,
> o `AGENTS.md` e o `docs/ROADMAP.md`. Vamos fazer a S6 (`pwa-offline`), spec-driven
> como nas anteriores: proponha o escopo exato e as decisões em aberto, e pare para eu
> aprovar antes dos requisitos. Depois seguimos para a S7 (`compartilhar`), que depende
> de decidirmos como o app reconhece a Lila (Cloudflare Access).

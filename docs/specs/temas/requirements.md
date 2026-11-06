# Requisitos — Temas (F2.3)

## Introdução

As 302 obras têm hoje 496 temas distintos (493 depois de juntar caixa e acento),
em média 4 por obra. A distribuição é de cauda longa: **330 temas aparecem em uma
única obra**, 73 em duas e só 52 em cinco ou mais (medido em 6/nov/2026). Cada
tema vira uma página `/tema/{slug}`, então o app tem 493 páginas de tema, a
maioria com um livro só. A nuvem do Atlas, os chips da Obra e os temas da Autoria
funcionam bem para o núcleo frequente e ficam poluídos pela cauda.

O núcleo já existe: os 52 temas com 5+ obras (memória 62, família 57, identidade
37, amor 34, maternidade 25...) cobrem 279 das 302 obras. O trabalho é mapear a
cauda para um conjunto canônico de **~40 a 60 temas**, sem perder a informação
específica ("Argélia colonial", "crise dos opioides"), que passa a ser guardada
como registro.

A migração da F1 (`migrate_legacy.py`) recompõe `themes` a partir do CSV a cada
execução. Por isso o mapa é aplicado **dentro do build do catálogo**, no mesmo
lugar em que `merge_cover` preserva as capas; senão qualquer migração desfaria a
normalização.

### Decisões já tomadas (nesta sessão)

- **Os temas específicos não são descartados.** Ficam no catálogo como `tags`, só
  para registro: sem página, sem destaque, sem busca, em nenhuma tela.
- **O mapa é redigido por mim e revisado com a Lila.** Sem OpenAI nesta spec; é
  um trabalho que roda uma vez e passa por revisão humana.
- **Início continua automático:** os 4 temas mais frequentes, sem lista editorial.
  A Lila gostou do resultado atual. Fica registrado que o único incômodo com o
  Início é o carrossel "família"; não vira regra agora.
- **Tema não mapeado nunca passa em silêncio.** Obra nova com tema fora do mapa
  interrompe a migração e lista o que falta.
- Itens que entram junto, vindos das pequenas dívidas: o `404.astro` (as URLs de
  ~440 temas deixam de existir) e a escolha dos carrosséis do Início (handoff
  §12.4), resolvida pela decisão acima.

### Glossário

- **Tema canônico:** tema do conjunto final (~40 a 60), com página própria, usado
  na nuvem do Atlas, nos chips da Obra, nos temas da Autoria e no Início.
- **Tema original:** cada string de `themes` como vem do CSV legado (496 hoje).
- **Taxonomia:** a lista dos temas canônicos.
- **Mapa:** relação de cada tema original com zero ou mais temas canônicos.
- **Tag:** tema original guardado no campo `tags` da obra, só para registro.
- **Piso:** número mínimo de obras para um tema canônico valer uma página. Vale 5,
  o mesmo piso da nuvem do Atlas (`CLOUD_MIN_WORKS`).
- **Chave de comparação:** o tema sem caixa, acento e pontuação extra
  (`Nordeste` e `nordeste` são o mesmo tema original).

## Requisitos

### Requisito 1 — Taxonomia canônica

**História:** Como leitora, quero poucos temas claros para navegar, em vez de
centenas de temas com um livro só.

#### Critérios de aceitação

1. O projeto SHALL ter `pipeline/config/themes.json` com a taxonomia (lista de temas canônicos) e o mapa (R2), versionado e com campo `version`.
2. A taxonomia SHALL ter entre 40 e 60 temas, em pt-BR e em minúsculas (como os atuais), sem repetição pela chave de comparação.
3. Dois temas canônicos SHALL NOT gerar o mesmo slug de URL (`slugifyTheme`).
4. Cada tema canônico SHOULD ter pelo menos o piso de obras (5). Os que ficarem abaixo SHALL ser listados no relatório de cobertura, sem bloquear a migração (uma obra removida não pode travar o catálogo).
5. A taxonomia SHALL incluir os 52 temas que hoje têm 5+ obras, salvo os que a revisão decidir fundir; cada fusão SHALL ficar visível no mapa.
6. Todo conteúdo de `themes.json` SHALL ser decisão humana revisada: o arquivo SHALL NOT ser reescrito por script.

### Requisito 2 — Mapa dos temas originais

**História:** Como mantenedor, quero cada tema original com um destino explícito,
para auditar de onde saiu cada tema canônico.

#### Critérios de aceitação

1. O mapa SHALL ter uma entrada para cada tema original (pela chave de comparação). Os 496 atuais SHALL estar cobertos.
2. O valor de uma entrada SHALL ser uma lista de temas canônicos. Um original pode ir para mais de um (ex.: "violência doméstica" para `violência` e `família`).
3. Uma lista vazia SHALL significar "só tag": o original não vira tema, mas continua guardado em `tags`.
4. Um tema canônico citado no mapa que não esteja na taxonomia SHALL ser erro.
5. Um tema canônico da taxonomia que nenhuma entrada do mapa alcance SHALL ser erro (taxonomia sem uso).
6. Variantes de caixa e acento (`Nordeste`/`nordeste`, `Guerra Fria`/`guerra fria`, `Segunda Guerra Mundial`/`segunda guerra mundial`) SHALL compartilhar uma única entrada.

### Requisito 3 — Aplicação no build do catálogo

**História:** Como mantenedor, quero que o mapa seja aplicado sempre que o
catálogo é reconstruído, para que a normalização não se perca numa migração.

#### Critérios de aceitação

1. `migrate_legacy.py` (via `lib/build.py`) SHALL ler `pipeline/config/themes.json` e, para cada obra, gravar `themes` como a união ordenada e sem repetição dos temas canônicos dos seus originais, na ordem de primeira aparição no CSV.
2. O build SHALL gravar em `tags` da obra todos os temas originais, sem repetição pela chave de comparação, na ordem do CSV e com a grafia do CSV (sem perda).
3. IF algum tema original não tiver entrada no mapa, THEN a migração SHALL parar com código de saída 1, SHALL NOT gravar nada e SHALL listar os temas sem mapeamento com a obra de origem.
4. IF alguma obra ficar com zero temas canônicos, THEN a migração SHALL parar com código de saída 1 e SHALL listar a obra e seus originais.
5. IF `themes.json` estiver ausente ou inválido, THEN a migração SHALL parar com mensagem clara (código de saída 2).
6. `vocabularies.themes` SHALL ser a lista dos temas canônicos em uso, em ordem alfabética (`vocab_sort_key`).
7. Rodar a migração duas vezes SHALL produzir o mesmo catálogo, byte a byte. O resultado SHALL NOT depender de estado anterior de `themes`.
8. O `--dry-run` SHALL mostrar, sem gravar, o número de temas canônicos, de obras por tema abaixo do piso e as pendências de mapeamento.

### Requisito 4 — Esquema, vocabulário e validação

**História:** Como mantenedor, quero que o validador garanta que só temas
canônicos aparecem nas obras.

#### Critérios de aceitação

1. `catalog/schema/work.schema.json`, o Zod (`app/src/lib/catalog/schema.ts`) e `docs/DATA_MODEL.md` SHALL ganhar o campo `tags` (lista de textos), **opcional e aditivo**: obras sem `tags` continuam válidas.
2. O validador SHALL continuar exigindo que todo tema de obra esteja em `vocabularies.themes` (regra `vocab` existente) e, além disso, SHALL ler `pipeline/config/themes.json` e acusar erro se algum tema de obra, ou de `vocabularies.themes`, não pertencer à taxonomia. A regra existente sozinha não basta, porque o vocabulário é derivado das próprias obras.
3. `docs/DATA_MODEL.md` SHALL documentar a diferença entre `themes` (canônicos, navegáveis) e `tags` (originais, só registro) e que a normalização vive em `pipeline/config/themes.json`.
4. Para toda obra com `tags`, o validador SHALL aplicar o mapa às `tags` e acusar erro se o resultado diferir de `themes` (mapa editado sem rodar a migração). Como as `tags` guardam os originais sem perda, a conferência dispensa o CSV legado.
5. `docs/plans/cobertura.md` SHALL ganhar uma seção de temas: nº de temas canônicos, obras por tema (os 10 maiores), temas abaixo do piso, média de temas por obra, obras com um único tema e total de tags.

### Requisito 5 — Revisão com a Lila

**História:** Como Lila, quero rever os grupos de temas sem mexer em JSON.

#### Critérios de aceitação

1. O projeto SHALL ter uma CLI de **leitura** (`pipeline/review_themes.py`) que gera `docs/plans/revisao-temas.md` a partir do CSV legado e de `themes.json`, sem gravar no catálogo.
2. O documento SHALL listar, por tema canônico: o número de obras, os temas originais que caem nele (com a contagem de obras de cada um) e as obras que ficam só com ele.
3. SHALL listar à parte os temas originais "só tag" (lista vazia) e os mapeados para mais de um tema.
4. SHALL listar as obras que ficam com um único tema e as que perdem mais da metade dos temas originais, para atenção na revisão.
5. A saída SHALL ser determinística (mesma entrada, mesmo arquivo) e SHALL cobrir todos os originais; um original ausente do mapa SHALL aparecer em destaque como pendência.
6. A revisão SHALL acontecer em sessão: a Lila indica os ajustes, eu edito `themes.json` e regenero o documento. Nenhuma aprovação é automática.

### Requisito 6 — Telas do app

**História:** Como leitora, quero que as telas de tema mostrem só o núcleo
canônico, sem páginas com um livro.

#### Critérios de aceitação

1. O app SHALL gerar uma página `/tema/{slug}` para cada tema canônico, e nenhuma além delas. O número de páginas `/tema` SHALL ser igual ao tamanho da taxonomia.
2. A regra de slug (`slugifyTheme`) e a rota `/tema/{slug}` SHALL permanecer as mesmas.
3. A nuvem do Atlas, os chips da Obra e os temas da Autoria SHALL consumir os temas canônicos sem mudar de regra de seleção (piso de 5 na nuvem e na contagem da Obra, 2 obras na Autoria). Os testes SHALL ser atualizados para refletir os novos números.
4. `tags` SHALL NOT aparecer em nenhuma tela, rota, índice de busca ou HTML gerado. O modelo (`WorkView`) SHALL NOT expô-las.
5. O teste de integridade de rotas (`route-integrity`) SHALL continuar provando que todo `href` de `/tema` emitido resolve para uma página existente.
6. O total de páginas do build SHALL cair de forma consistente: `1080 − (493 − N) + 1`, em que N é o tamanho da taxonomia e o `+1` é a página 404 (R8).

### Requisito 7 — Início

**História:** Como Lila, quero que o Início continue mostrando os temas que mais
aparecem na minha estante.

#### Critérios de aceitação

1. O Início SHALL continuar com os 4 temas canônicos mais frequentes, escolhidos automaticamente (`THEME_RAIL_COUNT`), sem lista editorial nem exclusões.
2. A regra de teto de ~20 itens por carrossel e o cartão final "ver todos" SHALL permanecer.
3. A seleção SHALL ser determinística: empate de contagem desempatado como hoje.
4. Nenhum arquivo de configuração de exclusão de temas SHALL ser criado nesta spec.

### Requisito 8 — Página 404

**História:** Como visitante, quero uma página clara quando abro um endereço que
não existe, em vez de cair no Início como se tudo estivesse certo.

#### Critérios de aceitação

1. O app SHALL ter `src/pages/404.astro`, que gera `404.html` na raiz do build, em pt-BR e no mesmo visual das outras telas.
2. A página SHALL dizer, em uma frase, que o endereço não existe e SHALL oferecer links para o Início, o Atlas e a Linha do tempo (alvos de 44 px). SHALL NOT usar "—" nem mensagem técnica.
3. A página SHALL funcionar sem JavaScript.
4. No preview do PR, abrir uma rota inexistente (por exemplo, o slug de um tema removido) SHALL devolver status HTTP 404 com essa página. O Cloudflare Pages passa a servir o 404 quando existe `404.html`; essa verificação SHALL ser feita no preview e registrada.
5. Rotas existentes SHALL NOT mudar de resposta.

### Requisito 9 — Execução, proposta e aprovação

**História:** Como mantenedor, quero que o mapa passe por revisão antes de
alterar o catálogo.

#### Critérios de aceitação

1. Eu SHALL redigir a taxonomia e o mapa inicial em `themes.json` a partir dos 496 originais, usando a frequência e o contexto das obras, sem chamar serviços pagos.
2. O mapa SHALL ser gerado e revisado em `revisao-temas.md` **antes** de qualquer alteração no catálogo; a migração real só roda depois da aprovação da Lila.
3. A aprovação SHALL ser registrada no `tasks.md` (data e ajustes pedidos).
4. O catálogo resultante SHALL passar no validador da F1 com 0 erros; se não passar, nada é gravado.
5. A alteração SHALL seguir o fluxo branch, PR com preview, merge; docs direto na `main`.

### Requisito 10 — Testes

**História:** Como mantenedor, quero testar a regra sem depender dos dados reais.

#### Critérios de aceitação

1. Os testes do pipeline SHALL rodar offline, com CSV e `themes.json` pequenos, e cobrir: união ordenada sem repetição; mapa de um para vários; lista vazia (só tag); variantes de caixa e acento; `tags` sem perda e na ordem do CSV; tema sem mapeamento (saída 1, nada gravado); obra com zero temas (saída 1); taxonomia sem uso e tema fora da taxonomia (erro); `themes.json` ausente (saída 2); idempotência byte a byte; `--dry-run`.
2. O teste do documento de revisão SHALL provar que é determinístico e cobre todos os originais.
3. A migração SHALL ter teste de que um catálogo já normalizado não é desfeito ao migrar de novo.
4. Os testes do app SHALL cobrir: Zod aceita `tags`; `WorkView` não expõe `tags`; Início escolhe os 4 mais frequentes entre os canônicos; `route-integrity` com os temas novos; a página 404 é gerada.
5. O diff de HTML contra a `main` SHALL provar que telas sem relação com temas (Linha do tempo, Ano, País, Idioma sem chips de tema) não mudam.

## Fora do escopo

- **Geração automática da taxonomia** (por exemplo, para a lista de outra pessoa ou
  de um clube de leitura). O mapa e a taxonomia são dados em JSON, separados do
  código, justamente para que um gerador futuro (agrupamento por LLM ou por
  similaridade, com piso de frequência e revisão humana) escreva o mesmo formato.
  Anotado no ROADMAP.
- **Exibir ou pesquisar `tags`**, ou dar página a elas.
- **Lista editorial ou exclusão de temas no Início** (o incômodo com "família").
- **Redirecionamentos** das URLs de temas removidos para os temas canônicos. Nada
  foi compartilhado ainda (a S7 não existe), então o `404.astro` basta.
- **Resumos de ano e país, dados das obras, polimento do desktop, S6 e S7.**
- Mudar o desenho da nuvem do Atlas, os pisos de contagem ou o índice de busca.

# Requisitos — Enriquecimento de autorias (F2.1)

## Introdução

As 215 autorias do catálogo têm hoje só nome, aliases e idiomas derivados das
obras. País, foto e bio estão vazios (ver `docs/plans/cobertura.md`). Sem país,
não existem o Atlas por país nem a página País. Sem foto e bio, a página de
Autoria fica só com o avatar de iniciais.

Esta spec cria os scripts que identificam cada autoria no **Wikidata** e, a
partir dele, preenchem **país principal**, **foto** e **bio** (busca de fontes +
resumo em pt-BR por LLM). Os mesmos scripts serão reaproveitados pelo admin (F5)
quando uma nova leitura trouxer uma autoria nova.

### Decisões já tomadas

- Só o **país principal** de cada autoria é guardado.
- Fotos podem vir de qualquer fonte. A origem é sempre registrada.
- Bio = busca de fontes + resumo/tradução para pt-BR via **OpenAI**.
- Fontes da bio: Wikipédia em vários idiomas, em ordem de preferência
  (`BIO_SOURCE_LANGUAGES`), com **Tavily** como fallback.
- Fotos ausentes no Wikidata/Commons: imagem principal dos verbetes da
  Wikipédia em outros idiomas e, por fim, imagens do **Tavily**
  (`include_images` + `include_image_descriptions`). Sem Brave Search.
- Chaves de API em `.env` (modelo em `.env.example`), nunca versionadas.

### Glossário

- **QID**: identificador de uma entidade no Wikidata (ex.: `Q3378` para Machado de Assis).
- **Identificação**: o vínculo entre uma autoria do catálogo e um QID.
- **Fonte**: texto de referência usado para gerar a bio (verbete da Wikipédia ou resultado de busca).
- **Cache**: respostas de APIs gravadas em disco em `pipeline/cache/`, fora do git.
- **Decisões manuais**: arquivos em `pipeline/config/`, versionados, que fixam escolhas humanas.

## Requisitos

### Requisito 1 — Identificação no Wikidata

**História:** Como mantenedor, quero cada autoria ligada à pessoa certa no
Wikidata, para que país, foto e bio não venham de um homônimo.

#### Critérios de aceitação

1. O script SHALL buscar candidatos no Wikidata pelo nome canônico e pelos aliases de cada autoria, considerando só entidades humanas (`P31 = Q5`).
2. O script SHALL confirmar um candidato quando ele for autor (`P50`) de alguma obra da autoria na estante, identificada por ISBN (`P212`/`P957`), Open Library ID (`P648`) ou título (rótulo ou título original) com autoria correspondente.
3. WHEN não houver confirmação por obra, THE script SHALL aceitar o candidato se ele for o único humano com ocupação ligada à escrita (escritor, romancista, poeta, jornalista, ensaísta, roteirista, quadrinista ou similar) e nome compatível. Nesse caso, SHALL marcar a identificação como `probable`.
4. IF houver mais de um candidato plausível ou nenhum, THEN THE script SHALL marcar a autoria como `ambiguous` ou `not_found` e SHALL NOT preencher nenhum dado a partir do Wikidata.
5. THE projeto SHALL ter `pipeline/config/author_wikidata.json`, onde um QID pode ser fixado à mão (ou marcado como "sem Wikidata"). A escolha manual SHALL vencer a busca automática.
6. Cada autoria SHALL guardar o QID, o estado (`confirmed`, `probable`, `manual`, `ambiguous`, `not_found`) e a evidência da confirmação (qual obra ou regra).
7. O QID SHALL ser incluído em `references` da autoria, com a URL do Wikidata.

### Requisito 2 — País principal

**História:** Como leitora, quero ver de onde vem cada autoria, para explorar a
estante por país.

#### Critérios de aceitação

1. O país SHALL ser derivado da cidadania (`P27`) da autoria identificada e gravado como código ISO 3166-1 alfa-2 em `country`.
2. WHEN houver uma só cidadania, THE script SHALL usá-la.
3. WHEN houver várias, THE script SHALL escolher por regra determinística: (a) o país cujo idioma oficial é o `primaryLanguage` da autoria; (b) em empate, o país de nascimento (`P19` → `P17`); (c) em último caso, a cidadania listada primeiro. O caso SHALL ser listado no relatório como "país escolhido entre vários".
4. WHEN não houver cidadania, THE script SHALL usar o país do local de nascimento.
5. WHEN a cidadania for de um Estado extinto sem código ISO atual (ex.: União Soviética, Império Russo, Tchecoslováquia), THE script SHALL usar um mapeamento explícito para o país atual mais apropriado, definido em configuração, e SHALL listar o caso no relatório.
6. `pipeline/config/author_overrides.json` SHALL aceitar `country`, que vence a regra.
7. IF não for possível determinar o país, THEN `country` SHALL continuar `null`, e a autoria SHALL aparecer no relatório.
8. O catálogo SHALL ter um vocabulário de países (`vocabularies.json` → `countries`) com código, nome em pt-BR e idioma principal, e o validador SHALL conferir que todo `country` usado está nele.

### Requisito 3 — Foto

**História:** Como leitora, quero ver o rosto de quem escreveu, para que a página
de Autoria tenha cara de pessoa e não de ficha.

#### Critérios de aceitação

1. WHEN a autoria identificada tiver imagem no Wikidata (`P18`), THE script SHALL baixar o arquivo do Wikimedia Commons e registrar a licença e a autoria da imagem a partir dos metadados do Commons.
2. WHEN não houver `P18`, THE script SHALL reunir até 3 imagens candidatas, nesta ordem: a imagem principal dos verbetes da Wikipédia ligados ao QID (em `BIO_SOURCE_LANGUAGES`) e as imagens do Tavily para "{nome} escritor(a) {obra da estante}", com descrição, excluindo redes sociais. O script SHALL NOT escolher sozinho: as candidatas vão para revisão humana.
2a. Para não gastar créditos à toa, a busca de imagens do Tavily SHALL reutilizar a mesma chamada usada para as fontes da bio quando as duas forem necessárias.
3. THE script SHALL gerar uma folha de revisão (`docs/plans/revisao-fotos.html`, fora do git) com as candidatas lado a lado, por autoria, para escolha numa sessão.
4. A escolha SHALL ser registrada em `pipeline/config/author_photos.json` (URL escolhida ou "sem foto"), e o script SHALL baixar só a escolhida.
5. A imagem mestre SHALL ser gravada em `catalog/media/authors/{slug}.{ext}` com, no mínimo, 400 px no lado menor quando a fonte permitir. Ela SHALL NOT ser redimensionada nem recortada pelo pipeline (os derivados são do build do app).
6. `photo` SHALL registrar `file`, `license` (ou `null` quando desconhecida), `author` (ou `null`) e `sourceUrl`.
7. IF o download falhar ou o arquivo não for uma imagem válida, THEN `photo` SHALL continuar `null`, e o caso SHALL ir para o relatório.
8. O script SHALL NOT fazer hotlink: o app usa só o arquivo local.

### Requisito 4 — Fontes da bio

**História:** Como mantenedor, quero que toda bio venha de fontes reais e
guardadas, para conferir de onde saiu cada frase.

#### Critérios de aceitação

1. Para autorias identificadas, o script SHALL usar os verbetes da Wikipédia ligados ao QID (sitelinks), na ordem de `BIO_SOURCE_LANGUAGES` (padrão `pt,en,es,fr,it`), e SHALL usar o primeiro que tiver texto suficiente (introdução com pelo menos ~300 caracteres).
2. WHEN não houver verbete suficiente ou a autoria não estiver identificada, THE script SHALL buscar fontes no Tavily com o nome, "escritor(a)" e o título de uma obra da autoria na estante, excluindo redes sociais e sites de vídeo (`linkedin.com`, `facebook.com`, `instagram.com`, `tiktok.com`, `x.com`, `youtube.com`). Sem o título da obra, a busca traz homônimos (teste real: "Han Kang" retornou só perfis do LinkedIn).
3. Cada fonte SHALL ser guardada em cache com URL, idioma, título, texto extraído e data da coleta.
4. IF nenhuma fonte for encontrada, THEN a autoria SHALL ficar sem bio e aparecer no relatório.

### Requisito 5 — Resumo da bio (LLM)

**História:** Como Lila, quero uma bio curta em português sobre cada autoria, que
eu aprovo antes de aparecer na estante.

#### Critérios de aceitação

1. O script SHALL gerar, com o modelo definido em `OPENAI_MODEL`, uma bio em pt-BR de 2 a 3 frases (até ~400 caracteres), traduzindo quando a fonte estiver em outro idioma.
2. O prompt SHALL restringir o texto aos fatos presentes nas fontes fornecidas, SHALL proibir opiniões, superlativos e informações sobre a vida pessoal que não sejam relevantes para a obra, e SHALL pedir resposta estruturada (texto + indicação de fonte usada + flag "fontes insuficientes").
3. WHEN o modelo indicar fontes insuficientes, THE script SHALL NOT gravar bio.
4. A bio SHALL ser gravada em `catalog/summaries.json` com `scope: "autoria:{slug}"`, `approved: false`, `source` (nome da fonte), `sourceUrl`, `sourceLanguage`, `model` e `updatedAt`.
5. WHEN já existir uma bio para a autoria, THE script SHALL NOT sobrescrevê-la, salvo com `--regenerate`. Uma bio **aprovada** SHALL nunca ser sobrescrita automaticamente.
6. O campo `bio` SHALL sair do schema de autoria: a bio vive só em `summaries.json`, no mesmo fluxo de aprovação dos resumos de ano e país.
7. O script SHALL registrar tokens usados e custo estimado por execução.

### Requisito 6 — Revisão e aprovação

**História:** Como Lila, quero revisar bios e escolhas com pouco esforço, sem
mexer em JSON.

#### Critérios de aceitação

1. O pipeline SHALL gerar `docs/plans/revisao-autorias.md` com, por autoria pendente: nome, QID e estado da identificação, país escolhido (e alternativas), foto (ou candidatas) e a bio proposta com a fonte.
2. O projeto SHALL ter uma CLI `pipeline/review_summaries.py` para aprovar, rejeitar ou editar resumos por escopo (`--approve autoria:han-kang`, `--reject …`, `--edit … --text "…"`), e para aprovar em lote uma lista de escopos.
3. Editar o texto de um resumo SHALL mantê-lo aprovado só se o comando for de aprovação. A edição SHALL registrar `editedBy: "human"`.
4. Rejeitar SHALL remover o resumo e registrar a rejeição em cache, para que ele não seja gerado de novo sem `--regenerate`.

### Requisito 7 — Execução, cache e custos

**História:** Como mantenedor, quero rodar o enriquecimento em partes e de novo,
sem gastar créditos à toa.

#### Critérios de aceitação

1. O enriquecimento SHALL ser uma CLI (`pipeline/enrich_authors.py`) com etapas selecionáveis (`--steps identify,country,photo,bio`), filtro por autoria (`--only slug,...`), limite (`--limit N`) e `--dry-run`.
2. Toda resposta externa SHALL ser guardada em cache em `pipeline/cache/{provedor}/`, e uma nova execução SHALL reutilizá-la, salvo com `--refresh`.
3. O `--dry-run` SHALL mostrar quantas chamadas a cada API seriam feitas (descontando o cache) e o custo estimado da OpenAI, sem chamar nada pago.
4. THE script SHALL respeitar limites de taxa (pausa entre chamadas e novas tentativas com espera crescente em HTTP 429/5xx) e SHALL enviar o `WIKIMEDIA_USER_AGENT` nas chamadas à Wikimedia.
5. THE script SHALL ler as chaves do ambiente ou do `.env`, SHALL NOT registrar chaves em log ou cache e SHALL parar com mensagem clara quando faltar a chave de uma etapa pedida.
6. IF uma autoria falhar, THEN o script SHALL seguir para as próximas e listar as falhas no fim (código de saída 1 quando houver falha).
7. THE script SHALL usar só a biblioteca padrão do Python (HTTP com `urllib`).
8. A gravação no catálogo SHALL passar pelo validador da F1: se o resultado for inválido, nada é gravado.
9. Rodar duas vezes com o cache completo SHALL produzir o mesmo catálogo, byte a byte.

### Requisito 8 — Proveniência e catálogo

**História:** Como mantenedor, quero saber de onde veio cada dado novo.

#### Critérios de aceitação

1. Cada autoria SHALL ganhar um objeto `wikidata` com `id`, `status` e `evidence`, e `country` SHALL ter a origem registrada (`countrySource`: `wikidata-citizenship`, `wikidata-birthplace`, `override`).
2. Os schemas de autoria e de resumo SHALL ser atualizados para os novos campos, e `docs/DATA_MODEL.md` SHALL refletir o formato.
3. A migração da F1 SHALL continuar funcionando sem apagar os dados enriquecidos. Ela SHALL preservar `country`, `wikidata`, `photo` e `references` existentes das autorias.

### Requisito 9 — Relatório de cobertura

**História:** Como mantenedor, quero ver o progresso do enriquecimento.

#### Critérios de aceitação

1. `docs/plans/cobertura.md` SHALL mostrar, para autorias: identificadas por estado, com país, com foto (Commons × busca), com bio proposta e com bio aprovada.
2. O relatório SHALL listar as autorias ambíguas, não encontradas, sem país e com país escolhido entre vários.

### Requisito 10 — Testes

**História:** Como mantenedor, quero testar a lógica sem gastar créditos nem
depender da rede.

#### Critérios de aceitação

1. Todos os testes SHALL rodar offline, com respostas de API simuladas (fixtures JSON pequenas).
2. Os testes SHALL cobrir: confirmação por obra, `probable`, `ambiguous`, escolha manual; cada regra de país (inclusive Estado extinto e override); foto do Commons, candidatas e escolha; escolha da fonte por idioma e fallback para Tavily; resposta do LLM com e sem "fontes insuficientes"; não sobrescrever bio aprovada; cache e `--dry-run`; falta de chave.
3. A migração da F1 SHALL ter teste de preservação dos dados enriquecidos.

### Requisito 11 — Carga inicial e manutenção

**História:** Como mantenedor, quero um mesmo processo para a carga inicial das
215 autorias (uma vez) e para cada autoria nova que entrar com um livro novo,
para que a manutenção use o que foi aprendido na carga.

#### Critérios de aceitação

1. O script SHALL selecionar por padrão só as autorias **pendentes**: as que têm algum campo vazio (identificação, país, foto, bio) sem decisão registrada (escolha manual, "sem foto", rejeição ou estado definitivo).
2. A carga inicial SHALL rodar em **ondas**, com revisão entre elas: (1) fontes gratuitas (Wikidata, Wikipédia, Commons); (2) bios via OpenAI a partir dessas fontes; (3) fallbacks com cota (SerpApi, Tavily).
3. A ordem de processamento SHALL priorizar as autorias mais visíveis: nº de leituras, depois a presença no ano corrente, depois o slug. Se a cota acabar, as mais visíveis já estarão feitas.
4. A carga SHALL poder ser interrompida e retomada (inclusive em outro mês) sem refazer chamadas, usando o cache e o estado do catálogo.
5. A manutenção SHALL ser a mesma CLI aplicada a uma ou poucas autorias (`--only`), com as mesmas regras, sem passos manuais além da revisão.

### Requisito 12 — Orçamento dos planos gratuitos

**História:** Como mantenedor, quero que os scripts nunca estourem os planos
gratuitos do Tavily (1.000 créditos/mês) e da SerpApi (250 buscas/mês), e que
sobre cota para a manutenção e para as outras specs da F2 (capas).

#### Critérios de aceitação

1. O projeto SHALL ter `pipeline/config/budgets.json` com, por provedor com cota: limite mensal, reserva para manutenção e teto por execução; e, para a OpenAI, um teto de custo em US$ por execução.
2. Antes de cada chamada **paga ou com cota** (que não esteja no cache), THE script SHALL conferir o saldo disponível = limite − uso do mês − reserva, e SHALL pular a chamada quando não houver saldo, registrando a autoria como "adiada por cota".
3. O uso do mês SHALL ser o maior entre o registro local (`pipeline/cache/usage/{provedor}-{AAAA-MM}.json`) e o informado pela API (SerpApi `/account`, Tavily `/usage`, que não consomem cota), consultado no início de cada execução.
4. O `--dry-run` SHALL mostrar, por provedor, as chamadas necessárias, o saldo atual e se a execução cabe no mês. Se não couber, SHALL mostrar quantas autorias (na ordem de prioridade) cabem.
5. A reserva SHALL poder ser usada com `--use-reserve`, nunca por padrão.

### Requisito 13 — Registro de execuções e aprendizados

**História:** Como mantenedor, quero que cada execução real deixe números
comparáveis, para ajustar as regras com base na carga inicial e manter a
manutenção barata.

#### Critérios de aceitação

1. Cada execução real (não `--dry-run`) SHALL acrescentar uma entrada a `docs/plans/enriquecimento-execucoes.md` com: data, seleção, etapas, autorias processadas, resultado por fonte (ex.: fotos via Commons/Wikipédia/SerpApi/Tavily, bios via Wikipédia/Tavily, por idioma), chamadas por provedor (rede × cache), tokens, custo e falhas.
2. Os parâmetros ajustáveis (mínimo da introdução, modelos de consulta, domínios excluídos, prompt da bio, tamanho mínimo de imagem, ordem das fontes) SHALL ficar em configuração versionada (`pipeline/config/enrich.json` e `pipeline/config/prompts/`), e não no código, para que os aprendizados mudem o comportamento sem alterar código.
3. Cada resumo gerado SHALL registrar a versão do prompt usada (`promptVersion`), para regenerar só o que foi gerado por um prompt antigo.
4. Ao fim da carga inicial, SHALL ser escrito `docs/plans/aprendizados-enriquecimento.md` com taxas de acerto por fonte, ajustes feitos e a estimativa de custo por autoria nova, para guiar a manutenção (F5).

## Fora do escopo

- Resumos de ano e de país (spec `resumos`, que reaproveita o cliente OpenAI e a CLI de revisão desta spec).
- Capas, temas e romanizações (outras specs da F2).
- Redimensionamento e otimização de imagens (build do app, F3).
- Interface gráfica de revisão (admin, F5). Nesta fase, a revisão é feita em sessão.

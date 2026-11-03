# Requisitos — Infra e hospedagem (F4)

## Introdução

A S1 (`estante-fundacao`) entregou o app Astro estático em `app/`, que builda
com código 0 e gera HTML sem JavaScript. Esta spec publica esse app na web,
para a Lila poder testar no Samsung cedo — antes mesmo das telas de leitura
(S2+) existirem.

A decisão de hospedagem foi tomada: **Cloudflare Pages**, com deploy por
**GitHub Actions** (Direct Upload com Wrangler). O endereço de teste é um
**subdomínio**, `liliane.prateleira.site`, com o app na raiz (`base: "/"`). O
Cloudflare Access protege o modo autenticado da Lila (que só existe na S7) sem
código, por hostname.

Esta spec cobre o caminho público: build no CI → publicação no Pages → domínio
custom no ar. A proteção do modo da Lila (Access) é **preparada**, não ativada
sobre a estante pública.

### Decisões já tomadas

- **Cloudflare Pages**, não AWS. Pesa a favor: o Access protege o modo da Lila
  sem código, e o custo-alvo fica perto de zero.
- **Subdomínio** `liliane.prateleira.site`, app na raiz (`base: "/"`). Evita o
  `base` por subcaminho em todo link, imagem, service worker e manifest.
- **Deploy por GitHub Actions**, não pela integração Git nativa do Cloudflare
  nem da máquina de ninguém. Todo deploy é rastreável e reproduzível.
- **Token do Cloudflare é credencial de CI**: vive nos **secrets do GitHub**
  (`CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`), nunca no `.env` nem no git.
  O `.env` é do pipeline Python; não tem relação com o deploy.
- O **domínio custom** é apontado uma vez no painel do Cloudflare, não pelo
  pipeline (não damos poder de DNS ao token de CI).

### Glossário

- **Pages**: Cloudflare Pages, hospedagem de sites estáticos.
- **Direct Upload**: publicar no Pages enviando artefatos já prontos (o `dist/`
  do Astro), em vez de deixar o Cloudflare buildar.
- **Wrangler**: a CLI do Cloudflare usada pelo CI para o Direct Upload.
- **Access**: Cloudflare Access, proteção de rotas/hostnames por identidade,
  sem código na aplicação.
- **Secret de CI**: valor cifrado em Settings → Secrets do repositório no
  GitHub, lido só pelo workflow.

## Requisitos

### Requisito 1 — App na raiz do subdomínio

**História:** Como mantenedor, quero o app servido na raiz de
`liliane.prateleira.site`, para não carregar um prefixo de caminho em todo
link, imagem, service worker e manifest.

#### Critérios de aceitação

1. THE app SHALL ser configurado com `base: "/"` (raiz), sem prefixo de subcaminho.
2. THE site publicado SHALL responder em `https://liliane.prateleira.site/` com a página inicial, e em `/styleguide` com a vitrine.
3. THE links internos, imagens derivadas e caminhos de asset SHALL funcionar em produção sem ajuste manual de prefixo.
4. WHERE o app evoluir para PWA (S6), THE escopo na raiz SHALL permitir o service worker cobrir o app inteiro sem configuração extra de escopo.

### Requisito 2 — Deploy contínuo por GitHub Actions

**História:** Como mantenedor, quero que um push para `main` publique o site,
para que o deploy seja rastreável, reproduzível e não dependa da máquina de
ninguém.

#### Critérios de aceitação

1. THE projeto SHALL ter um workflow do GitHub Actions que, ao receber push em `main` que afete o app ou o catálogo, rode o build e publique no Cloudflare Pages via Wrangler (Direct Upload).
2. THE workflow SHALL instalar dependências com versões fixadas (do `package-lock.json`), rodar `npm run check` e `npm test`, e só publicar se tudo passar.
3. IF o build falhar (ex.: catálogo inválido quebra o build, conforme a S1), THEN THE workflow SHALL falhar e SHALL NOT publicar.
4. THE workflow SHALL autenticar no Cloudflare usando os secrets `CLOUDFLARE_API_TOKEN` e `CLOUDFLARE_ACCOUNT_ID`, lidos do repositório; SHALL NOT conter credenciais em texto no arquivo.
5. THE workflow SHALL publicar o conteúdo do diretório de saída do Astro (`app/dist`).
6. WHERE houver pull request, THE workflow MAY gerar um deploy de pré-visualização (preview), sem afetar o endereço de produção.
7. THE Node e as ferramentas no CI SHALL casar com o ambiente local (Node 22), para o build do CI reproduzir o local.

### Requisito 3 — Token e permissões mínimas

**História:** Como mantenedor, quero o token de deploy com o menor privilégio
possível, para limitar o estrago caso ele vaze.

#### Critérios de aceitação

1. THE token do Cloudflare SHALL ter apenas as permissões necessárias para o Direct Upload com Wrangler v4: `Account → Cloudflare Pages → Edit`, `User → Memberships → Read` e `User → User Details → Read`.
2. THE token SHALL ser limitado em Account Resources à conta do projeto, não a todas as contas.
3. THE token e o account ID SHALL residir nos secrets do GitHub; a documentação da spec SHALL instruir a criá-los e a NÃO os colocar no `.env` nem no git.
4. THE spec SHALL registrar a recomendação de rotacionar o token antes do uso em produção (porque esteve em texto puro no `.env` local durante o setup) e de dar TTL ao token.
5. THE token SHALL NOT incluir permissões de Zone/DNS, Workers, R2, KV ou Access — nenhuma delas é necessária para o Direct Upload.

### Requisito 4 — Domínio custom

**História:** Como leitora, quero acessar a estante por um endereço memorável,
para abrir no celular sem decorar uma URL do Pages.

#### Critérios de aceitação

1. THE projeto do Pages SHALL ter o domínio custom `liliane.prateleira.site` apontado a ele, configurado uma vez no painel do Cloudflare (não pelo pipeline).
2. THE site SHALL ser servido por HTTPS, com certificado gerido pelo Cloudflare.
3. THE endereço padrão do Pages (`*.pages.dev`) MAY continuar acessível, mas o endereço canônico divulgado SHALL ser o domínio custom.
4. THE spec SHALL documentar o passo manual de apontar o domínio, com os nomes de tela atuais do painel (sujeitos a mudança, com ressalva).

### Requisito 5 — Preparar o modo da Lila (Access), sem bloquear a estante

**História:** Como Lila, quero que o meu modo autenticado (quando existir, na
S7) seja protegível sem código, enquanto a estante pública fica aberta a todos.

#### Critérios de aceitação

1. THE estante pública SHALL ficar acessível sem autenticação em `liliane.prateleira.site`.
2. THE spec SHALL documentar como o Cloudflare Access protegerá, por hostname ou rota, o futuro modo da Lila, sem exigir código na aplicação.
3. THE configuração de Access SHALL ser **preparada/documentada**, não ativada sobre a estante pública nesta fase (o modo da Lila é a S7).
4. WHERE o modo da Lila vier a existir, THE isolamento por hostname (ex.: um subdomínio de administração) SHALL permitir aplicar o Access só a ele.

### Requisito 6 — Documentação e reprodutibilidade

**História:** Como mantenedor, quero o processo documentado em `infra/`, para
reproduzir ou retomar o deploy sem redescobrir os passos.

#### Critérios de aceitação

1. THE configuração de deploy (workflow, `wrangler` config) SHALL viver no repositório, versionada.
2. THE `infra/` SHALL ter um README que descreva: a arquitetura (Pages + Actions), os secrets necessários, os passos manuais (domínio, Access), e como disparar/rever um deploy.
3. THE `.env.example` SHALL registrar que as chaves do Cloudflare são secrets de CI (GitHub), não do `.env`.
4. THE documentação SHALL assumir que a S1 precisa estar commitada e no `main` antes do primeiro deploy (o pipeline publica o que está no repositório).
5. THE custo-alvo SHALL ser perto de zero; a spec SHALL evitar recursos pagos desnecessários.

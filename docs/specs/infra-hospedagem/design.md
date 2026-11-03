# Design — Infra e hospedagem (F4)

## Visão geral

Publicar o app estático da S1 em **Cloudflare Pages**, com deploy por **GitHub
Actions** (Direct Upload via Wrangler), servido em **`liliane.prateleira.site`**
na raiz. O caminho é:

```
push em main → GitHub Actions: check + test + build (app/dist)
            → wrangler pages deploy app/dist → Cloudflare Pages
            → domínio custom liliane.prateleira.site (apontado 1× no painel)
```

Princípios que guiam as escolhas:

- **Deploy reproduzível e rastreável.** Sai do CI a partir do que está no
  `main`, nunca da máquina de alguém. O mesmo build que passou local roda no CI.
- **Menor privilégio.** O token de deploy só tem Pages:Edit + Memberships:Read,
  escopado à conta. Nada de DNS, Workers, Access no token.
- **Segredo só no lugar certo.** Credencial vive nos secrets do GitHub, nunca
  no `.env` nem no git. O `.env` é do pipeline Python e não tem relação com isso.
- **Custo perto de zero.** Pages estático no plano gratuito; sem recurso pago.

### Mapa de requisitos → seção

| Requisito | Onde é atendido |
|---|---|
| R1 App na raiz | §1 Configuração do app |
| R2 Deploy por Actions | §3 Workflow de CI |
| R3 Token mínimo | §4 Token e secrets |
| R4 Domínio custom | §5 Domínio |
| R5 Access preparado | §6 Access (preparação) |
| R6 Documentação | §7 Arquivos em `infra/` |

> Versões fixadas (estáveis em nov/2026): `wrangler@4.157.0`,
> `cloudflare/wrangler-action@v4.1.3`. Node 22 (casa com a S1). Wrangler v4 é a
> linha atual; o comando de deploy do Pages é `wrangler pages deploy`.

## 1. Configuração do app (R1)

A S1 já assume a raiz — o placeholder e a vitrine usam caminhos de raiz e não há
`base` configurado, então `base` já é `/` por padrão. O design apenas **torna
isso explícito** e adiciona o que o deploy precisa:

- `astro.config.mjs`: manter `output: "static"`; deixar `site:
  "https://liliane.prateleira.site"` explícito (ajuda sitemap/meta absolutos no
  futuro) e `base` implícito em `/`.
- Nenhuma mudança nos componentes ou na camada de dados da S1.

Decisão: **não** definir `base` com subcaminho. O subdomínio mantém tudo na
raiz — links, imagens derivadas, e o futuro service worker (S6) e manifest —
sem prefixo a carregar em cada caminho.

## 2. Topologia no Cloudflare

- **Um projeto Pages** (ex.: `prateleira-liliane`), que recebe os Direct Uploads.
- **Produção** = deploys da branch `main`. **Previews** = deploys de outras
  branches/PRs (URLs `*.pages.dev` efêmeras).
- **Domínio custom** `liliane.prateleira.site` ligado ao projeto, apontando
  para a produção.
- O endereço `prateleira-liliane.pages.dev` continua existindo, mas o canônico
  divulgado é o domínio custom (R4.3).

## 3. Workflow de CI (R2)

Arquivo: `.github/workflows/deploy.yml`. Dispara em push para `main` que afete
o app ou o catálogo, e em PR (para preview).

Estrutura:

```yaml
name: Deploy
on:
  push:
    branches: [main]
    paths: ["app/**", "catalog/**", ".github/workflows/deploy.yml"]
  pull_request:
    paths: ["app/**", "catalog/**", ".github/workflows/deploy.yml"]

permissions:
  contents: read
  deployments: write   # para registrar o deployment no GitHub

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm
          cache-dependency-path: app/package-lock.json
      - run: npm ci
        working-directory: app
      - run: npm run check
        working-directory: app
      - run: npm test
        working-directory: app
      - run: npm run build
        working-directory: app
      - name: Publicar no Cloudflare Pages
        uses: cloudflare/wrangler-action@v4.1.3
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          workingDirectory: app
          command: pages deploy dist --project-name=prateleira-liliane
```

Pontos de design:

- **Ordem com portão de qualidade (R2.2, R2.3):** `npm ci` (versões travadas do
  lockfile) → `check` → `test` → `build`. Qualquer um falhando aborta o job
  **antes** do passo de publicação. Catálogo inválido quebra o `build` (trava da
  S1) e nada é publicado.
- **Node 22** no CI, igual ao local (R2.7), com cache de npm pelo lockfile.
- **`wrangler pages deploy dist`** publica a saída do Astro (R2.5). O
  `--project-name` fixa o projeto do Pages.
- **Preview em PR (R2.6):** o mesmo job roda em `pull_request`; como o deploy de
  uma branch ≠ `main` vira um preview no Pages, o PR ganha uma URL efêmera sem
  tocar produção. (Deploy de produção só quando o push é em `main`.)
- **Sem credencial no arquivo (R2.4):** só referências a `secrets.*`.

Decisão: usar a **action oficial `cloudflare/wrangler-action`** em vez de
instalar o wrangler à mão. Ela encapsula instalação e autenticação, e é a
mantida pela Cloudflare. Alternativa (rodar `npx wrangler` direto) foi
descartada por reinventar o que a action já faz.

### Gatilho por `paths`

O deploy só dispara quando muda o que vai ao ar (`app/**`, `catalog/**`) ou o
próprio workflow. Mudança só em `docs/` ou `pipeline/` não republica o site —
economiza build e deixa o histórico de deploy limpo.

## 4. Token e secrets (R3)

### Permissões do token (menor privilégio)

| Permissão | Para quê |
|---|---|
| `Account → Cloudflare Pages → Edit` | criar deploys no projeto Pages |
| `User → Memberships → Read` | o Wrangler v4 exige para autenticar na conta |
| `User → User Details → Read` | o Wrangler v4 lê a identidade do dono do token antes de publicar |

- **Account Resources:** restrito à conta do projeto (não "todas as contas").
- **Nada além disso:** sem Zone/DNS, Workers, R2, KV, Access (R3.5).
- **TTL:** recomendado pôr expiração no token (R3.4).

### Secrets no GitHub

Em `Settings → Secrets and variables → Actions`:

| Secret | Conteúdo |
|---|---|
| `CLOUDFLARE_API_TOKEN` | o token acima |
| `CLOUDFLARE_ACCOUNT_ID` | o Account ID (Workers & Pages → painel) |

### Higiene (registrado como ação do mantenedor)

- O token esteve em texto puro no `.env` local durante o setup. Recomenda-se
  **rotacioná-lo** (recriar no Cloudflare, atualizar o secret, invalidar o
  antigo) antes de produção de verdade (R3.4).
- Remover o `CLOUDFLARE_API_TOKEN` do `.env` (é de CI, não do pipeline).

## 5. Domínio custom (R4)

Passo manual, uma vez, no painel do Cloudflare (não pelo pipeline — não damos
DNS ao token de CI):

1. No projeto Pages → **Custom domains** → adicionar
   `liliane.prateleira.site`.
2. Como `prateleira.site` já está no Cloudflare, o registro DNS
   (CNAME para o `*.pages.dev`) é criado/validado pelo próprio painel.
3. O certificado TLS é emitido e gerido pelo Cloudflare (R4.2); o site passa a
   responder em HTTPS.

> Os nomes de tela do painel ("Custom domains", "Workers & Pages") são os
> atuais (nov/2026) e podem mudar; o README de `infra/` repete o passo a passo
> com essa ressalva (R4.4).

## 6. Access — preparação, sem bloquear a estante (R5)

Nesta fase a estante é **pública**: nenhuma regra de Access sobre
`liliane.prateleira.site` (R5.1, R5.3). O que o design deixa **documentado**
para a S7 (modo da Lila):

- O Cloudflare Access aplica políticas por **hostname/rota**. Quando o modo da
  Lila existir, ele vive isolado — p. ex. um subdomínio de administração
  (`admin.liliane.prateleira.site`) ou uma rota dedicada — e **só esse
  hostname/rota** recebe a política de Access (R5.2, R5.4).
- Assim a estante pública nunca fica atrás de login, e o modo da Lila fica
  protegido sem uma linha de código na aplicação.

> Variante possível, se você quiser a estante **inteira** fechada durante os
> testes (antes de ser divulgada): aplicar uma política de Access ao hostname
> todo, temporariamente. Não é o default desta spec; é uma decisão à parte.

## 7. Arquivos em `infra/` (R6)

Tudo versionado no repositório:

```text
.github/workflows/deploy.yml   workflow de CI (vive na raiz, exigência do GitHub)
infra/
  README.md                    arquitetura, secrets, passos manuais, como operar
  wrangler.toml                config mínima do Pages (name, pages_build_output_dir)
```

- `wrangler.toml` (mínimo, para o Direct Upload saber o projeto e a saída):

  ```toml
  name = "prateleira-liliane"
  pages_build_output_dir = "app/dist"
  compatibility_date = "2026-11-03"
  ```

- `infra/README.md` cobre (R6.2): o desenho Pages + Actions; os dois secrets e
  como criá-los; os passos manuais (domínio custom, e a preparação do Access);
  como disparar um deploy (push em `main`) e onde revê-lo (aba Actions no
  GitHub e Deployments no painel do Pages); a ressalva de nomes de tela.
- `.env.example` ganha um comentário: as chaves do Cloudflare são **secrets de
  CI (GitHub)**, não do `.env` (R6.3).

### Dependência de commit (R6.4)

O pipeline publica o que está no `main`. A S1 ainda **não está commitada**.
Antes do primeiro deploy, a S1 (o `app/` e as specs) precisa estar commitada e
no `main`. Isso é pré-condição da primeira execução do workflow — não um passo
automatizável aqui.

## 8. Fluxo do primeiro deploy (ordem de execução)

1. (Mantenedor) Criar o projeto Pages `prateleira-liliane` no painel (uma vez), ou
   deixar o primeiro `wrangler pages deploy` criá-lo.
2. (Mantenedor) Criar o token e pôr os dois secrets no GitHub.
3. (Repo) Commitar a S1 + os arquivos desta F4 e dar push em `main`.
4. (CI) O workflow roda check + test + build e publica.
5. (Mantenedor) Apontar o domínio custom `liliane.prateleira.site` no painel.
6. Verificar o site no ar e testar no Samsung da Lila.

## 9. Decisões e alternativas

| Decisão | Alternativa descartada | Porquê |
|---|---|---|
| Cloudflare Pages | AWS S3+CloudFront | Access protege o modo da Lila sem código; custo ~zero; menos peças |
| Deploy por GitHub Actions | integração Git nativa do Cloudflare | build controlado por nós (check+test+trava do catálogo), reproduzível |
| `wrangler-action` oficial | `npx wrangler` na mão | mantida pela Cloudflare; encapsula install e auth |
| Subdomínio na raiz | subcaminho `/liliane` com `base` | sem prefixo em link/imagem/SW/manifest; PWA e Access mais simples |
| Token Pages:Edit + Memberships:Read | template "Edit Cloudflare Workers" | menor privilégio; o template dá permissão demais |
| Domínio apontado no painel | automatizar DNS no CI | não dar poder de DNS ao token de CI |

## 10. Riscos e limites conhecidos

- **Nomes de tela do painel mudam.** O passo a passo do domínio e do token pode
  divergir do rótulo atual; o README avisa e descreve o conceito, não só o
  clique.
- **Token já exposto localmente.** Mitigado pela rotação recomendada (§4).
- **Primeiro deploy depende de commit da S1.** Explícito em §7 e §8.
- **Preview em PR cria URLs efêmeras.** Aceitável; não afetam produção. Se o
  volume incomodar, dá para restringir o gatilho de PR depois.

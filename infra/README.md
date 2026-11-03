# infra/ — hospedagem da Estante da Lila

A estante é publicada em **Cloudflare Pages**, com deploy por **GitHub
Actions**. Endereço: **`liliane.prateleira.site`** (subdomínio, app na raiz).

Spec: [`docs/specs/infra-hospedagem/`](../docs/specs/infra-hospedagem/).

## Arquitetura

```
push em main ─► GitHub Actions (.github/workflows/deploy.yml)
                 ├─ npm ci  (versões travadas)
                 ├─ npm run check   (tipos)
                 ├─ npm test        (camada de dados)
                 ├─ npm run build   (quebra se o catálogo for inválido)
                 └─ wrangler pages deploy app/dist  ─► Cloudflare Pages
                                                       └─ liliane.prateleira.site
```

- **Produção**: deploys da branch `main`.
- **Preview**: deploys de pull requests (URLs `*.pages.dev` efêmeras).
- O build no CI é o mesmo do local (Node 22). Catálogo inválido quebra o build
  e **nada** é publicado.

## Secrets necessários (GitHub)

Em `Settings → Secrets and variables → Actions` do repositório:

| Secret | Conteúdo |
|---|---|
| `CLOUDFLARE_API_TOKEN` | token de API do Cloudflare (ver abaixo) |
| `CLOUDFLARE_ACCOUNT_ID` | Account ID (painel: Workers & Pages) |

> As chaves do Cloudflare são **secrets de CI**, não entram no `.env` nem no
> git. O `.env` é do pipeline Python e não tem relação com o deploy.

### Token — permissões mínimas

Criar em **My Profile → API Tokens → Create Custom Token**:

- `Account → Cloudflare Pages → Edit`
- `User → Memberships → Read`  ← o Wrangler v4 exige para autenticar na conta

**Account Resources**: restrito à sua conta (não "todas as contas"). TTL
opcional, recomendado. **Não** incluir Zone/DNS, Workers, R2, KV ou Access —
nada disso é necessário para o Direct Upload.

> Higiene: se o token esteve em texto puro em algum lugar (ex.: `.env` durante o
> setup), **rotacione-o** antes de produção — recrie no Cloudflare, atualize o
> secret no GitHub e invalide o antigo. E remova-o do `.env`.

## Passos manuais (uma vez, no painel do Cloudflare)

1. **Projeto Pages**: criar `prateleira-liliane` (ou deixar o primeiro
   `wrangler pages deploy` criá-lo).
2. **Domínio custom**: no projeto → **Custom domains** → adicionar
   `liliane.prateleira.site`. Como `prateleira.site` já está no Cloudflare, o
   CNAME é criado/validado no painel e o TLS é emitido pelo Cloudflare.
3. **Access (preparação, não agora)**: o modo autenticado da Lila é a spec S7.
   Quando existir, o Cloudflare Access o protegerá por hostname/rota (ex.: um
   `admin.liliane.prateleira.site`), sem código na aplicação. A estante pública
   fica aberta.

> Os nomes de tela do painel ("Custom domains", "Workers & Pages", "Create
> Custom Token") são os atuais e podem mudar. Se o rótulo divergir, o conceito
> continua o mesmo.

## Operar

- **Disparar um deploy**: push em `main` que toque `app/**` ou `catalog/**`.
- **Rever um deploy**: aba **Actions** no GitHub (log do build) e
  **Deployments** no projeto do Pages (histórico e URLs).
- **Trocar o nome do projeto Pages**: editar `infra/wrangler.toml` e o
  `--project-name` em `.github/workflows/deploy.yml`.

## Pré-condição do primeiro deploy

O pipeline publica o que está no `main`. A S1 (o `app/`) precisa estar commitada
e no `main` antes do primeiro deploy.

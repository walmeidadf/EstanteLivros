# Tarefas — Infra e hospedagem (F4)

Referências: [`requirements.md`](requirements.md) · [`design.md`](design.md).

Esta spec tem dois tipos de tarefa:

- **Implementação (eu):** arquivos versionados no repositório (config do app,
  workflow, `wrangler.toml`, READMEs). Terminam com o workflow válido e o build
  local verde.
- **Operação (você), marcadas (manual):** passos no painel do Cloudflare e nos
  secrets do GitHub — credenciais e DNS que **não** passam por mim nem pelo
  pipeline.

O nome do projeto Pages usado nos arquivos é **`prateleira-liliane`**. Se mudar,
trocar em `wrangler.toml` e no `--project-name` do workflow.

Dependências:

```
1 → 2 → 3 → 4 → (5, 6 manuais) → 7 → 8 (primeiro deploy) → 9 (verificação)
```

## Implementação (repositório)

- [x] 1. Configuração do app para produção
  - [x] 1.1 `app/astro.config.mjs`: `site: "https://liliane.prateleira.site"` explícito; `output: "static"` e `base` na raiz (sem subcaminho).
    - _Requisitos: 1.1, 1.3_
  - [x] 1.2 Build local do zero: caminhos saem na raiz (`/_astro/...`), zero ocorrências de `/liliane`.
    - _Requisitos: 1.1, 1.2, 1.3_

- [x] 2. Config do Wrangler (`infra/wrangler.toml`)
  - `name = "prateleira-liliane"`, `pages_build_output_dir = "app/dist"`, `compatibility_date`. Mínimo necessário para o Direct Upload.
  - _Requisitos: 2.5, 6.1_

- [x] 3. Workflow de CI (`.github/workflows/deploy.yml`)
  - [x] 3.1 Gatilhos: push em `main` e `pull_request`, filtrados por `paths` (`app/**`, `catalog/**`, o próprio workflow).
    - _Requisitos: 2.1, 2.6_
  - [x] 3.2 Job: checkout; `setup-node@v4` Node 22 com cache de npm; `npm ci`; `npm run check`; `npm test`; `npm run build` — em `working-directory: app`, nesta ordem (portão de qualidade). `concurrency` para cancelar deploys sobrepostos.
    - _Requisitos: 2.2, 2.3, 2.7_
  - [x] 3.3 Publicação com `cloudflare/wrangler-action@v4.1.3`: `command: pages deploy dist --project-name=prateleira-liliane`, `workingDirectory: app`, lendo os dois secrets. Nenhuma credencial em texto.
    - _Requisitos: 2.4, 2.5_
  - [x] 3.4 YAML validado (chaves de topo, ordem do portão, indentação por espaços, secrets referenciados).
    - _Requisitos: 2.1_

- [x] 4. Documentação (`infra/README.md` e `.env.example`)
  - [x] 4.1 `infra/README.md`: arquitetura, os dois secrets, permissões exatas do token, passos manuais (projeto, domínio, preparação do Access), como operar, ressalva de nomes de tela.
    - _Requisitos: 3.3, 4.4, 6.2_
  - [x] 4.2 `.env.example`: bloco comentando que as chaves do Cloudflare são **secrets de CI (GitHub)**, não do `.env`.
    - _Requisitos: 6.3_
  - [x] 4.3 Recomendação de rotacionar o token e removê-lo do `.env`, registrada no README.
    - _Requisitos: 3.4_

## Operação (você — no Cloudflare e no GitHub)

- [ ] 5. (manual) Token e secrets
  - [ ] 5.1 Criar o token custom no Cloudflare: `Account → Cloudflare Pages → Edit` **e** `User → Memberships → Read`; Account Resources restrito à sua conta; TTL opcional.
    - _Requisitos: 3.1, 3.2, 3.5_
  - [x] 5.2 `CLOUDFLARE_API_TOKEN` e `CLOUDFLARE_ACCOUNT_ID` nos secrets do repo. Token com Pages:Edit + Memberships:Read + User Details:Read; Account Resources incluindo a conta `45bfe9cc…` (esse escopo era o que faltava).
    - _Requisitos: 3.3_

- [x] 6. (manual/terminal) Projeto Pages e domínio
  - [x] 6.1 Projeto Pages `prateleira-liliane` criado (via `wrangler pages project create`). Disponível em `prateleira-liliane.pages.dev`.
    - _Requisitos: 4.1_
  - [x] 6.2 Domínio custom `liliane.prateleira.site` apontado e no ar por HTTPS (home e `/styleguide/` em 200; TLS do Cloudflare/Google Trust Services, válido até fev/2027).
    - _Requisitos: 4.1, 4.2, 4.3_

## Fechamento

- [ ] 7. (manual) Commit e push da S1 + F4
  - A S1 ainda não está commitada. Commitar `app/`, as specs e os arquivos desta F4, e dar push em `main` — pré-condição do primeiro deploy (o pipeline publica o que está no `main`). Commit só com seu aval.
  - _Requisitos: 6.4_

- [x] 8. Primeiro deploy
  - Primeiro deploy feito pelo terminal (`wrangler pages deploy dist`) para destravar: 198 arquivos publicados, no ar em `prateleira-liliane.pages.dev`. Os próximos deploys saem do workflow em push para `main`.
  - _Requisitos: 2.1, 2.2, 2.3_

- [x] 9. Verificação no ar
  - [x] 9.1 Site no ar por HTTPS no domínio custom `liliane.prateleira.site` (home 200, `/styleguide/` 200) e em `prateleira-liliane.pages.dev`.
    - _Requisitos: 1.2, 4.2_
  - [x] 9.2 Prova da trava validada: build quebra com catálogo inválido (feito em cópia temporária na S1) e o portão check+test+build roda antes do publish no CI. CI de produção verde no merge.
    - _Requisitos: 2.3_
  - [ ] 9.3 Abrir no Samsung da Lila e confirmar que carrega e está legível. **(você)**
    - _Requisitos: 1.2_
  - [x] 9.4 `docs/ROADMAP.md` atualizado (F4 no ar) e nota de operação registrada.
    - _Requisitos: 6.4_

### Pendências manuais (você)
- Apontar o domínio custom `liliane.prateleira.site` no painel do Pages (tarefa 6.2).
- Sincronizar o secret `CLOUDFLARE_API_TOKEN` com o `.env` sempre que rotacionar (hoje: feito via `gh secret set`).
- Higiene: rotacionar o token e tirá-lo do `.env` quando quiser (o deploy já lê dos secrets do GitHub).

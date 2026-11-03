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
  - [ ] 5.2 Pôr `CLOUDFLARE_API_TOKEN` e `CLOUDFLARE_ACCOUNT_ID` em Settings → Secrets → Actions do repo. (Você disse que já fez — confirmar que estão com esses nomes exatos.)
    - _Requisitos: 3.3_

- [ ] 6. (manual) Projeto Pages e domínio
  - [ ] 6.1 Criar o projeto Pages `prateleira-liliane` (ou deixar o primeiro deploy criá-lo).
    - _Requisitos: 4.1_
  - [ ] 6.2 Após o primeiro deploy, apontar o domínio custom `liliane.prateleira.site` no projeto (Custom domains); confirmar o CNAME e o TLS do Cloudflare.
    - _Requisitos: 4.1, 4.2, 4.3_

## Fechamento

- [ ] 7. (manual) Commit e push da S1 + F4
  - A S1 ainda não está commitada. Commitar `app/`, as specs e os arquivos desta F4, e dar push em `main` — pré-condição do primeiro deploy (o pipeline publica o que está no `main`). Commit só com seu aval.
  - _Requisitos: 6.4_

- [ ] 8. Primeiro deploy
  - Push em `main` dispara o workflow: check + test + build passam e o site é publicado. Conferir a aba Actions (verde) e o Deployments no painel do Pages.
  - _Requisitos: 2.1, 2.2, 2.3_

- [ ] 9. Verificação no ar
  - [ ] 9.1 `https://liliane.prateleira.site/` responde (placeholder) e `/styleguide` mostra a vitrine, por HTTPS.
    - _Requisitos: 1.2, 4.2_
  - [ ] 9.2 Prova da trava em produção: um commit que invalide o catálogo (numa branch/PR, **nunca** quebrando o `main`) faz o workflow falhar **antes** de publicar.
    - _Requisitos: 2.3_
  - [ ] 9.3 Abrir no Samsung da Lila e confirmar que carrega e está legível.
    - _Requisitos: 1.2_
  - [ ] 9.4 Atualizar `docs/ROADMAP.md` (F4 no ar) e deixar nota de operação para as próximas specs.

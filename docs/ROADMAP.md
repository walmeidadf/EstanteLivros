# Roadmap

```text
F0 Fundação ─► F1 Catálogo canônico ─┬─► F2 Enriquecimento (sessões de conversa) ──┐
                                     └─► F3 App (specs) ─► F4 Deploy contínuo ─────┴─► F5 Admin
```

F2 e F3 andam em paralelo depois da F1: o design tem fallback para capa
(tipográfica), foto (iniciais), bio e resumos (a seção some). A exceção é o país
da autoria, necessário para o Atlas por país e a página País — por isso a F2.1
(autorias) foi feita antes do app. O resto da base se corrige vendo a interface.

## Decisões tomadas
- PWA (site estático instalável), não app nativo.
- Estante pública; só a Lila compartilha (modo autenticado dela).
- Resumos gerados e aprovados para autoria, ano e país. Sem sinopse de obra.
- Catálogo em arquivos JSON versionados no git.
- Capas e fotos hospedadas pelo projeto (sem hotlink); derivados gerados no build.
- Legado local em `legacy/`, fora do git.

## Decisões em aberto
- Hospedagem: AWS (S3 + CloudFront) ou Cloudflare Pages. Pesa a favor da
  Cloudflare: o Cloudflare Access protege o modo da Lila sem código. Na AWS,
  isso exige Cognito ou uma função na borda.
- Domínio.

## Decisões resolvidas na F2.1
- Fotos de autoria: **qualquer fonte**, não só licença livre. A origem é
  registrada. Commons automático; as demais escolhidas em revisão.
- Bio: busca (Wikipédia, depois Tavily) + resumo/tradução via OpenAI; aprovação
  humana. A bio vive em `summaries.json` (`autoria:{slug}`), não na autoria.
- País: só o principal. Chaves de API em `.env` (modelo em `.env.example`).
- A base não precisa estar completa para a F3 começar: corrige-se vendo o app.

## F0 — Fundação
- [x] Estrutura de pastas, legado em `legacy/`
- [x] `AGENTS.md` + hook de início de sessão; detalhes em `docs/`
- [x] Primeiro commit e push para `walmeidadf/EstanteLivros`

## F1 — Catálogo canônico ✓
Spec: [`docs/specs/catalogo-canonico/`](specs/catalogo-canonico/).
- [x] Schema de obra, autoria, leitura, vocabulários e resumo, com slugs estáveis
- [x] Migração de `legacy/exports/*.csv` para `catalog/` (302 obras, 215 autorias, 309 leituras)
- [x] Validador e relatório de cobertura (`docs/plans/cobertura.md`)

## F2 — Enriquecimento (por impacto visual)
1. [x] **F2.1 Autorias** via Wikidata: país, idiomas, foto, bio. Spec:
   [`docs/specs/enriquecimento-autorias/`](specs/enriquecimento-autorias/).
   206/215 identificadas, 202 com país, 174 com foto, 209 bios aprovadas.
   Em revisão contínua: 40 fotos, 9 sem Wikidata, 6 sem bio.
2. [ ] Capas: baixar as 223, trocar as de baixa resolução, buscar as 79 que faltam
3. [ ] Temas: reduzir 496 para ~40–60, revisado com a Lila
4. [ ] Títulos originais: separar título e romanização (21 não latinos)
5. [ ] Wikidata das obras e o `first_publication_year` que falta
6. [ ] Resumos de ano e país, com o mesmo fluxo da bio (reaproveita F2.1)

A F2.1 vem **antes** da F3 por causa do país (necessário ao Atlas). As demais
frentes da F2 rodam depois do app, corrigindo o que a interface mostrar.

## F3 — App (spec-driven)
| Spec | Escopo |
|---|---|
| S1 `estante-fundacao` ✓ | Astro 7, tokens, fontes (Fontsource), camada de dados (Zod), componentes base, vitrine |
| S2 `estante-inicio-busca` | Início e busca |
| S3 `linha-do-tempo` | Linha do tempo, Ano, Sem data |
| S4 `atlas` | Atlas (idioma e país), Idioma, País, Tema |
| S5 `obra-autoria` | Obra e Autoria |
| S6 `pwa-offline` | Manifest, offline, instalação |
| S7 `compartilhar` | Modo da Lila, retrospectiva 9:16, card de livro |

## F4 — Infra e deploy ✓ (no ar)
- Spec [`infra-hospedagem`](specs/infra-hospedagem/) concluída. App no ar em
  `prateleira-liliane.pages.dev` (Cloudflare Pages), deploy automático por
  GitHub Actions a cada push em `main`, com portão check + test + build.
- No ar em `liliane.prateleira.site` (domínio custom, HTTPS) e em
  `prateleira-liliane.pages.dev`.
- Cloudflare Access (modo da Lila) fica preparado para a S7.

## F5 — Admin
- Adicionar leitura em poucos toques, reaproveitando os scripts da F2.

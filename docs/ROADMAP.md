# Roadmap

```text
F0 Fundação ─► F1 Catálogo canônico ─┬─► F2 Enriquecimento (sessões de conversa) ──┐
                                     └─► F3 App (specs) ─► F4 Deploy contínuo ─────┴─► F5 Admin
```

F2 e F3 andam em paralelo depois da F1: o design tem fallback para capa
(tipográfica), foto (iniciais), bio e resumos (a seção some). A exceção é o país
da autoria, necessário para o Atlas por país e a página País.

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
- Fotos de autoria: aceitar só licenças livres (Wikimedia Commons)?

## F0 — Fundação
- [x] Estrutura de pastas, legado em `legacy/`
- [x] `AGENTS.md` + hook de início de sessão; detalhes em `docs/`
- [ ] Primeiro commit e push para `walmeidadf/EstanteLivros`

## F1 — Catálogo canônico
- [ ] Schema de obra, autoria, leitura, tema e resumo, com slugs estáveis
- [ ] Migração de `legacy/exports/*.csv` para `catalog/`
- [ ] Validador e relatório de cobertura

## F2 — Enriquecimento (por impacto visual)
1. [ ] Autorias via Wikidata: país, idiomas, idioma principal, foto Commons + licença
2. [ ] Capas: baixar as 223, trocar as de baixa resolução, buscar as 79 que faltam
3. [ ] Temas: reduzir 496 para ~40–60, revisado com a Lila
4. [ ] Títulos originais: separar título e romanização (21 não latinos)
5. [ ] Wikidata das obras e o `first_publication_year` que falta
6. [ ] Resumos de autoria, ano e país, com fluxo de aprovação

## F3 — App (spec-driven)
| Spec | Escopo |
|---|---|
| S1 `estante-fundacao` | Astro, tokens, fontes, camada de dados, componentes base |
| S2 `estante-inicio-busca` | Início e busca |
| S3 `linha-do-tempo` | Linha do tempo, Ano, Sem data |
| S4 `atlas` | Atlas (idioma e país), Idioma, País, Tema |
| S5 `obra-autoria` | Obra e Autoria |
| S6 `pwa-offline` | Manifest, offline, instalação |
| S7 `compartilhar` | Modo da Lila, retrospectiva 9:16, card de livro |

## F4 — Infra e deploy
- Spec `infra-hospedagem`, logo após S1, para a Lila testar no Samsung cedo.

## F5 — Admin
- Adicionar leitura em poucos toques, reaproveitando os scripts da F2.

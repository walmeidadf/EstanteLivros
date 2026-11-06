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
- Nenhuma de infraestrutura. As abertas hoje são de produto: quais temas
  sobrevivem à redução (F2.3) e quais anos ganham retrospectiva (S7).

## Decisões resolvidas na F4
- Hospedagem: **Cloudflare Pages** (o Cloudflare Access protege o modo da Lila
  sem código). Domínio: `liliane.prateleira.site`.

## Decisões resolvidas na F2.1
- Fotos de autoria: **qualquer fonte**, não só licença livre. A origem é
  registrada. Commons automático; as demais escolhidas em revisão.
- Bio: busca (Wikipédia, depois Tavily) + resumo/tradução via OpenAI; aprovação
  humana. A bio vive em `summaries.json` (`autoria:{slug}`), não na autoria.
- País: só o principal. Chaves de API em `.env` (modelo em `.env.example`).
- A base não precisa estar completa para a F3 começar: corrige-se vendo o app.

## Decisões resolvidas nas capas (F2.2)
- A capa real **não entra sozinha**: a Lila escolhe por obra; a tipográfica é um
  fallback digno e fica onde a real não acrescenta.
- Padrão estético acima de cobertura: só entram capas com boa resolução e
  enquadramento. Rejeitadas: página de rosto escaneada, capa de edição
  estrangeira, proporção que perde as laterais no corte 2:3.
- Corte central 2:3 por padrão; `focus` (`top`/`center`/`bottom`) só sob demanda.
- Onda 1 gratuita (URL do catálogo + Open Library por ISBN). Onda 2, paga
  (SerpApi/Tavily), só depois, para o backlog.

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
2. [x] **F2.2 Capas** (onda gratuita). Spec: [`docs/specs/capas-obras/`](specs/capas-obras/).
   131 de 302 obras com capa real (mestres em `catalog/media/covers/`); 171
   seguem na tipográfica e em `docs/plans/capas-backlog.md` (melhoria contínua,
   2ª onda paga). A maioria das capas da Literal tem lado menor < 400 px
   (mediana 319 px); só 25 passam de 400 px.
3. [ ] **F2.3 Temas**: reduzir 496 para ~40–60, revisado com a Lila (spec própria;
   leva junto o `404.astro` e a escolha dos temas do Início)
4. [ ] **F2.4/2.5 Dados das obras**: *quase pronto*, então vira tarefa curta, sem
   spec. Medido em `cobertura.md` (6/nov/2026): título original 185/187,
   romanização 8/21 (faltam 13), ano de primeira publicação 301/302. A lista de
   16 campos vai para `docs/plans/`. Wikidata das obras não é mais necessário.
5. [ ] **F2.6 Resumos de ano e país**, com o mesmo fluxo da bio (spec própria,
   reaproveita F2.1; ~49 textos: 13 anos e 36 países)

A F2.1 vem **antes** da F3 por causa do país (necessário ao Atlas). As demais
frentes da F2 rodam depois do app, corrigindo o que a interface mostrar.

## F3 — App (spec-driven)
| Spec | Escopo |
|---|---|
| S1 `estante-fundacao` ✓ | Astro 7, tokens, fontes (Fontsource), camada de dados (Zod), componentes base, vitrine |
| S2 `estante-inicio-busca` ✓ | Início (carrosséis + cartão Linha do tempo) e busca (índice estático + ilha). No ar. |
| S3 `linha-do-tempo` ✓ | Linha do tempo, Ano, Sem data. Quita o 404 de `/linha-do-tempo` e `/ano/{ano}`. |
| S4 `atlas` ✓ | Atlas (idioma e país), Idioma, País, Tema. Quita o 404 de `/atlas` e `/tema/{slug}`. No ar. |
| S5 `obra-autoria` ✓ | Obra (`/obra/{slug}`, 302) e Autoria (`/autoria/{slug}`, 215). Quita a última dívida de rota. No ar. |
| S6 `pwa-offline` | Manifest, offline, instalação |
| S7 `compartilhar` | Modo da Lila, retrospectiva 9:16, card de livro |

## F4 — Infra e deploy ✓ (no ar)
- Spec [`infra-hospedagem`](specs/infra-hospedagem/) concluída. App no ar em
  `prateleira-liliane.pages.dev` (Cloudflare Pages), deploy automático por
  GitHub Actions a cada push em `main`, com portão check + test + build.
- No ar em `liliane.prateleira.site` (domínio custom, HTTPS) e em
  `prateleira-liliane.pages.dev`.
- Cloudflare Access (modo da Lila) fica preparado para a S7.

## Próximos passos e o que fica para depois
**Escolha o próximo (nenhum depende do outro):**
- **F2.3 Temas** (spec): reduzir ~496 para ~40–60, revisado com a Lila. Afeta
  nuvem do Atlas, chips da Obra e temas da Autoria. Leva junto o `404.astro` (as
  páginas de tema caem de ~493 para ~50, e as URLs antigas somem) e a decisão de
  quais temas viram carrossel no Início (handoff §12.4).
- **F2.6 Resumos de ano e país** (spec): mesmo fluxo da bio. Ao aprovar, as
  seções que hoje somem em Ano e País passam a aparecer. Vem depois dos temas,
  porque o prompt pode citar temas e já usa os normalizados.
- **F2.4/2.5 Dados das obras** (tarefa curta, sem spec): 13 romanizações, 2
  títulos originais e 1 ano de primeira publicação. Inclui a fonte da capa
  tipográfica coreana, que também trata título não latino.
- **S6 `pwa-offline`:** manifest, service worker, ícones, instalação, offline.
- **S7 `compartilhar`** (precisa do modo autenticado da Lila): botão
  "Compartilhar {ano}" nos anos fechados (Ano, handoff §6.3) e retrospectiva
  9:16 por ano e "de sempre"; botão "Compartilhar" na Obra e card do livro. O
  botão só aparece no modo dela (PRODUCT.md). Não existe nem como stub.

**Melhoria contínua (sem prazo):**
- Capas: 171 obras no backlog. Segunda onda paga ou escolha manual de edição.
  Obra nova: `enrich_covers.py --only slug`.
- Autorias: 40 fotos a escolher, 9 sem Wikidata, 6 sem bio.

**Fica para depois (F5 Admin):** adicionar leitura em poucos toques,
reaproveitando os scripts da F2.

**Pequenas dívidas anotadas:**
- *Polimento do desktop* (mini-spec futura): CSS de grade repetido (Ano, Sem data,
  WorkGrid), mais colunas na grade, setas nos carrosséis, capa da Obra com 136 px
  (poderia ser maior).
- *Tarefa isolada:* renomear `photo.author` para `photo.credit` nas autorias,
  por consistência com `cover.credit` (mexe em 215 autorias, schema e pipeline).
- *Entram na F2.3:* `404.astro` (hoje rota desconhecida serve o Início com 200).
- *Entra nos dados das obras:* fonte da capa tipográfica coreana.

## F5 — Admin
- Adicionar leitura em poucos toques, reaproveitando os scripts da F2.

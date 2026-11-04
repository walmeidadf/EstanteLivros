# AGENTS.md — Estante da Lila

Referência rápida do projeto para agentes e pessoas. Detalhes ficam em `docs/`.

## O que é
Estante pública e instalável (PWA) dos ~300 livros lidos pela Lila desde 2014.
Visitantes só consultam; só a Lila compartilha. Público principal: a Lila, num
Samsung Android. Interface em português do Brasil.

## Estrutura
```text
AGENTS.md           esta referência
catalog/            FONTE DE VERDADE (dados canônicos, versionados)
  source/           lista original do caderno, nunca alterar
  works/ authors/   um JSON por obra / por autoria
  schema/           JSON Schema do catálogo
  media/            capas e fotos mestre
pipeline/           Python: migração, enriquecimento, validação
app/                PWA em Astro (só lê catalog/)
infra/              hospedagem (AWS ou Cloudflare, em decisão)
design/             handoff de design aprovado + telas de referência
docs/               documentação detalhada
  specs/            specs (requisitos → design → tarefas), uma pasta por spec
  plans/            planos e notas de sessão
legacy/             legado local, FORA do git (CSVs validados, caches, scripts antigos)
```

## Regras
- `app/` só lê `catalog/`; não chama APIs externas.
- `pipeline/` é o único que escreve em `catalog/`, sempre com proveniência.
- Scripts do pipeline são CLIs idempotentes, com cache das respostas externas.
- Nada depende de `legacy/` em tempo de build; ele é só referência e fonte da migração.
- Specs e planos vão em `docs/specs/` e `docs/plans/`, não em `.kiro/specs/`.
- Só o **ano** de leitura existe: nunca mostrar ou inventar dia e mês.
- Sem estrelas ou notas. Dados incompletos usam os fallbacks do design, nunca "—".
- Código e identificadores em inglês; interface e docs em pt-BR.
- Dependências com versão fixada. Não fazer hotlink de imagens externas.
- Artefatos descartáveis (screenshots, dumps, builds de verificação) vão em
  `temp/` (dentro do projeto, no `.gitignore`), nunca em `/tmp` ou fora do
  workspace — escrever fora exige aprovação e trava o fluxo.

## Documentos
| Documento | Conteúdo |
|---|---|
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Fases, specs planejadas, decisões tomadas e em aberto |
| [`docs/PRODUCT.md`](docs/PRODUCT.md) | Pessoas, decisões de produto, princípios |
| [`docs/TECH.md`](docs/TECH.md) | Stack, pipeline, hospedagem, convenções |
| [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md) | Obra, edição, leitura, autoria, resumo; invariantes |
| [`design/DESIGN_HANDOFF.md`](design/DESIGN_HANDOFF.md) | Tokens, componentes, telas, rotas e estados (base das specs visuais) |
| [`design/DESIGN_BRIEF.md`](design/DESIGN_BRIEF.md) | Briefing de design e números do catálogo |

## Comandos
Python 3.9+, só biblioteca padrão.

```bash
python3 pipeline/migrate_legacy.py --dry-run   # resumo, sem gravar
python3 pipeline/migrate_legacy.py             # legacy/exports/*.csv → catalog/
python3 pipeline/validate_catalog.py           # valida e gera docs/plans/cobertura.md
python3 -m unittest discover -s pipeline/tests # testes
```

O validador sai com código 1 se houver qualquer erro. Rode-o depois de toda
alteração no `catalog/`.

### Enriquecimento de autorias (Wikidata, país, foto, bio)
Chaves em `.env` (modelo: `.env.example`). Rode **sempre** `--dry-run` antes:
ele mostra o que gastaria (OpenAI, SerpApi, Tavily) sem gastar.

```bash
python3 pipeline/enrich_authors.py --build-countries        # 1x: pipeline/config/countries.json
python3 pipeline/enrich_authors.py --wave 1 [--dry-run]     # carga: grátis (Wikidata, Wikipédia, Commons)
python3 pipeline/enrich_authors.py --wave 2 [--dry-run]     # carga: bios via OpenAI
python3 pipeline/enrich_authors.py --wave 3 [--dry-run]     # carga: fotos/fontes com cota (SerpApi, Tavily)
python3 pipeline/enrich_authors.py --only slug-da-autora    # manutenção (livro novo)
python3 pipeline/review_summaries.py --list --pending       # bios para revisar
python3 pipeline/review_summaries.py --approve autoria:slug # aprovar (ou --reject, --edit … --text …)
```

- Por padrão processa só pendências, na ordem de visibilidade (mais leituras primeiro).
- Planos gratuitos: SerpApi 250/mês, Tavily 1.000/mês. Limites e reserva em
  `pipeline/config/budgets.json`. Sem saldo, a etapa fica "adiada por cota".
- Decisões humanas em `pipeline/config/`: `author_wikidata.json` (QID),
  `author_photos.json` (foto), `author_overrides.json` (país),
  `summary_rejections.json`. Parâmetros e prompt: `enrich.json`, `prompts/`.
- Revisão: `docs/plans/revisao-autorias.md` e `docs/plans/revisao-fotos.html` (local).
  Log de cada execução: `docs/plans/enriquecimento-execucoes.md`.

## Estado atual
- **F0 e F1 concluídas.** `catalog/` tem 302 obras, 215 autorias e 309 leituras,
  validados (0 erros). Cobertura em `docs/plans/cobertura.md`.
- **F2.1 (autorias) concluída.** 206 de 215 autorias identificadas no Wikidata,
  202 com país, 174 com foto e **209 bios aprovadas**. Aprendizados em
  `docs/plans/aprendizados-enriquecimento.md`.
- **Revisão contínua, não bloqueante:** 40 fotos a escolher
  (`docs/plans/revisao-fotos.html`), 9 autorias sem Wikidata e 6 sem bio. Isso
  será corrigido olhando o app, não antes dele.
- **F3 · S1 (`estante-fundacao`) concluída.** App em `app/` (Astro 7 estático):
  tokens, fontes, cor por idioma, camada de dados (Zod), componentes base e a
  vitrine `/styleguide`. 32 testes verdes, build do catálogo real em código 0.
- **F4 (`infra-hospedagem`) concluída — no ar.** Publicado em
  `liliane.prateleira.site` (Cloudflare Pages), deploy automático por GitHub
  Actions a cada push em `main` (portão check + test + build).
- **F3 · S2 (`estante-inicio-busca`) concluída — no ar.** Tela Início (`/`,
  carrosséis + cartão Linha do tempo) e busca (índice estático de 517 entradas
  + ilha vanilla). Componente `Carousel` reusável e a regra de seleção em
  `app/src/lib/home.ts`. 54 testes verdes. Validada em produção (desktop +
  celular).
- **F3 · S3 (`linha-do-tempo`) concluída — no ar.** Telas Linha do tempo
  (`/linha-do-tempo`), Ano (`/ano/{ano}`, 13 anos) e Sem data (`/ano/sem-data`),
  quitando a dívida de rota da S2. Componente novo `YearBand` (Faixa do ano,
  reusa `Spine`+`Shelf`) e a regra de seleção em `app/src/lib/timeline.ts`.
  Única mudança na camada de dados: `approvedSummaryByScope` no modelo (para o
  resumo de ano). 69 testes verdes; build do catálogo real em código 0.
  Validada em produção (desktop + celular). Na grade de Ano/Sem data, as capas
  do desktop têm largura fixa (`--cover-hero-w`), igual ao Início, e não esticam.
- **Próximo (nova sessão): F3 · S4 (`atlas`).** Atlas (idioma e país), Idioma,
  País e Tema. Ver `docs/plans/handover-s3-s4.md` (a `YearBand` já serve à
  prateleira por país; `/obra`, `/autoria`, `/tema`, `/atlas` seguem 404 até
  S4/S5).
- Depois da F3: o resto da F2 (capas, temas, resumos de ano/país).
- Specs em `docs/specs/` (`.kiro/specs` é link simbólico para lá).
- Deploy/segredos: token do Cloudflare é secret de CI no GitHub (não no `.env`);
  `gh secret set CLOUDFLARE_API_TOKEN` após rotacionar. Detalhes em `infra/README.md`.
- Remoto: `git@github.com:walmeidadf/EstanteLivros.git`.

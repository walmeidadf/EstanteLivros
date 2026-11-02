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

## Estado atual
- F0 e F1 concluídas: `catalog/` tem 302 obras, 215 autorias e 309 leituras,
  validados. Cobertura em `docs/plans/cobertura.md`.
- Próximo: F2 (enriquecimento: autorias, capas, temas) e S1 do app, em paralelo.
- Specs em `docs/specs/` (`.kiro/specs` é link simbólico para lá).
- Remoto: `git@github.com:walmeidadf/EstanteLivros.git`.

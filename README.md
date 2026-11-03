# Estante da Lila

Estante pública e instalável (PWA) dos livros lidos pela Lila desde 2014.

## Situação

Catálogo pronto e validado: 302 obras, 215 autorias, 309 leituras. Autorias
enriquecidas (país, foto e bio) na F2.1. Próximo passo: a interface (F3), a
partir de `design/DESIGN_HANDOFF.md`. Roadmap em `docs/ROADMAP.md`;
handover da sessão atual em `docs/plans/HANDOVER.md`.

## Comandos

```bash
python3 pipeline/validate_catalog.py            # valida o catálogo (código 1 se houver erro)
python3 -m unittest discover -s pipeline/tests  # testes do pipeline
```

Mais comandos (migração, enriquecimento, revisão de bios) em `AGENTS.md`.

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `catalog/` | Fonte de verdade: obras, autorias, leituras, vocabulários, resumos e mídia mestre |
| `catalog/source/` | Lista original do caderno, preservada sem alterações |
| `pipeline/` | Scripts Python de migração, enriquecimento e validação |
| `app/` | PWA em Astro (somente leitura do `catalog/`) |
| `infra/` | Infraestrutura de hospedagem |
| `design/` | Handoff de design aprovado e telas de referência |
| `docs/` | Roadmap, produto, tecnologia, modelo de dados, specs e planos |
| `.kiro/` | Hooks do Kiro |

Referência rápida para agentes: `AGENTS.md`.

O legado (catálogo validado em CSV, caches de APIs e scripts antigos) fica em
`legacy/`, fora do git.

Veja `docs/ROADMAP.md`.

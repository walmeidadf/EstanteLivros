# Estante da Lila

Estante pública e instalável (PWA) dos livros lidos pela Lila desde 2014.

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `catalog/` | Fonte de verdade: obras, autorias, leituras, temas, resumos e mídia mestre |
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

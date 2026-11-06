# Tarefas — Temas (F2.3)

Referências: [`requirements.md`](requirements.md) · [`design.md`](design.md).

Cada tarefa de código termina verde: no pipeline
`python3 -m unittest discover -s pipeline/tests` (offline) e
`python3 pipeline/validate_catalog.py` em 0 erros; no app `npm run check` e
`node --test` em `app/`. As tarefas 1–9 são implementação; 10–13 são a redação
do mapa, a revisão com a Lila e o fechamento, com pontos **(revisão)**.

Dependências: 1 → 2 → 3 → 4 → {5, 6, 7}. As tarefas do app (8, 9) só dependem da 1.2 e
podem andar em paralelo. Todas → 10 → 11 (revisão) → 12 → 13.

## Fundação: schema e módulo de temas

- [x] 1. Campo `tags` (aditivo)
  - [x] 1.1 `catalog/schema/work.schema.json`: `tags` (textList) opcional, depois de `themes`.
    - _Requisitos: 4.1_
  - [x] 1.2 `app/src/lib/catalog/schema.ts`: `workSchema` ganha `tags: textList.optional()` (espelha o JSON Schema). Teste novo `schema.test.ts`: aceita `tags`, rejeita campo desconhecido.
    - _Requisitos: 4.1, 10.4_
  - [x] 1.3 `docs/DATA_MODEL.md`: `themes` (canônicos, navegáveis) × `tags` (originais, só registro); normalização em `pipeline/config/themes.json`.
    - _Requisitos: 4.3_
  - [x] 1.4 Atualizar fixtures/helpers (pipeline e app) para o `tags` opcional; testes atuais verdes sem `tags`.
    - _Requisitos: 4.1_

- [x] 2. `lib/themes.py` — carga, validação e aplicação
  - [x] 2.1 `theme_key` (= `unify_key`), `slugify_theme` (espelho do app), `THEME_FLOOR = 5` (com comentário cruzando com `CLOUD_MIN_WORKS`).
    - _Requisitos: 1.3_
  - [x] 2.2 `ThemeConfig.load`: valida `version`, `targetSize`, tamanho da taxonomia, minúsculas, sem repetição por chave, sem colisão de slug, chaves do mapa únicas, destino na taxonomia, taxonomia toda alcançada; erros viram `ThemeConfigError`.
    - _Requisitos: 1.1, 1.2, 1.3, 2.4, 2.5, 2.6_
  - [x] 2.3 `apply(raw, cfg)` → `Applied(themes, tags, unmapped)`: união ordenada sem repetição; `tags` sem perda, uma por chave, grafia do CSV; `[]` = só tag.
    - _Requisitos: 2.1, 2.2, 2.3, 3.1, 3.2_
  - [x] 2.4 `summary(works, cfg)` para dry-run/cobertura/revisão (canônicos, abaixo do piso, média, único tema, total de tags).
    - _Requisitos: 3.8, 4.5_
  - [x] 2.5 `test_themes.py`: `apply` (união, um-para-vários, só tag, variantes de caixa/acento, tags sem perda) e `load` (destino fora da taxonomia, taxonomia sem uso, chave repetida, slug colidindo, fora do targetSize, arquivo ausente).
    - _Requisitos: 10.1_

## Build e migração

- [x] 3. Aplicar no build (`lib/build.py`)
  - [x] 3.1 `build(..., themes=None)`: sem config, comportamento atual; com config, cada obra recebe `themes`/`tags` de `apply`. `vocabularies.themes` = canônicos em uso.
    - _Requisitos: 3.1, 3.2, 3.6, 3.7_
  - [x] 3.2 `ThemeMappingError(LegacyDataError)` acumulando todas as obras: temas sem mapeamento (tema + obra) e obras sem tema (obra + originais); build não grava nada.
    - _Requisitos: 3.3, 3.4_
  - [x] 3.3 Testes: `themes=None` == antigo; erro acumulado; vocabulário = canônicos; idempotência (resultado não depende de `themes` anterior).
    - _Requisitos: 10.1, 10.3_

- [x] 4. `migrate_legacy.py`
  - [x] 4.1 Carregar `config/themes.json`: ausente/inválido → código 2 com mensagem; passar a config a `build` e a `check_catalog`.
    - _Requisitos: 3.5, 4.2_
  - [x] 4.2 `--dry-run`: linha `temas: N canônicos · M originais · K abaixo do piso`.
    - _Requisitos: 3.8_
  - [x] 4.3 Helper de fixture (`themes.json` mínimo) e ajustar `test_cli.py` (setUp, `ValidateCliTest`) e demais chamadores de `migrate_legacy.run`.
    - _Requisitos: 10.1_
  - [x] 4.4 Testes de CLI: código 1 nada gravado (`tree_bytes` igual); código 2 sem arquivo; idempotência byte a byte; catálogo já normalizado não é desfeito; dry-run imprime a linha.
    - _Requisitos: 3.3, 3.5, 3.7, 10.1, 10.3_

## Validador e cobertura

- [x] 5. Regras do validador (`lib/checks.py`)
  - [x] 5.1 `check_themes(cat, themes_cfg)`: `theme.taxonomy` (tema de obra ou de `vocabularies.themes` fora da taxonomia) e `theme.drift` (`apply(tags).themes` ≠ `themes`). Sem config, pulado.
    - _Requisitos: 4.2, 4.4_
  - [x] 5.2 `check_catalog(..., themes_cfg=None)` chama a nova regra; `validate_catalog.py` procura `themes.json` em `../pipeline/config`, carrega e passa; ausente → pula, inválido → erro (código 1).
    - _Requisitos: 4.2_
  - [x] 5.3 Testes: `theme.taxonomy` e `theme.drift` (válido e inválido); sem config, regras puladas.
    - _Requisitos: 10.1_

- [x] 6. Cobertura (`lib/coverage.py`)
  - Seção `## Temas`: canônicos, média por obra, obras com um único tema, 10 maiores, abaixo do piso, total de tags. Teste em `test_coverage.py`.
  - _Requisitos: 4.5, 10.1_

## Revisão (CLI de leitura)

- [x] 7. `pipeline/review_themes.py`
  - `read_legacy` + `ThemeConfig.load` → `docs/plans/revisao-temas.md` (não grava no catálogo): pendências, resumo, bloco por tema, só tag, mapeados para vários, atenção (único tema, perda > 50%). Determinístico, cobre todos os originais. Teste em `test_themes.py`.
  - _Requisitos: 5.1, 5.2, 5.3, 5.4, 5.5, 10.2_

## App

- [x] 8. Modelo e navegação
  - [x] 8.1 `model.ts`: `WorkView` NÃO expõe `tags`; teste em `model.test.ts`.
    - _Requisitos: 6.4, 10.4_
  - [x] 8.2 `NavChips.astro`: `active` aceita `null` (nenhum ativo). Páginas atuais com HTML idêntico (diff).
    - _Requisitos: 8.2_
  - [x] 8.3 `route-integrity` roda sobre os temas novos; sem mudança de código.
    - _Requisitos: 6.5, 10.4_

- [x] 9. Página 404 (`src/pages/404.astro`)
  - _Como ficou:_ 1081 páginas no build (1080 + `404.html`); as 1080 existentes idênticas ao baseline (corpo e CSS).
  - `Base` com `noindex`, `h1` "Esse endereço não existe", uma frase, `NavChips active={null}` (Início, Atlas, Linha do tempo, 44 px); sem JS; gera `dist/404.html`. Build com rotas existentes inalteradas.
  - _Requisitos: 8.1, 8.2, 8.3, 8.5_

## Dados reais: mapa, revisão e aplicação

- [x] 10. Redigir a taxonomia e o mapa (rascunho em `temp/`)
  - Listar os 496 originais com contagem e co-ocorrência; núcleo nos 52 com 5+ obras; fusões e temas novos para a cauda; mapear cada original (núcleo / tema novo / vários / só tag). `themes.json` fica em `temp/temas/` (fora do commit). Rodar `review_themes.py` apontando para ele.
  - _Requisitos: 1.5, 2.1, 9.1_
  - _Resultado (6/nov/2026):_ rascunho em `temp/temas/themes.json` (gerado por `temp/temas/draft.py`, fora do commit). 58 temas canônicos, todos com 5 ou mais obras (escravidão, educação e nápoles no piso exato); 493 originais mapeados, 51 só tag (lugares e termos únicos); 45 originais com mais de um destino. Média de 3,40 temas por obra (era 3,99); 12 obras com um tema só (quase todas não ficção). Build previsto: 58 páginas `/tema`, 646 no total. Início: os mesmos 4 temas, em outra ordem (família 77, memória 65, amor 46, identidade 43). Documento para a revisão: `docs/plans/revisao-temas.md` (gerado do rascunho, ainda não commitado).

- [x] 11. **(revisão)** Revisar com a Lila
  - Abrir `docs/plans/revisao-temas.md`; a Lila indica ajustes (fundir, separar, promover a só tag); eu edito o `themes.json` e regenero. Iterar até aprovar. Registrar a aprovação (data e ajustes) aqui.
  - _Requisitos: 5.6, 9.2, 9.3_
  - _Aprovação (6/nov/2026):_ o mantenedor dispensou a rodada de revisão do documento e manteve o rascunho **como está, sem ajustes** (58 temas, 493 originais mapeados). A Lila informou estar satisfeita. Os quatro pontos levantados (tamanho de "família", "nápoles" como único lugar, nome "existencialismo", fusões de classe social, feminismo e violência) ficam como estão e podem ser revistos depois editando `themes.json`; o validador (`theme.drift`) acusa se o catálogo não acompanhar.

- [x] 12. Aplicar ao catálogo (branch + PR)
  - Mover `themes.json` aprovado para `pipeline/config/`; `python3 pipeline/migrate_legacy.py`; conferir o diff de `catalog/` (themes/tags/vocabulário) e o `cobertura.md`; validador em 0 erros. `themes.json` + catálogo normalizado no mesmo commit.
  - _Requisitos: 3.1, 3.6, 4.2, 9.4, 9.5_
  - _Resultado (6/nov/2026):_ migração real sem slugs novos; 302 obras com `themes` e `tags`, vocabulário com 58 temas; idempotente nos dados reais. **Achado e correção:** o diff mostrou 60 capas alteradas, o que não deveria acontecer. Duas causas, ambas das capas (PR #10): (1) nas escolhas provisórias eu gravei `source: "literal"` para toda capa do catálogo, e o CSV diz `openlibrary`, `editora` ou `busca_web` (43 obras com `source` errado); (2) quando a Lila escolheu a imagem da Open Library no lugar da do catálogo (17 obras), o `merge_cover` trocava a `sourceUrl` pela do CSV e mantinha o `file`, casando a imagem de uma origem com a URL de outra. Corrigido: `merge_cover` mantém `file` e a proveniência dele juntos quando a origem difere, e deixa o CSV mandar quando a URL é a mesma (o que corrige a `source` errada); `cover_choices.json` perdeu o `source` fixo. Resultado: só 43 valores de `source` mudaram, nenhum `sourceUrl` nem `file`; `enrich_covers.py --steps apply` segue sem efeito. 2 testes novos de migração.

## Fechar a spec

- [ ] 13. Fechamento
  - [x] 13.1 `validate_catalog.py` 0 erros; `npm run check` + `node --test` + `npm run build` verdes; total de páginas = `1080 − (493 − N) + 1`.
    - _Requisitos: 6.1, 6.6, 8.5_
    - _Resultado:_ validador 0 erros; 272 testes do pipeline e 159 do app; `npm run check` limpo; build com **646 páginas** (= 1080 − 493 + 58 + 1), 58 de tema.
  - [x] 13.2 Diff de HTML contra a `main`: Linha do tempo, Ano, País, Idioma e Sem data inalterados; nenhuma `tag` fora da taxonomia em `dist/` nem em `search-index.json`.
    - _Requisitos: 6.3, 6.4, 10.5_
    - _Resultado:_ mudaram só Início (1), Atlas (2), Tema (55 das 58; 3 idênticas), Obra (302) e Autoria (35). Ano (14), Idioma (15), País (36), Linha do tempo e vitrine idênticos ao baseline; 435 páginas de tema extintas. Nenhuma `tag` só-tag aparece em HTML ou no índice de busca, exceto onde é nome legítimo (países, a autora Clarice Lispector, o título *Doutor Jivago*). Os 1177 links `/tema/` resolvem.
  - [x] 13.3 No preview do PR: `curl -sI` em rota inexistente (status 404) e olhada em Início, Atlas (nuvem), Obra e Autoria (desktop + celular). Registrar o status aqui.
    - _Requisitos: 8.4_
  - [x] 13.4 Atualizar `ROADMAP.md` (F2.3 feita), `AGENTS.md` (`review_themes.py`), `DESIGN_HANDOFF.md` (§12.4 resolvido) e escrever `docs/plans/handover-temas.md`.
    - _Requisitos: —_

_Registro (6/nov/2026), preview do PR #11:_ rotas existentes 200; `/tema/rota-que-nao-existe` e `/obra/nao-existe` devolvem **404** com a página nova (título "Página não encontrada"); `/404.html` responde 308 para `/404`. A parte do status do 13.3 está comprovada; falta a olhada visual depois da migração.

_Fechamento (6/nov/2026):_ PR #11 mergeado (`2e1e19f`). O mantenedor testou em produção, no desktop e no celular: por autoria, por obra e com slug inexistente (página 404). Docs atualizados na `main`; handover em `docs/plans/handover-temas.md`.

# Tarefas — Catálogo canônico (F1)

Referências: [`requirements.md`](requirements.md) · [`design.md`](design.md).

Cada tarefa termina com os testes dela passando
(`python3 -m unittest discover -s pipeline/tests`). As tarefas seguem a ordem
das dependências: primeiro as funções puras, depois a montagem, a escrita, as
CLIs e, por fim, a execução real.

- [ ] 1. Esqueleto do pipeline
  - Criar `pipeline/lib/__init__.py`, `pipeline/tests/__init__.py` e `pipeline/config/`.
  - Criar `pipeline/tests/helpers.py` com utilitários de fixture: um diretório temporário com CSVs sintéticos (`obras.csv`, `leituras.csv` e `fontes.csv` com todas as colunas obrigatórias) e um catálogo mínimo válido.
  - Remover os `.gitkeep` de `pipeline/`.
  - Conferir que `python3 -m unittest discover -s pipeline/tests` roda (zero testes, código 0) no Python 3.9.
  - _Requisitos: 6.6, 9.1, 9.3_

- [ ] 2. Slugs (`lib/slugs.py`)
  - [ ] 2.1 `slugify(s)`: NFKD, remoção de marcas, minúsculas, `[^a-z0-9]+` → `-`, sem hífen nas pontas.
    - _Requisitos: 5.2_
  - [ ] 2.2 `truncate(slug, 80)`: corta no último hífen dentro do limite; sem hífen, corte seco.
    - _Requisitos: 5.6_
  - [ ] 2.3 `SlugRegistry`: carrega e salva `slugs.json` (`works`, `authors`), reserva os slugs já mapeados antes de gerar novos, desempata com `-{ano}` e depois `-2`, `-3`…, e nunca remove entradas.
    - _Requisitos: 5.1, 5.3, 5.4, 5.5_
  - [ ] 2.4 `test_slugs.py`: acentos, pontuação, título só não latino, truncamento (inclusive um caso real acima de 80), desempate por ano e por sufixo, reuso do mapa, slug novo não rouba slug antigo, título alterado mantém o slug.
    - _Requisitos: 9.2_

- [ ] 3. Títulos originais (`lib/titles.py`)
  - [ ] 3.1 `split_original(s)` → `(originalTitle, romanized)`, separando só quando a parte de fora dos parênteses tem letra não latina.
    - _Requisitos: 2.3, 2.4_
  - [ ] 3.2 `test_titles.py`: os 8 padrões reais (japonês, coreano, hebraico), cirílico sem parênteses, título latino com parênteses intacto, vazio → `(None, None)`.
    - _Requisitos: 9.2_

- [ ] 4. Autorias (`lib/names.py`)
  - [ ] 4.1 `unify_key(name)` e `group_names(names_with_counts)` → grupos com nome canônico (placar: iniciais maiúsculas ignorando partículas → nº de acentos → frequência → ordem alfabética) e `aliases` ordenados.
    - _Requisitos: 3.1, 3.2, 3.3_
  - [ ] 4.2 Aplicação de `author_overrides.json` (nome e slug), vencendo a regra e o mapa de slugs.
    - _Requisitos: 3.4_
  - [ ] 4.3 `languages_for(author, works, first_sequence)`: lista por frequência, desempate pela menor `sequence`; `primaryLanguage` é o primeiro.
    - _Requisitos: 3.6_
  - [ ] 4.4 `find_suspects(groups)`: pares não unificados com o mesmo sobrenome (chave) e as mesmas iniciais.
    - _Requisitos: 3.8_
  - [ ] 4.5 Criar `pipeline/config/author_overrides.json` com `valter hugo mãe`.
    - _Requisitos: 3.4_
  - [ ] 4.6 `test_names.py`: os 3 casos reais de unificação, placar e cada desempate, exceção vence a regra, idioma principal com empate, "Luiz" × "Luís" vira suspeita e não é unificado.
    - _Requisitos: 9.2_

- [ ] 5. Validador de schema (`lib/schema.py`)
  - [ ] 5.1 `load_schema(path)`, que falha com palavra-chave fora do subconjunto suportado.
  - [ ] 5.2 `validate(instance, schema)` → lista de `(path, message)` para `type` (incluindo união), `properties`, `required`, `additionalProperties: false`, `items`, `enum`, `const`, `pattern`, `minimum`, `maximum`, `minLength`, `maxLength`, `minItems`, `uniqueItems`, `$ref` local e `oneOf`.
    - _Requisitos: 7.2_
  - [ ] 5.3 `test_schema.py`: um caso válido e um inválido por palavra-chave; caminho do erro correto em objetos aninhados e listas; palavra-chave desconhecida falha; `bool` não é aceito como `integer`.
    - _Requisitos: 9.2_

- [ ] 6. Schemas do catálogo (`catalog/schema/`)
  - [ ] 6.1 `work.schema.json` e `author.schema.json` (com `bio`/`photo` como `oneOf` de `null` e objeto), conforme as tabelas de restrições do design.
    - _Requisitos: 1.6, 2.2, 2.6, 2.7, 2.10, 3.5_
  - [ ] 6.2 `readings.schema.json`, `summaries.schema.json` e `vocabularies.schema.json`.
    - _Requisitos: 1.3, 1.4, 1.5, 1.6, 4.2_
  - [ ] 6.3 Teste: todos os schemas carregam com `load_schema`, e os exemplos de obra, autoria e leitura do design validam.
    - _Requisitos: 9.2_

- [ ] 7. Regras do validador (`lib/checks.py`)
  - [ ] 7.1 Modelo `Issue(file, path, code, message)` e `load_catalog(dir)`, que coleta erros de JSON malformado sem parar.
    - _Requisitos: 7.8_
  - [ ] 7.2 Regras `schema`, `file.slug`, `ref.reading-work`, `ref.work-author`, `orphan.work`, `orphan.author`.
    - _Requisitos: 7.2, 7.3, 7.5_
  - [ ] 7.3 Regras `seq.contiguous`, `year.monotonic`, `year.undated-head` (`UNDATED_HEAD = 53`), `reread.order`.
    - _Requisitos: 7.4_
  - [ ] 7.4 Regras `vocab` e `summary.approved`.
    - _Requisitos: 7.6, 7.7_
  - [ ] 7.5 `check_catalog(model)`, que roda todas as regras sobre o modelo em memória (usado pela migração e pelo validador).
  - [ ] 7.6 `test_checks.py`: um caso válido e um inválido por regra; vários erros simultâneos são todos reportados.
    - _Requisitos: 9.2_

- [ ] 8. Leitura do legado (`lib/legacy_reader.py`)
  - [ ] 8.1 Colunas obrigatórias por CSV; conferência do cabeçalho antes de ler; `LegacyInputError` com arquivo e colunas faltantes.
    - _Requisitos: 6.1, 6.5_
  - [ ] 8.2 Conversões com erro localizado (arquivo, linha, coluna): inteiros, `sim`/`não`, vazio → `None`, listas separadas por `;`.
    - _Requisitos: 2.5_
  - [ ] 8.3 Testes: CSV ausente, coluna ausente, ano não numérico, listas com espaços e itens vazios.
    - _Requisitos: 9.2_

- [ ] 9. Montagem do modelo (`lib/build.py`)
  - [ ] 9.1 Autorias: grupos, slugs via `SlugRegistry`, `languages` e `primaryLanguage`, `country`/`bio`/`photo` nulos.
    - _Requisitos: 3.1–3.7_
  - [ ] 9.2 Obras: mapeamento campo a campo do design (`edition`, `cover`, `audit`, `desconhecido` → `null`, capa sem URL → `null`), ordem de chaves do schema, processamento em ordem de `legacyId`.
    - _Requisitos: 2.1–2.7, 2.9, 2.10_
  - [ ] 9.3 Referências: `fontes.csv` + colunas de `obras.csv` + URLs adicionais, `busca_web` → `web`, sem duplicatas, na ordem de origem.
    - _Requisitos: 2.8_
  - [ ] 9.4 Leituras: conversões e `work_id` → slug.
    - _Requisitos: 4.1–4.6_
  - [ ] 9.5 Vocabulários derivados, com ordenação por chave sem acentos; `summaries` vazio.
    - _Requisitos: 1.4, 1.5_
  - [ ] 9.6 `test_build.py`: ausências, capa, referências, releitura apontando para a mesma obra, obra sem campos de leitura.
    - _Requisitos: 9.2_

- [ ] 10. Escrita canônica e atômica (`lib/jsonio.py`)
  - [ ] 10.1 `dumps_canonical(obj)` (UTF-8, `ensure_ascii=False`, indentação 2, `\n` final) e `read_json`.
    - _Requisitos: 1.8_
  - [ ] 10.2 `write_catalog(model, catalog_dir)`: grava em `catalog/.tmp-migrate/`, troca `works/`, `authors/` e os arquivos soltos com `os.replace`, apaga o temporário em caso de erro e nunca toca `schema/`, `source/` e `media/`.
    - _Requisitos: 6.4, 6.5_
  - [ ] 10.3 Testes: arquivo órfão removido após renomeação; falha simulada no meio deixa o catálogo intacto; `schema/` e `source/` preservados.
    - _Requisitos: 9.2_

- [ ] 11. Relatório de cobertura (`lib/coverage.py`)
  - [ ] 11.1 `render_coverage(model, unified, suspects)` → Markdown com as seções 1–5 do design, sem data.
    - _Requisitos: 8.1, 8.2, 8.3_
  - [ ] 11.2 `test_coverage.py`: percentuais com denominadores corretos (título original só para não português; romanização só para não latinos); duas renderizações iguais.
    - _Requisitos: 9.2_

- [ ] 12. CLI de validação (`pipeline/validate_catalog.py`)
  - Opções `--catalog`, `--report` e `--no-report`; uma linha por erro (`arquivo  caminho  código  mensagem`), total no fim, código 0 ou 1.
  - Teste: catálogo válido → 0 e relatório gerado; catálogo com dois erros → 1 e as duas linhas.
  - _Requisitos: 7.1, 7.8, 8.1_

- [ ] 13. CLI de migração (`pipeline/migrate_legacy.py`)
  - [ ] 13.1 Opções `--legacy`, `--catalog` e `--dry-run`; fluxo ler → montar → `check_catalog` → gravar → salvar `slugs.json` → gerar relatório; resumo no formato do design; códigos 0/1/2.
    - _Requisitos: 6.1, 6.3, 6.7_
  - [ ] 13.2 `test_migrate.py` ponta a ponta na fixture (4 obras, 5 leituras, 1 releitura, 1 unificação): migração byte a byte idêntica na segunda execução; `--dry-run` não grava nada (nem `slugs.json`); coluna ausente → código 2 e catálogo intacto; `legacy/` de entrada sem alteração (hash antes e depois).
    - _Requisitos: 6.2, 6.4, 6.5, 6.7, 9.2_

- [ ] 14. Execução real e conferência
  - [ ] 14.1 Rodar `--dry-run` sobre `legacy/exports/` e conferir: 302 obras, 309 leituras, 7 releituras, 215 autorias com 3 unificações.
    - _Requisitos: 2.1, 3.2, 4.1, 4.5_
  - [ ] 14.2 Rodar a migração e o validador (código 0). Revisar no relatório as autorias unificadas e as suspeitas, e ajustar `author_overrides.json` se for preciso.
    - _Requisitos: 3.8, 7.1, 8.2_
  - [ ] 14.3 Rodar a migração de novo e confirmar com `git status` que nada mudou. Conferir as amostras: A Vegetariana (romanização e duas leituras), uma obra sem capa, uma com 3 autorias e os 3 slugs truncados.
    - _Requisitos: 4.4, 5.6, 6.2_
  - [ ] 14.4 Remover os `.gitkeep` de `catalog/works/`, `catalog/authors/` e `catalog/schema/`.

- [ ] 15. Documentação
  - Atualizar `docs/DATA_MODEL.md` com o formato final, os exemplos de obra, autoria e leitura, `UNDATED_HEAD` e o papel de `slugs.json` e `author_overrides.json`.
  - Atualizar `AGENTS.md` com os comandos de migração, validação e testes, e o estado atual.
  - Marcar a F1 como concluída em `docs/ROADMAP.md`.
  - _Requisitos: 10.1, 10.2, 10.3_

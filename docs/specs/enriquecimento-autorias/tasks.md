# Tarefas — Enriquecimento de autorias (F2.1)

Referências: [`requirements.md`](requirements.md) · [`design.md`](design.md).

Cada tarefa de código termina com os testes passando
(`python3 -m unittest discover -s pipeline/tests`), todos offline. As tarefas
1–16 são implementação. As tarefas 17–22 são a execução real, com pontos de
revisão humana marcados com **(revisão)**.

Dependências: 1 → 2 → {3, 4, 5, 6} → {7, 8, 9, 10} → 11 → {12, 13} → 14 → 15 → 16.
Tarefas na mesma chave podem ser feitas em paralelo.

## Fundação

- [x] 1. Configuração e schemas
  - [x] 1.1 Criar `pipeline/config/enrich.json`, `budgets.json`, `writer_occupations.json`, `languages.json` (15 idiomas do catálogo → QID), `author_wikidata.json` (`{}`), `author_photos.json` (`{}`), `summary_rejections.json` (`[]`) e `prompts/author-bio-v1.md`, conforme o design.
    - _Requisitos: 1.5, 3.4, 5.2, 6.4, 12.1, 13.2_
  - [x] 1.2 Atualizar `author.schema.json`: remover `bio`; adicionar `countrySource`, `wikidata`, `photo.source`; `photo.file` com o padrão `authors/…`; `photo.license` anulável.
    - _Requisitos: 5.6, 8.1, 8.2_
  - [x] 1.3 Atualizar `summaries.schema.json` (`sourceUrl`, `sourceLanguage`, `model`, `promptVersion`, `editedBy`) e `vocabularies.schema.json` (`countries`).
    - _Requisitos: 2.8, 5.4, 13.3_
  - [x] 1.4 Atualizar fixtures e `helpers.valid_catalog()` para o schema novo; testes da F1 verdes.
    - _Requisitos: 10.3_

- [x] 2. Ajustes na F1
  - [x] 2.1 `checks.py`: regras `vocab.country`, `photo.file` (arquivo existe em `catalog/media/`) e `summary.scope-unique`, com testes válido/inválido.
    - _Requisitos: 2.8, 3.5_
  - [x] 2.2 `build.py`/`migrate_legacy.py`: preservar `country`, `countrySource`, `wikidata`, `photo`, as `references` não vindas do legado e `vocabularies.countries`. As autorias novas nascem com `wikidata: null`, `countrySource: null`.
    - _Requisitos: 8.3_
  - [x] 2.3 Teste de migração com catálogo enriquecido: os dados preservados e a segunda execução byte a byte igual.
    - _Requisitos: 10.3_
  - [x] 2.4 Rodar migração + validador no catálogo real (as 215 autorias perdem `bio: null` e ganham os campos novos nulos) e conferir o diff.

## Infraestrutura de chamadas

- [x] 3. Ambiente (`lib/env.py`)
  - Leitura de `.env` (aspas, comentários; ambiente vence arquivo), `get`, `require(step)` com a tabela de chaves por etapa, mensagem "defina X no .env (veja .env.example)".
  - `test_env.py`.
  - _Requisitos: 7.5_

- [x] 4. Cliente HTTP (`lib/http.py`)
  - [x] 4.1 Transporte injetável, `get_json`, `post_json`, `get_bytes`; cache por `sha256` sem segredos; cache de erros definitivos; `refresh`; `offline` → `CacheMiss`.
    - _Requisitos: 7.2, 7.3_
  - [x] 4.2 Retries em 429/5xx com espera crescente e `Retry-After`; pausa mínima por provedor (hits não esperam); User-Agent nos domínios Wikimedia; URLs sem segredos nas mensagens.
    - _Requisitos: 7.4, 7.5_
  - [x] 4.3 Gancho para o orçamento: o `Http` chama `budget.spend(provider)` antes de toda chamada de rede a um provedor com cota.
    - _Requisitos: 12.2_
  - [x] 4.4 `FakeTransport` em `tests/helpers.py` e `test_http.py`.
    - _Requisitos: 10.1, 10.2_

- [x] 5. Orçamento (`lib/budget.py`)
  - Livro-razão em `pipeline/cache/usage/{provedor}-{AAAA-MM}.json`; uso = max(local, remoto); saldo com reserva e teto por execução; `--use-reserve`; `BudgetExhausted`; teto de US$ da OpenAI.
  - Consulta remota de uso: SerpApi `/account`, Tavily `/usage`.
  - `test_budget.py`.
  - _Requisitos: 12.1–12.5_

- [x] 6. Imagens (`lib/images.py`)
  - Tipo por bytes mágicos e dimensões de JPEG, PNG, WebP (VP8/VP8L/VP8X) e GIF; `test_images.py` com imagens mínimas geradas no teste.
  - _Requisitos: 3.5, 3.7_

## Provedores

- [x] 7. Wikimedia (`providers/wikidata.py`, `wikipedia.py`, `commons.py`)
  - Wikidata: `search(name, lang)`, `entities(ids)` em lotes de 50, `works_of(qids)` (SPARQL com `P50`, rótulos, `P648`, ISBNs das edições), helpers de claims (`P31`, `P27` com rank e qualificador de fim, `P19`→`P17`, `P18`, `P106`, sitelinks).
  - Wikipédia: `intro(lang, title)` e `page_image(lang, title, width)`.
  - Commons: `image_info(file, width)` com URL da miniatura, dimensões, `LicenseShortName` e `Artist` sem HTML.
  - Fixtures recortadas das respostas reais (Han Kang, Itamar Vieira Junior); testes de parsing.
  - _Requisitos: 1.1, 1.2, 2.1, 3.1, 4.1_

- [x] 8. SerpApi e Tavily (`providers/serpapi.py`, `tavily.py`)
  - SerpApi `google_images` (filtros de tamanho mínimo e de domínios) e `account_usage()`.
  - Tavily `search(query, include_images=True, include_image_descriptions=True, exclude_domains)` e `usage()`.
  - Fixtures e testes de parsing.
  - _Requisitos: 3.2, 4.2, 12.3_

- [x] 9. OpenAI (`providers/openai_client.py`)
  - Responses API com `text.format` JSON Schema estrito; leitura de `output_text`/`output`; `usage` → tokens e custo (`OPENAI_PRICE_*`); erro de recusa ou JSON inválido como exceção própria.
  - Fixtures e testes.
  - _Requisitos: 5.1, 5.2, 5.7_

- [x] 10. Resumos (`lib/summaries.py`)
  - `upsert` (ordenado por escopo; não toca em aprovados), `approve`, `reject` (remove + registra em `summary_rejections.json`), `edit` (`editedBy: "human"`), `is_rejected`.
  - `test_summaries.py`.
  - _Requisitos: 5.4, 5.5, 6.3, 6.4_

## Etapas

- [x] 11. Seleção e países
  - [x] 11.1 `lib/selection.py`: pendência por etapa (tabela do design), `rulesVersion`, fontes permitidas por onda, ordem de prioridade (leituras desc → ano corrente → slug), `--only`/`--limit`. `test_selection.py`.
    - _Requisitos: 11.1–11.3, 11.5_
  - [x] 11.2 `--build-countries`: SPARQL de países soberanos (`P297`, rótulo pt, `P37` mapeado por `languages.json`) → `pipeline/config/countries.json`, mais a tabela `defunct` do design. Teste com fixture.
    - _Requisitos: 2.5, 2.8_

- [x] 12. Etapa `identify` (`authors/identify.py`)
  - Escolha manual (`manual`/`none`); candidatos por nome e aliases em pt e en; filtro de humanos; casamento por ISBN > Open Library > título; tabela de decisão; evidência; referência `wikidata`.
  - `test_identify.py`: cada linha da tabela de decisão.
  - _Requisitos: 1.1–1.7_

- [x] 13. Etapa `country` (`authors/country.py`)
  - Override; cidadanias (sem as encerradas antes de 1800); mapeamento por `countries.json`/`defunct`; desempates por idioma oficial → nascimento → ordem/rank; fallback para o local de nascimento; casos para o relatório.
  - `test_country.py`.
  - _Requisitos: 2.1–2.7_

- [x] 14. Etapa `photo` (`authors/photo.py`)
  - Escolha manual e `none`; Commons automático; candidatas (Wikipédia → SerpApi → Tavily, até 3, sem repetir, filtradas) só para revisão; download com validação (tipo, lado mínimo, aviso entre 200 e 400 px), deduplicação por hash e substituição de arquivo antigo, num diretório temporário.
  - `test_photo.py`.
  - _Requisitos: 3.1–3.8, 2a_

- [x] 15. Etapa `bio` (`authors/bio.py`)
  - Regras de pular (existente, aprovada, rejeitada, `--regenerate`, `--regenerate-prompt`); fonte Wikipédia por idioma e limiares; fallback Tavily com filtro por sobrenome e limite de caracteres (reaproveitando as imagens para a etapa `photo`); prompt carregado de `prompts/{promptVersion}.md`; verificações pós-resposta com uma nova tentativa; `upsert` com `promptVersion`.
  - `test_bio.py`.
  - _Requisitos: 4.1–4.4, 5.1–5.5, 13.3_

## CLIs e relatórios

- [x] 16. CLIs, relatórios e documentação
  - [x] 16.1 `lib/enrich_report.py`: `revisao-autorias.md` (pendências + comandos de aprovação), `revisao-fotos.html` (cartões com candidatas e o JSON pronto) e a entrada em `enriquecimento-execucoes.md`.
    - _Requisitos: 3.3, 6.1, 13.1_
  - [x] 16.2 `coverage.py`: seção de autorias por estado, país, foto (commons × outras), bio proposta/aprovada, adiadas por cota, fotos órfãs e as listas do Req. 9.2.
    - _Requisitos: 9.1, 9.2_
  - [x] 16.3 `pipeline/enrich_authors.py`: opções do design, fluxo validar → orçamento → seleção → etapas → validar → gravar (atômico, com as fotos) → relatórios; `--dry-run` com a tabela de orçamento; códigos 0/1/2.
    - _Requisitos: 7.1, 7.6, 7.8, 11.4, 12.4_
  - [x] 16.4 `pipeline/review_summaries.py`: `--list [--pending] [--scope-prefix]`, `--approve`, `--approve-file`, `--reject`, `--edit [--approve]`, sempre validando antes de gravar.
    - _Requisitos: 6.2–6.4_
  - [x] 16.5 `test_enrich_cli.py` e `test_review_cli.py` (cenários do design, inclusive segunda execução sem chamadas e manutenção com `--only` igual à carga).
    - _Requisitos: 7.9, 10.1, 10.2, 11.5_
  - [x] 16.6 Atualizar `docs/DATA_MODEL.md` (autoria, resumo, países), `AGENTS.md` (comandos de enriquecimento e revisão, ondas, orçamento) e o `.env.example`, se preciso.
    - _Requisitos: 8.2_

## Execução real

- [x] 17. Países
  - Rodar `--build-countries`. **(revisão)** Conferir nomes em pt-BR dos países que aparecerem, idiomas e a tabela `defunct`. Commitar `countries.json`.
  - _Requisitos: 2.5, 2.8_

- [x] 18. Amostra de 10 autorias
  - `--dry-run` e depois a execução com todas as ondas para Han Kang, Machado de Assis, Elena Ferrante, Liev Tolstói, valter hugo mãe, Luís Fernando Veríssimo, Sidarta Ribeiro, uma coautoria, um autor russo/soviético e um hebraico.
  - **(revisão)** Conferir identificações, países, fotos e bios. Calibrar `enrich.json` e o prompt (nova versão se mudar). Registro no log.
  - _Requisitos: 11.4, 13.1, 13.2_

- [x] 19. Onda 1 (grátis) em todas
  - `--wave 1`. **(revisão)** Resolver `ambiguous`/`not_found` em `author_wikidata.json`, os países entre vários e os não mapeados em `author_overrides.json`. Rodar `--wave 1` de novo só nas resolvidas.
  - _Requisitos: 1.4, 1.5, 2.3, 11.2_

- [ ] 20. Onda 2 (bios via Wikipédia)
  - `--dry-run --wave 2` (custo) e `--wave 2`. **(revisão)** Ler uma amostra de 20 bios. Se o prompt mudar, criar a nova versão e usar `--regenerate-prompt`.
  - _Requisitos: 5.1–5.4, 13.3_

- [ ] 21. Onda 3 (cota)
  - `--dry-run --wave 3` para conferir o orçamento, depois `--wave 3`. **(revisão com a Lila)** Escolher fotos em `revisao-fotos.html` → `author_photos.json` → nova execução da etapa `photo`. Aprovar ou rejeitar bios com `review_summaries.py`.
  - _Requisitos: 3.3, 3.4, 6.2, 12.2, 12.4_

- [ ] 22. Fechamento
  - Validador com 0 erros; cobertura atualizada; escrever `docs/plans/aprendizados-enriquecimento.md` (acerto por fonte, ajustes e motivos, decisões manuais, custo por autoria nova).
  - Atualizar `docs/ROADMAP.md` (F2.1 concluída) e `AGENTS.md` (estado atual).
  - _Requisitos: 9.1, 13.4_

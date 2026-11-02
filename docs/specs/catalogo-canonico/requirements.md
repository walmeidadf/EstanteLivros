# Requisitos — Catálogo canônico (F1)

## Introdução

O catálogo validado existe hoje só em CSVs locais (`legacy/exports/`), fora do
git, com autorias como texto livre e sem identificadores estáveis. Esta spec cria
o **catálogo canônico** em `catalog/`: a fonte de verdade versionada que o app
(F3) vai ler e que o enriquecimento (F2) vai completar.

O escopo é **migrar e validar**, sem consultar serviços externos e sem mudar o
conteúdo bibliográfico já validado. Enriquecimento (país, bio, fotos, capas,
temas normalizados) fica para a F2.

### Estado de partida (medido nos CSVs)

- `obras.csv`: 302 obras, 37 colunas; `leituras.csv`: 309 leituras;
  `fontes.csv`: referências por provedor.
- 218 nomes de autoria distintos, com variações de grafia do mesmo nome
  (ex.: "Luís Fernando Veríssimo" / "Luis Fernando Verissimo",
  "Érico Veríssimo" / "Erico Veríssimo", "valter hugo mãe" / "Valter Hugo Mãe").
- Até 3 autorias por obra.
- 15 idiomas originais; 16 tipos de obra; 496 temas não normalizados.
- 1 obra sem ano de primeira publicação ("Essencial Franz Kafka").
- 21 títulos originais em alfabeto não latino; 8 trazem a romanização entre
  parênteses.
- Não há colisão de slug por título.

### Glossário

- **Catálogo**: o conjunto de arquivos em `catalog/`.
- **Migração**: o script `pipeline/migrate_legacy.py`.
- **Validador**: o script `pipeline/validate_catalog.py`.
- **Slug**: identificador estável, em ASCII minúsculo com hífens, usado em URLs.
- **Proveniência**: a origem de um valor (fonte, identificador, URL e data).

## Requisitos

### Requisito 1 — Formato do catálogo

**História:** Como desenvolvedor do app, quero um catálogo com formato
definido e documentado, para ler os dados sem conhecer a origem deles.

#### Critérios de aceitação

1. O catálogo SHALL conter um arquivo JSON por obra em `catalog/works/{slug}.json`.
2. O catálogo SHALL conter um arquivo JSON por autoria em `catalog/authors/{slug}.json`.
3. O catálogo SHALL conter todas as leituras em `catalog/readings.json`, ordenadas por `sequence`.
4. O catálogo SHALL conter `catalog/summaries.json`, inicialmente com uma lista vazia.
5. O catálogo SHALL conter `catalog/vocabularies.json` com as listas de idiomas, tipos de obra, gêneros e temas usados.
6. Cada tipo de arquivo SHALL ter um JSON Schema em `catalog/schema/`.
7. Os campos SHALL usar nomes em inglês em `camelCase`; os valores de conteúdo (títulos, idiomas, temas) SHALL permanecer em português.
8. Os arquivos SHALL ser gravados em UTF-8, com indentação de 2 espaços, chaves em ordem estável e quebra de linha final, para gerar diffs legíveis.

### Requisito 2 — Obras

**História:** Como leitora da estante, quero que cada livro tenha os mesmos dados
já validados, para que nada se perca na migração.

#### Critérios de aceitação

1. A migração SHALL gerar exatamente 302 obras.
2. Cada obra SHALL ter: `slug`, `title`, `originalTitle`, `originalTitleRomanized`, `authors` (lista ordenada de slugs de autoria), `language`, `firstPublished`, `type`, `genres`, `themes`, `edition`, `cover`, `catalogerNote`, `confidence`, `references` e `legacyId`.
3. WHEN `original_title` trouxer a romanização entre parênteses ao final, THE migração SHALL separar o título original e a romanização em `originalTitle` e `originalTitleRomanized`.
4. WHEN uma obra for escrita em português e não tiver `original_title`, THE migração SHALL gravar `originalTitle` como `null`.
5. WHEN um valor estiver ausente no CSV, THE migração SHALL gravar `null` (ou lista vazia, nos campos de lista), nunca string vazia ou "—".
6. `edition` SHALL conter `title`, `language`, `publisher`, `year`, `isbn13`, `isbn10`, `format` e `match` (`exact` ou `representative`).
7. `cover` SHALL conter `sourceUrl` e `source` (provedor de origem), e `null` quando não houver capa. A migração SHALL NOT baixar imagens.
8. `references` SHALL reunir os identificadores e URLs de Literal, Open Library, Google Books, Wikidata e referências adicionais, a partir de `obras.csv` e `fontes.csv`.
9. `legacyId` SHALL guardar o `work_id` do legado, para rastreabilidade.
10. Os campos de auditoria do legado (`validation_status`, `source_conflicts`, `validated_at`) SHALL ser preservados em um objeto `audit`.

### Requisito 3 — Autorias

**História:** Como leitora, quero que cada autoria seja uma só, mesmo quando o
nome foi escrito de jeitos diferentes, para ver todos os livros dela juntos.

#### Critérios de aceitação

1. A migração SHALL gerar uma autoria por pessoa, a partir dos nomes em `authors` (separados por `; `).
2. WHEN dois nomes gerarem o mesmo slug (diferença só de acento ou caixa), THE migração SHALL tratá-los como a mesma autoria.
3. THE migração SHALL escolher a grafia canônica do nome por uma regra determinística (preferir a forma com acentos e com maiúsculas iniciais; em empate, a mais frequente) e SHALL registrar as demais grafias em `aliases`.
4. WHERE a grafia em minúsculas for intencional (ex.: "valter hugo mãe"), THE migração SHALL respeitar um arquivo de exceções `pipeline/config/author_overrides.json`, que define nome canônico e slug manualmente.
5. Cada autoria SHALL ter: `slug`, `name`, `aliases`, `country`, `languages`, `primaryLanguage`, `bio`, `photo` e `references`.
6. `languages` SHALL ser derivado dos idiomas originais das obras da autoria, e `primaryLanguage` SHALL ser o mais frequente entre eles (em empate, o da obra de menor `sequence`).
7. `country`, `bio` e `photo` SHALL ser `null` nesta fase.
8. A migração SHALL produzir um relatório com as autorias unificadas, para revisão humana.

### Requisito 4 — Leituras

**História:** Como leitora, quero a ordem e o ano do meu caderno preservados,
para que a linha do tempo seja fiel ao que eu registrei.

#### Critérios de aceitação

1. A migração SHALL gerar exatamente 309 leituras.
2. Cada leitura SHALL ter: `sequence`, `year` (ou `null`), `work` (slug da obra), `reread` (booleano), `originalEntry` e `notes` (ou `null`).
3. As leituras 1–53 SHALL ter `year` igual a `null`.
4. Os anos das leituras SHALL ser exatamente os mesmos de `leituras.csv`.
5. As 7 obras lidas duas vezes SHALL ter duas leituras apontando para o mesmo slug, e a segunda leitura SHALL ter `reread: true`.
6. Os dados de leitura SHALL ficar só em `readings.json`; a obra SHALL NOT duplicar ano ou sequência.

### Requisito 5 — Slugs estáveis

**História:** Como visitante, quero que o link de um livro ou de uma autoria
continue funcionando, para poder salvá-lo e compartilhá-lo.

#### Critérios de aceitação

1. O slug de obra SHALL ser derivado do título pt-BR e da primeira autoria (ex.: `a-vegetariana-han-kang`); o slug de autoria, do nome canônico (ex.: `han-kang`).
2. A geração de slug SHALL remover acentos, converter para minúsculas e trocar sequências de caracteres não alfanuméricos por um hífen.
3. WHEN dois slugs colidirem, THE migração SHALL desempatar de forma determinística (acrescentando o ano de primeira publicação e, se ainda colidir, um sufixo numérico).
4. THE migração SHALL manter `pipeline/config/slugs.json`, mapeando `legacyId` para slug de obra e nome de autoria para slug de autoria.
5. WHEN o mapa já tiver um slug para uma obra ou autoria, THE migração SHALL reutilizá-lo, mesmo que o título ou o nome mude.
6. Todos os slugs SHALL ter no máximo 80 caracteres.

### Requisito 6 — Migração idempotente

**História:** Como mantenedor, quero rodar a migração quantas vezes precisar,
para corrigir regras sem medo de estragar o catálogo.

#### Critérios de aceitação

1. A migração SHALL ser uma CLI (`python3 pipeline/migrate_legacy.py`) que lê `legacy/exports/obras.csv`, `leituras.csv` e `fontes.csv`.
2. WHEN executada duas vezes sobre a mesma entrada, THE migração SHALL produzir arquivos byte a byte idênticos.
3. THE migração SHALL NOT fazer chamadas de rede.
4. THE migração SHALL NOT alterar `legacy/` nem `catalog/source/`.
5. IF um arquivo de entrada estiver ausente ou com colunas faltando, THEN THE migração SHALL parar com uma mensagem clara e sem gravar nada em `catalog/`.
6. THE migração SHALL usar só a biblioteca padrão do Python 3.
7. THE migração SHALL ter uma opção `--dry-run` que mostra o resumo sem gravar arquivos.

### Requisito 7 — Validação

**História:** Como mantenedor, quero um validador que barre um catálogo
inconsistente, para que nem o enriquecimento nem o app partam de dados quebrados.

#### Critérios de aceitação

1. O validador SHALL ser uma CLI (`python3 pipeline/validate_catalog.py`) que sai com código 0 quando o catálogo é válido e diferente de 0 quando não é.
2. O validador SHALL conferir cada arquivo contra seu JSON Schema.
3. O validador SHALL conferir a integridade referencial: toda leitura aponta para uma obra existente; toda obra aponta para autorias existentes; toda obra tem ao menos uma leitura; toda autoria tem ao menos uma obra.
4. O validador SHALL conferir os invariantes: sequências de 1 a N sem lacunas nem repetições; anos não decrescentes ao longo da sequência (ignorando `null`); leituras 1–53 sem ano; `reread: true` só a partir da segunda leitura de uma obra.
5. O validador SHALL conferir que o nome do arquivo é igual ao `slug` do conteúdo e que não há slugs duplicados.
6. O validador SHALL conferir que idiomas, tipos, gêneros e temas usados pertencem a `vocabularies.json`.
7. O validador SHALL conferir que todo resumo com `approved: true` tem texto não vazio e um `scope` válido (`autoria:{slug}`, `ano:{ano}` ou `pais:{ISO}`) que aponta para algo existente.
8. IF houver erros, THEN THE validador SHALL listar todos eles (não só o primeiro), com arquivo e campo.

### Requisito 8 — Relatório de cobertura

**História:** Como mantenedor, quero ver o que falta em cada campo, para
priorizar as sessões de enriquecimento da F2.

#### Critérios de aceitação

1. O validador SHALL gerar `docs/plans/cobertura.md` com a contagem e o percentual de preenchimento de cada campo relevante para o design: capa, título original, romanização, ano de primeira publicação, ISBN-13, editora; e, por autoria, país, bio e foto.
2. O relatório SHALL listar as autorias unificadas e os casos que a migração não resolveu sozinha.
3. O relatório SHALL ser determinístico (mesma entrada, mesmo conteúdo), sem data de execução no corpo.

### Requisito 9 — Testes

**História:** Como mantenedor, quero testes automatizados das regras da
migração, para mudar o código com segurança.

#### Critérios de aceitação

1. O projeto SHALL ter testes `unittest` em `pipeline/tests/`, executáveis com `python3 -m unittest discover -s pipeline/tests`.
2. Os testes SHALL cobrir: geração e desempate de slug; unificação de autorias e exceções; separação da romanização; conversão de ausências para `null`; idempotência; e cada regra do validador com um caso válido e um inválido.
3. Os testes SHALL usar dados sintéticos pequenos e SHALL NOT depender de `legacy/`.

### Requisito 10 — Documentação

**História:** Como agente ou pessoa chegando ao projeto, quero saber como o
catálogo funciona sem ler o código.

#### Critérios de aceitação

1. `docs/DATA_MODEL.md` SHALL descrever o formato final dos arquivos, com um exemplo de obra, autoria e leitura.
2. `AGENTS.md` SHALL indicar os comandos de migração, validação e testes.
3. `docs/ROADMAP.md` SHALL marcar a F1 como concluída ao final.

## Fora do escopo

- Consultas a serviços externos e qualquer enriquecimento (F2).
- Download, cópia ou geração de imagens.
- Normalização dos 496 temas (o vocabulário inicial é a lista atual, sem cortes).
- Correções bibliográficas de conteúdo, salvo a unificação de grafia de autorias.
- O app e a hospedagem.

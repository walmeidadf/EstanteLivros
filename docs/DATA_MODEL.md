# Modelo de dados

O catálogo canônico fica em `catalog/` e é a fonte de verdade do projeto. Ele é
escrito só pelo `pipeline/` e lido pelo `app/`. Os schemas (JSON Schema 2020-12)
ficam em `catalog/schema/`.

```text
catalog/
  works/{slug}.json     uma obra por arquivo           schema/work.schema.json
  authors/{slug}.json   uma autoria por arquivo        schema/author.schema.json
  readings.json         todas as leituras, por ordem   schema/readings.schema.json
  summaries.json        resumos gerados (autoria/ano/país)  schema/summaries.schema.json
  vocabularies.json     idiomas, tipos, gêneros, temas schema/vocabularies.schema.json
  source/               lista original do caderno (nunca alterar)
  media/                capas e fotos mestre (F2)
```

## Convenções

- Campos em inglês, `camelCase`. Valores de conteúdo (títulos, idiomas, temas)
  em português.
- Todo campo existe sempre. Ausência é `null` (ou `[]` em listas), **nunca**
  string vazia ou "—".
- JSON em UTF-8, indentação de 2 espaços, chaves na ordem do schema e quebra de
  linha final. A migração é idempotente: rodar de novo não gera diff.
- Slugs: ASCII minúsculo com hífens, até 80 caracteres, **estáveis** (ver abaixo).

## Obra

```json
{
  "slug": "a-vegetariana-han-kang",
  "title": "A Vegetariana",
  "originalTitle": "채식주의자",
  "originalTitleRomanized": "Chaesikjuuija",
  "authors": ["han-kang"],
  "language": "coreano",
  "firstPublished": 2007,
  "type": "romance",
  "genres": ["drama psicológico", "ficção literária"],
  "themes": ["corpo", "família", "liberdade", "loucura", "violência"],
  "edition": {
    "title": "A Vegetariana", "language": "português", "publisher": "Todavia",
    "year": 2018, "isbn13": "9788588808294", "isbn10": "8588808293",
    "format": "brochura", "match": "representative"
  },
  "cover": { "sourceUrl": "https://assets.literal.club/…", "source": "literal" },
  "catalogerNote": "Nome da autora corrigido de 'Hang kang' para 'Han Kang'. …",
  "confidence": "high",
  "references": [
    { "provider": "literal", "id": "cksj…", "url": null, "fields": "edição, ISBN, editora, capa" }
  ],
  "legacyId": "work-9866809d7276",
  "audit": { "validationStatus": "validated", "sourceConflicts": "…", "validatedAt": "2026-08-13" }
}
```

- `authors`: slugs de autoria, na ordem de crédito.
- `originalTitle`: `null` quando a obra foi escrita em português.
  `originalTitleRomanized` só existe para títulos em alfabeto não latino.
- `edition`: edição brasileira **de referência**. `match: representative` quer
  dizer que não é necessariamente a edição que a Lila leu; `exact`, que é.
- `cover`: `null` quando não há capa (o app usa a capa tipográfica). Fora isso,
  `sourceUrl`/`source` são **proveniência** (nunca viram `src`). Os campos de
  enriquecimento (F2 · capas) são aditivos e opcionais:
  - `file`: `covers/{slug}.{ext}` — o mestre local, baixado para
    `catalog/media/covers/` e **nunca** usado por hotlink; o build do app deriva
    o `src` a partir dele.
  - `license`, `credit`: licença e crédito da imagem (ou `null`).
  - `focus`: `top` | `center` | `bottom` — enquadramento do corte 2:3 no build
    (ausente = `center`). O mestre não é recortado; só o derivado muda.
  - `display`: `"typographic"` marca "revisada: fica a capa tipográfica".
  - **Três estados da capa:** `file` presente → usa a capa real; `display:
    "typographic"` → revisada, fica tipográfica; nenhum dos dois → ainda não
    revisada (o app mostra a tipográfica como padrão seguro).
- `references`: `provider` ∈ `literal`, `openlibrary`, `google_books`,
  `wikidata`, `web`.
- `legacyId`: `work_id` do catálogo legado, para rastreabilidade. Obras novas
  terão `null`.
- A obra **não** guarda dados de leitura: ano, sequência e contagem saem de
  `readings.json`.

## Autoria

```json
{
  "slug": "han-kang",
  "name": "Han Kang",
  "aliases": [],
  "country": "KR",
  "countrySource": "wikidata-citizenship",
  "languages": ["coreano"],
  "primaryLanguage": "coreano",
  "wikidata": {
    "id": "Q5646626",
    "status": "confirmed",
    "evidence": "P50 em \"A Vegetariana\" (título)",
    "rulesVersion": 1
  },
  "photo": {
    "file": "authors/han-kang.jpg",
    "license": "CC BY-SA 4.0",
    "author": "John Sears",
    "sourceUrl": "https://commons.wikimedia.org/wiki/File:…",
    "source": "commons"
  },
  "references": [
    { "provider": "wikidata", "id": "Q5646626", "url": "https://www.wikidata.org/wiki/Q5646626" }
  ]
}
```

- `aliases`: outras grafias encontradas nos dados (unificadas por acento e caixa).
- `languages`: idiomas originais das obras dela na estante, do mais frequente ao
  menos frequente. `primaryLanguage` (o primeiro) define a cor do avatar.
- `country`: país **principal**, código ISO de 2 letras (está em
  `vocabularies.countries`). `countrySource`: `wikidata-citizenship`,
  `wikidata-birthplace` ou `override` (`pipeline/config/author_overrides.json`).
- `wikidata.status`: `confirmed` (autora de uma obra da estante no Wikidata),
  `probable` (único escritor com o nome), `manual`, `ambiguous`, `not_found` ou
  `none` (marcada à mão como sem Wikidata). Sem `id` nos três últimos.
- `photo.file`: relativo a `catalog/media/`. `source`: `commons` (automática) ou
  `wikipedia`/`serpapi`/`tavily`/`manual` (escolhida na revisão,
  `pipeline/config/author_photos.json`). `license`/`author` podem ser `null`.
- **Não há `bio` na autoria**: a bio é um resumo `autoria:{slug}` em
  `summaries.json`.

## Leitura

```json
{
  "readings": [
    {
      "sequence": 197,
      "year": 2022,
      "work": "a-vegetariana-han-kang",
      "reread": false,
      "originalEntry": "A vegetariana - Hang kang",
      "notes": null
    }
  ]
}
```

- `sequence`: ordem no caderno, de 1 a N, sem lacunas. Dentro de um ano, é a
  única ordem que existe.
- `year`: só o ano. Dia e mês não existem e nunca devem ser mostrados.
- `reread`: `true` em toda leitura de uma obra que não seja a primeira.
- `originalEntry`: o texto como está no caderno.

## Resumo

```json
{ "summaries": [
  {
    "scope": "autoria:han-kang",
    "text": "Han Kang é uma escritora sul-coreana…",
    "approved": false,
    "updatedAt": "2026-11-02",
    "source": "Wikipédia (en)",
    "sourceUrl": "https://en.wikipedia.org/wiki/Han_Kang",
    "sourceLanguage": "en",
    "model": "gpt-5.4-mini",
    "promptVersion": "author-bio-v1",
    "editedBy": null
  }
] }
```

- `scope`: `autoria:{slug}` (bio), `ano:{aaaa}` ou `pais:{ISO}`. Não há resumo de
  obra. No máximo um resumo por escopo.
- `editedBy: "human"` quando o texto foi editado na revisão.
- Aprovar, rejeitar e editar: `pipeline/review_summaries.py`. Rejeições ficam em
  `pipeline/config/summary_rejections.json` (não são geradas de novo).
- Só aparece no app com `approved: true`, que exige texto e escopo existente.
- A migração preserva o `summaries.json` existente.

## Vocabulários

`vocabularies.json` lista os valores permitidos de idioma, tipo, gênero e tema,
e os países usados (`countries`: `{ code, name, languages }`, nomes em pt-BR, de
`pipeline/config/countries.json`).
Na F1 eles são **derivados dos dados**, ordenados sem acento. Na F2, os temas
viram uma lista fechada e editada à mão.

## Invariantes (conferidos pelo validador)

| Código | Regra |
|---|---|
| `schema` | cada arquivo segue seu schema |
| `file.slug` | nome do arquivo = `slug`; sem slugs repetidos |
| `ref.reading-work`, `ref.work-author` | toda referência aponta para algo existente |
| `orphan.work`, `orphan.author` | toda obra tem leitura; toda autoria tem obra |
| `seq.contiguous` | sequências 1..N, sem lacunas nem repetidas |
| `year.monotonic` | anos não decrescem ao longo da sequência (ignorando `null`) |
| `year.undated-head` | leituras 1–53 (`UNDATED_HEAD`) não têm ano; o registro 54 inicia 2014 |
| `reread.order` | `reread: true` ⇔ não é a primeira leitura da obra |
| `vocab` | idiomas, tipos, gêneros e temas estão nos vocabulários |
| `vocab.country` | `country` de toda autoria está em `vocabularies.countries` |
| `photo.file` | a foto referenciada existe em `catalog/media/` |
| `summary.scope-unique` | no máximo um resumo por escopo |
| `summary.approved` | resumo aprovado tem texto e escopo existente |

Uma obra lida mais de uma vez é **uma** obra com várias leituras.

## Slugs estáveis e exceções

- `pipeline/config/slugs.json` mapeia `legacyId` → slug de obra e nome
  normalizado → slug de autoria. É gerado pela migração e **versionado**: um
  slug publicado nunca muda, mesmo que o título seja corrigido. O mapa só ganha
  entradas.
- Slug de obra = título + primeira autoria. Colisão: `-{ano}` e depois `-2`, `-3`…
- `pipeline/config/author_overrides.json` define à mão o nome e o slug de uma
  autoria (ex.: "valter hugo mãe", em minúsculas por escolha do autor). A chave é
  o nome sem acentos e em minúsculas.

## Cobertura

`docs/plans/cobertura.md` é gerado pelo validador e mostra o que falta
preencher. É a base para priorizar o enriquecimento (F2).

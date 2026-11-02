# Modelo de dados

## Conceitos
- **Obra**: título pt-BR, título original (+ romanização), autorias, idioma
  original, primeira publicação, tipo, gêneros, temas, edição de referência, capa.
- **Edição de referência**: editora, ano, ISBN-13, `edition_match`
  (`exact` ou `representative`). `representative` não é necessariamente a edição
  que a Lila leu.
- **Leitura**: `reading_sequence` (ordem do caderno, 1–309), `read_year` (pode
  ser nulo), releitura, entrada original do caderno.
- **Autoria**: slug, nome, país (ISO), idiomas, idioma principal (define a cor do
  avatar), bio curta + fonte, foto + licença.
- **Resumo**: `scope` (`autoria:{slug}`, `ano:{ano}`, `pais:{ISO}`), texto,
  `approved`, `updated_at`.

## Invariantes
- Uma obra lida mais de uma vez é **uma** obra com várias leituras.
- Leituras 1–53 não têm ano. O registro 54 inicia 2014; o 227 inicia 2024.
- Dentro de um ano, a ordem é `reading_sequence`.
- A lista original em `catalog/source/` nunca é modificada.
- Slugs são estáveis: uma vez publicados, não mudam.
- Campos enriquecidos guardam a fonte.

## Estado de partida (legado validado)
302 obras, 309 leituras, 7 releituras, 218 autorias distintas, 223 capas (em
hotlink), 290 ISBN-13, 496 temas não normalizados.

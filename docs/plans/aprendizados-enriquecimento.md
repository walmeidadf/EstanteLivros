# Aprendizados do enriquecimento de autorias

Registro vivo dos ajustes feitos com base em execuções reais. Ele guia a
carga inicial e o fluxo de "adicionar livro" (F5). Os números brutos de cada
execução estão em [`enriquecimento-execucoes.md`](enriquecimento-execucoes.md).

## Amostra de 10 autorias (2026-11-02)

Autorias: Han Kang, Machado de Assis, Elena Ferrante, Liev Tolstói, valter hugo
mãe, Luís Fernando Veríssimo, Sidarta Ribeiro, Wellington Srbek, Mikhail
Bulgakov, Amos Oz.

### Resultado

| Etapa | Resultado |
|---|---|
| Identificação | 7 confirmadas por obra (4 por título, 2 por ISBN, 1 por Open Library), 2 prováveis, 1 não encontrada (Sidarta Ribeiro) |
| País | 9 de 9 identificadas; 2 vieram de Estado extinto (Império Russo, URSS, RSFS → RU) |
| Foto | 7 do Commons, automáticas; 2 com candidatas para revisão; 1 sem foto por decisão (Ferrante) |
| Bio | 10 propostas: 7 da Wikipédia pt, 2 da en, 1 da es; 1 do Tavily (Sidarta) |
| Custo | OpenAI ~US$ 0,02 no total (2 rodadas de prompt) · SerpApi 8 buscas · Tavily 2 créditos |

### Bugs e ajustes

| Achado | Causa | Ajuste |
|---|---|---|
| valter hugo mãe "não encontrado", apesar de ser o único escritor com o nome | o Wikidata guarda o nome só no rótulo multilíngue `mul`, e pedíamos `pt\|en` | entidades carregadas com `pt\|en\|mul`; `rulesVersion` 1 → 2 (reabre `not_found`/`ambiguous`) |
| autoria identificada depois de ter candidatas nunca recebia a foto do Commons | as candidatas já preenchiam o limite | pendência de foto considera "Commons ainda não tentado para este QID" |
| crédito "Unknown authorUnknown author" (Machado) | o Commons duplica o nome num `<span style="display:none">` | o limpador de HTML ignora elementos ocultos; "Unknown author" vira `null` |
| fotos candidatas da SerpApi eram **capas de livro** (Amazon) | a consulta incluía o título da obra | consulta `"{nome} escritor"`; lojas em `excludedDomains` |
| `--dry-run` subestimava a OpenAI | bloqueava também as chamadas grátis ao Wikidata | `--dry-run` bloqueia só OpenAI, SerpApi, Tavily e downloads |
| custo registrado como US$ 0,00 | o `.env` não tinha os preços | o script usa o preço de referência e avisa |
| Bulgakov com país `Q2184` não mapeado | RSFS da Rússia não estava em `defunct` | acrescentado → RU |

### Prompt da bio: v1 → v2

A v1 gastava espaço com dados pouco úteis para a estante: data completa de
nascimento, lista de 9 ocupações, cargo de professora, número de livros. A
v2 pede origem e época **só com anos**, pelo menos uma frase sobre a obra e no
máximo duas ocupações além de escritor.

Ganhou: Han Kang, Tolstói, Machado, valter hugo mãe e Bulgakov ficaram sem dia
e mês e mais focadas na obra.

Perdeu: a v2 foi rígida demais em alguns casos.
- Bulgakov perdeu os títulos principais ("conhecida pelo romance e pela novela").
- Sidarta Ribeiro perdeu a profissão principal ("é brasileiro").
- Wellington Srbek ficou tautológico ("se destaca por histórias em quadrinhos").
- Veríssimo continuou listando ocupações.

Pendente: decidir com a Lila entre v2 e um ajuste v3 (manter a profissão
principal quando não for escritor; permitir 1–2 obras centrais destacadas
pela fonte).

### Decisões manuais desta rodada

- `elena-ferrante`: sem foto (pseudônimo; identidade não pública).
- Sugerido: fixar `sidarta-ribeiro` → `Q7508008` (neurocientista; os livros não
  estão no Wikidata). Isso destrava o verbete da Wikipédia pt para a bio e a foto.

### Estimativa para a carga completa (215 autorias)

- OpenAI: ~US$ 0,001 por bio → ~US$ 0,25.
- SerpApi: ~1 busca por autoria sem foto no Commons → ~40.
- Tavily: ~1 crédito por autoria sem verbete útil → ~20–40.

Tudo cabe num mês dos planos gratuitos.

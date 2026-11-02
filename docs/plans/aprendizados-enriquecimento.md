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

### Prompt da bio: v2 → v3 (adotada)

A v3 acrescenta três coisas: manter a profissão principal de quem não é só
escritor, proibir frases circulares e permitir até duas obras que a fonte
destaca. Corrigiu os casos da v2.
- Bulgakov voltou a citar O Mestre e Margarida e Coração de Cão.
- Sidarta virou "neurocientista e escritor… escreve sobre cérebro, sonho e consciência".
- Veríssimo e Wellington ficaram concretos.
- Tolstói e Machado ganharam os títulos centrais.

O modelo ainda escorrega nas regras. Amos Oz saiu com 4 ocupações e 3
títulos; Wellington, com um cargo; Sidarta, com um detalhe irrelevante (coluna
bimestral). As regras do prompt reduzem esses desvios, mas não os eliminam. A
garantia final é a aprovação ou edição pela Lila (`review_summaries.py`).
Custo das três rodadas: ~US$ 0,03.

### Decisões manuais desta rodada

- `elena-ferrante`: sem foto (pseudônimo; identidade não pública).
- `sidarta-ribeiro` → `Q7508008` (neurocientista; os livros não estão no
  Wikidata). Com o QID, a bio passou a vir da Wikipédia pt e a foto, do Commons.
- `wellington-srbek`: foto escolhida na revisão (blog do autor, via SerpApi).
- Lição para a carga completa: autorias `not_found` com um único candidato
  humano coerente (o relatório mostra a descrição) se resolvem com um QID
  manual, que destrava foto e bio grátis antes de gastar cota.

## Onda 1 nas 205 restantes (2026-11-02, grátis)

| Etapa | Resultado |
|---|---|
| Identificação | 151 confirmadas por obra · 39 prováveis (todas conferidas: nenhum homônimo) · 12 não encontradas · 3 ambíguas |
| País | 188 · 2 sem dado no Wikidata (Will Schwalbe, Lara Prescott) |
| Foto | 161 do Commons · 4 do Commons pequenas demais (viram candidatas) · 38 sem foto |
| Fonte da bio | 178 da Wikipédia · 27 sem verbete (Tavily na onda 3) |

Decisões manuais: 6 QIDs (John Williams, Ana Miranda, José Aguiar, Elise
Loehnen, Lisa Mosconi, Thamirys Nunes) e 4 países onde a regra errou:

| Autoria | Regra | Correto | Por que a regra errou |
|---|---|---|---|
| Oscar Wilde | GB | IE | a Irlanda era parte do Reino Unido na época |
| Italo Svevo | AT | IT | Trieste era da Áustria-Hungria |
| Svetlana Aleksiévitch | RU | BY | o desempate foi pelo idioma (ela escreve em russo) |
| Jhumpa Lahiri | GB | US | o desempate foi pelo país de nascimento (Londres) |

Bugs achados e corrigidos:
- uma foto do Commons pequena demais era tratada como falha (agora vira nota e segue para as candidatas);
- autorias identificadas depois da 1ª tentativa não buscavam o verbete da
  Wikipédia (o registro de tentativa agora guarda o QID, como foto e país);
- foto, país e bio ficavam pendentes para sempre quando não havia o que
  achar: a seleção selecionava 202 autorias sem nada a fazer.

Lição para a manutenção: a regra de país erra em quem tem cidadania de um
Estado anterior (Irlanda/Reino Unido, Trieste/Áustria) ou que escreve num idioma
de outro país. Vale conferir o país de toda autoria nova no relatório.

## Onda 2: bios via OpenAI (2026-11-02)

- 183 bios propostas, 0 falhas, 1 nova tentativa · US$ 0,19 (165 mil tokens de
  entrada, 15 mil de saída) · ~US$ 0,001 por bio, como estimado.
- Fontes: Wikipédia pt 121 · en 50 · es 16 · fr 4 · it 2 (contando a amostra).
  Algumas brasileiras saíram da es, porque a introdução em pt era curta (Ana
  Miranda, Andréa del Fuego).
- Verificações automáticas: nenhum dia e mês; 3 "superlativos", todos falsos
  positivos ou leves ("A Amiga Genial" é título); 1 bio com 4 frases.
- **Achado:** o modelo marca títulos com Markdown (`*Auto da Compadecida*`) e
  mistura três estilos de aspas. O app não renderiza Markdown. Ajuste: a função
  `clean_text` converte ênfase e aspas retas em “…” antes de gravar. Aplicada às
  38 bios afetadas.
- Desvios que ficam para a revisão da Lila: lista de ocupações (Kazuo Ishiguro
  "músico"), frase sem sentido (Saramago "se destaca por adaptações para o
  cinema"), estilo "(1935–)" para quem está vivo.

## Onda 3: fontes com cota (2026-11-02)

- 43 autorias. Foram 40 buscas na SerpApi (uma por autoria sem foto do Commons)
  e 22 créditos do Tavily (fontes de bio). A OpenAI custou US$ 0,02.
- Fotos: as 40 autorias ganharam 3 candidatas cada, para escolha humana.
- Bios: 16 propostas a partir de páginas da web, 5 com "fontes insuficientes"
  (Renato Fino, Beatriz Leal Craveiro, Kim Hye-jin, Lara Prescott, Valeska
  Zanello) e 1 sem fonte (Eugênio Vinci de Moraes).
- As bios do Tavily trazem a pessoa certa (o filtro pelo sobrenome e o livro na
  consulta funcionaram), mas a qualidade varia mais que nas da Wikipédia:
  fontes de loja ou de um único livro dão textos genéricos (Carolina Schettini,
  Stefanie Stahl, José Aguiar).
- Cotas depois da carga: SerpApi 47/250 no mês, Tavily 24/1.000. Sobra muito
  para a manutenção e para a spec de capas.

### Carga completa: estimado × real

| Provedor | Estimado | Real (amostra + 3 ondas) |
|---|---|---|
| OpenAI | ~US$ 0,25 | ~US$ 0,24 (inclui as rodadas de calibração do prompt) |
| SerpApi | ~40 | 47 (8 na amostra, antes do ajuste da consulta) |
| Tavily | ~20–40 | 24 |

Por autoria nova (manutenção), a média ficou em ~US$ 0,001 de OpenAI, 0,2
busca da SerpApi e 0,1 crédito do Tavily.

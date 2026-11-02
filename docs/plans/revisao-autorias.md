# Revisão de autorias

Gerado por `python3 pipeline/enrich_authors.py`. Não editar à mão: as decisões
vão em `pipeline/config/` (QIDs, fotos, países) ou pelo `review_summaries.py` (bios).

## Amos Oz (`amos-oz`)

- **Bio para aprovar** (fonte: [Wikipédia (en)](https://en.wikipedia.org/wiki/Amos_Oz)):

  > Amos Oz (1939–2018) foi um escritor israelense. Escreveu romances, coletâneas de contos, livros infantis e ensaios, e sua obra foi publicada em 45 idiomas.

## Elena Ferrante (`elena-ferrante`)

- **Sem foto** e sem candidatas.
- **Bio para aprovar** (fonte: [Wikipédia (pt)](https://pt.wikipedia.org/wiki/Elena_Ferrante)):

  > Elena Ferrante é o pseudônimo de uma escritora italiana que publica em italiano desde 1991. É conhecida pelos romances e por livros de não ficção, com destaque para a série Romances de Nápoles, que se tornou um sucesso internacional.

## Han Kang (`han-kang`)

- **Bio para aprovar** (fonte: [Wikipédia (en)](https://en.wikipedia.org/wiki/Han_Kang)):

  > Han Kang (1970) é uma escritora sul-coreana. Sua obra ganhou projeção internacional com romances em prosa poética intensa, que confrontam traumas históricos e expõem a fragilidade da vida humana; foi a primeira asiática e coreana a receber o Nobel de Literatura, em 2024.

## Liev Tolstói (`liev-tolstoi`)

- País: Estado extinto Império Russo → RU.
- **Bio para aprovar** (fonte: [Wikipédia (pt)](https://pt.wikipedia.org/wiki/Liev_Tolst%C3%B3i)):

  > Liev Tolstói (1828–1910) foi um escritor russo, nascido em Iasnaia Poliana, no Governorado de Tula. Sua obra inclui romances, novelas, contos, peças e ensaios filosóficos, com destaque para a ficção realista e para títulos como Guerra e Paz e Anna Kariênina.

## Luís Fernando Veríssimo (`luis-fernando-verissimo`)

- **Bio para aprovar** (fonte: [Wikipédia (pt)](https://pt.wikipedia.org/wiki/Luis_Fernando_Verissimo)):

  > Luís Fernando Veríssimo (Porto Alegre, 1936–2025) foi um escritor brasileiro, também cartunista, tradutor, roteirista, dramaturgo e romancista. Sua obra reúne humor e diferentes gêneros, e ele foi também publicitário, revisor de jornal e músico, com atuação em saxofone em alguns conjuntos.

## Machado de Assis (`machado-de-assis`)

- **Bio para aprovar** (fonte: [Wikipédia (pt)](https://pt.wikipedia.org/wiki/Machado_de_Assis)):

  > Machado de Assis (Rio de Janeiro, 1839–1908) foi um escritor brasileiro. Sua obra abrange poesia, romance, crônica, dramaturgia, conto, folhetim, jornalismo e crítica literária, e é marcada por crítica social, ironia e traços do Romantismo e do Realismo.

## Mikhail Bulgákov (`mikhail-bulgakov`)

- País: Estado extinto Império Russo → RU.
- País: país Q2184 não mapeado em countries.json.
- País: Estado extinto União Soviética → RU.
- **Bio para aprovar** (fonte: [Wikipédia (pt)](https://pt.wikipedia.org/wiki/Mikhail_Bulg%C3%A1kov)):

  > Mikhail Afanásievitch Bulgákov (1891–1940) foi um escritor e dramaturgo russo, nascido em Kiev. Sua obra é conhecida pelo romance e pela novela satírica, com destaque para o tom crítico ao regime soviético.

## Sidarta Ribeiro (`sidarta-ribeiro`)

- **Identificação not_found**: nenhum escritor com o mesmo nome nem obra casada. Candidatos: Q7508008 (neurocientista brasileiro).
- **Sem foto**: 3 candidata(s) em `docs/plans/revisao-fotos.html`.
- **Bio para aprovar** (fonte: [As flores do bem, de Sidarta Ribeiro](https://www.fosforoeditora.com.br/produto/as-flores-do-bem-a-ciencia-e-a-historia-da-libertacao-da-maconha-70176)):

  > Sidarta Ribeiro (1971) é brasileiro. Em sua obra, mescla história, cultura, depoimentos pessoais e rigor científico para tratar da maconha e combater a desinformação sobre o tema.

## valter hugo mãe (`valter-hugo-mae`)

- Identificação provável: [Q2509574](https://www.wikidata.org/wiki/Q2509574) — único escritor com o mesmo nome (sem obra casada).
- **Bio para aprovar** (fonte: [Wikipédia (es)](https://es.wikipedia.org/wiki/Valter_Hugo_M%C3%A3e)):

  > valter hugo mãe é o nome artístico de Valter Hugo Lemos, escritor, poeta e narrador português, nascido em Angola em 1971. Sua obra inclui poesia e narrativa, e ele recebeu o Prémio José Saramago (2007) e o Grande Prémio Portugal Telecom de literatura (2012).

## Wellington Srbek (`wellington-srbek`)

- Identificação provável: [Q10393368](https://www.wikidata.org/wiki/Q10393368) — único escritor com o mesmo nome (sem obra casada).
- **Sem foto**: 3 candidata(s) em `docs/plans/revisao-fotos.html`.
- **Bio para aprovar** (fonte: [Wikipédia (pt)](https://pt.wikipedia.org/wiki/Wellington_Srbek)):

  > Wellington Srbek (Belo Horizonte, Minas Gerais, 1974) é um quadrinista e roteirista brasileiro. Sua obra se destaca por histórias em quadrinhos.

_205 autorias ainda não processadas (não listadas)._

## Aprovar bios

Depois de ler, aprove todas de uma vez (remova antes as que não quiser):

```bash
python3 pipeline/review_summaries.py --approve \
  autoria:amos-oz \
  autoria:elena-ferrante \
  autoria:han-kang \
  autoria:liev-tolstoi \
  autoria:luis-fernando-verissimo \
  autoria:machado-de-assis \
  autoria:mikhail-bulgakov \
  autoria:sidarta-ribeiro \
  autoria:valter-hugo-mae \
  autoria:wellington-srbek
```

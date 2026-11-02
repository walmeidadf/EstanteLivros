# Revisão de autorias

Gerado por `python3 pipeline/enrich_authors.py`. Não editar à mão: as decisões
vão em `pipeline/config/` (QIDs, fotos, países) ou pelo `review_summaries.py` (bios).

## Amos Oz (`amos-oz`)

- **Bio para aprovar** (fonte: [Wikipédia (en)](https://en.wikipedia.org/wiki/Amos_Oz)):

  > Amos Oz (Israel, 1939–2018) foi escritor, romancista, jornalista e intelectual israelense. Escreveu romances, coletâneas de contos, livros infantis e ensaios; sua obra também trata do conflito israelense-palestino e inclui títulos como Judas, De Amor e Trevas e A Caixa Preta.

## Elena Ferrante (`elena-ferrante`)

- **Sem foto** e sem candidatas.
- **Bio para aprovar** (fonte: [Wikipédia (pt)](https://pt.wikipedia.org/wiki/Elena_Ferrante)):

  > Elena Ferrante é o pseudônimo de uma escritora italiana. Ela escreve romances e livros de não ficção em italiano desde 1991; seus romances mais conhecidos são os de Nápoles, começando por “A Amiga Genial”.

## Han Kang (`han-kang`)

- **Bio para aprovar** (fonte: [Wikipédia (en)](https://en.wikipedia.org/wiki/Han_Kang)):

  > Han Kang (nascida em 1970) é uma escritora sul-coreana. Sua obra ganhou projeção internacional com "A Vegetariana" e, em sua escrita, a prosa poética enfrenta traumas históricos e expõe a fragilidade da vida humana.

## Liev Tolstói (`liev-tolstoi`)

- País: Estado extinto Império Russo → RU.
- **Bio para aprovar** (fonte: [Wikipédia (pt)](https://pt.wikipedia.org/wiki/Liev_Tolst%C3%B3i)):

  > Liev Tolstói (1828–1910) foi um escritor russo. É conhecido pelos romances Guerra e Paz e Anna Kariênina, e sua ficção inclui também novelas como A Morte de Ivan Ilitch e Felicidade Conjugal.

## Luís Fernando Veríssimo (`luis-fernando-verissimo`)

- **Bio para aprovar** (fonte: [Wikipédia (pt)](https://pt.wikipedia.org/wiki/Luis_Fernando_Verissimo)):

  > Luís Fernando Veríssimo (1936–2025), de Porto Alegre, foi escritor, humorista e cartunista brasileiro. Sua obra inclui humor, crônicas, contos, romances, quadrinhos e literatura infantil, marcada por textos de humor e sátira, além de personagens como Ed Mort e o Analista de Bagé.

## Machado de Assis (`machado-de-assis`)

- **Bio para aprovar** (fonte: [Wikipédia (pt)](https://pt.wikipedia.org/wiki/Machado_de_Assis)):

  > Machado de Assis (Rio de Janeiro, 1839–1908) foi um escritor brasileiro. Sua obra abrange romance, conto, crônica e crítica literária, com destaque para o Realismo; em sua segunda fase, aparecem crítica social, ironia e pessimismo. Entre seus livros mais conhecidos estão Memórias Póstumas de Brás Cubas e Dom Casmurro.

## Mikhail Bulgákov (`mikhail-bulgakov`)

- País: Estado extinto Império Russo → RU.
- País: país Q2184 não mapeado em countries.json.
- País: Estado extinto União Soviética → RU.
- **Bio para aprovar** (fonte: [Wikipédia (pt)](https://pt.wikipedia.org/wiki/Mikhail_Bulg%C3%A1kov)):

  > Mikhail Bulgákov (1891–1940) foi um escritor e dramaturgo russo da primeira metade do século XX, nascido em Kiev. Seus trabalhos mais conhecidos são o romance O Mestre e Margarida e a novela satírica Coração de Cão, em que critica o regime soviético.

## Sidarta Ribeiro (`sidarta-ribeiro`)

- **Bio para aprovar** (fonte: [Wikipédia (pt)](https://pt.wikipedia.org/wiki/Sidarta_Ribeiro)):

  > Sidarta Ribeiro (Brasília, 1971) é um neurocientista e escritor brasileiro. Escreve sobre cérebro, sonho e consciência, e também mantém uma coluna bimestral no umaúma.

## valter hugo mãe (`valter-hugo-mae`)

- Identificação provável: [Q2509574](https://www.wikidata.org/wiki/Q2509574) — único escritor com o mesmo nome (sem obra casada).
- **Bio para aprovar** (fonte: [Wikipédia (es)](https://es.wikipedia.org/wiki/Valter_Hugo_M%C3%A3e)):

  > valter hugo mãe é o nome artístico de Valter Hugo Lemos, escritor, poeta e narrador português nascido em Angola em 1971. Passou a infância em Paços de Ferreira. Sua obra inclui poesia e narrativa, com livros traduzidos para o espanhol, e recebeu o Prémio José Saramago em 2007.

## Wellington Srbek (`wellington-srbek`)

- Identificação provável: [Q10393368](https://www.wikidata.org/wiki/Q10393368) — único escritor com o mesmo nome (sem obra casada).
- **Bio para aprovar** (fonte: [Wikipédia (pt)](https://pt.wikipedia.org/wiki/Wellington_Srbek)):

  > Wellington Srbek (Belo Horizonte, Minas Gerais, 1974) é um historiador, pesquisador, quadrinista e roteirista brasileiro. Trabalha com histórias em quadrinhos e coordena o selo Nemo, da Editora Autêntica, voltado para a publicação de HQs.

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

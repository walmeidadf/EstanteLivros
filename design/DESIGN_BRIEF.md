# Livros da Lila — briefing para exploração de design

Documento autocontido para o Claude Design. Objetivo: **explorar o design de
uma estante/visualização dos livros lidos pela Lila**. Ainda não há site nem
app — só os dados, já limpos e validados.

## 1. O que é o projeto

A Lila mantém desde 2014 uma lista simples de livros lidos (um caderno/texto
com 309 entradas numeradas). Transformamos essa lista em um catálogo
estruturado e validado: título correto, autoria, idioma original, ano de
primeira publicação, tipo de obra, gêneros, temas, edição brasileira
representativa (ISBN, editora, ano), capa e referências.

O que queremos agora é **uma forma bonita e útil de ver e explorar esses
livros**, e depois (separadamente) uma forma simples de registrar novas
leituras.

## 2. Para quem é

- **Lila**: leitora, não técnica. Quer registrar rápido e ver sua história de
  leitura. Prioridade nº 1 dela: **simplicidade**.
- **Amigas dela**: estão no **Instagram**, não em redes de leitura. Um recurso
  de compartilhar (imagem/card/story) é um bônus bem-vindo, não requisito.
- O catálogo é pessoal e pequeno (~300 livros, poucas leituras novas por mês).
  Não é um produto de massa nem precisa escalar.

## 3. Os dados (o que existe hoje)

| Item | Quantidade |
|---|---|
| Leituras registradas | **309** (2014–2026) |
| Obras únicas | **302** (7 foram lidas 2 vezes) |
| Com capa (URL) | **223** (74%) — 79 precisam de capa substituta/tipográfica |
| Com ISBN-13 | 290 (96%) |
| Com ano de leitura | 256 leituras; **53 não têm ano** (as primeiras da lista, anteriores a 2014 ou sem marcação) |
| Confiança dos dados | 285 alta, 17 média |

**Leituras por ano:** 2014: 20 · 2015: 21 · 2016: 7 · 2017: 18 · 2018: 13 ·
2019: 7 · 2020: 22 · 2021: 21 · 2022: 22 · 2023: 22 · 2024: 30 · 2025: 27 ·
2026: 26 · sem ano: 53.

**Idioma original (top):** português 115 · inglês 81 · espanhol 30 · francês 28
· italiano 12 · russo 9 · japonês 6 · alemão 5 · hebraico 5 · coreano 5 · outros.

**Tipo de obra (top):** romance 210 · autobiografia/memórias 21 · novela 15 ·
coletânea de contos 13 · não-ficção 12 · ensaio 7 · infantojuvenil 6 · crônica,
biografia, quadrinhos (3 cada) · poesia, teatro, filosofia, ciência etc.

**Gêneros:** "ficção literária" domina (194/302), então **não é um bom eixo de
filtro sozinho**. Outros: realismo mágico 20, memórias 20, ficção histórica 18,
drama 12, autoficção 11, romance de formação 8, humor 7, sátira 7.

**Temas (bons eixos de exploração):** memória 62 · família 57 · identidade 37 ·
amor 34 · maternidade 25 · infância 19 · amizade 18 · classe social 17 · morte
16 · violência 16 · luto 16 · racismo 14 · imigração 13 · solidão 11 · casamento 11.

**Autoria recorrente (por nº de leituras):** Elena Ferrante 8 · Gabriel García
Márquez 7 · José Saramago 6 · Amos Oz, Ian McEwan, Machado de Assis, Itamar
Vieira Junior, Rosa Montero 4 cada.

**Década de primeira publicação:** concentrado em 2010s (94) e 2000s (48),
2020s (51); clássicos do séc. XIX (~20) e do séc. XX espalhados.

## 4. Campos disponíveis por livro

Arquivos para anexar à exploração: `exports/obras.csv` (uma linha por obra) e
`exports/catalogo_completo.csv` (uma linha por leitura, 309). Principais campos:

- **Obra:** `title_pt_br`, `original_title` (vazio se escrito em português),
  `authors` (separados por `; `), `original_language`,
  `first_publication_year`, `work_type`, `genres`, `themes` (listas com `; `).
- **Edição representativa:** `edition_title`, `isbn13`, `publisher`,
  `edition_publication_year`, `cover_url`, `edition_match`
  (`representative` em 292 casos — não é necessariamente a edição física que ela
  leu; `exact` em 10).
- **Leitura:** `reading_sequence` (ordem na lista, 1–309), `read_year`,
  `reread` (sim/não), `original_entry` (texto original da lista dela).
- **Auditoria:** `confidence` (high/medium), `decision_reason` (justificativa
  curta, útil como "nota do catalogador"), `validation_status`.

**Exemplo de registro:**

```json
{
  "title_pt_br": "A Vegetariana",
  "original_title": "채식주의자 (Chaesikjuuija)",
  "authors": "Han Kang",
  "original_language": "coreano",
  "first_publication_year": 2007,
  "work_type": "romance",
  "genres": ["drama psicológico", "ficção literária"],
  "themes": ["corpo", "família", "liberdade", "loucura", "violência"],
  "publisher": "Todavia", "edition_publication_year": 2018,
  "isbn13": "9788588808294",
  "cover_url": "https://assets.literal.club/3/cksj5wvsy1084367q298bwk52jgt.jpg",
  "readings": [{"sequence": 197, "year": 2022}, {"sequence": 271, "year": 2025, "reread": true}]
}
```

## 5. Limites dos dados que afetam o design

1. **Capas faltando (26%)**: precisa de um estado "sem capa" bonito (capa
   tipográfica gerada com título/autor/cor), não um buraco cinza.
2. **53 leituras sem ano**: precisam de um lugar na linha do tempo ("antes de
   2014 / sem data") sem parecer erro.
3. **Só temos o ano de leitura**, nunca dia ou mês. A visualização não deve
   sugerir precisão que não existe (nada de "lido em 14/03").
4. **Sem nota/avaliação pessoal** e sem resenha: a Lila nunca registrou. Não
   desenhar a experiência em torno de estrelas — a menos que seja um campo novo,
   opcional.
5. **Capas vêm de fontes variadas** (Literal, Open Library, Google Books,
   editoras): tamanhos/proporções inconsistentes. Pensar em corte/enquadramento
   uniforme.
6. **Títulos longos** (ex.: "Emburrecimento Programado: O Currículo Oculto da
   Escolarização Obrigatória") e títulos originais em alfabetos não latinos
   (russo, coreano, japonês, hebraico, árabe).
7. **Releituras**: 7 livros aparecem 2 vezes — mostrar como um livro com duas
   leituras, não como duplicata.

## 6. Visualizações desejadas (do roadmap)

- **Estante de capas** (a vista principal, a mais "bonita").
- **Linha do tempo anual** (2014 → 2026, + "sem data").
- **Busca** por título e autoria.
- **Filtros**: idioma original, país/origem, gênero, tema, tipo de obra, ano.
- **Página de cada obra** com histórico de leituras (releituras).
- **Estatísticas e retrospectiva anual** (livros por ano, idiomas, autoras mais
  lidas, temas recorrentes).
- **Compartilhar**: card/imagem de um livro ou da retrospectiva anual, pensado
  para Instagram (stories 9:16 e/ou feed 1:1/4:5). Bônus.

## 7. Princípios e restrições

- **Simplicidade primeiro.** Poucos toques, nada de feed, nada de login social.
- Pessoal e acolhedor, com cara de **estante de casa**, não de dashboard.
- Mobile-first (provavelmente usada no celular), mas funcionar bem no desktop.
- Português do Brasil.
- Acessível (contraste, tamanhos de toque) e rápido com ~300 capas (carregamento
  progressivo).
- Os dados continuam em arquivos/planilha; o design não depende de backend
  complexo.

## 8. O que gostaríamos de explorar

1. 2–3 **direções visuais distintas** para a estante principal (ex.: grade de
   capas; lombadas em prateleira; mosaico por ano/cor).
2. Como **navegar por tema/idioma/ano** sem virar um painel de filtros pesado.
3. A **página de uma obra** (capa, título original, autoria, edição, leituras,
   temas, nota do catalogador).
4. A **retrospectiva anual** como peça compartilhável no Instagram.
5. O **estado vazio/incompleto**: sem capa, sem ano, sem ISBN.
6. (Opcional) o **fluxo de registrar nova leitura** em poucos toques: buscar
   livro → confirmar edição → marcar ano → pronto.

## 9. Contexto de decisão (para não desenhar algo incompatível)

Estamos testando o **StoryGraph** como ferramenta de registro (import de CSV,
conta de teste) e, se não servir, faremos um **pequeno app sob medida**. O
design da visualização deve funcionar tanto se os dados vierem do StoryGraph
(export CSV) quanto de um app/planilha próprio — ou seja, **tratar a camada
visual como independente da origem dos dados**.

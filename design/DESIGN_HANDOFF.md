# Livros da Lila — handoff de design para desenvolvimento

Este documento descreve a **proposta visual aprovada** para a vista de leitura
(estante) dos livros da Lila. Leia junto com `DESIGN_BRIEF.md` (contexto, dados
e restrições do projeto). O cadastro de novas leituras está **fora do escopo**.

Conteúdo da pasta:

| Arquivo | O que é |
|---|---|
| `DESIGN_HANDOFF.md` | Este documento: regras visuais, componentes, telas, rotas, dados, estados. |
| `DESIGN_BRIEF.md` | Briefing original (dados, limites, público, princípios). |
| `telas/*.dc.html` | Telas de referência exportadas do canvas de design (ver §11). |

---

## 1. Princípios (não negociáveis)

- **Simplicidade primeiro.** Poucos toques, nada de login, nada de feed.
- **Cara de estante de casa, não de dashboard.** Lombadas, prateleiras de madeira, capas.
- **Mobile-first** (largura de referência 390 px), funcionando bem no desktop.
- **Português do Brasil.**
- **Só o ano de leitura existe.** Nunca mostrar dia/mês nem inventar datas. Dentro de um ano, a ordem é `reading_sequence` (ordem do caderno).
- **Sem estrelas/notas.** A Lila nunca registrou avaliação.
- **Camada visual independente da origem dos dados** (CSV próprio ou export do StoryGraph).
- **Dados incompletos não podem parecer erro** (ver §8).

## 2. Stack sugerida (sugestão, não exigência)

- Site estático, sem backend. Ex.: **Astro** ou **Vite + Preact/React**.
- Um script de build lê `exports/obras.csv` e `exports/catalogo_completo.csv` e gera um JSON normalizado (§7). As páginas são geradas a partir desse JSON.
- Rotas estáticas por ano, idioma, país, autoria e obra (§6).
- Hospedagem estática (Netlify, Vercel, GitHub Pages ou Cloudflare Pages).

## 3. Tokens visuais

### 3.1 Cores da interface

| Token | Hex | Uso |
|---|---|---|
| `--ground` | `#0E1714` | Fundo de todas as telas |
| `--surface` | `#15211D` | Campo de busca, caixas (edição) |
| `--line-soft` | `#1F2D28` | Divisórias entre linhas de lista |
| `--line` | `#2D3E37` | Divisórias de seção |
| `--border` | `#33443D` | Borda de chips e botões secundários |
| `--border-input` | `#3A4C45` | Borda do campo de busca |
| `--dashed` | `#4A5C54` | Borda tracejada ("ver todos", "sem data") |
| `--text` | `#EDE6D6` | Texto corrente |
| `--title` | `#F4EBD8` | Títulos em serifa |
| `--muted` | `#BFC8C2` | Texto secundário |
| `--faint` | `#A9B5AE` | Rótulos, contagens (passa 4.5:1 no `--ground`) |
| `--accent` | `#E8C678` | Destaque: chip ativo, contagens clicáveis, ano atual |
| `--accent-ink` | `#1A1408` | Texto sobre `--accent` |
| `--wood-top` / `--wood-bottom` | `#5B3E26` / `#3A2716` | Prateleira (gradiente vertical) |
| `--bar-neutral` | `#4B5E55` | Barras neutras de gráfico |

### 3.2 Cor por idioma original (sistema central)

A cor do **idioma original** é usada em tudo: lombadas, capas tipográficas,
avatares de iniciais, pontos/lombadas do Atlas e cabeçalho da página de idioma.

| Idioma | Fundo | Texto sobre o fundo |
|---|---|---|
| português | `#C89B3C` | `#1A1408` |
| inglês | `#2F5D9E` | `#F4EFE6` |
| espanhol | `#A8432C` | `#F7EDE6` |
| francês | `#6B4F9A` | `#F3EEF8` |
| italiano | `#3F7A5C` | `#F2F0E8` |
| russo | `#7E2433` | `#F6E9EB` |
| japonês | `#E8DFCB` | `#2A2418` |
| alemão | `#5A5A5A` | `#F2F2F2` |
| hebraico | `#2A7F86` | `#EEF7F7` |
| coreano | `#E3A9B0` | `#2A1418` |
| outros | `#4B5E55` | `#EDE6D6` |

Idiomas novos que aparecerem nos dados caem em "outros" até ganharem cor própria.

### 3.3 Tipografia (Google Fonts)

- **Display / títulos:** `Bodoni Moda` (opsz 6–96). Títulos de tela e de seção em *itálico 500*; números grandes (anos, contagens) em *regular 700*.
- **Interface / texto:** `Manrope` 400–800.
- **Títulos originais em outros alfabetos:** `Noto Serif KR`, `Noto Serif JP`, `Noto Serif Hebrew` (carregar só quando necessário; usar `lang` e `dir="rtl"` para hebraico/árabe).

| Papel | Fonte | Tamanho |
|---|---|---|
| Título de tela | Bodoni itálico 500 | 46–50 px, `line-height` 0.95, `letter-spacing` −0.02em |
| Ano gigante (página do ano) | Bodoni 700 | 132 px, `line-height` 0.84 |
| Título de seção | Bodoni itálico 500 | 24–28 px |
| Big number | Bodoni 700 | 40–48 px |
| Rótulo em caixa alta | Manrope 700 | 11–12 px, `letter-spacing` 0.14–0.18em |
| Texto corrente | Manrope 400–600 | 13–16 px |

### 3.4 Medidas

- Margem lateral: **16 px**.
- Alvos de toque **≥ 44 px** (chips e botões: `min-height: 44px`, raio 22 px).
- Capa: sempre **2:3**. Tamanhos: destaque 136×204, carrossel 104×156, grade em 3 colunas (gap 12 px na horizontal, 20 px na vertical).
- Sombra da capa: `0 16px 22px -14px rgba(0,0,0,.8)`.

## 4. Componentes

| Componente | Descrição | Onde aparece |
|---|---|---|
| **Prateleira** | Faixa de 6–9 px com gradiente `--wood-top → --wood-bottom` e sombra embaixo; capas e lombadas "apoiadas" nela. | Início, Linha do tempo, Obra |
| **Lombada mini** | Barra de 4 px de largura e 30–48 px de altura (variação determinística por índice) na cor do idioma. Uma por livro. | Linha do tempo, Atlas, faixa do ano |
| **Capa** | Imagem 2:3 com `object-fit: cover` e corte central. Sem `cover_url`, cai na capa tipográfica. | Todas as grades e carrosséis |
| **Capa tipográfica** | Fundo na cor do idioma; título em Bodoni itálico no topo; título original (quando houver) e autoria em caixa alta no rodapé, separados por um filete de 1 px. Título encolhe em até 3 passos; o subtítulo vai para a página da obra. | Fallback de capa (referência: `telas/Capas.dc.html`) |
| **Selo de releitura** | Pastilha "2×" no canto da capa. | Capas de obras com mais de uma leitura |
| **Carrossel** | Rolagem horizontal com `scroll-snap`; última capa visível cortada (sinaliza que rola); termina num cartão tracejado "ver todos (N)". | Início |
| **Faixa do ano** | Linha com ano (Bodoni), nota opcional, contagem "N ›" em `--accent` e, embaixo, uma fileira de lombadas mini sobre a prateleira. A linha inteira é clicável. | Linha do tempo (e prateleira por país, §6.5) |
| **Avatar de iniciais** | Círculo na cor do idioma principal da autoria, com as iniciais em Bodoni itálico. É substituído pela foto quando o enriquecimento trouxer uma. | Início, Atlas, Autoria, Obra |
| **Big numbers** | Grade de 2 ou 3 colunas: número em Bodoni 700 e rótulo embaixo, separados por filetes. | Ano, Idioma, País, Autoria |
| **Chips** | Pílulas de 44 px; a ativa usa `--accent` + `--accent-ink`. | Navegação, temas, países |
| **Busca** | Campo arredondado (52 px de altura) com ícone de lupa; busca título (pt-BR e original) e autoria; tolerante a acentos. | Início |

## 5. Navegação (mapa)

```
Início ─┬─ Linha do tempo ── Ano ── Obra
        ├─ Atlas ─┬─ Idioma (ver todos) ── Obra
        │         └─ País: prateleiras por país ── País (ver todos) ── Obra
        ├─ Carrossel de autoria ── Autoria ── Obra
        ├─ Carrosséis de tema ── Tema (pendente) ── Obra
        └─ Busca ── Obra / Autoria
Obra ── Autoria · Idioma · Ano(s) da leitura · Compartilhar (retrospectiva/card)
```

## 6. Telas

Para cada tela: o arquivo de referência, a rota sugerida, o conteúdo e os links.

### 6.1 Início — `telas/Inicio.dc.html` — `/`
- Título "A estante da Lila", busca, chips `Estante` (ativa) · `Atlas` · `Linha do tempo`.
- Carrossel de destaque **"Em {ano atual}"** (capas 136 px, título + autoria embaixo). O título da seção e o cartão final levam a `/ano/{ano}`.
- **"Quem sempre volta"**: carrossel de avatares das autorias com 3 ou mais leituras, cada um levando a `/autoria/{slug}`.
- Carrosséis por **tema** (os mais frequentes: memória, família, maternidade…) e **"Lidos duas vezes"** (releituras).
- Cartão **"Linha do tempo"** no fim, com mini-gráfico de barras.
- **O ano não organiza mais a tela principal**, exceto pelo ano atual. Idioma e país ficam no Atlas.

### 6.2 Linha do tempo — `telas/LinhaTempo.dc.html` — `/linha-do-tempo`
- Uma **faixa do ano** por ano, do mais recente ao mais antigo. Cada lombada é um livro, na cor do idioma, na ordem do caderno.
- Notas automáticas opcionais: "em andamento" (ano atual), "o ano mais cheio" (máximo), "N releituras".
- No fim, o bloco tracejado **"Os primeiros da lista"** (leituras sem `read_year`), que leva a `/ano/sem-data`.

### 6.3 Ano (ver todos) — `telas/VerAno.dc.html` — `/ano/{ano}` e `/ano/sem-data`
- Navegação "‹ ano anterior · próximo ano ›"; o voltar vai para a Linha do tempo.
- Ano gigante em `--accent` e uma nota curta (ex.: "o ano mais cheio da estante").
- Big numbers: leituras · idiomas originais distintos · autorias distintas · releituras.
- Barra proporcional com o mix de idiomas do ano.
- **Resumo do ano** (opcional): texto gerado por IA e **revisado pela Lila**. Só aparece com `approved: true` (§7.3). Sem resumo aprovado, o bloco não aparece.
- Grade de 3 colunas com todas as leituras do ano, na ordem do caderno.
- Botão "Compartilhar {ano}" leva à retrospectiva (§6.9).
- Em `sem-data`: título "Os primeiros da lista", sem big numbers de ano; cada item mostra "nº N da lista".

### 6.4 Atlas — `telas/AtlasV2.dc.html` — `/atlas?por=idioma|pais`
- Alternador **Idioma original | País** (padrão: idioma).
- **Por idioma:** uma linha por idioma (nome, contagem "N ›" e lombadas mini, uma por obra), ordenada por quantidade. A linha leva a `/idioma/{slug}`.
- **Quem ela mais lê:** lista de autorias com avatar e contagem, levando a `/autoria/{slug}`.
- **Temas que voltam:** nuvem tipográfica (tamanho proporcional à frequência; os maiores em itálico e `--accent`). Leva a `/tema/{slug}`.
- **Quando foram escritos:** barras por época (séc. XIX, séc. XX, 2000s, 2010s, 2020s) a partir de `first_publication_year`.

### 6.5 Atlas · por país — `/atlas?por=pais` (**ainda não desenhado; seguir esta descrição**)
- Mesma linguagem da Linha do tempo: **uma faixa por país** (nome do país em Bodoni, contagem "N ›" e fileira de lombadas mini na cor do idioma de cada obra, sobre a prateleira).
- Ordenado por quantidade. Países com poucas obras podem ser agrupados em "outros países" depois das 10 primeiras faixas.
- Tocar numa faixa leva a `/pais/{slug}` (§6.7).
- Fonte do país: o país da **autoria** (§7.2). Uma obra com várias autorias de países diferentes conta em cada um deles.

### 6.6 Idioma (ver todos) — `telas/VerIdioma.dc.html` — `/idioma/{slug}`
- Cabeçalho em bloco com a **cor do idioma**: rótulo "Idioma original", nome do idioma (Bodoni itálico, 78 px) e big numbers (obras · % da estante · autorias).
- Carrossel de avatares das autorias daquele idioma.
- Ordenação: da lista · título · autoria · ano de publicação.
- Grade de 3 colunas mostrando título pt-BR + **título original** (em itálico, com `lang`).
- **Sem texto descritivo** (decisão de design: o cabeçalho colorido e os números bastam).

### 6.7 País (ver todos) — `telas/VerPais.dc.html` — `/pais/{slug}`
- Voltar para o Atlas (modo país).
- Para países que compartilham um idioma, chips com os outros países desse idioma (ex.: em português: Brasil · Portugal · Angola · Moçambique).
- Nome do país em Bodoni 700, na cor do idioma.
- Frase curta **opcional** (mesma regra do resumo do ano: gerada e aprovada). Sem aprovação, não aparece.
- Big numbers (obras · autorias) e destaque da autoria mais lida no país.
- Grade de 3 colunas.

### 6.8 Autoria — `telas/Autor.dc.html` — `/autoria/{slug}`
- Retrato: foto, quando houver, ou avatar de iniciais grande (132 px, com anel na cor do idioma).
- Nome em Bodoni itálico; linha "País · escreve em {idiomas}".
- Big numbers: livros lidos · posição no ranking da estante (só se estiver entre as 10 primeiras; senão, mostrar outra métrica ou omitir).
- **Bio curta** (2–3 frases) com a fonte citada embaixo.
- Grade "Na estante da Lila" com "lido em {ano}" sob cada capa.
- Temas que mais aparecem nos livros dessa autoria.

### 6.9 Obra — `telas/ObraV2.dc.html` — `/obra/{slug}`
- Capa grande sobre a prateleira; título pt-BR; título original (no alfabeto original, mais a romanização quando houver).
- Autoria com avatar, levando a `/autoria/{slug}`.
- Ficha: idioma original (link para `/idioma/{slug}`), primeira publicação, tipo, gêneros.
- **Leituras:** uma linha por leitura com ano (link para `/ano/{ano}`), "primeira leitura" ou "releitura" e "nº N da lista". O título da seção acompanha a quantidade ("Lido uma vez" / "Lido duas vezes").
- Temas como chips, com a contagem da estante nos temas frequentes.
- Caixa "Edição brasileira de referência": editora, ano, ISBN formatado. Se `edition_match = representative`, isso não é necessariamente a edição que ela leu, e o rótulo deixa isso implícito.
- "Nota do catalogador" (`decision_reason`) e "Como estava no caderno" (`original_entry`).
- Botão "Compartilhar" gera um card do livro (§6.10).

### 6.10 Retrospectiva / compartilhar — `telas/Retro.dc.html`
- Peça **story 9:16** (referência em 540×960; exportar em **1080×1920 PNG**).
- Conteúdo: período, total de leituras, barras por ano, mix de idiomas, autoria mais lida, 3 temas que voltam, rodapé com @ e endereço da estante.
- Gerar uma versão por ano e uma "de sempre". Sugestão técnica: renderizar no build com Satori + resvg, ou no navegador com html-to-image.
- Variações futuras: card de livro em 1:1 ou 4:5.

### 6.11 Tema (ver todos) — `/tema/{slug}` (**pendente**)
- Reutilizar o template de Idioma: cabeçalho escuro em vez de colorido, nome do tema em Bodoni itálico, big numbers e grade.

## 7. Dados

### 7.1 Campos existentes (ver o briefing, §4)
- **Obra:** `title_pt_br`, `original_title`, `authors` (separados por `; `), `original_language`, `first_publication_year`, `work_type`, `genres`, `themes` (separados por `; `).
- **Edição:** `edition_title`, `isbn13`, `publisher`, `edition_publication_year`, `cover_url`, `edition_match`.
- **Leitura:** `reading_sequence`, `read_year`, `reread`, `original_entry`.
- **Auditoria:** `confidence`, `decision_reason`, `validation_status`.

### 7.2 Campos novos necessários (vêm do enriquecimento, fora deste escopo)
- **Autoria** (tabela `autores`): `slug`, `name`, `country` (código ISO), `languages` (lista), `bio` (2–3 frases), `bio_source`, `photo_url` (opcional), `primary_language` (decide a cor do avatar).
- **Resumos gerados** (tabela `resumos`): `scope` (`ano:2024`, `pais:PT`…), `text`, `approved` (bool), `updated_at`.

### 7.3 JSON normalizado (sugestão)

```json
{
  "works": [{
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
    "edition": { "publisher": "Todavia", "year": 2018, "isbn13": "9788588808294", "match": "representative" },
    "cover": "https://…",
    "readings": [{ "sequence": 197, "year": 2022 }, { "sequence": 271, "year": 2025, "reread": true }],
    "catalogerNote": "…",
    "originalEntry": "…"
  }],
  "authors": [{ "slug": "han-kang", "name": "Han Kang", "country": "KR", "languages": ["coreano"], "bio": "…", "bioSource": "…", "photo": null }],
  "summaries": [{ "scope": "ano:2024", "text": "…", "approved": true }]
}
```

- Uma obra lida mais de uma vez é **uma** obra com várias `readings`, nunca uma duplicata.
- Agregados (contagem por ano, idioma, país, tema e autoria) são calculados no build.
- O título original vem de `original_title`; quando ele traz a romanização entre parênteses, separe as duas partes.

## 8. Estados incompletos

| Caso | Comportamento |
|---|---|
| Sem `cover_url` (ou imagem quebrada) | Capa tipográfica (§4). |
| Sem `read_year` | Vai para "Os primeiros da lista"; mostra "nº {reading_sequence} da lista" no lugar do ano. |
| Sem ISBN ou edição | A linha some. Nada de "—" ou "não informado". |
| Releitura | Uma capa com selo "2×"; conta nos dois anos; a página da obra lista as duas leituras. |
| Título longo | Até 2 linhas com reticências (…) nos rótulos; subtítulo só na página da obra. |
| Título original não latino | Fonte Noto correspondente, atributo `lang`, `dir="rtl"` para hebraico/árabe. |
| Autoria sem foto | Avatar de iniciais. |
| Sem bio | A seção "Sobre" some. |
| Resumo não aprovado | O bloco não aparece. |
| `confidence = medium` | Nenhum sinal visual para visitantes. Opcional: um indicador discreto num modo de revisão da Lila. |

## 9. Carrosséis (boas práticas adotadas)

- No máximo **~20 itens** por carrossel; depois vem um cartão final "ver todos (N)".
- A **última capa visível fica cortada**, para indicar que a fileira rola.
- `scroll-snap` no início de cada item.
- **Sem rolagem automática, bolinhas, contador ou barra de rolagem.**
- O título da seção também é link para a página completa.
- Título (e autoria) **em texto sob a capa**, nunca só na imagem.
- **Desktop:** setas ‹ › ao lado da fileira, fora das capas, e rolagem por teclado.

## 10. Acessibilidade e desempenho

- Controles reais: `<a href>` para navegação, `<button>` para ações e `<label>` em campos. Botões só com ícone levam `aria-label`.
- Contraste de 4.5:1 no texto (os tokens de §3.1 já passam sobre `--ground`). Texto sobre cor de idioma usa a coluna "Texto" de §3.2.
- Barras e lombadas decorativas levam `aria-hidden`; o dado correspondente existe em texto.
- ~300 capas: `loading="lazy"`, `srcset` com miniaturas e dimensões fixas 2:3 (sem salto de layout). Pré-gerar miniaturas no build.
- Funciona sem JavaScript para leitura básica (páginas estáticas).

## 11. Sobre os arquivos `telas/*.dc.html`

- São exportados de um canvas de design. A marcação fica dentro de `<x-dc>`; os trechos `{{…}}` são preenchidos pelo `renderVals()` do `<script type="text/x-dc">` ao final de cada arquivo.
- **Usar como referência visual e de medidas** (cores, tamanhos, espaçamentos e estrutura estão nos `style` inline), **não como código de produção**.
- Os arquivos não abrem sozinhos no navegador: dependem do runtime do editor (`support.js`).
- **Os dados dentro das telas são ilustrativos.** Os títulos são exemplos dos autores recorrentes, os anos são inventados (exceto A Vegetariana) e algumas contagens das páginas de ano, país e idioma também são ilustrativas. Os números reais vêm sempre dos CSVs.
- `Capas.dc.html` usa o fundo claro de uma exploração anterior; vale a **regra** da capa tipográfica com as cores de §3.2.

## 12. Pendências

1. Desenhar `/atlas?por=pais` (§6.5) e `/tema/{slug}` (§6.11).
2. Layout desktop: largura máxima do conteúdo, mais colunas na grade e setas nos carrosséis.
3. Card de livro para compartilhar (1:1 ou 4:5).
4. Definir quais temas viram carrossel no Início (sugestão: os 4 mais frequentes + "Lidos duas vezes").
5. Fluxo de revisão dos resumos gerados pela Lila (fora deste escopo).

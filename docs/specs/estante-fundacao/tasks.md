# Tarefas — Estante: fundação (S1)

Referências: [`requirements.md`](requirements.md) · [`design.md`](design.md).

Cada tarefa de código é incremental e termina **verde**: `npm run check`
(tipos) passa e, quando a tarefa tem testes, `npm test` (runner nativo do Node)
passa. Nada chama rede em build nem em teste. Nenhuma tarefa escreve em
`catalog/`.

A entrega visível da S1 é a vitrine `/__styleguide` (tarefa 13): ela é a
verificação final e a tela de abertura da palestra.

Dependências (tarefas na mesma chave podem ir em paralelo):

```
1 → 2 → 3 → {4, 5} → 6 → 7 → 8 → {9, 10, 11, 12} → 13 → 14
```

## Fundação do projeto

- [x] 1. Esqueleto do projeto Astro
  - [x] 1.1 Criar o projeto em `app/` com Astro 7.x, `output: "static"`, TypeScript `strict`, aliases `@` → `src/` e a constante `CATALOG_DIR` resolvendo a raiz do catálogo a partir da raiz do repositório.
    - _Requisitos: 1.1, 1.2, 1.5, 1.6_
  - [x] 1.2 `package.json` com versões **fixadas** (sem `^`/`~`), `package-lock.json` versionado, `.nvmrc`/`engines`, e os scripts `dev`, `build`, `preview`, `check` (`astro check` + `tsc --noEmit`).
    - _Requisitos: 1.3, 1.4_
  - [x] 1.3 `README.md` do app: o que é, os quatro scripts, a regra "só lê `catalog/`, nunca rede, nunca `legacy/`", e o passo de setup das fontes (tarefa 4).
    - _Requisitos: 1.3, 1.5, 1.6_
  - [x] 1.4 `app/` entra no `.gitignore` certo (ignorar `node_modules`, `dist`, `.astro`); garantir que `catalog/` não seja copiado para dentro de `app/`.
    - _Requisitos: 1.5_
  - Fim: `npm run check` passa num projeto que compila vazio.

## Tokens, tipografia e fontes

- [ ] 2. Tokens e medidas (`src/styles/`)
  - [ ] 2.1 `tokens.css`: todas as custom properties de cor de §3.1 com os valores exatos do handoff e as medidas de §3.4 (`--gutter`, `--tap`, `--radius-pill`, `--cover-ratio`, `--cover-shadow`, tamanhos de capa, gaps da grade).
    - _Requisitos: 2.1, 2.3_
  - [x] 2.2 `global.css`: reset enxuto, `background: var(--ground)`, `color: var(--text)` no corpo.
    - _Requisitos: 2.2_
  - _Requisitos: 2.1, 2.2, 2.3_

- [x] 3. Tipografia (`src/styles/type.css`)
  - Classes `.t-screen-title`, `.t-year-giant`, `.t-section-title`, `.t-bignumber`, `.t-label`, `.t-body` com fonte, peso, tamanho, `line-height` e `letter-spacing` de §3.3; faixas (46–50, 24–28) via `clamp()`.
  - _Requisitos: 2.4_

- [x] 4. Fontes auto-hospedadas (Fontsource, `src/styles/fonts.css`)
  - [x] 4.1 Fontes via pacotes `@fontsource*` (versões fixadas), empacotadas no build — sem hotlink e sem passo manual de download. (Desvio aprovado do plano de baixar para `public/fonts/`.)
    - _Requisitos: 2.5_
  - [x] 4.2 `fonts.css`: importa Bodoni/Manrope variáveis e os subsets Noto (KR/JP/Hebrew) peso 400; cada subset traz seu `unicode-range` para carga sob demanda sem JS.
    - _Requisitos: 2.5_
  - [x] 4.3 `Base.astro` (layout): `<html lang="pt-BR">`, `<head>` importando tokens, fontes, tipografia e global; aplica o fundo (§3.1).
    - _Requisitos: 2.2, 2.6, 9.1_

## Cor por idioma

- [x] 5. Módulo de cor por idioma (`src/lib/language-color.ts`)
  - [x] 5.1 Mapa idioma → `{ bg, ink }` de §3.2, fallback `OTHER`, `languageColor(language)`, e um helper que emite `--lang-bg`/`--lang-ink` para compor em CSS.
    - _Requisitos: 3.1, 3.2, 3.3_
  - [x] 5.2 Teste: cada idioma de §3.2 devolve o par certo; idioma fora do mapa (ex.: catalão) devolve `OTHER`; cobre os 15 idiomas de `vocabularies.json`.
    - _Requisitos: 3.2, 3.4_

## Camada de dados

- [x] 6. Esquemas Zod (`src/lib/catalog/schema.ts`)
  - Reescrever em Zod os cinco JSON Schema reais de `catalog/schema/`, campo a campo, com os pontos fixados no design §6.1 (`cover` objeto-ou-`null`, `photo` objeto-ou-`null`, bio **fora** da autoria, `reading.year` anulável, `summary.scope`). Tipos derivados via `z.infer`.
  - Teste: coberto pelos testes do loader (carga real do catálogo valida os 5 esquemas).
  - _Requisitos: 4.1, 4.5_

- [x] 7. Loader (`src/lib/catalog/load.ts`)
  - [x] 7.1 Ler `readings.json`, `summaries.json`, `vocabularies.json` e todos os `works/*.json` e `authors/*.json` a partir de `CATALOG_DIR`, validando cada um com o Zod da tarefa 6; em erro, lançar com **arquivo + campo** na mensagem.
    - _Requisitos: 4.2, 4.3, 4.6_
  - [x] 7.2 Invariantes de referência: `work.authors[]` existe; `reading.work` existe; `primaryLanguage ∈ languages`; `summary.scope` coerente (`autoria:{slug}` existe, `ano:{aaaa}` tem leitura, `pais:{XX}` existe).
    - _Requisitos: 4.4_
  - [x] 7.3 Teste com fixtures: catálogo válido carrega; cada invariante quebrada (autor inexistente, reading órfã, scope órfão, primaryLanguage fora) faz o loader lançar.
    - _Requisitos: 4.4, 5.8_

- [x] 8. Modelo de domínio (`src/lib/catalog/model.ts`)
  - [x] 8.1 Montar o grafo tipado: obra com autorias resolvidas, leituras, cor de idioma; autoria com obras, país resolvido (via `vocabularies`), cor do `primaryLanguage`, foto e bio.
    - _Requisitos: 5.1_
  - [x] 8.2 Regras: releitura = uma obra com várias leituras (5.2); só o `year`, leitura sem ano marcada "sem data" com `sequence` (5.3); `bio` só com `summary` `approved` (5.4); país da obra derivado das autorias (5.6).
    - _Requisitos: 5.2, 5.3, 5.4, 5.6_
  - [x] 8.3 Teste: releitura aparece uma vez e conta nos dois anos; leitura sem ano vira "sem data" com `sequence`; bio não aprovada → `null`.
    - _Requisitos: 5.2, 5.3, 5.4, 5.8_

- [x] 9. Agregados (`src/lib/catalog/aggregates.ts`)
  - Contagens por ano, idioma, país (obra conta em cada país das autorias), autoria e tema; devolver mapa **e** lista ordenada por quantidade. Teste das contagens e da ordenação.
  - _Requisitos: 5.5, 5.6, 5.8_

- [x] 10. Fachada (`src/lib/catalog/index.ts`)
  - `getCatalog()` roda load → model → aggregate **uma vez** e memoiza para o build. Rodado contra o catálogo real: 302 obras, 215 autorias, 309 leituras, 209 bios; ano mais cheio 2024 (30), 53 sem data.
  - _Requisitos: 5.7, 4.2_

## Imagens

- [x] 11. Derivação de imagens (`src/lib/images.ts`)
  - Resolve o mestre de autoria (`catalog/media/authors/{slug}.{ext}`) via `import.meta.glob` e gera derivados com `astro:assets` (sharp): AVIF, corte central, 1:1 (avatar) ou 2:3, `srcset`. `src` é **sempre** o derivado local; `cover.sourceUrl` nunca vira `src`. Fallback `null` quando não há mestre.
  - _Requisitos: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

## Componentes base

- [x] 12. Os cinco componentes (`src/components/`)
  - [x] 12.1 `Shelf.astro`: faixa de madeira com gradiente e sombra; `aria-hidden`.
    - _Requisitos: 7.5, 7.6_
  - [x] 12.2 `Spine.astro`: barra 4px, altura determinística 30–48px por `index`, cor do idioma; `aria-hidden`.
    - _Requisitos: 7.3, 7.6_
  - [x] 12.3 `TypographicCover.astro`: fundo/texto na cor do idioma; título Bodoni itálico; título original com `lang`/`dir` e fonte Noto quando não latino; autoria em caixa alta com filete; título encolhe em 3 passos por faixa de comprimento, sem JS.
    - _Requisitos: 7.2, 7.7, 9.2_
  - [x] 12.4 `Cover.astro`: quadro 2:3 com sombra; usa o derivado quando há mestre, senão delega para `TypographicCover`; selo "2×" opcional; `alt` = título; tamanhos hero/rail/grid.
    - _Requisitos: 7.1, 7.7, 6.5, 9.3_
  - [x] 12.5 `InitialsAvatar.astro`: círculo na cor do `primaryLanguage`, iniciais em Bodoni; troca pela foto local quando houver; `alt` = nome; tamanho parametrizável.
    - _Requisitos: 7.4, 7.7_
  - [x] 12.6 `src/lib/text.ts`: iniciais a partir do nome, detecção de alfabeto (faixas Unicode) → fonte Noto + `dir`. Testado (latino, cirílico, hebraico RTL, japonês, coreano).
    - _Requisitos: 7.2, 7.7, 9.2_
  - Props tipadas; zero JS; sem acesso direto ao catálogo (R7.8, R7.6).
  - _Requisitos: 7.6, 7.8_

## Vitrine e fechamento

- [ ] 13. Vitrine (`src/pages/__styleguide/index.astro`)
  - [x] 13.1 Seções de tokens de cor, paleta por idioma (com o caso "outros": catalão) e tipografia.
    - _Requisitos: 8.1_
  - [x] 13.2 Componentes em estados, com **dados reais** via `getCatalog()`: `InitialsAvatar` com foto (`han-kang`) e sem foto (`beatriz-leal`); `TypographicCover` curto/longo/cirílico/hebraico RTL/japonês; `Spine` em fileira sobre `Shelf`; `Cover` com capa tipográfica.
    - _Requisitos: 8.2, 8.5_
  - [x] 13.3 Rota em `/styleguide` com `noindex`, sem link a partir de páginas públicas; renderiza sem JS. (Underscore `__styleguide` era excluído do roteamento do Astro, então não gerava página; a exclusão do público fica para o deploy, F4.)
    - _Requisitos: 8.3, 8.4_
  - _Requisitos: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 14. Verificação de ponta a ponta
  - [x] 14.1 `npm run build` do zero contra o catálogo real: código 0, 2 páginas, foto de han-kang derivada em 3 tamanhos AVIF.
    - _Requisitos: 1.8, 9.4_
  - [x] 14.2 Prova da trava: numa **cópia temporária** do catálogo, corromper `cover` (vira string) e uma referência de leitura → build falha com código 1 e mensagem citando arquivo e campo. Real intocado.
    - _Requisitos: 4.3, 1.8_
  - [x] 14.3 Acessibilidade/desempenho: `dir="rtl"` e `lang="he"/"ko"` nos títulos não latinos, imagens com `alt` e `srcset`, decorativos `aria-hidden`, zero `<script>` na vitrine.
    - _Requisitos: 9.1, 9.2, 9.3, 9.4, 9.5_
  - [x] 14.4 Atualizar `docs/ROADMAP.md` (S1 concluída) e nota de handover para a S2.

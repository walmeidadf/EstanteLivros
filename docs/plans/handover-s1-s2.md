# Handover — fim da S1, início da S2

Escrito ao concluir a spec `estante-fundacao` (S1). Serve para retomar a F3 na
spec seguinte (S2 `estante-inicio-busca`).

## O que a S1 entregou

O app em `app/` (Astro 7 estático) com a fundação pronta e verificada:

- **Projeto**: `output: "static"`, TypeScript estrito, versões fixadas. Scripts
  `dev`, `build`, `preview`, `check`, `test`. Node 22.
- **Visual como código**: `src/styles/` com `tokens.css` (§3.1/§3.4),
  `type.css` (§3.3), `fonts.css` (Fontsource, auto-hospedado, Noto sob demanda
  por `unicode-range`), `global.css`. Layout `Base.astro`.
- **Cor por idioma**: `src/lib/language-color.ts` (§3.2 + fallback "outros").
- **Camada de dados** em `src/lib/catalog/`: `schema.ts` (Zod espelhando os 5
  JSON Schema reais), `load.ts` (lê + valida + invariantes de referência),
  `model.ts` (grafo tipado com as regras: releitura, só ano, bio aprovada,
  país da autoria), `aggregates.ts` (contagens por ano/idioma/país/autoria/
  tema), `index.ts` (`getCatalog()` memoizado).
- **Imagens**: `src/lib/images.ts` deriva fotos no build via `astro:assets`
  (AVIF, corte central, 1:1/2:3, srcset). Nunca hotlink.
- **Componentes**: `Shelf`, `Spine`, `Cover`, `TypographicCover`,
  `InitialsAvatar` + `src/lib/text.ts` (iniciais, detecção de alfabeto).
- **Vitrine**: `/styleguide` (`noindex`), com dados reais, prova visual da S1.

Verificação: 32 testes verdes (`npm test`), `npm run check` limpo, build do
catálogo real em código 0 (302 obras, 215 autorias, 309 leituras, 209 bios;
ano mais cheio 2024, 53 sem data). Prova da trava: catálogo inválido quebra o
build com código 1 e mensagem citando arquivo e campo.

## Convenções estabelecidas (seguir na S2)

- Dentro de `src/lib`, **imports relativos** (a camada roda sob `node --test`);
  o alias `@/` fica para os arquivos `.astro`.
- Regra de negócio só em `src/lib/catalog`; componentes recebem props já
  resolvidas e não leem o catálogo direto.
- `CATALOG_DIR` resolve a partir de `process.cwd()` (a pasta `app/`), com
  override por env — por isso os builds e a prova da trava não tocam o catálogo
  real.
- Testes com o runner nativo do Node, em arquivos `*.test.ts`.

## O que fica para a S2 (`estante-inicio-busca`)

- Tela **Início** (`/`): carrossel "Em {ano atual}", "Quem sempre volta"
  (autorias com 3+ leituras — já dá para tirar de `aggregates.readingsByAuthor`),
  carrosséis de tema e "Lidos duas vezes", cartão Linha do tempo. Compor com os
  componentes da S1.
- **Busca**: índice próprio tolerante a acento (título pt-BR, original e
  autoria), como ilha. A S1 não montou índice nenhum — é o grosso da S2.
- O placeholder atual de `/` (`src/pages/index.astro`) será substituído.

## Pendências herdadas (não bloqueiam a S2)

- Capas de obra ainda não existem no catálogo (frente de F2). `Cover` já cai na
  capa tipográfica; quando as capas entrarem, passam pelo mesmo `images.ts`
  (estender para capas de obra, hoje só fotos de autoria).
- Excluir `/styleguide` do deploy público: tratar na F4.

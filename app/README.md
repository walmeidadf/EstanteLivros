# app/ — a Estante da Lila (PWA)

Interface pública e instalável da estante. Feita em **Astro** com saída
estática: cada rota vira HTML que funciona sem JavaScript.

Esta pasta é a entrega da fase **F3**. A spec de fundação é
[`docs/specs/estante-fundacao/`](../docs/specs/estante-fundacao/).

## Regras (não negociáveis)

- O app **só lê** o `catalog/` (um nível acima desta pasta). Nunca escreve lá.
- O app **não chama APIs externas** em build nem em runtime.
- O app **não depende de `legacy/`**.
- Imagens são derivadas no build a partir dos mestres em `catalog/media/`;
  **nunca** hotlink de URLs externas.
- Dependências com versão **fixada** (sem `^`/`~`).

## Requisitos

- Node 22 LTS (ver `.nvmrc`).

## Scripts

```bash
npm install        # instala as dependências (versões fixadas)
npm run dev        # servidor de desenvolvimento
npm run build      # build estático; quebra se o catálogo for inválido
npm run preview    # serve o resultado do build localmente
npm run check      # astro check + tsc --noEmit (tipos)
npm test           # testes da camada de dados (runner nativo do Node)
```

O `build` valida o `catalog/` com Zod antes de gerar qualquer página. Catálogo
inválido quebra o build com código ≠ 0 e uma mensagem que aponta o arquivo e o
campo.

## Fontes

As fontes (Bodoni Moda, Manrope e Noto Serif KR/JP/Hebrew) são
**auto-hospedadas** via pacotes [Fontsource](https://fontsource.org), nunca
servidas por hotlink. Os arquivos `.woff2` vêm dos pacotes `@fontsource*`
(versões fixadas no `package.json`) e são empacotados no build em
`dist/_astro/`. As fontes Noto carregam **sob demanda**: cada subset traz seu
próprio `unicode-range`, então o navegador só baixa a fonte de um alfabeto
quando um glifo dele aparece na página. Ver `src/styles/fonts.css`.

## Vitrine

A rota interna `/__styleguide` mostra os tokens, a cor por idioma e os
componentes base em todos os seus estados. Serve de verificação visual e fica
**fora** do site público.

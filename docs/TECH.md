# Tecnologia

## App (`app/`)
- **Astro** com saída estática. Páginas funcionam sem JavaScript.
- Interatividade em ilhas pequenas (busca, alternador do Atlas, ordenação,
  compartilhar). Sem framework pesado.
- Busca com índice JSON próprio gerado no build, tolerante a acentos, cobrindo
  título pt-BR, título original e autoria.
- Validação do catálogo no build com **Zod**. Catálogo inválido quebra o build.
- PWA com `@vite-pwa/astro` (manifest, offline, instalação no Android).
- Imagens: derivados WebP/AVIF (2:3, corte central) gerados no build a partir dos
  mestres em `catalog/media/`. Nunca fazer hotlink de imagens externas.
- Retrospectiva e cards de compartilhamento: Satori + resvg no build (PNG
  1080×1920), entregues pela Web Share API.
- Fontes: Bodoni Moda, Manrope e Noto Serif (KR, JP, Hebrew) sob demanda.

## Pipeline (`pipeline/`)
- **Python 3**, só biblioteca padrão quando possível.
- Todo script é uma CLI **idempotente**, com cache de respostas externas em disco.
- Fontes externas: Wikidata, Wikipedia pt, Wikimedia Commons, Open Library,
  Literal, Google Books e sites de editoras.
- Todo dado enriquecido registra proveniência (fonte, URL, data).
- Testes com `unittest`.

## Hospedagem (`infra/`) — em decisão
- Opção A: AWS S3 privado + CloudFront (OAC) + ACM, via CDK em TypeScript.
- Opção B: Cloudflare Pages, com Cloudflare Access protegendo o modo da Lila.
- Nas duas: CI/CD no GitHub Actions; custo-alvo perto de zero.

## Convenções
- Interface, conteúdo e documentação em português do Brasil. Código e
  identificadores em inglês.
- Versões de dependências fixadas.
- Acessibilidade: `<a>` para navegar, `<button>` para ações, contraste 4.5:1,
  alvos de toque ≥ 44 px, `lang` e `dir` corretos em títulos originais.

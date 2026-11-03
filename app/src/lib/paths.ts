import { resolve } from "node:path";

/**
 * Raiz do catálogo (a fonte de verdade).
 *
 * O app **só lê** o catálogo: nunca escreve aqui, nunca chama rede e nunca
 * depende de `legacy/`. Toda leitura de disco do catálogo passa por este
 * caminho.
 *
 * Resolvido a partir do diretório de trabalho do build (a pasta `app/`, de
 * onde os scripts npm rodam) subindo um nível até a raiz do repo e entrando em
 * `catalog/`. Usar `process.cwd()` em vez de `import.meta.url` é o que mantém o
 * caminho correto depois do empacotamento do Astro, que move os módulos para
 * `dist/.prerender/chunks/` e muda a profundidade relativa.
 *
 * Pode ser sobrescrito por `CATALOG_DIR` no ambiente (útil para CI e testes).
 */
export const CATALOG_DIR =
  process.env.CATALOG_DIR ?? resolve(process.cwd(), "..", "catalog");

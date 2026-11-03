/*
 * Fachada do catálogo.
 *
 * `getCatalog()` roda o caminho de mão única (ler → validar → modelar →
 * agregar) UMA vez e memoiza o resultado para o build inteiro, para que
 * páginas e componentes não releiam disco (R5.7).
 *
 * Convenção de import: dentro de `src/lib` usamos caminhos relativos (para a
 * camada rodar sob `node --test`); o alias `@/` fica para os arquivos `.astro`
 * (layouts, páginas, componentes), que só rodam via Astro.
 */
import { loadRawCatalog } from "./load.ts";
import { buildModel, type CatalogModel } from "./model.ts";
import { buildAggregates, type Aggregates } from "./aggregates.ts";

export type Catalog = CatalogModel & { aggregates: Aggregates };

let cached: Catalog | null = null;

/** Devolve o catálogo modelado e agregado, memoizado por build. */
export function getCatalog(): Catalog {
  if (cached) return cached;
  const model = buildModel(loadRawCatalog());
  cached = { ...model, aggregates: buildAggregates(model) };
  return cached;
}

export type {
  CatalogModel,
  AuthorView,
  WorkView,
  ReadingView,
} from "./model.ts";
export type { Aggregates, Count } from "./aggregates.ts";

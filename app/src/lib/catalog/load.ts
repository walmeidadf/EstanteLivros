/*
 * Loader do catálogo (executa no build).
 *
 * Caminho de mão única, passo 1: ler → validar. Lê todos os arquivos do
 * catálogo a partir de CATALOG_DIR, valida cada um com o Zod correspondente e
 * confere invariantes de referência que o schema isolado não vê. Qualquer
 * problema lança — e o build morre com código ≠ 0 e uma mensagem que aponta o
 * arquivo e o campo.
 */
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { z } from "zod";
import { CATALOG_DIR } from "../paths.ts";
import {
  authorSchema,
  readingsFileSchema,
  summariesFileSchema,
  vocabulariesSchema,
  workSchema,
  type Author,
  type Reading,
  type Summary,
  type Vocabularies,
  type Work,
} from "./schema.ts";

export type RawCatalog = {
  works: Work[];
  authors: Author[];
  readings: Reading[];
  summaries: Summary[];
  vocabularies: Vocabularies;
};

/** Erro de catálogo inválido, com arquivo e campo na mensagem. */
export class CatalogError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "CatalogError";
  }
}

function readJson(file: string): unknown {
  let raw: string;
  try {
    raw = readFileSync(file, "utf8");
  } catch (cause) {
    throw new CatalogError(`não consegui ler ${file}: ${String(cause)}`);
  }
  try {
    return JSON.parse(raw);
  } catch (cause) {
    throw new CatalogError(`JSON inválido em ${file}: ${String(cause)}`);
  }
}

/** Valida `data` com `schema`, citando o arquivo e o campo em caso de erro. */
function parseOrThrow<T>(schema: z.ZodType<T>, data: unknown, file: string): T {
  const result = schema.safeParse(data);
  if (!result.success) {
    const first = result.error.issues[0];
    const path = first && first.path.length ? first.path.join(".") : "(raiz)";
    const msg = first ? first.message : "erro desconhecido";
    throw new CatalogError(`${file}: campo "${path}": ${msg}`);
  }
  return result.data;
}

function listJsonFiles(dir: string): string[] {
  return readdirSync(dir)
    .filter((name) => name.endsWith(".json"))
    .sort()
    .map((name) => join(dir, name));
}

/**
 * Lê e valida o catálogo inteiro. Parametrizado por `catalogDir` para os testes
 * poderem apontar para fixtures; o padrão é o catálogo real (CATALOG_DIR).
 */
export function loadRawCatalog(catalogDir: string = CATALOG_DIR): RawCatalog {
  // Arquivos únicos.
  const readings = parseOrThrow(
    readingsFileSchema,
    readJson(join(catalogDir, "readings.json")),
    "readings.json",
  ).readings;

  const summaries = parseOrThrow(
    summariesFileSchema,
    readJson(join(catalogDir, "summaries.json")),
    "summaries.json",
  ).summaries;

  const vocabularies = parseOrThrow(
    vocabulariesSchema,
    readJson(join(catalogDir, "vocabularies.json")),
    "vocabularies.json",
  );

  // Um arquivo por obra e por autoria.
  const works: Work[] = [];
  for (const file of listJsonFiles(join(catalogDir, "works"))) {
    works.push(parseOrThrow(workSchema, readJson(file), rel(file)));
  }

  const authors: Author[] = [];
  for (const file of listJsonFiles(join(catalogDir, "authors"))) {
    authors.push(parseOrThrow(authorSchema, readJson(file), rel(file)));
  }

  const catalog: RawCatalog = {
    works,
    authors,
    readings,
    summaries,
    vocabularies,
  };
  checkInvariants(catalog);
  return catalog;
}

/** Caminho curto para mensagens (works/x.json em vez do absoluto). */
function rel(file: string): string {
  const parts = file.split(/[\\/]/);
  return parts.slice(-2).join("/");
}

/**
 * Invariantes de referência entre arquivos (o schema isolado não as vê):
 *  - toda work.authors[] existe em authors/;
 *  - toda reading.work existe em works/;
 *  - author.primaryLanguage ∈ author.languages;
 *  - summary.scope tem alvo coerente (autoria existe; ano tem leitura; país existe).
 */
export function checkInvariants(catalog: RawCatalog): void {
  const authorSlugs = new Set(catalog.authors.map((a) => a.slug));
  const workSlugs = new Set(catalog.works.map((w) => w.slug));
  const years = new Set(
    catalog.readings
      .map((r) => r.year)
      .filter((y): y is number => y !== null),
  );
  const countryCodes = new Set(catalog.vocabularies.countries.map((c) => c.code));

  for (const work of catalog.works) {
    for (const author of work.authors) {
      if (!authorSlugs.has(author)) {
        throw new CatalogError(
          `works/${work.slug}.json: autoria "${author}" não existe em authors/`,
        );
      }
    }
  }

  for (const reading of catalog.readings) {
    if (!workSlugs.has(reading.work)) {
      throw new CatalogError(
        `readings.json: leitura nº ${reading.sequence} aponta para obra "${reading.work}" inexistente`,
      );
    }
  }

  for (const author of catalog.authors) {
    if (!author.languages.includes(author.primaryLanguage)) {
      throw new CatalogError(
        `authors/${author.slug}.json: primaryLanguage "${author.primaryLanguage}" não está em languages`,
      );
    }
  }

  for (const summary of catalog.summaries) {
    const [kind, value] = splitScope(summary.scope);
    if (kind === "autoria" && !authorSlugs.has(value)) {
      throw new CatalogError(
        `summaries.json: scope "${summary.scope}" aponta para autoria inexistente`,
      );
    }
    if (kind === "ano" && !years.has(Number(value))) {
      throw new CatalogError(
        `summaries.json: scope "${summary.scope}" não tem leitura no ano ${value}`,
      );
    }
    if (kind === "pais" && !countryCodes.has(value)) {
      throw new CatalogError(
        `summaries.json: scope "${summary.scope}" aponta para país inexistente`,
      );
    }
  }
}

function splitScope(scope: string): [kind: string, value: string] {
  const idx = scope.indexOf(":");
  return [scope.slice(0, idx), scope.slice(idx + 1)];
}

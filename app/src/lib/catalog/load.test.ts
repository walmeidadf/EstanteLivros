import { test } from "node:test";
import assert from "node:assert/strict";
import { checkInvariants, CatalogError, type RawCatalog } from "./load.ts";
import type { Author, Work, Reading } from "./schema.ts";

function author(slug: string, extra: Partial<Author> = {}): Author {
  return {
    slug,
    name: slug,
    aliases: [],
    country: null,
    countrySource: null,
    languages: ["português"],
    primaryLanguage: "português",
    wikidata: null,
    photo: null,
    references: [],
    ...extra,
  };
}

function work(slug: string, authors: string[], extra: Partial<Work> = {}): Work {
  return {
    slug,
    title: slug,
    originalTitle: null,
    originalTitleRomanized: null,
    authors,
    language: "português",
    firstPublished: null,
    type: "romance",
    genres: [],
    themes: [],
    edition: {
      title: null,
      language: null,
      publisher: null,
      year: null,
      isbn13: null,
      isbn10: null,
      format: null,
      match: "representative",
    },
    cover: null,
    catalogerNote: null,
    confidence: "high",
    references: [],
    legacyId: null,
    audit: { validationStatus: null, sourceConflicts: null, validatedAt: null },
    ...extra,
  };
}

function reading(sequence: number, w: string, year: number | null): Reading {
  return {
    sequence,
    year,
    work: w,
    reread: false,
    originalEntry: `entry ${sequence}`,
    notes: null,
  };
}

function baseCatalog(): RawCatalog {
  return {
    works: [work("obra-a", ["autora-a"])],
    authors: [author("autora-a")],
    readings: [reading(1, "obra-a", 2020)],
    summaries: [],
    vocabularies: {
      languages: ["português"],
      workTypes: ["romance"],
      genres: [],
      themes: [],
      countries: [{ code: "BR", name: "Brasil", languages: ["português"] }],
    },
  };
}

test("catálogo coerente passa nas invariantes", () => {
  assert.doesNotThrow(() => checkInvariants(baseCatalog()));
});

test("obra apontando para autoria inexistente lança", () => {
  const c = baseCatalog();
  c.works = [work("obra-a", ["fantasma"])];
  assert.throws(() => checkInvariants(c), CatalogError);
});

test("leitura apontando para obra inexistente lança", () => {
  const c = baseCatalog();
  c.readings = [reading(1, "obra-fantasma", 2020)];
  assert.throws(() => checkInvariants(c), CatalogError);
});

test("primaryLanguage fora de languages lança", () => {
  const c = baseCatalog();
  c.authors = [
    author("autora-a", { languages: ["inglês"], primaryLanguage: "português" }),
  ];
  assert.throws(() => checkInvariants(c), CatalogError);
});

test("summary com scope de autoria órfã lança", () => {
  const c = baseCatalog();
  c.summaries = [summaryFor("autoria:fantasma")];
  assert.throws(() => checkInvariants(c), CatalogError);
});

test("summary de ano sem leitura naquele ano lança", () => {
  const c = baseCatalog();
  c.summaries = [summaryFor("ano:1999")];
  assert.throws(() => checkInvariants(c), CatalogError);
});

test("summary de país inexistente lança", () => {
  const c = baseCatalog();
  c.summaries = [summaryFor("pais:ZZ")];
  assert.throws(() => checkInvariants(c), CatalogError);
});

test("summary de autoria/ano/país válidos passa", () => {
  const c = baseCatalog();
  c.summaries = [
    summaryFor("autoria:autora-a"),
    summaryFor("ano:2020"),
    summaryFor("pais:BR"),
  ];
  assert.doesNotThrow(() => checkInvariants(c));
});

function summaryFor(scope: string) {
  return {
    scope,
    text: "…",
    approved: true,
    updatedAt: "2026-11-03",
    source: null,
    sourceUrl: null,
    sourceLanguage: null,
    model: null,
    promptVersion: null,
    editedBy: null,
  };
}

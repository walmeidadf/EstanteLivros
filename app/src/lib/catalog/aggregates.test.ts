import { test } from "node:test";
import assert from "node:assert/strict";
import { buildModel } from "./model.ts";
import { buildAggregates } from "./aggregates.ts";
import type { RawCatalog } from "./load.ts";
import type { Author, Work, Reading } from "./schema.ts";

function author(slug: string, extra: Partial<Author> = {}): Author {
  return {
    slug, name: slug, aliases: [], country: "BR", countrySource: "override",
    languages: ["português"], primaryLanguage: "português", wikidata: null,
    photo: null, references: [], ...extra,
  };
}

function work(slug: string, authors: string[], extra: Partial<Work> = {}): Work {
  return {
    slug, title: slug, originalTitle: null, originalTitleRomanized: null,
    authors, language: "português", firstPublished: null, type: "romance",
    genres: [], themes: [],
    edition: { title: null, language: null, publisher: null, year: null, isbn13: null, isbn10: null, format: null, match: "representative" },
    cover: null, catalogerNote: null, confidence: "high", references: [],
    legacyId: null, audit: { validationStatus: null, sourceConflicts: null, validatedAt: null },
    ...extra,
  };
}

function reading(sequence: number, w: string, year: number | null, reread = false): Reading {
  return { sequence, year, work: w, reread, originalEntry: `e${sequence}`, notes: null };
}

function catalog(parts: Partial<RawCatalog>): RawCatalog {
  return {
    works: [], authors: [], readings: [], summaries: [],
    vocabularies: {
      languages: ["português", "coreano", "inglês"], workTypes: ["romance"],
      genres: [], themes: [],
      countries: [
        { code: "BR", name: "Brasil", languages: ["português"] },
        { code: "KR", name: "Coreia do Sul", languages: ["coreano"] },
      ],
    },
    ...parts,
  };
}

test("releitura conta no ano de cada leitura", () => {
  const agg = buildAggregates(buildModel(catalog({
    authors: [author("a")],
    works: [work("obra", ["a"])],
    readings: [reading(1, "obra", 2020), reading(2, "obra", 2025, true)],
  })));
  assert.equal(agg.readingsByYear.get(2020), 1);
  assert.equal(agg.readingsByYear.get(2025), 1);
});

test("leituras sem ano somam em undatedCount", () => {
  const agg = buildAggregates(buildModel(catalog({
    authors: [author("a")],
    works: [work("o1", ["a"]), work("o2", ["a"])],
    readings: [reading(1, "o1", null), reading(2, "o2", null), reading(3, "o2", 2020)],
  })));
  assert.equal(agg.undatedCount, 2);
  assert.equal(agg.readingsByYear.get(2020), 1);
});

test("obras por idioma", () => {
  const agg = buildAggregates(buildModel(catalog({
    authors: [author("a"), author("k", { languages: ["coreano"], primaryLanguage: "coreano", country: "KR" })],
    works: [
      work("o1", ["a"], { language: "português" }),
      work("o2", ["a"], { language: "português" }),
      work("o3", ["k"], { language: "coreano" }),
    ],
    readings: [],
  })));
  assert.equal(agg.worksByLanguage.get("português"), 2);
  assert.equal(agg.worksByLanguage.get("coreano"), 1);
  // ordenado por quantidade decrescente
  assert.equal(agg.worksByLanguageDesc[0]!.key, "português");
  assert.equal(agg.worksByLanguageDesc[0]!.count, 2);
});

test("obra com autorias de países diferentes conta em cada país", () => {
  const agg = buildAggregates(buildModel(catalog({
    authors: [
      author("br", { country: "BR" }),
      author("kr", { country: "KR", languages: ["coreano"], primaryLanguage: "coreano" }),
    ],
    works: [work("obra", ["br", "kr"])],
    readings: [],
  })));
  assert.equal(agg.worksByCountry.get("BR"), 1);
  assert.equal(agg.worksByCountry.get("KR"), 1);
});

test("leituras por autoria e tema", () => {
  const agg = buildAggregates(buildModel(catalog({
    authors: [author("a")],
    works: [work("o1", ["a"], { themes: ["memória", "família"] }), work("o2", ["a"], { themes: ["memória"] })],
    readings: [reading(1, "o1", 2020), reading(2, "o2", 2021), reading(3, "o2", 2022, true)],
  })));
  // o1: 1 leitura, o2: 2 leituras → autoria a: 3
  assert.equal(agg.readingsByAuthor.get("a"), 3);
  assert.equal(agg.worksByTheme.get("memória"), 2);
  assert.equal(agg.worksByTheme.get("família"), 1);
  assert.equal(agg.worksByThemeDesc[0]!.key, "memória");
});

test("ordenação decrescente com empate estável", () => {
  const agg = buildAggregates(buildModel(catalog({
    authors: [author("a")],
    works: [
      work("o1", ["a"], { themes: ["b"] }),
      work("o2", ["a"], { themes: ["a"] }),
    ],
    readings: [],
  })));
  // ambos contam 1; empate resolve por chave em pt-BR (a antes de b)
  assert.deepEqual(agg.worksByThemeDesc.map((c) => c.key), ["a", "b"]);
});

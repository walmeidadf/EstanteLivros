import { test } from "node:test";
import assert from "node:assert/strict";
import { buildModel } from "./catalog/model.ts";
import { buildAggregates } from "./catalog/aggregates.ts";
import type { RawCatalog } from "./catalog/load.ts";
import type { Catalog } from "./catalog/index.ts";
import type { Author, Work, Reading } from "./catalog/schema.ts";
import { allWorkAndAuthorLinks, orphanLinks } from "./route-integrity.ts";

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
    authors, language: "português", firstPublished: 2010, type: "romance",
    genres: [], themes: ["memória"],
    edition: { title: null, language: null, publisher: null, year: null, isbn13: null, isbn10: null, format: null, match: "representative" },
    cover: null, catalogerNote: null, confidence: "high", references: [],
    legacyId: null, audit: { validationStatus: null, sourceConflicts: null, validatedAt: null },
    ...extra,
  };
}

function reading(sequence: number, w: string, year: number | null = 2020): Reading {
  return { sequence, year, work: w, reread: false, originalEntry: `e${sequence}`, notes: null };
}

function catalog(parts: Partial<RawCatalog>): Catalog {
  const model = buildModel({
    works: [], authors: [], readings: [], summaries: [],
    vocabularies: {
      languages: ["português"], workTypes: ["romance"], genres: [], themes: [],
      countries: [{ code: "BR", name: "Brasil", languages: ["português"] }],
    },
    ...parts,
  });
  return { ...model, aggregates: buildAggregates(model) };
}

function sample(): Catalog {
  return catalog({
    authors: [author("a1"), author("a2")],
    works: [
      work("obra-1", ["a1"]),
      work("obra-2", ["a2"]),
      work("obra-sem-data", ["a1"]),
    ],
    readings: [
      reading(1, "obra-1", 2020),
      reading(2, "obra-1", 2024), // releitura
      reading(3, "obra-2", 2021),
      reading(9, "obra-sem-data", null),
    ],
  });
}

test("todos os links de obra/autoria apontam para páginas existentes", () => {
  const c = sample();
  assert.deepEqual(orphanLinks(c), []);
});

test("coleta links das várias telas (não vazio, com origem)", () => {
  const links = allWorkAndAuthorLinks(sample());
  assert.ok(links.length > 0);
  // cobre busca, grade de ano, sem-data e autorias
  const froms = new Set(links.map((l) => l.from));
  assert.ok([...froms].some((f) => f === "busca"));
  assert.ok([...froms].some((f) => f.startsWith("ano/")));
  assert.ok([...froms].some((f) => f === "ano/sem-data"));
});

test("um link órfão é detectado e nomeia a origem", () => {
  // Catálogo íntegro; injetamos um link órfão manualmente para provar o filtro.
  const c = sample();
  // remove a obra do mapa para simular página faltante
  c.worksBySlug.delete("obra-2");
  const orphans = orphanLinks(c);
  assert.ok(orphans.length > 0);
  assert.ok(orphans.every((o) => o.href.includes("obra-2")));
  assert.ok(orphans.some((o) => o.from === "busca"));
});

import { test } from "node:test";
import assert from "node:assert/strict";
import { buildModel } from "./model.ts";
import { OTHER_LANGUAGE_COLOR } from "../language-color.ts";
import type { RawCatalog } from "./load.ts";
import type { Author, Summary, Work } from "./schema.ts";

function author(slug: string, extra: Partial<Author> = {}): Author {
  return {
    slug,
    name: slug,
    aliases: [],
    country: "BR",
    countrySource: "override",
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

function summary(scope: string, approved: boolean, text: string): Summary {
  return {
    scope,
    text,
    approved,
    updatedAt: "2026-11-03",
    source: null,
    sourceUrl: null,
    sourceLanguage: null,
    model: null,
    promptVersion: null,
    editedBy: null,
  };
}

function catalog(parts: Partial<RawCatalog>): RawCatalog {
  return {
    works: [],
    authors: [],
    readings: [],
    summaries: [],
    vocabularies: {
      languages: ["português", "coreano"],
      workTypes: ["romance"],
      genres: [],
      themes: [],
      countries: [
        { code: "BR", name: "Brasil", languages: ["português"] },
        { code: "KR", name: "Coreia do Sul", languages: ["coreano"] },
      ],
    },
    ...parts,
  };
}

test("releitura: uma obra com duas leituras, conta nos dois anos", () => {
  const model = buildModel(
    catalog({
      authors: [author("a")],
      works: [work("obra", ["a"])],
      readings: [
        { sequence: 10, year: 2020, work: "obra", reread: false, originalEntry: "e1", notes: null },
        { sequence: 40, year: 2025, work: "obra", reread: true, originalEntry: "e2", notes: null },
      ],
    }),
  );
  assert.equal(model.works.length, 1, "não duplica a obra");
  const w = model.works[0]!;
  assert.equal(w.readings.length, 2);
  assert.equal(w.reread, true);
  assert.deepEqual(
    w.readings.map((r) => r.year),
    [2020, 2025],
  );
});

test("leitura sem ano vira 'sem data' e guarda a sequence", () => {
  const model = buildModel(
    catalog({
      authors: [author("a")],
      works: [work("obra", ["a"])],
      readings: [
        { sequence: 7, year: null, work: "obra", reread: false, originalEntry: "e", notes: null },
      ],
    }),
  );
  const r = model.works[0]!.readings[0]!;
  assert.equal(r.undated, true);
  assert.equal(r.year, null);
  assert.equal(r.sequence, 7);
});

test("bio aprovada aparece; não aprovada vira null", () => {
  const model = buildModel(
    catalog({
      authors: [author("com-bio"), author("sem-bio"), author("bio-pendente")],
      works: [],
      summaries: [
        summary("autoria:com-bio", true, "bio da autora"),
        summary("autoria:bio-pendente", false, "ainda em revisão"),
      ],
    }),
  );
  const byslug = model.authorsBySlug;
  assert.equal(byslug.get("com-bio")!.bio, "bio da autora");
  assert.equal(byslug.get("sem-bio")!.bio, null);
  assert.equal(byslug.get("bio-pendente")!.bio, null);
});

test("país da obra vem das autorias (uma por país)", () => {
  const model = buildModel(
    catalog({
      authors: [
        author("br", { country: "BR" }),
        author("kr", { country: "KR", languages: ["coreano"], primaryLanguage: "coreano" }),
      ],
      works: [work("obra", ["br", "kr"])],
      readings: [],
    }),
  );
  assert.deepEqual(model.works[0]!.countries.sort(), ["BR", "KR"]);
});

test("idioma sem cor própria cai em 'outros'", () => {
  const model = buildModel(
    catalog({
      authors: [
        author("a", { languages: ["catalão"], primaryLanguage: "catalão" }),
      ],
      works: [work("obra", ["a"], { language: "catalão" })],
      readings: [],
    }),
  );
  assert.deepEqual(model.works[0]!.color, OTHER_LANGUAGE_COLOR);
});

test("back-reference: a autoria conhece suas obras", () => {
  const model = buildModel(
    catalog({
      authors: [author("a")],
      works: [work("obra-1", ["a"]), work("obra-2", ["a"])],
      readings: [],
    }),
  );
  assert.deepEqual(
    model.authorsBySlug.get("a")!.works.map((w) => w.slug).sort(),
    ["obra-1", "obra-2"],
  );
});

test("countryName é resolvido pelo vocabulário", () => {
  const model = buildModel(
    catalog({ authors: [author("a", { country: "BR" })] }),
  );
  assert.equal(model.authorsBySlug.get("a")!.countryName, "Brasil");
});

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

test("approvedSummaryByScope: ano aprovado entra, não-aprovado fica fora", () => {
  const model = buildModel(
    catalog({
      authors: [author("a")],
      works: [work("obra", ["a"])],
      readings: [
        { sequence: 1, year: 2024, work: "obra", reread: false, originalEntry: "e1", notes: null },
        { sequence: 2, year: 2025, work: "obra", reread: false, originalEntry: "e2", notes: null },
      ],
      summaries: [
        summary("ano:2024", true, "o ano das estreias"),
        summary("ano:2025", false, "rascunho não revisado"),
      ],
    }),
  );
  assert.equal(model.approvedSummaryByScope.get("ano:2024"), "o ano das estreias");
  assert.equal(model.approvedSummaryByScope.get("ano:2025"), undefined);
});

test("approvedSummaryByScope inclui a bio de autoria; a bio segue intacta", () => {
  const model = buildModel(
    catalog({
      authors: [author("com-bio"), author("bio-pendente")],
      works: [],
      summaries: [
        summary("autoria:com-bio", true, "bio da autora"),
        summary("autoria:bio-pendente", false, "ainda em revisão"),
      ],
    }),
  );
  // mesma fonte: o mapa e o campo bio batem para o aprovado
  assert.equal(model.approvedSummaryByScope.get("autoria:com-bio"), "bio da autora");
  assert.equal(model.authorsBySlug.get("com-bio")!.bio, "bio da autora");
  // o não aprovado fica de fora dos dois
  assert.equal(model.approvedSummaryByScope.get("autoria:bio-pendente"), undefined);
  assert.equal(model.authorsBySlug.get("bio-pendente")!.bio, null);
});

test("originalEntry chega à leitura", () => {
  const model = buildModel(
    catalog({
      authors: [author("a")],
      works: [work("obra", ["a"])],
      readings: [
        {
          sequence: 3,
          year: 2021,
          work: "obra",
          reread: false,
          originalEntry: "47. A Vegetariana - Han Kang",
          notes: null,
        },
      ],
    }),
  );
  assert.equal(
    model.works[0]!.readings[0]!.originalEntry,
    "47. A Vegetariana - Han Kang",
  );
});

test("crédito da foto: presente quando há foto, campos nulos preservados", () => {
  const model = buildModel(
    catalog({
      authors: [
        author("com-foto", {
          photo: {
            file: "authors/com-foto.jpg",
            license: "CC BY-SA 4.0",
            author: "Fulano",
            sourceUrl: "https://commons.wikimedia.org/x",
            source: "commons",
          },
        }),
        author("sem-foto"),
        author("foto-sem-credito", {
          photo: {
            file: "authors/foto-sem-credito.jpg",
            license: null,
            author: null,
            sourceUrl: "https://commons.wikimedia.org/y",
            source: "commons",
          },
        }),
      ],
    }),
  );
  const comFoto = model.authorsBySlug.get("com-foto")!.photo!;
  assert.equal(comFoto.file, "authors/com-foto.jpg");
  assert.equal(comFoto.author, "Fulano");
  assert.equal(comFoto.license, "CC BY-SA 4.0");
  assert.equal(comFoto.sourceUrl, "https://commons.wikimedia.org/x");
  assert.equal(model.authorsBySlug.get("sem-foto")!.photo, null);
  const semCredito = model.authorsBySlug.get("foto-sem-credito")!.photo!;
  assert.equal(semCredito.author, null);
  assert.equal(semCredito.license, null);
  assert.equal(semCredito.sourceUrl, "https://commons.wikimedia.org/y");
});

test("bioSource: vem do summary aprovado; null sem bio; link só com url", () => {
  const withSource = summary("autoria:com-fonte", true, "bio");
  withSource.source = "Wikipédia (pt)";
  withSource.sourceUrl = "https://pt.wikipedia.org/wiki/X";
  const noUrl = summary("autoria:sem-url", true, "bio");
  noUrl.source = "Enciclopédia";
  noUrl.sourceUrl = null;
  const model = buildModel(
    catalog({
      authors: [
        author("com-fonte"),
        author("sem-url"),
        author("sem-bio"),
        author("bio-pendente"),
      ],
      summaries: [
        withSource,
        noUrl,
        (() => {
          const s = summary("autoria:bio-pendente", false, "rascunho");
          s.source = "Wikipédia (pt)";
          return s;
        })(),
      ],
    }),
  );
  const byslug = model.authorsBySlug;
  assert.deepEqual(byslug.get("com-fonte")!.bioSource, {
    label: "Wikipédia (pt)",
    url: "https://pt.wikipedia.org/wiki/X",
  });
  assert.deepEqual(byslug.get("sem-url")!.bioSource, {
    label: "Enciclopédia",
    url: null,
  });
  // bio aprovada mas sem campo source → bioSource null
  assert.equal(byslug.get("sem-bio")!.bioSource, null);
  // bio não aprovada → sem bio e sem fonte, mesmo com source no JSON
  assert.equal(byslug.get("bio-pendente")!.bio, null);
  assert.equal(byslug.get("bio-pendente")!.bioSource, null);
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

test("capa: três estados chegam à WorkView; a sourceUrl segue só como proveniência", () => {
  const url = "https://example.org/capa.jpg";
  const model = buildModel(
    catalog({
      authors: [author("a")],
      works: [
        work("sem-capa", ["a"]),
        work("nao-revisada", ["a"], { cover: { sourceUrl: url, source: "literal" } }),
        work("real", ["a"], {
          cover: { sourceUrl: url, source: "openlibrary", file: "covers/real.jpg", focus: "bottom" },
        }),
        work("tipografica", ["a"], {
          cover: { sourceUrl: url, source: "literal", display: "typographic" },
        }),
      ],
      readings: [],
    }),
  );
  const view = (slug: string) => model.worksBySlug.get(slug)!;
  assert.deepEqual(
    [view("sem-capa").coverFile, view("sem-capa").coverFocus, view("sem-capa").coverDisplay],
    [null, "center", null],
  );
  assert.equal(view("nao-revisada").coverFile, null);
  assert.equal(view("nao-revisada").coverSourceUrl, url);
  assert.deepEqual(
    [view("real").coverFile, view("real").coverFocus, view("real").coverDisplay],
    ["covers/real.jpg", "bottom", null],
  );
  assert.equal(view("tipografica").coverDisplay, "typographic");
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

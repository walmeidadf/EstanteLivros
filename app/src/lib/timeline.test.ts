import { test } from "node:test";
import assert from "node:assert/strict";
import { buildModel } from "./catalog/model.ts";
import { buildAggregates } from "./catalog/aggregates.ts";
import type { RawCatalog } from "./catalog/load.ts";
import type { Catalog } from "./catalog/index.ts";
import type { Author, Work, Reading, Summary } from "./catalog/schema.ts";
import { buildTimeline, buildYear, buildUndated } from "./timeline.ts";

/* ---- fixtures (mesmo molde dos testes da camada de dados e do home) ---- */

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

function summary(scope: string, approved: boolean, text: string): Summary {
  return {
    scope, text, approved, updatedAt: "2026-11-03", source: null, sourceUrl: null,
    sourceLanguage: null, model: null, promptVersion: null, editedBy: null,
  };
}

function rawCatalog(parts: Partial<RawCatalog>): RawCatalog {
  return {
    works: [], authors: [], readings: [], summaries: [],
    vocabularies: {
      languages: ["português", "coreano"], workTypes: ["romance"], genres: [], themes: [],
      countries: [
        { code: "BR", name: "Brasil", languages: ["português"] },
        { code: "KR", name: "Coreia do Sul", languages: ["coreano"] },
      ],
    },
    ...parts,
  };
}

function catalog(parts: Partial<RawCatalog>): Catalog {
  const model = buildModel(rawCatalog(parts));
  return { ...model, aggregates: buildAggregates(model) };
}

/* ---- faixas: ordem cronológica decrescente ---- */

test("faixas em ordem de ANO decrescente (não por quantidade)", () => {
  // 2019 tem mais leituras que 2024, mas 2024 vem primeiro (mais recente).
  const bands = buildTimeline(catalog({
    authors: [author("a")],
    works: [work("o1", ["a"]), work("o2", ["a"]), work("o3", ["a"])],
    readings: [
      reading(1, "o1", 2019), reading(2, "o2", 2019), reading(3, "o3", 2024),
    ],
  }));
  assert.deepEqual(bands.map((b) => b.year), [2024, 2019]);
  assert.equal(bands[0]!.href, "/ano/2024");
  assert.equal(bands.find((b) => b.year === 2019)!.count, 2);
});

test("faixa: uma lombada por LEITURA na ordem do caderno (sequence)", () => {
  const bands = buildTimeline(catalog({
    authors: [author("br"), author("kr", { country: "KR", languages: ["coreano"], primaryLanguage: "coreano" })],
    works: [work("tarde", ["br"]), work("cedo", ["kr"], { language: "coreano" })],
    readings: [reading(9, "tarde", 2024), reading(3, "cedo", 2024)],
  }));
  const band = bands[0]!;
  // "cedo" (sequence 3, coreano) antes de "tarde" (sequence 9, português)
  assert.deepEqual(band.spines.map((s) => s.language), ["coreano", "português"]);
  assert.equal(band.count, 2);
});

test("faixa: obra relida no mesmo ano gera DUAS lombadas (por leitura)", () => {
  const bands = buildTimeline(catalog({
    authors: [author("a")],
    works: [work("o", ["a"])],
    readings: [reading(1, "o", 2024), reading(2, "o", 2024, true)],
  }));
  assert.equal(bands[0]!.spines.length, 2);
  assert.equal(bands[0]!.count, 2);
});

/* ---- notas automáticas ---- */

test("nota 'em andamento' no ano atual, com prioridade sobre 'mais cheio'", () => {
  // 2024 é o ano atual E o mais cheio: a nota de andamento ganha.
  const bands = buildTimeline(catalog({
    authors: [author("a")],
    works: [work("o1", ["a"]), work("o2", ["a"]), work("o3", ["a"])],
    readings: [
      reading(1, "o1", 2019),
      reading(2, "o2", 2024), reading(3, "o3", 2024),
    ],
  }));
  const b2024 = bands.find((b) => b.year === 2024)!;
  assert.ok(b2024.notes.includes("em andamento"));
  assert.ok(!b2024.notes.includes("o ano mais cheio da estante"));
});

test("'o ano mais cheio' vai para o ano de máximo que não é o atual", () => {
  // 2020 tem 3 leituras (máximo), 2024 (atual) tem 1.
  const bands = buildTimeline(catalog({
    authors: [author("a")],
    works: [work("o1", ["a"]), work("o2", ["a"]), work("o3", ["a"]), work("o4", ["a"])],
    readings: [
      reading(1, "o1", 2020), reading(2, "o2", 2020), reading(3, "o3", 2020),
      reading(4, "o4", 2024),
    ],
  }));
  const b2020 = bands.find((b) => b.year === 2020)!;
  const b2024 = bands.find((b) => b.year === 2024)!;
  assert.ok(b2020.notes.includes("o ano mais cheio da estante"));
  assert.ok(b2024.notes.includes("em andamento"));
});

test("'mais cheio' com empate escolhe o ano mais recente", () => {
  // 2018 e 2020 têm 2 leituras cada; 2020 (mais recente) leva a nota.
  // ano atual (2022) tem só 1, para não roubar a nota.
  const bands = buildTimeline(catalog({
    authors: [author("a")],
    works: ["o1","o2","o3","o4","o5"].map((s) => work(s, ["a"])),
    readings: [
      reading(1, "o1", 2018), reading(2, "o2", 2018),
      reading(3, "o3", 2020), reading(4, "o4", 2020),
      reading(5, "o5", 2022),
    ],
  }));
  assert.ok(bands.find((b) => b.year === 2020)!.notes.includes("o ano mais cheio da estante"));
  assert.ok(!bands.find((b) => b.year === 2018)!.notes.includes("o ano mais cheio da estante"));
});

test("nota complementar de releituras, no plural certo, coexiste com a principal", () => {
  // 2024 é o atual (andamento) e tem 1 releitura → duas notas.
  const bands = buildTimeline(catalog({
    authors: [author("a")],
    works: [work("o", ["a"]), work("x", ["a"])],
    readings: [
      reading(1, "o", 2019),
      reading(2, "o", 2024, true), reading(3, "x", 2024),
    ],
  }));
  const b2024 = bands.find((b) => b.year === 2024)!;
  assert.deepEqual(b2024.notes, ["em andamento", "1 releitura"]);
});

test("ano sem nada notável fica sem nota", () => {
  const bands = buildTimeline(catalog({
    authors: [author("a")],
    works: [work("o1", ["a"]), work("o2", ["a"]), work("o3", ["a"])],
    readings: [
      // 2020 não é atual, não é o mais cheio (2024 tem 2), sem releitura
      reading(1, "o1", 2020),
      reading(2, "o2", 2024), reading(3, "o3", 2024),
    ],
  }));
  assert.deepEqual(bands.find((b) => b.year === 2020)!.notes, []);
});

/* ---- tela Ano: big numbers, mix, vizinhos, resumo ---- */

test("buildYear: big numbers por leitura (leituras, idiomas, autorias, releituras)", () => {
  const year = buildYear(
    catalog({
      authors: [
        author("br"),
        author("kr", { country: "KR", languages: ["coreano"], primaryLanguage: "coreano" }),
      ],
      works: [
        work("p1", ["br"]),
        work("p2", ["br"]),
        work("k1", ["kr"], { language: "coreano" }),
      ],
      readings: [
        reading(1, "p1", 2024), reading(2, "p2", 2024),
        reading(3, "p1", 2024, true), // releitura no mesmo ano
        reading(4, "k1", 2024),
      ],
    }),
    2024,
  );
  assert.equal(year.readings, 4);        // uma peça por leitura
  assert.equal(year.languages, 2);       // português + coreano
  assert.equal(year.authors, 2);         // br + kr
  assert.equal(year.rereads, 1);
  // mix: português 3 (75%), coreano 1 (25%)
  assert.deepEqual(year.mix.map((m) => [m.language, m.count, m.pct]), [
    ["português", 3, 75],
    ["coreano", 1, 25],
  ]);
  assert.equal(year.items.length, 4);
  assert.equal(year.items[0]!.href, "/obra/p1");
});

test("buildYear: vizinhos saltam pelos anos existentes e são null nos extremos", () => {
  const cat = catalog({
    authors: [author("a")],
    works: ["o1","o2","o3"].map((s) => work(s, ["a"])),
    readings: [reading(1, "o1", 2015), reading(2, "o2", 2019), reading(3, "o3", 2024)],
  });
  // 2019 no meio: anterior 2015, próximo 2024 (pula os buracos)
  const mid = buildYear(cat, 2019);
  assert.equal(mid.prev, 2015);
  assert.equal(mid.next, 2024);
  // 2015 é o mais antigo: sem anterior
  assert.equal(buildYear(cat, 2015).prev, null);
  assert.equal(buildYear(cat, 2015).next, 2019);
  // 2024 é o mais recente: sem próximo
  assert.equal(buildYear(cat, 2024).next, null);
  assert.equal(buildYear(cat, 2024).prev, 2019);
});

test("buildYear: resumo só quando há summary aprovado de scope ano:{ano}", () => {
  const parts: Partial<RawCatalog> = {
    authors: [author("a")],
    works: [work("o1", ["a"]), work("o2", ["a"])],
    readings: [reading(1, "o1", 2024), reading(2, "o2", 2025)],
    summaries: [
      summary("ano:2024", true, "o ano das estreias"),
      summary("ano:2025", false, "rascunho"),
    ],
  };
  assert.equal(buildYear(catalog(parts), 2024).summary, "o ano das estreias");
  assert.equal(buildYear(catalog(parts), 2025).summary, null);
});

/* ---- sem data ---- */

test("buildUndated: leituras sem ano pela sequence, com 'nº N da lista'", () => {
  const undated = buildUndated(catalog({
    authors: [author("a")],
    works: [work("tarde", ["a"]), work("cedo", ["a"]), work("comano", ["a"])],
    readings: [
      reading(12, "tarde", null),
      reading(3, "cedo", null),
      reading(5, "comano", 2020), // tem ano: não entra
    ],
  }));
  assert.ok(undated);
  assert.deepEqual(undated!.items.map((i) => i.work.slug), ["cedo", "tarde"]);
  assert.equal(undated!.items[0]!.undatedLabel, "nº 3 da lista");
  assert.equal(undated!.items[1]!.undatedLabel, "nº 12 da lista");
  assert.equal(undated!.items[0]!.href, "/obra/cedo");
});

test("buildUndated: null quando toda leitura tem ano", () => {
  const undated = buildUndated(catalog({
    authors: [author("a")],
    works: [work("o", ["a"])],
    readings: [reading(1, "o", 2020)],
  }));
  assert.equal(undated, null);
});

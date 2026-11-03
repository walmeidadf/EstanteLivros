import { test } from "node:test";
import assert from "node:assert/strict";
import { buildModel } from "./catalog/model.ts";
import { buildAggregates } from "./catalog/aggregates.ts";
import type { RawCatalog } from "./catalog/load.ts";
import type { Catalog } from "./catalog/index.ts";
import type { Author, Work, Reading } from "./catalog/schema.ts";
import {
  buildHome,
  slugifyTheme,
  THEME_RAIL_COUNT,
  RECURRING_MIN_READINGS,
} from "./home.ts";

/* ---- fixtures (mesmo molde dos testes da camada de dados) ---- */

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

function rawCatalog(parts: Partial<RawCatalog>): RawCatalog {
  return {
    works: [], authors: [], readings: [], summaries: [],
    vocabularies: {
      languages: ["português"], workTypes: ["romance"], genres: [], themes: [],
      countries: [{ code: "BR", name: "Brasil", languages: ["português"] }],
    },
    ...parts,
  };
}

function catalog(parts: Partial<RawCatalog>): Catalog {
  const model = buildModel(rawCatalog(parts));
  return { ...model, aggregates: buildAggregates(model) };
}

/* ---- ano atual ---- */

test("ano atual é o maior ano COM leitura, não o relógio", () => {
  const home = buildHome(catalog({
    authors: [author("a")],
    works: [work("o1", ["a"]), work("o2", ["a"]), work("o3", ["a"])],
    readings: [reading(1, "o1", 2019), reading(2, "o2", 2024), reading(3, "o3", null)],
  }));
  assert.equal(home.currentYearValue, 2024);
  assert.equal(home.currentYear?.title, "Em 2024");
  assert.equal(home.currentYear?.href, "/ano/2024");
});

test("Em {ano}: só obras do ano, na ordem do caderno (sequence)", () => {
  const home = buildHome(catalog({
    authors: [author("a")],
    works: [work("tarde", ["a"]), work("cedo", ["a"]), work("fora", ["a"])],
    readings: [
      reading(9, "tarde", 2024),
      reading(3, "cedo", 2024),
      reading(1, "fora", 2019),
    ],
  }));
  assert.deepEqual(home.currentYear?.items.map((i) => i.work.slug), ["cedo", "tarde"]);
  assert.equal(home.currentYear?.items[0]?.href, "/obra/cedo");
});

test("obra relida no mesmo ano aparece uma vez", () => {
  const home = buildHome(catalog({
    authors: [author("a")],
    works: [work("o", ["a"])],
    readings: [reading(1, "o", 2024), reading(2, "o", 2024, true)],
  }));
  assert.equal(home.currentYear?.items.length, 1);
  assert.equal(home.currentYear?.total, 1);
});

test("sem nenhuma leitura datada, Em {ano} é null", () => {
  const home = buildHome(catalog({
    authors: [author("a")],
    works: [work("o", ["a"])],
    readings: [reading(1, "o", null)],
  }));
  assert.equal(home.currentYearValue, null);
  assert.equal(home.currentYear, null);
});

/* ---- quem sempre volta ---- */

test("quem sempre volta: só autorias com 3+ leituras, decrescente", () => {
  const home = buildHome(catalog({
    authors: [author("tres"), author("quatro"), author("duas")],
    works: [
      work("t1", ["tres"]), work("t2", ["tres"]), work("t3", ["tres"]),
      work("q1", ["quatro"]), work("q2", ["quatro"]), work("q3", ["quatro"]), work("q4", ["quatro"]),
      work("d1", ["duas"]), work("d2", ["duas"]),
    ],
    readings: [
      reading(1, "t1", 2020), reading(2, "t2", 2020), reading(3, "t3", 2020),
      reading(4, "q1", 2020), reading(5, "q2", 2020), reading(6, "q3", 2020), reading(7, "q4", 2020),
      reading(8, "d1", 2020), reading(9, "d2", 2020),
    ],
  }));
  assert.equal(RECURRING_MIN_READINGS, 3);
  assert.deepEqual(home.recurringAuthors?.map((p) => p.author.slug), ["quatro", "tres"]);
  assert.equal(home.recurringAuthors?.[0]?.readings, 4);
  assert.equal(home.recurringAuthors?.[0]?.href, "/autoria/quatro");
});

test("quem sempre volta: null quando ninguém atinge o corte", () => {
  const home = buildHome(catalog({
    authors: [author("a")],
    works: [work("o1", ["a"]), work("o2", ["a"])],
    readings: [reading(1, "o1", 2020), reading(2, "o2", 2020)],
  }));
  assert.equal(home.recurringAuthors, null);
});

/* ---- temas ---- */

test("temas: no máximo 4, na ordem de frequência dos agregados", () => {
  const home = buildHome(catalog({
    authors: [author("a")],
    works: [
      work("o1", ["a"], { themes: ["memória", "família", "corpo", "exílio", "fé"] }),
      work("o2", ["a"], { themes: ["memória", "família", "corpo", "exílio"] }),
      work("o3", ["a"], { themes: ["memória", "família", "corpo"] }),
      work("o4", ["a"], { themes: ["memória", "família"] }),
      work("o5", ["a"], { themes: ["memória"] }),
    ],
    readings: [],
  }));
  assert.equal(home.themeRails.length, THEME_RAIL_COUNT);
  assert.deepEqual(home.themeRails.map((r) => r.title), ["memória", "família", "corpo", "exílio"]);
  // o tema "memória" está em todas as 5 obras
  const memoria = home.themeRails[0]!;
  assert.equal(memoria.total, 5);
  assert.equal(memoria.href, "/tema/memoria");
});

test("temas: mostra quantos houver quando há menos de 4", () => {
  const home = buildHome(catalog({
    authors: [author("a")],
    works: [work("o1", ["a"], { themes: ["memória", "família"] })],
    readings: [],
  }));
  assert.equal(home.themeRails.length, 2);
});

/* ---- lidos duas vezes ---- */

test("lidos duas vezes: só releituras, uma peça por obra", () => {
  const home = buildHome(catalog({
    authors: [author("a")],
    works: [work("relido", ["a"]), work("uma-vez", ["a"])],
    readings: [
      reading(1, "relido", 2019), reading(2, "relido", 2024, true),
      reading(3, "uma-vez", 2020),
    ],
  }));
  assert.equal(home.rereads?.items.length, 1);
  assert.equal(home.rereads?.items[0]?.work.slug, "relido");
  assert.equal(home.rereads?.items[0]?.work.reread, true);
});

test("lidos duas vezes: null quando não há releitura", () => {
  const home = buildHome(catalog({
    authors: [author("a")],
    works: [work("o", ["a"])],
    readings: [reading(1, "o", 2020)],
  }));
  assert.equal(home.rereads, null);
});

/* ---- barras da linha do tempo ---- */

test("barras: só anos conhecidos, crescente, ano atual marcado", () => {
  const home = buildHome(catalog({
    authors: [author("a")],
    works: [work("o1", ["a"]), work("o2", ["a"]), work("o3", ["a"])],
    readings: [reading(1, "o1", 2024), reading(2, "o2", 2019), reading(3, "o3", null)],
  }));
  assert.deepEqual(home.yearBars.map((b) => b.year), [2019, 2024]);
  assert.equal(home.yearBars.find((b) => b.year === 2024)?.current, true);
  assert.equal(home.yearBars.find((b) => b.year === 2019)?.current, false);
});

/* ---- teto ---- */

test("railCap corta os itens mas preserva o total real", () => {
  const works = Array.from({ length: 25 }, (_, i) => work(`o${i}`, ["a"], { themes: ["memória"] }));
  const home = buildHome(
    catalog({ authors: [author("a")], works, readings: [] }),
    20,
  );
  const memoria = home.themeRails[0]!;
  assert.equal(memoria.items.length, 20);
  assert.equal(memoria.total, 25);
});

/* ---- slug de tema ---- */

test("slugifyTheme é tolerante a acento", () => {
  assert.equal(slugifyTheme("memória"), "memoria");
  assert.equal(slugifyTheme("relações família"), "relacoes-familia");
});

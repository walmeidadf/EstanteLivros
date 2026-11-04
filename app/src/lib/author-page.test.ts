import { test } from "node:test";
import assert from "node:assert/strict";
import { buildModel } from "./catalog/model.ts";
import { buildAggregates } from "./catalog/aggregates.ts";
import type { RawCatalog } from "./catalog/load.ts";
import type { Catalog } from "./catalog/index.ts";
import type { Author, Work, Reading, Summary } from "./catalog/schema.ts";
import { buildAuthorPage, authorRank } from "./author-page.ts";

/* ---- fixtures ---- */

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

function reading(sequence: number, w: string, year: number | null = 2020): Reading {
  return { sequence, year, work: w, reread: false, originalEntry: `e${sequence}`, notes: null };
}

function summary(scope: string, approved: boolean, text: string, extra: Partial<Summary> = {}): Summary {
  return {
    scope, text, approved, updatedAt: "2026-11-03", source: null, sourceUrl: null,
    sourceLanguage: null, model: null, promptVersion: null, editedBy: null, ...extra,
  };
}

const COUNTRIES = [
  { code: "BR", name: "Brasil", languages: ["português"] },
  { code: "IT", name: "Itália", languages: ["italiano"] },
];

function catalog(parts: Partial<RawCatalog>): Catalog {
  const model = buildModel({
    works: [], authors: [], readings: [], summaries: [],
    vocabularies: {
      languages: ["português", "italiano"],
      workTypes: ["romance"], genres: [], themes: [], countries: COUNTRIES,
    },
    ...parts,
  });
  return { ...model, aggregates: buildAggregates(model) };
}

/**
 * Catálogo com N autorias, cada uma com `counts[i]` leituras (uma obra por
 * leitura). A primeira autoria é a "alvo".
 */
function ranked(counts: number[]): Catalog {
  const authors: Author[] = [];
  const works: Work[] = [];
  const readings: Reading[] = [];
  let seq = 1;
  counts.forEach((n, ai) => {
    const a = `a${ai}`;
    authors.push(author(a));
    for (let i = 0; i < n; i++) {
      const w = `w${ai}-${i}`;
      works.push(work(w, [a]));
      readings.push(reading(seq++, w));
    }
  });
  return catalog({ authors, works, readings });
}

/* ---- ranking ---- */

test("authorRank: posição = 1 + autorias com mais leituras", () => {
  const c = ranked([8, 5, 5, 2]); // a0=8, a1=5, a2=5, a3=2
  assert.deepEqual(authorRank(c, "a0"), { position: 1, tied: false });
  assert.deepEqual(authorRank(c, "a1"), { position: 2, tied: true }); // empata com a2
  assert.deepEqual(authorRank(c, "a2"), { position: 2, tied: true });
  assert.deepEqual(authorRank(c, "a3"), { position: 4, tied: false });
});

test("authorRank: autoria sem leitura → null", () => {
  const c = catalog({ authors: [author("x")], works: [], readings: [] });
  assert.equal(authorRank(c, "x"), null);
});

/* ---- números e posição ---- */

test("números: posição mostrada só no top 10", () => {
  // 11 autorias com leituras decrescentes: a10 fica em 11º.
  const c = ranked([11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]);
  const top = buildAuthorPage(c, "a9").numbers; // a9 = 2 leituras → 10º
  assert.ok(top.some((n) => n.label === "posição na estante" && n.value === "10º"));

  const out = buildAuthorPage(c, "a10").numbers; // a10 = 1 leitura → 11º
  assert.equal(out.some((n) => n.label.startsWith("posição")), false);
});

test("números: empate marca '(empatada)'", () => {
  const c = ranked([5, 5, 1]);
  const n = buildAuthorPage(c, "a0").numbers;
  assert.ok(n.some((x) => x.label === "posição na estante (empatada)" && x.value === "1º"));
});

test("números: fora do top 10 entra a primeira leitura; omitida se sem ano", () => {
  const authors = Array.from({ length: 11 }, (_, i) => author(`a${i}`));
  const works: Work[] = [];
  const readings: Reading[] = [];
  let seq = 1;
  // a0..a9 com muitas leituras; a10 com 1 leitura em 2015
  for (let ai = 0; ai < 10; ai++) {
    for (let i = 0; i < 10 - ai + 2; i++) {
      const w = `w${ai}-${i}`; works.push(work(w, [`a${ai}`])); readings.push(reading(seq++, w));
    }
  }
  works.push(work("alvo", ["a10"])); readings.push(reading(seq++, "alvo", 2015));
  const c = catalog({ authors, works, readings });
  const n = buildAuthorPage(c, "a10").numbers;
  assert.ok(n.some((x) => x.label === "primeira leitura" && x.value === "2015"));

  // mesma autoria, mas leitura sem ano → primeira leitura omitida
  const authors2 = [author("a10"), ...Array.from({ length: 10 }, (_, i) => author(`b${i}`))];
  const works2: Work[] = [work("alvo2", ["a10"])];
  const readings2: Reading[] = [reading(1, "alvo2", null)];
  let s2 = 2;
  for (let ai = 0; ai < 10; ai++) for (let i = 0; i < 5; i++) { const w = `z${ai}-${i}`; works2.push(work(w, [`b${ai}`])); readings2.push(reading(s2++, w)); }
  const c2 = catalog({ authors: authors2, works: works2, readings: readings2 });
  const n2 = buildAuthorPage(c2, "a10").numbers;
  assert.equal(n2.length, 1); // só "livros lidos"
  assert.equal(n2[0]!.label, "livro lido");
});

test("números: plural de 'livro lido'", () => {
  const one = catalog({ authors: [author("a")], works: [work("w", ["a"])], readings: [reading(1, "w")] });
  assert.equal(buildAuthorPage(one, "a").numbers[0]!.label, "livro lido");
  const two = catalog({ authors: [author("a")], works: [work("w1", ["a"]), work("w2", ["a"])], readings: [reading(1, "w1"), reading(2, "w2")] });
  assert.equal(buildAuthorPage(two, "a").numbers[0]!.label, "livros lidos");
});

/* ---- bio ---- */

test("bio: com fonte (link), sem url, e sem bio", () => {
  const c = catalog({
    authors: [author("com"), author("semurl"), author("sembio")],
    summaries: [
      summary("autoria:com", true, "bio A", { source: "Wikipédia (pt)", sourceUrl: "https://x" }),
      summary("autoria:semurl", true, "bio B", { source: "Enciclopédia", sourceUrl: null }),
    ],
  });
  const com = buildAuthorPage(c, "com").bio!;
  assert.equal(com.text, "bio A");
  assert.deepEqual(com.source, { label: "Wikipédia (pt)", url: "https://x" });

  const semurl = buildAuthorPage(c, "semurl").bio!;
  assert.deepEqual(semurl.source, { label: "Enciclopédia", url: null });

  assert.equal(buildAuthorPage(c, "sembio").bio, null);
});

/* ---- contexto ---- */

test("contexto: com e sem país", () => {
  const c = catalog({
    authors: [
      author("br", { country: "BR" }),
      author("sem", { country: null }),
      author("it", { country: "IT", languages: ["italiano"], primaryLanguage: "italiano" }),
    ],
  });
  const br = buildAuthorPage(c, "br").context;
  assert.equal(br.country?.text, "Brasil");
  assert.equal(br.country?.href, "/pais/brasil");
  assert.equal(br.languages[0]!.text, "Português");

  assert.equal(buildAuthorPage(c, "sem").context.country, null);
});

/* ---- crédito ---- */

test("crédito: presente só com foto", () => {
  const c = catalog({
    authors: [
      author("comfoto", { photo: { file: "authors/comfoto.jpg", license: "CC BY", author: "F", sourceUrl: "https://s", source: "commons" } }),
      author("semfoto"),
    ],
  });
  assert.deepEqual(buildAuthorPage(c, "comfoto").credit, { author: "F", license: "CC BY", sourceUrl: "https://s" });
  assert.equal(buildAuthorPage(c, "semfoto").credit, null);
});

/* ---- grade e legenda ---- */

test("legenda: um ano, dois anos e sem data", () => {
  const c = catalog({
    authors: [author("a")],
    works: [work("um", ["a"]), work("dois", ["a"]), work("sd", ["a"])],
    readings: [
      reading(1, "um", 2022),
      reading(2, "dois", 2019), reading(5, "dois", 2025),
      reading(9, "sd", null),
    ],
  });
  const cap = buildAuthorPage(c, "a").captionFor;
  assert.equal(cap("um"), "lido em 2022");
  assert.equal(cap("dois"), "lido em 2019 e 2025");
  assert.equal(cap("sd"), "nº 9 da lista");
});

test("grade: obras na ordem do caderno", () => {
  const c = catalog({
    authors: [author("a")],
    works: [work("tarde", ["a"]), work("cedo", ["a"])],
    readings: [reading(50, "tarde"), reading(3, "cedo")],
  });
  const slugs = buildAuthorPage(c, "a").works.map((g) => g.work.slug);
  assert.deepEqual(slugs, ["cedo", "tarde"]);
});

/* ---- temas ---- */

test("temas: só 2+, top 10, variante mais frequente, com contagem", () => {
  const works: Work[] = [
    work("w1", ["a"], { themes: ["Memória", "solidão"] }),
    work("w2", ["a"], { themes: ["memória", "Guerra"] }),
    work("w3", ["a"], { themes: ["memória"] }),
    work("w4", ["a"], { themes: ["solidão"] }),
  ];
  const readings = works.map((w, i) => reading(i + 1, w.slug));
  const c = catalog({ authors: [author("a")], works, readings });
  const themes = buildAuthorPage(c, "a").themes!;
  // memória: 3 obras (variantes Memória/memória → "memória" é a mais frequente)
  const mem = themes.find((t) => t.label === "Memória")!;
  assert.equal(mem.count, 3);
  // solidão: 2 obras
  assert.ok(themes.some((t) => t.label === "Solidão" && t.count === 2));
  // Guerra: só 1 obra → fora
  assert.equal(themes.some((t) => t.label === "Guerra"), false);
  // ordem: memória (3) antes de solidão (2)
  assert.equal(themes[0]!.label, "Memória");
});

test("temas: autoria de um livro só não tem bloco de temas", () => {
  const c = catalog({
    authors: [author("a")],
    works: [work("w", ["a"], { themes: ["memória", "guerra"] })],
    readings: [reading(1, "w")],
  });
  assert.equal(buildAuthorPage(c, "a").themes, null);
});

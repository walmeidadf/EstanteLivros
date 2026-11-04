import { test } from "node:test";
import assert from "node:assert/strict";
import { buildModel } from "./catalog/model.ts";
import { buildAggregates } from "./catalog/aggregates.ts";
import type { RawCatalog } from "./catalog/load.ts";
import type { Catalog } from "./catalog/index.ts";
import type { Author, Work, Reading } from "./catalog/schema.ts";
import { buildWorkPage, editionLabel } from "./work-page.ts";

/* ---- fixtures (mesmo molde de atlas.test.ts) ---- */

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

function reading(sequence: number, w: string, year: number | null = 2020, extra: Partial<Reading> = {}): Reading {
  return { sequence, year, work: w, reread: false, originalEntry: `e${sequence}`, notes: null, ...extra };
}

const COUNTRIES = [
  { code: "BR", name: "Brasil", languages: ["português"] },
  { code: "KR", name: "Coreia do Sul", languages: ["coreano"] },
  { code: "US", name: "Estados Unidos", languages: ["inglês"] },
];

function catalog(parts: Partial<RawCatalog>): Catalog {
  const model = buildModel({
    works: [], authors: [], readings: [], summaries: [],
    vocabularies: {
      languages: ["português", "coreano", "inglês"],
      workTypes: ["romance"], genres: [], themes: [], countries: COUNTRIES,
    },
    ...parts,
  });
  return { ...model, aggregates: buildAggregates(model) };
}

/* ---- título original ---- */

test("título original presente, diferente do pt-BR", () => {
  const c = catalog({
    authors: [author("kang", { languages: ["coreano"], primaryLanguage: "coreano" })],
    works: [work("a-vegetariana", ["kang"], {
      title: "A Vegetariana", originalTitle: "채식주의자",
      originalTitleRomanized: "Chaesikjuuija", language: "coreano",
    })],
    readings: [reading(1, "a-vegetariana")],
  });
  const p = buildWorkPage(c, "a-vegetariana");
  assert.equal(p.original?.text, "채식주의자");
  assert.equal(p.original?.lang, "ko");
  assert.equal(p.romanized, "Chaesikjuuija");
});

test("título original igual ao pt-BR (só acento) some", () => {
  const c = catalog({
    authors: [author("a", { languages: ["francês"], primaryLanguage: "francês" })],
    works: [work("jacaranda", ["a"], {
      title: "Jacarandá", originalTitle: "Jacaranda", language: "francês",
    })],
    readings: [reading(1, "jacaranda")],
  });
  assert.equal(buildWorkPage(c, "jacaranda").original, null);
});

test("sem título original: original e romanização nulos", () => {
  const c = catalog({
    authors: [author("a")],
    works: [work("obra", ["a"])],
    readings: [reading(1, "obra")],
  });
  const p = buildWorkPage(c, "obra");
  assert.equal(p.original, null);
  assert.equal(p.romanized, null);
});

/* ---- ficha ---- */

test("ficha: idioma, país, publicação, tipo, gêneros — pula vazios", () => {
  const c = catalog({
    authors: [author("a", { country: "US", languages: ["inglês"], primaryLanguage: "inglês" })],
    works: [work("obra", ["a"], {
      language: "inglês", firstPublished: 1999, type: "romance",
      genres: ["drama", "ficção literária"],
    })],
    readings: [reading(1, "obra")],
  });
  const facts = buildWorkPage(c, "obra").facts;
  assert.deepEqual(facts.map((f) => f.label), [
    "Idioma original", "País", "Primeira publicação", "Tipo", "Gêneros",
  ]);
  const pais = facts.find((f) => f.label === "País")!;
  assert.equal(pais.kind, "links");
  if (pais.kind === "links") assert.equal(pais.links[0]!.text, "Estados Unidos");
});

test("ficha: sem país, sem publicação e sem gênero — linhas somem", () => {
  const c = catalog({
    authors: [author("a", { country: null })],
    works: [work("obra", ["a"], { genres: [] })],
    readings: [reading(1, "obra")],
  });
  const labels = buildWorkPage(c, "obra").facts.map((f) => f.label);
  assert.deepEqual(labels, ["Idioma original", "Tipo"]);
});

test("ficha: obra com autorias de dois países lista os dois", () => {
  const c = catalog({
    authors: [
      author("br", { country: "BR" }),
      author("us", { country: "US", languages: ["inglês"], primaryLanguage: "inglês" }),
    ],
    works: [work("obra", ["br", "us"])],
    readings: [reading(1, "obra")],
  });
  const pais = buildWorkPage(c, "obra").facts.find((f) => f.label === "Países")!;
  assert.equal(pais.kind, "links");
  if (pais.kind === "links") {
    assert.deepEqual(pais.links.map((l) => l.text).sort(), ["Brasil", "Estados Unidos"]);
  }
});

/* ---- leituras ---- */

test("heading por número de leituras", () => {
  const one = catalog({ authors: [author("a")], works: [work("o", ["a"])], readings: [reading(1, "o")] });
  assert.equal(buildWorkPage(one, "o").readingsHeading, "Lido uma vez");

  const two = catalog({ authors: [author("a")], works: [work("o", ["a"])], readings: [reading(1, "o"), reading(2, "o", 2024)] });
  assert.equal(buildWorkPage(two, "o").readingsHeading, "Lido duas vezes");

  const three = catalog({ authors: [author("a")], works: [work("o", ["a"])], readings: [reading(1, "o"), reading(2, "o", 2023), reading(3, "o", 2025)] });
  assert.equal(buildWorkPage(three, "o").readingsHeading, "Lido 3 vezes");
});

test("releitura é a posição na ordem, não o campo reread", () => {
  // A segunda leitura (seq 2) tem reread=false; a página ainda a rotula
  // "releitura" por ser a 2ª da ordem.
  const c = catalog({
    authors: [author("a")],
    works: [work("o", ["a"])],
    readings: [
      reading(1, "o", 2020, { reread: true }),  // reread=true, mas é a 1ª → "primeira leitura"
      reading(2, "o", 2025, { reread: false }), // reread=false, mas é a 2ª → "releitura"
    ],
  });
  const lines = buildWorkPage(c, "o").readings;
  assert.equal(lines[0]!.role, "primeira leitura");
  assert.equal(lines[1]!.role, "releitura");
});

test("leitura sem ano: year null e undatedHref para /ano/sem-data", () => {
  const c = catalog({
    authors: [author("a")],
    works: [work("o", ["a"])],
    readings: [reading(7, "o", null)],
  });
  const line = buildWorkPage(c, "o").readings[0]!;
  assert.equal(line.year, null);
  assert.equal(line.undatedHref, "/ano/sem-data");
  assert.equal(line.sequence, 7);
});

test("leitura com ano: href para /ano/{ano}", () => {
  const c = catalog({
    authors: [author("a")],
    works: [work("o", ["a"])],
    readings: [reading(1, "o", 2022)],
  });
  const line = buildWorkPage(c, "o").readings[0]!;
  assert.deepEqual(line.year, { value: 2022, href: "/ano/2022" });
});

/* ---- temas ---- */

test("tema: contagem só a partir de 5 obras; abaixo disso é null", () => {
  // "memória" em 5 obras; "insônia" em 1.
  const works: Work[] = [];
  const readings: Reading[] = [];
  for (let i = 0; i < 5; i++) {
    works.push(work(`m${i}`, ["a"], { themes: ["memória"] }));
    readings.push(reading(i + 1, `m${i}`));
  }
  works.push(work("alvo", ["a"], { themes: ["memória", "insônia"] }));
  readings.push(reading(99, "alvo"));

  const c = catalog({ authors: [author("a")], works, readings });
  const chips = buildWorkPage(c, "alvo").themes!;
  const memoria = chips.find((t) => t.label === "Memória")!;
  const insonia = chips.find((t) => t.label === "Insônia")!;
  assert.equal(memoria.count, 6); // 5 + a própria "alvo"
  assert.equal(insonia.count, null);
  // ordenação: o tema mais frequente primeiro
  assert.equal(chips[0]!.label, "Memória");
});

test("tema: variantes de caixa/acento somam no mesmo slug", () => {
  const works: Work[] = [];
  const readings: Reading[] = [];
  const variants = ["Guerra", "guerra", "GUERRA", "Guerra", "guerra"];
  variants.forEach((t, i) => {
    works.push(work(`g${i}`, ["a"], { themes: [t] }));
    readings.push(reading(i + 1, `g${i}`));
  });
  works.push(work("alvo", ["a"], { themes: ["Guerra"] }));
  readings.push(reading(50, "alvo"));

  const c = catalog({ authors: [author("a")], works, readings });
  const chip = buildWorkPage(c, "alvo").themes![0]!;
  assert.equal(chip.count, 6); // 5 variantes + alvo, todas no slug "guerra"
});

test("obra sem tema: themes null", () => {
  const c = catalog({ authors: [author("a")], works: [work("o", ["a"], { themes: [] })], readings: [reading(1, "o")] });
  assert.equal(buildWorkPage(c, "o").themes, null);
});

/* ---- edição ---- */

test("rótulo de edição por match e idioma", () => {
  const exact = work("o", ["a"], { edition: { title: null, language: "português", publisher: "X", year: 2020, isbn13: null, isbn10: null, format: null, match: "exact" } });
  assert.equal(editionLabel(buildWorkPage(catalog({ authors: [author("a")], works: [exact], readings: [reading(1, "o")] }), "o").work), "Edição lida");

  const repPt = work("o", ["a"], { edition: { title: null, language: "português", publisher: "X", year: 2020, isbn13: null, isbn10: null, format: null, match: "representative" } });
  assert.equal(editionLabel(buildWorkPage(catalog({ authors: [author("a")], works: [repPt], readings: [reading(1, "o")] }), "o").work), "Edição brasileira de referência");

  const repEn = work("o", ["a"], { edition: { title: null, language: "inglês", publisher: "X", year: 2020, isbn13: null, isbn10: null, format: null, match: "representative" } });
  assert.equal(editionLabel(buildWorkPage(catalog({ authors: [author("a")], works: [repEn], readings: [reading(1, "o")] }), "o").work), "Edição de referência");
});

test("edição: linhas presentes; ISBN sem hífen; caixa some se vazia", () => {
  const full = work("o", ["a"], { edition: { title: null, language: "português", publisher: "Todavia", year: 2018, isbn13: "9788588808294", isbn10: null, format: null, match: "representative" } });
  const box = buildWorkPage(catalog({ authors: [author("a")], works: [full], readings: [reading(1, "o")] }), "o").edition!;
  assert.deepEqual(box.lines, [
    { label: "Editora", value: "Todavia" },
    { label: "Ano", value: "2018" },
    { label: "ISBN", value: "9788588808294" },
  ]);

  const empty = work("o", ["a"]); // edição toda null
  assert.equal(buildWorkPage(catalog({ authors: [author("a")], works: [empty], readings: [reading(1, "o")] }), "o").edition, null);
});

/* ---- registro ---- */

test("nota do catalogador: texto ou null", () => {
  const withNote = work("o", ["a"], { catalogerNote: "consenso entre fontes" });
  assert.equal(buildWorkPage(catalog({ authors: [author("a")], works: [withNote], readings: [reading(1, "o")] }), "o").catalogerNote, "consenso entre fontes");

  const without = work("o", ["a"], { catalogerNote: null });
  assert.equal(buildWorkPage(catalog({ authors: [author("a")], works: [without], readings: [reading(1, "o")] }), "o").catalogerNote, null);
});

test("caderno: uma entrada por leitura, identificada por ano ou nº da lista", () => {
  const c = catalog({
    authors: [author("a")],
    works: [work("o", ["a"])],
    readings: [
      reading(5, "o", 2021, { originalEntry: "47. A obra" }),
      reading(90, "o", null, { originalEntry: "0. A obra (sem data)" }),
    ],
  });
  const nb = buildWorkPage(c, "o").notebook;
  assert.deepEqual(nb, [
    { when: "em 2021", text: "47. A obra" },
    { when: "nº 90 da lista", text: "0. A obra (sem data)" },
  ]);
});

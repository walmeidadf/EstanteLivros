import { test } from "node:test";
import assert from "node:assert/strict";
import { buildModel } from "./catalog/model.ts";
import { buildAggregates } from "./catalog/aggregates.ts";
import type { RawCatalog } from "./catalog/load.ts";
import type { Catalog } from "./catalog/index.ts";
import type { Author, Work, Reading, Summary } from "./catalog/schema.ts";
import {
  buildAtlasByLanguage,
  buildAtlasByCountry,
  topAuthors,
  themeCloud,
  eras,
  buildAtlasShared,
  buildThemePages,
  buildLanguagePages,
  buildCountryPages,
  capitalizeFirst,
  readingsLabel,
} from "./atlas.ts";

/* ---- fixtures (mesmo molde de timeline.test.ts) ---- */

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

function summary(scope: string, approved: boolean, text: string): Summary {
  return {
    scope, text, approved, updatedAt: "2026-11-03", source: null, sourceUrl: null,
    sourceLanguage: null, model: null, promptVersion: null, editedBy: null,
  };
}

const COUNTRIES = [
  { code: "BR", name: "Brasil", languages: ["português"] },
  { code: "PT", name: "Portugal", languages: ["português"] },
  { code: "AO", name: "Angola", languages: ["português"] },
  { code: "KR", name: "Coreia do Sul", languages: ["coreano"] },
  { code: "US", name: "Estados Unidos", languages: ["inglês"] },
  { code: "FR", name: "França", languages: ["francês"] },
];

function catalog(parts: Partial<RawCatalog>): Catalog {
  const model = buildModel({
    works: [], authors: [], readings: [], summaries: [],
    vocabularies: {
      languages: ["português", "coreano", "inglês", "francês"],
      workTypes: ["romance"], genres: [], themes: [], countries: COUNTRIES,
    },
    ...parts,
  });
  return { ...model, aggregates: buildAggregates(model) };
}

/** N obras de uma autoria, com leituras sequenciais a partir de `from`. */
function manyWorks(prefix: string, authors: string[], n: number, from: number, extra: Partial<Work> = {}) {
  const works: Work[] = [];
  const readings: Reading[] = [];
  for (let i = 0; i < n; i++) {
    const slug = `${prefix}${i}`;
    works.push(work(slug, authors, extra));
    readings.push(reading(from + i, slug));
  }
  return { works, readings };
}

/* ---- helpers ---- */

test("capitalizeFirst e readingsLabel", () => {
  assert.equal(capitalizeFirst("segunda guerra"), "Segunda guerra");
  assert.equal(capitalizeFirst("álcool"), "Álcool");
  assert.equal(readingsLabel(1), "1 leitura");
  assert.equal(readingsLabel(8), "8 leituras");
});

/* ---- Atlas por idioma ---- */

test("idiomas por quantidade de obras; desempate pelo nome; lombada por obra", () => {
  const c = catalog({
    authors: [author("a"), author("k", { country: "KR", languages: ["coreano"], primaryLanguage: "coreano" })],
    works: [
      work("p1", ["a"]), work("p2", ["a"]),
      work("k1", ["k"], { language: "coreano" }),
      work("f1", ["a"], { language: "francês" }),
    ],
    readings: [reading(1, "p1"), reading(2, "k1"), reading(3, "p2"), reading(4, "f1")],
  });
  const bands = buildAtlasByLanguage(c);
  assert.deepEqual(bands.map((b) => b.label), ["Português", "Coreano", "Francês"]);
  assert.deepEqual(bands.map((b) => b.count), [2, 1, 1]);
  assert.equal(bands[0]!.href, "/idioma/portugues");
  assert.deepEqual(bands[0]!.spines, [{ language: "português" }, { language: "português" }]);
});

test("lombadas do idioma seguem a ordem do caderno", () => {
  const c = catalog({
    authors: [author("a")],
    works: [work("tarde", ["a"]), work("cedo", ["a"])],
    readings: [reading(9, "tarde"), reading(2, "cedo")],
  });
  // ambas português: a ordem só se vê pelo número de lombadas; checamos a página
  const page = buildLanguagePages(c)[0]!;
  assert.deepEqual(page.items.map((i) => i.work.slug), ["cedo", "tarde"]);
});

/* ---- Atlas por país ---- */

test("obra com duas autorias de países distintos conta e aparece nos dois", () => {
  const c = catalog({
    authors: [author("br"), author("pt", { country: "PT" })],
    works: [work("conjunta", ["br", "pt"]), work("so-br", ["br"])],
    readings: [reading(1, "conjunta"), reading(2, "so-br")],
  });
  const { bands } = buildAtlasByCountry(c);
  const br = bands.find((b) => b.label === "Brasil")!;
  const pt = bands.find((b) => b.label === "Portugal")!;
  assert.equal(br.count, 2);
  assert.equal(pt.count, 1);
});

test("obra sem país fica fora das faixas", () => {
  const c = catalog({
    authors: [author("sem", { country: null }), author("br")],
    works: [work("orfa", ["sem"]), work("ok", ["br"])],
    readings: [reading(1, "orfa"), reading(2, "ok")],
  });
  const { bands, others } = buildAtlasByCountry(c);
  assert.deepEqual(bands.map((b) => b.label), ["Brasil"]);
  assert.equal(others, null);
});

test("lombadas do país levam a cor do idioma de cada obra", () => {
  const c = catalog({
    authors: [author("br")],
    works: [work("a", ["br"]), work("b", ["br"], { language: "inglês" })],
    readings: [reading(1, "a"), reading(2, "b")],
  });
  assert.deepEqual(buildAtlasByCountry(c).bands[0]!.spines.map((s) => s.language), ["português", "inglês"]);
});

/** 12 países fictícios (BR e mais 11), com 12..1 obras. */
function manyCountries(): Catalog {
  const codes = ["BR", "PT", "AO", "KR", "US", "FR", "C1", "C2", "C3", "C4", "C5", "C6"];
  const countries = codes.map((code) => ({
    code, name: code === "BR" ? "Brasil" : `País ${code}`, languages: ["português"],
  }));
  const authors: Author[] = [];
  const works: Work[] = [];
  const readings: Reading[] = [];
  let seq = 1;
  codes.forEach((code, idx) => {
    authors.push(author(`a-${code}`, { country: code }));
    for (let i = 0; i < 12 - idx; i++) {
      const slug = `${code}-${i}`;
      works.push(work(slug, [`a-${code}`]));
      readings.push(reading(seq++, slug));
    }
  });
  return catalog({
    authors, works, readings,
    vocabularies: { languages: ["português"], workTypes: ["romance"], genres: [], themes: [], countries },
  });
}

test("10 faixas individuais e o resto em 'Outros países' com obras DISTINTAS", () => {
  const { bands, others } = buildAtlasByCountry(manyCountries());
  assert.equal(bands.length, 10);
  assert.equal(bands[0]!.label, "Brasil");
  assert.ok(others);
  assert.equal(others!.band.label, "Outros países");
  assert.equal(others!.band.href, undefined);
  assert.equal(others!.countries.length, 2);
  assert.equal(others!.band.count, 3); // 2 + 1 obras, nenhuma repetida
  assert.equal(others!.countries[0]!.href, "/pais/pais-c5");
});

test("'Outros países' conta uma obra em dois países agrupados uma vez", () => {
  // 12 países; C5 e C6 ficam agrupados, e uma obra "dupla" é de ambos com uma obra extra de duas autorias em países agrupados
  const codes = ["BR", "PT", "AO", "KR", "US", "FR", "C1", "C2", "C3", "C4", "C5", "C6"];
  const countries = codes.map((code) => ({ code, name: `País ${code}`, languages: ["português"] }));
  const authors: Author[] = codes.map((code) => author(`a-${code}`, { country: code }));
  const works: Work[] = [];
  const readings: Reading[] = [];
  let seq = 1;
  codes.forEach((code, idx) => {
    for (let i = 0; i < 12 - idx; i++) {
      works.push(work(`${code}-${i}`, [`a-${code}`]));
      readings.push(reading(seq++, `${code}-${i}`));
    }
  });
  works.push(work("dupla", ["a-C5", "a-C6"]));
  readings.push(reading(seq++, "dupla"));
  const c = catalog({
    authors, works, readings,
    vocabularies: { languages: ["português"], workTypes: ["romance"], genres: [], themes: [], countries },
  });
  const { others } = buildAtlasByCountry(c);
  // C5 tem 2 próprias, C6 tem 1; a "dupla" soma +1 em cada chip
  const c5 = others!.countries.find((x) => x.name === "País C5")!;
  const c6 = others!.countries.find((x) => x.name === "País C6")!;
  assert.equal(c5.count, 3);
  assert.equal(c6.count, 2);
  // mas na faixa as obras são distintas: 2 + 1 + 1 (a dupla conta uma vez)
  assert.equal(others!.band.count, 4);
});

test("um único país restante vira faixa individual (sem 'Outros')", () => {
  const codes = ["C0", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10"];
  const countries = codes.map((code) => ({ code, name: `País ${code}`, languages: ["português"] }));
  const authors = codes.map((code) => author(`a-${code}`, { country: code }));
  const works = codes.map((code) => work(`w-${code}`, [`a-${code}`]));
  const readings = codes.map((code, i) => reading(i + 1, `w-${code}`));
  const c = catalog({
    authors, works, readings,
    vocabularies: { languages: ["português"], workTypes: ["romance"], genres: [], themes: [], countries },
  });
  const { bands, others } = buildAtlasByCountry(c);
  assert.equal(bands.length, 11);
  assert.equal(others, null);
});

test("10 países ou menos: sem 'Outros países'; empate pelo NOME do país", () => {
  const c = catalog({
    authors: [author("b", { country: "BR" }), author("p", { country: "PT" })],
    works: [work("w1", ["b"]), work("w2", ["p"])],
    readings: [reading(1, "w1"), reading(2, "w2")],
  });
  const { bands, others } = buildAtlasByCountry(c);
  assert.deepEqual(bands.map((b) => b.label), ["Brasil", "Portugal"]);
  assert.equal(others, null);
});

/* ---- Quem ela mais lê ---- */

test("topAuthors: leituras desc, empate pelo nome, corte e vazio → null", () => {
  const c = catalog({
    authors: [author("zeca", { name: "Zeca" }), author("ana", { name: "Ana" }), author("beto", { name: "Beto" })],
    works: [work("w1", ["zeca"]), work("w2", ["ana"]), work("w3", ["beto"]), work("w4", ["beto"])],
    readings: [reading(1, "w1"), reading(2, "w2"), reading(3, "w3"), reading(4, "w3"), reading(5, "w4")],
  });
  const top = topAuthors(c)!;
  assert.deepEqual(top.map((p) => p.author.name), ["Beto", "Ana", "Zeca"]); // 3, 1, 1 → empate Ana<Zeca
  assert.equal(top[0]!.href, "/autoria/beto");
  assert.equal(topAuthors(c, 2)!.length, 2);
  assert.equal(topAuthors(catalog({})), null);
});

/* ---- Temas ---- */

function themed() {
  const authors = [author("a")];
  const works: Work[] = [];
  const readings: Reading[] = [];
  let seq = 1;
  const add = (slug: string, themes: string[]) => {
    works.push(work(slug, ["a"], { themes }));
    readings.push(reading(seq++, slug));
  };
  for (let i = 0; i < 10; i++) add(`m${i}`, ["memória"]);
  for (let i = 0; i < 5; i++) add(`f${i}`, ["família"]);
  for (let i = 0; i < 2; i++) add(`g${i}`, ["Segunda Guerra Mundial"]);
  for (let i = 0; i < 5; i++) add(`h${i}`, ["segunda guerra mundial"]);
  add("ambos", ["Segunda Guerra Mundial", "segunda guerra mundial"]);
  add("raro", ["raridade"]);
  return catalog({ authors, works, readings });
}

test("nuvem: piso, tiers, ordem alfabética e variantes unificadas", () => {
  const cloud = themeCloud(themed())!;
  assert.deepEqual(cloud.map((t) => t.label), ["família", "memória", "segunda guerra mundial"]);
  const byLabel = Object.fromEntries(cloud.map((t) => [t.label, t]));
  assert.equal(byLabel["memória"]!.tier, 4); // 10 / 10
  assert.equal(byLabel["família"]!.tier, 3); // 5 / 10 = 0,5
  // 2 + 5 + 1 (ambos) = 8 obras distintas (a obra com as duas variantes conta uma vez)
  assert.equal(byLabel["segunda guerra mundial"]!.count, 8);
  assert.equal(byLabel["segunda guerra mundial"]!.tier, 4); // 8/10 = 0,8
  assert.equal(byLabel["memória"]!.href, "/tema/memoria");
});

test("nuvem: ninguém atinge o piso → null", () => {
  const c = catalog({ authors: [author("a")], works: [work("w", ["a"], { themes: ["x"] })], readings: [reading(1, "w")] });
  assert.equal(themeCloud(c), null);
});

test("páginas de tema: slug único por variante; rótulo pela mais frequente; sem 'raridade' perdida", () => {
  const pages = buildThemePages(themed());
  const slugs = pages.map((p) => p.slug);
  assert.equal(new Set(slugs).size, slugs.length);
  const sgm = pages.find((p) => p.slug === "segunda-guerra-mundial")!;
  assert.equal(sgm.name, "Segunda guerra mundial");
  assert.equal(sgm.items.length, 8);
  assert.equal(sgm.numbers[0]!.value, "8");
  assert.equal(pages.find((p) => p.slug === "raridade")!.items.length, 1);
});

/* ---- Épocas ---- */

test("épocas: bordas, 'antes de 1800' condicional e obra sem ano ignorada", () => {
  const years = [1799, 1800, 1899, 1900, 1999, 2000, 2009, 2010, 2019, 2020, null];
  const works = years.map((y, i) => work(`w${i}`, ["a"], { firstPublished: y }));
  const c = catalog({
    authors: [author("a")], works,
    readings: works.map((w, i) => reading(i + 1, w.slug)),
  });
  const e = eras(c)!;
  assert.deepEqual(e.map((x) => [x.id, x.count]), [
    ["pre-1800", 1], ["xix", 2], ["xx", 2], ["2000s", 2], ["2010s", 2], ["2020s", 1],
  ]);
  assert.equal(e[1]!.pct, 100);
  assert.equal(e[0]!.pct, 50);
});

test("épocas: sem obra anterior a 1800, a época não aparece; vazias ficam em 0", () => {
  const c = catalog({
    authors: [author("a")],
    works: [work("w", ["a"], { firstPublished: 2015 })],
    readings: [reading(1, "w")],
  });
  const e = eras(c)!;
  assert.deepEqual(e.map((x) => x.id), ["xix", "xx", "2000s", "2010s", "2020s"]);
  assert.equal(e[0]!.count, 0);
  assert.equal(e[0]!.pct, 0);
});

test("épocas: nenhuma obra com ano → null", () => {
  const c = catalog({ authors: [author("a")], works: [work("w", ["a"])], readings: [reading(1, "w")] });
  assert.equal(eras(c), null);
  assert.deepEqual(Object.keys(buildAtlasShared(c)).sort(), ["authors", "cloud", "eras"]);
});

/* ---- Idioma ---- */

test("página de idioma: %, '<1%', autorias e carrossel", () => {
  const { works, readings } = manyWorks("p", ["a", "b"], 3, 1);
  const c = catalog({
    authors: [author("a"), author("b")],
    works: [...works, ...manyWorks("x", ["a"], 1, 10, { language: "coreano" }).works],
    readings: [...readings, reading(10, "x0")],
  });
  const pages = buildLanguagePages(c);
  const pt = pages.find((p) => p.slug === "portugues")!;
  assert.equal(pt.name, "Português");
  assert.deepEqual(pt.numbers.map((n) => n.value), ["3", "75%", "2"]);
  assert.equal(pt.authors!.length, 2);
  const ko = pages.find((p) => p.slug === "coreano")!;
  assert.equal(ko.numbers[0]!.label, "obra");
  assert.equal(ko.authors, null); // uma autoria só
});

test("'<1%' quando a fatia é menor que 1%", () => {
  const { works, readings } = manyWorks("p", ["a"], 300, 1);
  const c = catalog({
    authors: [author("a")],
    works: [...works, work("k", ["a"], { language: "coreano" })],
    readings: [...readings, reading(999, "k")],
  });
  const ko = buildLanguagePages(c).find((p) => p.slug === "coreano")!;
  assert.equal(ko.numbers[1]!.value, "<1%");
});

test("colisão de slug de idioma lança", () => {
  const c = catalog({
    authors: [author("a")],
    works: [work("w1", ["a"], { language: "inglês" }), work("w2", ["a"], { language: "ingles" })],
    readings: [reading(1, "w1"), reading(2, "w2")],
  });
  assert.throws(() => buildLanguagePages(c), /Colisão de slug de idioma/);
});

/* ---- País ---- */

test("página de país: dominante, chips de idioma, resumo e números", () => {
  const c = catalog({
    authors: [author("b1"), author("p1", { country: "PT" }), author("u1", { country: "US", languages: ["inglês"], primaryLanguage: "inglês" })],
    works: [work("wb", ["b1"]), work("wp", ["p1"]), work("wu", ["u1"], { language: "inglês" })],
    readings: [reading(1, "wb"), reading(2, "wp"), reading(3, "wu")],
    summaries: [summary("pais:BR", true, "Frase aprovada."), summary("pais:PT", false, "não")],
  });
  const pages = buildCountryPages(c);
  const br = pages.find((p) => p.slug === "brasil")!;
  assert.equal(br.dominantLanguage, "português");
  assert.deepEqual(br.sharing, [{ name: "Portugal", href: "/pais/portugal" }]);
  assert.equal(br.summary, "Frase aprovada.");
  assert.deepEqual(br.numbers.map((n) => n.value), ["1", "1"]);
  assert.equal(pages.find((p) => p.slug === "portugal")!.summary, null);
  const us = pages.find((p) => p.slug === "estados-unidos")!;
  assert.equal(us.sharing, null);
  assert.ok(us.nameColor.startsWith("#"));
  assert.equal(us.swatch, "#2F5D9E");
  assert.notEqual(us.nameColor, us.swatch); // inglês é clareado
});

test("destaque do país: máximo único ≥ 2; empate ou máximo 1 → null", () => {
  const c = catalog({
    authors: [author("ana"), author("beto"), author("pt1", { country: "PT" }), author("pt2", { country: "PT" })],
    works: [work("w1", ["ana"]), work("w2", ["ana"]), work("w3", ["beto"]), work("w4", ["pt1"]), work("w5", ["pt2"])],
    readings: [reading(1, "w1"), reading(2, "w2"), reading(3, "w3"), reading(4, "w4"), reading(5, "w5")],
  });
  const pages = buildCountryPages(c);
  assert.equal(pages.find((p) => p.slug === "brasil")!.topAuthor!.author.slug, "ana");
  assert.equal(pages.find((p) => p.slug === "portugal")!.topAuthor, null); // máximo 1
  const tie = catalog({
    authors: [author("ana"), author("beto")],
    works: [work("w1", ["ana"]), work("w2", ["ana"]), work("w3", ["beto"]), work("w4", ["beto"])],
    readings: [reading(1, "w1"), reading(2, "w2"), reading(3, "w3"), reading(4, "w4")],
  });
  assert.equal(buildCountryPages(tie)[0]!.topAuthor, null); // empate no topo
});

test("dominante empata → desempate pelo nome do idioma", () => {
  const c = catalog({
    authors: [author("a")],
    works: [work("w1", ["a"], { language: "português" }), work("w2", ["a"], { language: "inglês" })],
    readings: [reading(1, "w1"), reading(2, "w2")],
  });
  assert.equal(buildCountryPages(c)[0]!.dominantLanguage, "inglês");
});

test("obra de duas autorias aparece nas duas páginas de país", () => {
  const c = catalog({
    authors: [author("br"), author("pt", { country: "PT" })],
    works: [work("conjunta", ["br", "pt"])],
    readings: [reading(1, "conjunta")],
  });
  const pages = buildCountryPages(c);
  assert.equal(pages.find((p) => p.slug === "brasil")!.items[0]!.work.slug, "conjunta");
  assert.equal(pages.find((p) => p.slug === "portugal")!.items[0]!.work.slug, "conjunta");
});

test("colisão de slug de país lança", () => {
  const countries = [
    { code: "X1", name: "São Tomé", languages: ["português"] },
    { code: "X2", name: "Sao Tome", languages: ["português"] },
  ];
  const c = catalog({
    authors: [author("a", { country: "X1" }), author("b", { country: "X2" })],
    works: [work("w1", ["a"]), work("w2", ["b"])],
    readings: [reading(1, "w1"), reading(2, "w2")],
    vocabularies: { languages: ["português"], workTypes: ["romance"], genres: [], themes: [], countries },
  });
  assert.throws(() => buildCountryPages(c), /Colisão de slug de país/);
});

test("peça da grade: href, ordem do caderno e dados de ordenação dobrados", () => {
  const c = catalog({
    authors: [author("a", { name: "Éça de Queirós" })],
    works: [work("w", ["a"], { title: "Ação", firstPublished: 1875 })],
    readings: [reading(7, "w")],
  });
  const item = buildLanguagePages(c)[0]!.items[0]!;
  assert.equal(item.href, "/obra/w");
  assert.deepEqual(item.sort, { seq: 7, title: "acao", author: "eca de queiros", year: 1875 });
});

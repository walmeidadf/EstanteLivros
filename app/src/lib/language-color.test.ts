import { test } from "node:test";
import assert from "node:assert/strict";
import {
  languageColor,
  languageColorVars,
  languagesWithOwnColor,
  OTHER_LANGUAGE_COLOR,
  contrastRatio,
  onGround,
} from "./language-color.ts";

// Os 15 idiomas presentes hoje em catalog/vocabularies.json.
const CATALOG_LANGUAGES = [
  "alemão",
  "árabe",
  "catalão",
  "coreano",
  "espanhol",
  "francês",
  "hebraico",
  "holandês",
  "inglês",
  "italiano",
  "japonês",
  "norueguês",
  "português",
  "russo",
  "tcheco",
];

// Os que têm cor própria em §3.2.
const WITH_OWN_COLOR = [
  "português",
  "inglês",
  "espanhol",
  "francês",
  "italiano",
  "russo",
  "japonês",
  "alemão",
  "hebraico",
  "coreano",
];

test("cada idioma de §3.2 devolve o par certo", () => {
  assert.deepEqual(languageColor("português"), {
    bg: "#C89B3C",
    ink: "#1A1408",
  });
  assert.deepEqual(languageColor("coreano"), { bg: "#E3A9B0", ink: "#2A1418" });
  assert.deepEqual(languageColor("japonês"), { bg: "#E8DFCB", ink: "#2A2418" });
});

test("idioma fora do mapa cai em 'outros' sem erro", () => {
  assert.deepEqual(languageColor("catalão"), OTHER_LANGUAGE_COLOR);
  assert.deepEqual(languageColor("klingon"), OTHER_LANGUAGE_COLOR);
  assert.deepEqual(languageColor(""), OTHER_LANGUAGE_COLOR);
});

test("todos os 15 idiomas do catálogo resolvem (cor própria ou 'outros')", () => {
  for (const lang of CATALOG_LANGUAGES) {
    const color = languageColor(lang);
    assert.ok(color.bg.startsWith("#"), `${lang} tem bg`);
    assert.ok(color.ink.startsWith("#"), `${lang} tem ink`);
    const hasOwn = WITH_OWN_COLOR.includes(lang);
    const isOther =
      color.bg === OTHER_LANGUAGE_COLOR.bg &&
      color.ink === OTHER_LANGUAGE_COLOR.ink;
    assert.equal(hasOwn, !isOther, `${lang}: cor própria ⇔ não é 'outros'`);
  }
});

test("languagesWithOwnColor lista exatamente os 10 de §3.2", () => {
  assert.deepEqual(languagesWithOwnColor().sort(), [...WITH_OWN_COLOR].sort());
});

test("languageColorVars emite as custom properties", () => {
  assert.equal(
    languageColorVars("inglês"),
    "--lang-bg:#2F5D9E;--lang-ink:#F4EFE6;",
  );
  assert.equal(
    languageColorVars("tcheco"),
    `--lang-bg:${OTHER_LANGUAGE_COLOR.bg};--lang-ink:${OTHER_LANGUAGE_COLOR.ink};`,
  );
});

test("contrastRatio: preto/branco = 21 e cor igual = 1", () => {
  assert.equal(Math.round(contrastRatio("#000000", "#FFFFFF")), 21);
  assert.equal(contrastRatio("#C89B3C", "#C89B3C"), 1);
});

test("onGround mantém as cores que já passam 4.5:1 (português, japonês, coreano)", () => {
  for (const lang of ["português", "japonês", "coreano"]) {
    const { bg } = languageColor(lang);
    assert.equal(onGround(bg), bg.toUpperCase());
  }
});

test("onGround clareia as demais até passar 4.5:1 sobre --ground", () => {
  for (const lang of ["inglês", "francês", "russo", "alemão", "espanhol", "tcheco"]) {
    const { bg } = languageColor(lang);
    const out = onGround(bg);
    assert.notEqual(out, bg.toUpperCase(), `${lang} muda`);
    assert.ok(contrastRatio(out, "#0E1714") >= 4.5, `${lang} passa 4.5:1`);
  }
});

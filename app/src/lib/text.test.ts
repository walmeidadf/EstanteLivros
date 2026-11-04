import { test } from "node:test";
import assert from "node:assert/strict";
import { initials, detectScript, scriptDir, languageTag } from "./text.ts";

test("languageTag cobre os 15 idiomas e devolve undefined para o resto", () => {
  const all = ["português","inglês","espanhol","francês","italiano","russo","japonês","alemão","hebraico","coreano","norueguês","catalão","tcheco","árabe","holandês"];
  for (const l of all) assert.ok(languageTag(l), l);
  assert.equal(languageTag("português"), "pt");
  assert.equal(languageTag("klingon"), undefined);
});

test("árabe é detectado e escreve da direita para a esquerda", () => {
  assert.equal(detectScript("ألف ليلة وليلة"), "arabic");
  assert.equal(scriptDir("arabic"), "rtl");
  assert.equal(scriptDir("hebrew"), "rtl");
});

test("iniciais de nome com dois nomes", () => {
  assert.equal(initials("Han Kang"), "HK");
  assert.equal(initials("Clarice Lispector"), "CL");
  assert.equal(initials("Gabriel García Márquez"), "GM");
});

test("iniciais de nome único", () => {
  assert.equal(initials("Platão"), "P");
  assert.equal(initials("Ondjaki"), "O");
});

test("iniciais ignoram partículas", () => {
  assert.equal(initials("Machado de Assis"), "MA");
  assert.equal(initials("Simone de Beauvoir"), "SB");
  assert.equal(initials("Alba de Céspedes"), "AC");
});

test("iniciais de nome vazio", () => {
  assert.equal(initials(""), "");
  assert.equal(initials("   "), "");
});

test("detecção de alfabeto", () => {
  assert.equal(detectScript("Torto Arado"), "latin");
  assert.equal(detectScript("Преступление и наказание"), "cyrillic");
  assert.equal(detectScript("סיפור על אהבה וחושך"), "hebrew");
  assert.equal(detectScript("채식주의자"), "cjk");
  assert.equal(detectScript("海辺のカフカ"), "cjk");
});

test("direção de escrita (hebraico é RTL)", () => {
  assert.equal(scriptDir("hebrew"), "rtl");
  assert.equal(scriptDir("latin"), "ltr");
  assert.equal(scriptDir("cjk"), "ltr");
});

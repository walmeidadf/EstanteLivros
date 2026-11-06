import { test } from "node:test";
import assert from "node:assert/strict";
import { initials, detectScript, scriptDir, languageTag, originalTitleLang, originalTitleFont, originalTitlePresentation } from "./text.ts";

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

test("lang do título original: omite quando é romanização de idioma não latino", () => {
  assert.equal(originalTitleLang("japonês", "Nemureru Bijo"), undefined);
  assert.equal(originalTitleLang("japonês", "海辺のカフカ"), "ja");
  assert.equal(originalTitleLang("espanhol", "La tregua"), "es");
  assert.equal(originalTitleLang("hebraico", "סיפור על אהבה וחושך"), "he");
});

test("originalTitlePresentation: null quando ausente ou igual ao pt-BR", () => {
  assert.equal(originalTitlePresentation("português", "Torto Arado", null), null);
  assert.equal(originalTitlePresentation("português", "Torto Arado", ""), null);
  assert.equal(originalTitlePresentation("português", "Torto Arado", "  "), null);
  // igual ignorando caixa e acento
  assert.equal(
    originalTitlePresentation("inglês", "Beloved", "beloved"),
    null,
  );
  assert.equal(
    originalTitlePresentation("português", "A Hora da Estrela", "A hora da estréia")?.text,
    "A hora da estréia",
    "títulos diferentes não são colapsados",
  );
});

test("originalTitlePresentation: coreano em alfabeto nativo", () => {
  const p = originalTitlePresentation("coreano", "A Vegetariana", "채식주의자")!;
  assert.equal(p.text, "채식주의자");
  assert.equal(p.lang, "ko");
  assert.equal(p.dir, "ltr");
  assert.equal(p.font, "var(--font-serif-kr)");
});

test("originalTitlePresentation: japonês usa a fonte JP", () => {
  const p = originalTitlePresentation("japonês", "Kafka à Beira-Mar", "海辺のカフカ")!;
  assert.equal(p.font, "var(--font-serif-jp)");
  assert.equal(p.lang, "ja");
});

test("originalTitlePresentation: hebraico é RTL com fonte própria", () => {
  const p = originalTitlePresentation("hebraico", "De Amor e Trevas", "סיפור על אהבה וחושך")!;
  assert.equal(p.dir, "rtl");
  assert.equal(p.font, "var(--font-serif-hebrew)");
  assert.equal(p.lang, "he");
});

test("originalTitlePresentation: árabe é RTL, sem fonte dedicada", () => {
  const p = originalTitlePresentation("árabe", "As Mil e Uma Noites", "ألف ليلة وليلة")!;
  assert.equal(p.dir, "rtl");
  assert.equal(p.lang, "ar");
  assert.equal(p.font, undefined);
});

test("originalTitlePresentation: latino não ganha fonte e mantém lang do idioma", () => {
  const p = originalTitlePresentation("espanhol", "A Trégua", "La tregua")!;
  assert.equal(p.dir, "ltr");
  assert.equal(p.lang, "es");
  assert.equal(p.font, undefined);
});

test("originalTitlePresentation: romanização de idioma não latino não leva lang", () => {
  const p = originalTitlePresentation("japonês", "Sputnik, Meu Amor", "Supūtoniku no Koibito")!;
  assert.equal(p.text, "Supūtoniku no Koibito");
  assert.equal(p.lang, undefined);
  assert.equal(p.dir, "ltr");
  // detectado como latino → sem fonte CJK
  assert.equal(p.font, undefined);
});

test("originalTitleFont: coreano e japonês usam fontes diferentes (capa tipográfica)", () => {
  assert.equal(originalTitleFont("coreano", "cjk"), "var(--font-serif-kr)");
  assert.equal(originalTitleFont("japonês", "cjk"), "var(--font-serif-jp)");
  assert.equal(originalTitleFont("russo", "cyrillic"), undefined);
});

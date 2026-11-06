import { test } from "node:test";
import assert from "node:assert/strict";
import { workSchema } from "./schema.ts";

const base = {
  slug: "x-y",
  title: "X",
  originalTitle: null,
  originalTitleRomanized: null,
  authors: ["a-b"],
  language: "português",
  firstPublished: null,
  type: "romance",
  genres: [],
  themes: ["memória"],
  edition: {
    title: null,
    language: null,
    publisher: null,
    year: null,
    isbn13: null,
    isbn10: null,
    format: null,
    match: "representative" as const,
  },
  cover: null,
  catalogerNote: null,
  confidence: "high" as const,
  references: [],
  legacyId: null,
  audit: { validationStatus: null, sourceConflicts: null, validatedAt: null },
};

test("tags é opcional: obra sem tags e obra com tags são válidas", () => {
  assert.ok(workSchema.safeParse(base).success);
  assert.ok(
    workSchema.safeParse({ ...base, tags: ["tempo e memória", "Nova York"] }).success,
  );
  assert.ok(workSchema.safeParse({ ...base, tags: [] }).success);
});

test("tags rejeita item vazio e continua barrando campos desconhecidos", () => {
  assert.equal(workSchema.safeParse({ ...base, tags: [""] }).success, false);
  assert.equal(workSchema.safeParse({ ...base, keywords: ["x"] }).success, false);
});

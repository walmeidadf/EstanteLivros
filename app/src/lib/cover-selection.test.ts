import { test } from "node:test";
import assert from "node:assert/strict";
import { coverFields, localCover } from "./cover-selection.ts";

test("sem capa ou só proveniência: nada local, foco central", () => {
  assert.deepEqual(coverFields(null), {
    coverFile: null,
    coverFocus: "center",
    coverDisplay: null,
  });
  assert.deepEqual(coverFields({}), coverFields(null));
  assert.equal(localCover(coverFields(null)), null);
});

test("capa real escolhida: usa o mestre com o foco do catálogo", () => {
  const fields = coverFields({ file: "covers/x-y.jpg", focus: "top" });
  assert.deepEqual(localCover(fields), { file: "covers/x-y.jpg", focus: "top" });
});

test("sem foco no catálogo, o corte é central", () => {
  const fields = coverFields({ file: "covers/x-y.jpg", focus: null });
  assert.deepEqual(localCover(fields), { file: "covers/x-y.jpg", focus: "center" });
});

test("revisada como tipográfica: ignora o mestre, mesmo que exista", () => {
  const fields = coverFields({ file: "covers/x-y.jpg", display: "typographic" });
  assert.equal(fields.coverDisplay, "typographic");
  assert.equal(localCover(fields), null);
  assert.equal(localCover(coverFields({ display: "typographic" })), null);
});

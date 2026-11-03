import { test } from "node:test";
import assert from "node:assert/strict";
import { fold, matches, search, type SearchEntry } from "./search.ts";

/* ---- fold ---- */

test("fold remove acento e baixa a caixa", () => {
  assert.equal(fold("José"), "jose");
  assert.equal(fold("SARAMAGO"), "saramago");
  assert.equal(fold("Ensaio sobre a Cegueira"), "ensaio sobre a cegueira");
});

test("fold trata acento no meio da palavra", () => {
  assert.equal(fold("coração"), "coracao");
  assert.equal(fold("Mémoires"), "memoires");
});

test("fold troca pontuação por espaço e apara", () => {
  assert.equal(fold("  A Vegetariana (채식주의자)  "), "a vegetariana 채식주의자");
  assert.equal(fold("Crime e Castigo — Fiódor"), "crime e castigo fiodor");
});

test("fold preserva caracteres não latinos", () => {
  // CJK e cirílico não têm diacríticos combinantes a remover.
  assert.equal(fold("채식주의자"), "채식주의자");
  assert.equal(fold("Преступление"), "преступление");
});

/* ---- matches ---- */

const vegetariana: SearchEntry = {
  type: "work",
  slug: "a-vegetariana-han-kang",
  label: "A Vegetariana",
  href: "/obra/a-vegetariana-han-kang",
  keys: fold("A Vegetariana 채식주의자 Chaesikjuuija"),
};

const saramago: SearchEntry = {
  type: "author",
  slug: "jose-saramago",
  label: "José Saramago",
  href: "/autoria/jose-saramago",
  keys: fold("José Saramago"),
};

test("matches casa sem acento e sem caixa", () => {
  assert.equal(matches(saramago, fold("jose")), true);
  assert.equal(matches(saramago, fold("SARAMAGO")), true);
  assert.equal(matches(saramago, fold("saramago")), true);
});

test("matches exige todos os termos, em qualquer ordem", () => {
  assert.equal(matches(saramago, fold("jose sara")), true);
  assert.equal(matches(saramago, fold("saramago jose")), true);
  assert.equal(matches(saramago, fold("jose dinis")), false);
});

test("matches acha pelo título original e pela romanização", () => {
  assert.equal(matches(vegetariana, fold("vegetariana")), true);
  assert.equal(matches(vegetariana, fold("채식")), true);
  assert.equal(matches(vegetariana, fold("chaesik")), true);
});

test("matches com consulta vazia não casa", () => {
  assert.equal(matches(saramago, fold("")), false);
  assert.equal(matches(saramago, fold("   ")), false);
});

/* ---- search ---- */

test("search filtra, ordena na ordem de entrada e limita", () => {
  const entries: SearchEntry[] = [vegetariana, saramago];
  assert.deepEqual(search(entries, "jose").map((e) => e.slug), ["jose-saramago"]);
  assert.deepEqual(search(entries, "a").map((e) => e.slug), [
    "a-vegetariana-han-kang",
    "jose-saramago",
  ]);
  assert.equal(search(entries, "").length, 0);
  assert.equal(search(entries, "a", 1).length, 1);
});

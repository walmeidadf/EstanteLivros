import { test } from "node:test";
import assert from "node:assert/strict";
import {
  compareBy,
  toDataset,
  fromDataset,
  type SortData,
} from "./grid-sort.ts";

function d(seq: number, title: string, author: string, year: number | null): SortData {
  return { seq, title, author, year };
}

const items = [
  d(3, "zebra", "ana", 1990),
  d(1, "abelha", "caio", null),
  d(2, "morro", "ana", 1950),
  d(4, "cedro", "beto", 1990),
];

function order(key: Parameters<typeof compareBy>[0]): number[] {
  return [...items].sort(compareBy(key)).map((i) => i.seq);
}

test("seq: ordem do caderno", () => {
  assert.deepEqual(order("seq"), [1, 2, 3, 4]);
});

test("title: alfabética, tolerante ao dobramento prévio", () => {
  assert.deepEqual(order("title"), [1, 4, 2, 3]);
});

test("author: por autoria, depois título, depois seq", () => {
  // ana(morro 2, zebra 3), beto(4), caio(1)
  assert.deepEqual(order("author"), [2, 3, 4, 1]);
});

test("year: crescente, sem ano por último, empate pela seq", () => {
  assert.deepEqual(order("year"), [2, 3, 4, 1]);
});

test("empate total é estável pela seq", () => {
  const same = [d(2, "x", "a", 1), d(1, "x", "a", 1)];
  assert.deepEqual(same.sort(compareBy("title")).map((i) => i.seq), [1, 2]);
});

test("dois sem ano ficam pela seq", () => {
  const a = [d(5, "t", "a", null), d(2, "u", "b", null)];
  assert.deepEqual(a.sort(compareBy("year")).map((i) => i.seq), [2, 5]);
});

test("dataset: ida e volta, com e sem ano", () => {
  for (const item of [items[0]!, items[1]!]) {
    const attrs = toDataset(item);
    const ds: Record<string, string> = {};
    for (const [k, v] of Object.entries(attrs)) ds[k.replace("data-", "")] = v;
    assert.deepEqual(fromDataset(ds), item);
  }
  assert.equal(toDataset(items[1]!)["data-year"], "");
});

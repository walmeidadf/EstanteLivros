/*
 * Ordenação da grade de obras (Idioma e Tema, S4 R10).
 *
 * Roda nas duas pontas: no build (`toDataset` grava os `data-*` de cada peça) e
 * no navegador (a ilha de WorkGrid lê os `data-*` com `fromDataset` e ordena
 * com `compareBy`). `title` e `author` chegam JÁ DOBRADOS (sem acento, minúsculas,
 * via `fold` de search.ts), então o cliente só compara strings.
 *
 * Todo comparador termina em `seq`, o que torna a ordenação total e estável.
 * Puro e sem DOM — roda sob `node --test`.
 */

export type SortKey = "seq" | "title" | "author" | "year";

export type SortData = {
  /** Ordem do caderno: sequence da primeira leitura da obra. */
  seq: number;
  /** Título pt-BR dobrado. */
  title: string;
  /** Nome da primeira autoria, dobrado. */
  author: string;
  /** Ano da primeira publicação, ou null. */
  year: number | null;
};

const collator = new Intl.Collator("pt-BR");

function bySeq(a: SortData, b: SortData): number {
  return a.seq - b.seq;
}

/** Comparador total e estável para a chave pedida. */
export function compareBy(key: SortKey): (a: SortData, b: SortData) => number {
  switch (key) {
    case "title":
      return (a, b) => collator.compare(a.title, b.title) || bySeq(a, b);
    case "author":
      return (a, b) =>
        collator.compare(a.author, b.author) ||
        collator.compare(a.title, b.title) ||
        bySeq(a, b);
    case "year":
      return (a, b) => {
        if (a.year === null && b.year === null) return bySeq(a, b);
        if (a.year === null) return 1; // sem ano vai para o fim
        if (b.year === null) return -1;
        return a.year - b.year || bySeq(a, b);
      };
    default:
      return bySeq;
  }
}

/** Pares chave/valor para os atributos `data-*` de uma peça. */
export function toDataset(d: SortData): Record<string, string> {
  return {
    "data-seq": String(d.seq),
    "data-title": d.title,
    "data-author": d.author,
    "data-year": d.year === null ? "" : String(d.year),
  };
}

/** Lê o `dataset` (chaves camelCase: seq, title, author, year) de volta. */
export function fromDataset(ds: Record<string, string | undefined>): SortData {
  const year = ds["year"];
  return {
    seq: Number(ds["seq"] ?? 0),
    title: ds["title"] ?? "",
    author: ds["author"] ?? "",
    year: year === undefined || year === "" ? null : Number(year),
  };
}

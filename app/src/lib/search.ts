/*
 * Busca — normalização e formato do índice (regra compartilhada).
 *
 * Este módulo é a ÚNICA fonte da regra de busca, usada nas duas pontas:
 *   - no build, para gerar as chaves do índice estático (search-index.json);
 *   - no cliente, na ilha de busca, para filtrar o que a leitora digita.
 *
 * Manter uma função só (`fold`) nos dois lados evita divergência: uma chave
 * indexada e uma consulta são normalizadas exatamente igual (design §7).
 *
 * Puro e sem dependências — roda sob `node --test` e no navegador.
 */

/** Uma entrada do índice de busca (uma por obra e uma por autoria). */
export type SearchEntry = {
  type: "work" | "author";
  slug: string;
  /** Rótulo de exibição (título pt-BR ou nome da autoria). */
  label: string;
  /** Destino do resultado (/obra/{slug} ou /autoria/{slug}). */
  href: string;
  /** Chaves de busca já normalizadas e concatenadas. */
  keys: string;
};

/**
 * Dobra um texto para comparação: remove acentos, baixa a caixa e troca
 * pontuação por espaço. "José Saramago (Ensaio…)" → "jose saramago ensaio".
 *
 * Preserva letras e números de qualquer alfabeto (CJK, cirílico, hebraico),
 * que não têm diacríticos latinos a remover — então um título em coreano
 * continua buscável pelos seus próprios caracteres. Recompõe em NFC no fim
 * para que o Hangul (decomposto em jamo pela NFD) volte à forma normal e o
 * resultado não dependa da normalização do texto de entrada.
 */
export function fold(text: string): string {
  return text
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "") // remove diacríticos combinantes
    .normalize("NFC") // recompõe (Hangul, etc.) à forma canônica
    .toLowerCase()
    .replace(/[^\p{L}\p{N}]+/gu, " ") // pontuação/símbolos → espaço
    .trim();
}

/**
 * Casa uma consulta já dobrada contra uma entrada. Cada termo da consulta
 * (separado por espaço) precisa aparecer como substring nas chaves da entrada
 * — assim "jose sara" casa "jose saramago …", e a ordem não importa.
 * Consulta vazia não casa nada (a ilha nem chama com vazio).
 */
export function matches(entry: SearchEntry, foldedQuery: string): boolean {
  const terms = foldedQuery.split(/\s+/).filter((t) => t.length > 0);
  if (terms.length === 0) return false;
  return terms.every((term) => entry.keys.includes(term));
}

/**
 * Filtra e ordena as entradas para uma consulta crua (ainda não dobrada),
 * limitando a `limit` resultados. Usada pela ilha; exposta aqui para ser
 * testável sem DOM.
 */
export function search(
  entries: readonly SearchEntry[],
  rawQuery: string,
  limit = 20,
): SearchEntry[] {
  const q = fold(rawQuery);
  if (q.length === 0) return [];
  const hits = entries.filter((e) => matches(e, q));
  return hits.slice(0, limit);
}

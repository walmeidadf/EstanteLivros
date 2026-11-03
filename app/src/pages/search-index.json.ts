/*
 * Índice de busca estático (emitido no build).
 *
 * Endpoint do Astro que gera `/search-index.json`: uma entrada por obra
 * (chaves: título pt-BR + título original + romanização) e uma por autoria
 * (nome). As chaves já saem normalizadas pela MESMA `fold` que a ilha de busca
 * usa no cliente (design §7.2), então indexação e consulta não divergem.
 *
 * Com `output: "static"`, o Astro pré-renderiza este endpoint no build e grava
 * o JSON como asset do site. Nenhuma rede, nenhum passo manual (R7.9).
 */
import type { APIRoute } from "astro";
import { getCatalog } from "@/lib/catalog/index.ts";
import { fold, type SearchEntry } from "@/lib/search.ts";

export const prerender = true;

export const GET: APIRoute = () => {
  const catalog = getCatalog();
  const entries: SearchEntry[] = [];

  for (const work of catalog.works) {
    const keySource = [
      work.title,
      work.originalTitle,
      work.originalTitleRomanized,
    ]
      .filter((s): s is string => Boolean(s))
      .join(" ");
    entries.push({
      type: "work",
      slug: work.slug,
      label: work.title,
      href: `/obra/${work.slug}`,
      keys: fold(keySource),
    });
  }

  for (const author of catalog.authors) {
    entries.push({
      type: "author",
      slug: author.slug,
      label: author.name,
      href: `/autoria/${author.slug}`,
      keys: fold(author.name),
    });
  }

  return new Response(JSON.stringify(entries), {
    headers: { "content-type": "application/json; charset=utf-8" },
  });
};

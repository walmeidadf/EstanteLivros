/*
 * Integridade de rotas (executa em teste; pode rodar no build).
 *
 * Reúne todos os `href` para `/obra/{slug}` e `/autoria/{slug}` que as camadas
 * de seleção (home, timeline, atlas) e o índice de busca emitem, com a origem
 * de cada um. Um teste compara o conjunto com os slugs do catálogo e falha se
 * algum link apontar para uma página que a S5 não gera — pegando link órfão no
 * `node --test`, antes do build (R14.2).
 *
 * Puro: recebe o `Catalog` e devolve dados; não toca em Astro nem em disco.
 */
import type { Catalog } from "./catalog/index.ts";
import { buildHome } from "./home.ts";
import { buildTimeline, buildYear, buildUndated } from "./timeline.ts";
import {
  buildAtlasShared,
  buildLanguagePages,
  buildCountryPages,
  buildThemePages,
} from "./atlas.ts";

/** Um link coletado, com a tela/bloco de origem (para a mensagem de erro). */
export type CollectedLink = { href: string; from: string };

/** true para `/obra/…`; separa os dois universos de destino. */
function isWork(href: string): boolean {
  return href.startsWith("/obra/");
}

function slugOf(href: string): string {
  return href.replace(/^\/(obra|autoria)\//, "").replace(/\/$/, "");
}

/**
 * Todos os links de obra e autoria emitidos pelo app. Varre as mesmas funções
 * que as páginas usam, para refletir o que de fato vai ao HTML.
 */
export function allWorkAndAuthorLinks(catalog: Catalog): CollectedLink[] {
  const links: CollectedLink[] = [];
  const add = (href: string, from: string) => links.push({ href, from });

  // Início.
  const home = buildHome(catalog);
  for (const rail of [home.currentYear, home.rereads, ...home.themeRails]) {
    if (!rail) continue;
    // O título do carrossel leva a /ano, /tema ou /linha-do-tempo — não a
    // obra/autoria; só os ITENS (capas) levam à obra.
    for (const item of rail.items) add(item.href, `home: carrossel "${rail.title}"`);
  }
  if (home.recurringAuthors) {
    for (const pick of home.recurringAuthors) {
      add(pick.href, "home: quem sempre volta");
    }
  }

  // Linha do tempo: faixas (anos) + cada tela Ano + "sem data".
  buildTimeline(catalog); // faixas levam a /ano/{ano}, não a obra/autoria
  for (const year of knownYears(catalog)) {
    for (const item of buildYear(catalog, year).items) {
      add(item.href, `ano/${year}`);
    }
  }
  const undated = buildUndated(catalog);
  if (undated) for (const item of undated.items) add(item.href, "ano/sem-data");

  // Atlas: blocos compartilhados (Quem ela mais lê).
  const shared = buildAtlasShared(catalog);
  if (shared.authors) {
    for (const pick of shared.authors) add(pick.href, "atlas: quem ela mais lê");
  }

  // Idioma: grade de obras + carrossel de autorias.
  for (const page of buildLanguagePages(catalog)) {
    for (const g of page.items) add(g.href, `idioma/${page.slug}`);
    if (page.authors) for (const p of page.authors) add(p.href, `idioma/${page.slug}: autorias`);
  }

  // País: grade de obras + destaque de autoria.
  for (const page of buildCountryPages(catalog)) {
    for (const g of page.items) add(g.href, `pais/${page.slug}`);
    if (page.topAuthor) add(page.topAuthor.href, `pais/${page.slug}: destaque`);
  }

  // Tema: grade de obras.
  for (const page of buildThemePages(catalog)) {
    for (const g of page.items) add(g.href, `tema/${page.slug}`);
  }

  // Índice de busca: uma entrada por obra e por autoria.
  for (const work of catalog.works) add(`/obra/${work.slug}`, "busca");
  for (const author of catalog.authors) add(`/autoria/${author.slug}`, "busca");

  return links;
}

/** Anos com ao menos uma leitura (fonte dos recortes de Ano). */
function knownYears(catalog: Catalog): number[] {
  return [...catalog.aggregates.readingsByYear.keys()];
}

/** Links de obra/autoria que não correspondem a nenhuma página gerada. */
export function orphanLinks(catalog: Catalog): CollectedLink[] {
  const works = catalog.worksBySlug;
  const authors = catalog.authorsBySlug;
  const orphans: CollectedLink[] = [];
  for (const link of allWorkAndAuthorLinks(catalog)) {
    const slug = slugOf(link.href);
    const exists = isWork(link.href) ? works.has(slug) : authors.has(slug);
    if (!exists) orphans.push(link);
  }
  return orphans;
}

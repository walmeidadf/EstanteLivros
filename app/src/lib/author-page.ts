/*
 * Recorte da página de Autoria (executa no build).
 *
 * `buildAuthorPage(catalog, slug)` recebe o catálogo já modelado e agregado
 * (getCatalog()) e devolve tudo que `/autoria/{slug}` mostra, já pronto para o
 * layout: contexto (país/idiomas) com links, big numbers com a posição no
 * ranking, bio com a fonte citada, a grade "Na estante" com a legenda por obra
 * e os temas que mais aparecem. A página `.astro` só posiciona. Puro, sem
 * dependências de Astro.
 *
 * Regras herdadas e fixadas:
 *   - posição = 1 + autorias com estritamente MAIS leituras; só se ≤ 10 (R9);
 *   - a posição usa `readingsByAuthor` (mesma base de "Quem ela mais lê"),
 *     não um agregado novo (R13.4);
 *   - "livros lidos" conta OBRAS distintas; "primeira leitura" é o menor ano;
 *   - bio e fonte vêm do mesmo summary aprovado; sem bio, a seção some (R10);
 *   - temas: só os que aparecem em 2+ obras da autoria, top 10 (R12);
 *   - dado ausente some, sem "—" (handoff §8).
 */
import type { Catalog } from "./catalog/index.ts";
import type { AuthorView, BioSource } from "./catalog/model.ts";
import { slugifyTheme, themeHref } from "./home.ts";
import {
  TOP_AUTHORS,
  capitalizeFirst,
  countryHref,
  firstSequence,
  languageHref,
  toGridWork,
  type BigNumber,
  type GridWork,
} from "./atlas.ts";

/* -------------------------------------------------------------------- tipos */

/** Crédito da foto (atribuição), para a linha discreta sob o retrato. */
export type PhotoCredit = {
  author: string | null;
  license: string | null;
  sourceUrl: string | null;
};

/** Um pedaço com texto e, opcionalmente, link. */
export type ContextPiece = { text: string; href?: string };

/** Linha "{País} · escreve em {idiomas}" já montada em pedaços. */
export type ContextLine = {
  country: ContextPiece | null;
  languages: ContextPiece[];
};

/** Um chip de tema da autoria, com a contagem de obras dela. */
export type ThemeChip = { label: string; href: string; count: number };

export type AuthorPage = {
  author: AuthorView;
  /** Dados do retrato (a foto é derivada na página; aqui só a cor do anel). */
  portrait: { ring: true; language: string };
  credit: PhotoCredit | null;
  context: ContextLine;
  numbers: BigNumber[];
  bio: { text: string; source: BioSource | null } | null;
  works: GridWork[];
  captionFor: (slug: string) => string;
  themes: ThemeChip[] | null;
};

/* ---------------------------------------------------------------- ranking */

/** Posição no ranking de leituras; `tied` quando há empate na mesma contagem. */
export type AuthorRank = { position: number; tied: boolean } | null;

/**
 * Posição da autoria por número de LEITURAS (mesma base de "Quem ela mais lê"):
 * `position = 1 + (autorias com contagem estritamente maior)`. `tied` indica
 * que outra autoria tem exatamente a mesma contagem (posição compartilhada).
 * `null` se a autoria não tem leitura.
 */
export function authorRank(catalog: Catalog, slug: string): AuthorRank {
  const mine = catalog.aggregates.readingsByAuthor.get(slug);
  if (mine === undefined || mine === 0) return null;
  let greater = 0;
  let equals = 0;
  for (const [other, count] of catalog.aggregates.readingsByAuthor) {
    if (other === slug) continue;
    if (count > mine) greater += 1;
    else if (count === mine) equals += 1;
  }
  return { position: greater + 1, tied: equals > 0 };
}

/* ------------------------------------------------------------------ builder */

export function buildAuthorPage(catalog: Catalog, slug: string): AuthorPage {
  const author = catalog.authorsBySlug.get(slug);
  if (!author) throw new Error(`autoria inexistente: ${slug}`);

  const works = [...author.works]
    .sort((a, b) => firstSequence(a) - firstSequence(b) || a.slug.localeCompare(b.slug))
    .map(toGridWork);

  return {
    author,
    portrait: { ring: true, language: author.primaryLanguage },
    credit: author.photo
      ? { author: author.photo.author, license: author.photo.license, sourceUrl: author.photo.sourceUrl }
      : null,
    context: buildContext(author),
    numbers: buildNumbers(catalog, author),
    bio: author.bio ? { text: author.bio, source: author.bioSource } : null,
    works,
    captionFor: captionBuilder(author),
    themes: buildThemes(author),
  };
}

/* ----------------------------------------------------------------- contexto */

function buildContext(author: AuthorView): ContextLine {
  const country =
    author.countryName !== null
      ? { text: author.countryName, href: countryHref(author.countryName) }
      : null;
  const languages = author.languages.map((lang) => ({
    text: capitalizeFirst(lang),
    href: languageHref(lang),
  }));
  return { country, languages };
}

/* ------------------------------------------------------------------ números */

function buildNumbers(catalog: Catalog, author: AuthorView): BigNumber[] {
  const numbers: BigNumber[] = [];

  const read = author.works.length;
  numbers.push({ value: String(read), label: read === 1 ? "livro lido" : "livros lidos" });

  const rank = authorRank(catalog, author.slug);
  if (rank && rank.position <= TOP_AUTHORS) {
    numbers.push({
      value: `${rank.position}º`,
      label: rank.tied ? "posição na estante (empatada)" : "posição na estante",
    });
  } else {
    const first = firstReadingYear(author);
    if (first !== null) {
      numbers.push({ value: String(first), label: "primeira leitura" });
    }
  }

  return numbers;
}

/** Menor ano entre as leituras datadas de todas as obras da autoria. */
function firstReadingYear(author: AuthorView): number | null {
  let min: number | null = null;
  for (const work of author.works) {
    for (const r of work.readings) {
      if (r.year !== null && (min === null || r.year < min)) min = r.year;
    }
  }
  return min;
}

/* ------------------------------------------------------- legenda da grade */

/**
 * Monta "lido em {ano}" por obra, juntando as leituras daquela obra:
 *   - um ano → "lido em 2022";
 *   - vários → "lido em 2022 e 2025" (ou "2019, 2022 e 2025");
 *   - sem data → "nº {N} da lista";
 *   - mistura → anos primeiro, depois "nº N da lista".
 */
function captionBuilder(author: AuthorView): (slug: string) => string {
  const bySlug = new Map(author.works.map((w) => [w.slug, w] as const));
  return (slug: string): string => {
    const work = bySlug.get(slug);
    if (!work) return "";
    const years: number[] = [];
    const undated: number[] = [];
    for (const r of work.readings) {
      if (r.year !== null) years.push(r.year);
      else undated.push(r.sequence);
    }
    years.sort((a, b) => a - b);
    const parts: string[] = [];
    if (years.length > 0) parts.push(`lido em ${joinPt(years.map(String))}`);
    for (const seq of undated) parts.push(`nº ${seq} da lista`);
    return parts.join("; ");
  };
}

/** Junta em pt-BR: ["a"] → "a"; ["a","b"] → "a e b"; ["a","b","c"] → "a, b e c". */
function joinPt(items: string[]): string {
  if (items.length <= 1) return items.join("");
  return `${items.slice(0, -1).join(", ")} e ${items[items.length - 1]}`;
}

/* ------------------------------------------------------------------- temas */

/**
 * Temas que mais aparecem nos livros da autoria (R12): conta por OBRA,
 * agrupando variantes de caixa/acento pelo slug; mantém só os que aparecem em
 * 2+ obras; top 10 por contagem desc, empate pelo nome (pt-BR). O rótulo é a
 * variante mais frequente (empate: a de menor caixa; depois pt-BR).
 */
const THEME_MIN_WORKS = 2;
const THEME_LIMIT = 10;
const collator = new Intl.Collator("pt-BR");

function buildThemes(author: AuthorView): ThemeChip[] | null {
  // Por slug: nº de obras e contagem por variante exibida.
  const bySlug = new Map<string, { works: number; variants: Map<string, number> }>();
  for (const work of author.works) {
    // Um tema conta uma vez por obra mesmo se repetir dentro da obra.
    const seen = new Set<string>();
    for (const theme of work.themes) {
      const slug = slugifyTheme(theme);
      if (seen.has(slug)) continue;
      seen.add(slug);
      const entry = bySlug.get(slug) ?? { works: 0, variants: new Map() };
      entry.works += 1;
      entry.variants.set(theme, (entry.variants.get(theme) ?? 0) + 1);
      bySlug.set(slug, entry);
    }
  }

  const chips: ThemeChip[] = [];
  for (const [, entry] of bySlug) {
    if (entry.works < THEME_MIN_WORKS) continue;
    const label = capitalizeFirst(pickVariant(entry.variants));
    chips.push({ label, href: themeHref(label), count: entry.works });
  }
  if (chips.length === 0) return null;

  chips.sort((a, b) => b.count - a.count || collator.compare(a.label, b.label));
  return chips.slice(0, THEME_LIMIT);
}

/** Variante mais frequente; empate: a de menor caixa (minúscula), depois pt-BR. */
function pickVariant(variants: Map<string, number>): string {
  let best: string | null = null;
  let bestCount = -1;
  for (const [variant, count] of variants) {
    if (
      count > bestCount ||
      (count === bestCount && best !== null && preferLower(variant, best))
    ) {
      best = variant;
      bestCount = count;
    }
  }
  return best ?? "";
}

/** true quando `a` é preferível a `b`: menos maiúsculas, depois ordem pt-BR. */
function preferLower(a: string, b: string): boolean {
  const ua = uppercaseCount(a);
  const ub = uppercaseCount(b);
  if (ua !== ub) return ua < ub;
  return collator.compare(a, b) < 0;
}

function uppercaseCount(s: string): number {
  let n = 0;
  for (const ch of s) if (ch !== ch.toLowerCase() && ch === ch.toUpperCase()) n += 1;
  return n;
}

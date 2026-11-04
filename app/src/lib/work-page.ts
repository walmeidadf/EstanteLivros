/*
 * Recorte da página de Obra (executa no build).
 *
 * `buildWorkPage(catalog, slug)` recebe o catálogo já modelado e agregado
 * (getCatalog()) e devolve tudo que `/obra/{slug}` mostra, já pronto para o
 * layout: títulos com lang/dir resolvidos, ficha com as linhas vazias já
 * removidas, leituras rotuladas, temas com contagem só quando frequente,
 * edição com o rótulo certo e o registro do catálogo. A página `.astro` só
 * posiciona (design §"Camada de seleção"). Puro, sem dependências de Astro.
 *
 * Regras herdadas e fixadas:
 *   - título original só quando difere do pt-BR por fold (R2.4);
 *   - releitura é a POSIÇÃO na ordem, não o campo `reread` (R4.4);
 *   - só o ANO existe (nunca dia/mês); sem ano vira "Os primeiros da lista";
 *   - contagem de tema só a partir de CLOUD_MIN_WORKS obras (R5.2);
 *   - dado ausente some: a linha/bloco não aparece, sem "—" (handoff §8).
 */
import type { Catalog } from "./catalog/index.ts";
import type { ReadingView, WorkView } from "./catalog/model.ts";
import { authorHref, themeHref, slugifyTheme, yearHref } from "./home.ts";
import {
  CLOUD_MIN_WORKS,
  capitalizeFirst,
  countryHref,
  languageHref,
} from "./atlas.ts";
import {
  originalTitlePresentation,
  type OriginalTitlePresentation,
} from "./text.ts";

/* -------------------------------------------------------------------- tipos */

/** Um link de ficha (ex.: idioma, país, tema). */
export type FactLink = { text: string; href: string };

/** Uma linha da ficha: texto puro ou lista de links. */
export type Fact =
  | { label: string; kind: "text"; text: string }
  | { label: string; kind: "links"; links: FactLink[] };

/** Autoria com o destino montado. */
export type AuthorLink = { name: string; href: string; slug: string };

/** Uma linha de leitura (tela Obra). */
export type ReadingLine = {
  /** Ano + href, ou null quando "sem data". */
  year: { value: number; href: string } | null;
  /** Link de "sem data" quando não há ano. */
  undatedHref: string | null;
  /** "primeira leitura" | "releitura" (pela POSIÇÃO, não por `reread`). */
  role: "primeira leitura" | "releitura";
  sequence: number;
};

/** Um chip de tema; `count` só quando o tema é frequente na estante. */
export type ThemeChip = { label: string; href: string; count: number | null };

/** Caixa da edição de referência. */
export type EditionBox = {
  label: string;
  lines: { label: string; value: string }[];
};

/** Uma entrada de "Como estava no caderno". */
export type NotebookEntry = { when: string; text: string };

export type OriginalTitle = OriginalTitlePresentation;

export type WorkPage = {
  work: WorkView;
  /** Título original pronto (lang/dir/fonte), ou null. */
  original: OriginalTitle | null;
  /** Romanização, quando houver (linha à parte, sem lang). */
  romanized: string | null;
  authors: AuthorLink[];
  facts: Fact[];
  readings: ReadingLine[];
  readingsHeading: string;
  themes: ThemeChip[] | null;
  edition: EditionBox | null;
  catalogerNote: string | null;
  notebook: NotebookEntry[];
};

/* ------------------------------------------------------------------ builder */

export function buildWorkPage(catalog: Catalog, slug: string): WorkPage {
  const work = catalog.worksBySlug.get(slug);
  if (!work) throw new Error(`obra inexistente: ${slug}`);

  return {
    work,
    original: originalTitlePresentation(work.language, work.title, work.originalTitle),
    romanized: cleanText(work.originalTitleRomanized),
    authors: work.authors.map((a) => ({
      name: a.name,
      slug: a.slug,
      href: authorHref(a.slug),
    })),
    facts: buildFacts(work),
    readings: buildReadingLines(work.readings),
    readingsHeading: readingsHeading(work.readings.length),
    themes: buildThemeChips(catalog, work),
    edition: buildEdition(work),
    catalogerNote: cleanText(work.catalogerNote),
    notebook: buildNotebook(work.readings),
  };
}

/* ------------------------------------------------------------------- ficha */

function buildFacts(work: WorkView): Fact[] {
  const facts: Fact[] = [];

  facts.push({
    label: "Idioma original",
    kind: "links",
    links: [{ text: capitalizeFirst(work.language), href: languageHref(work.language) }],
  });

  const countryLinks = countryFactLinks(work);
  if (countryLinks.length > 0) {
    facts.push({
      label: countryLinks.length > 1 ? "Países" : "País",
      kind: "links",
      links: countryLinks,
    });
  }

  if (work.firstPublished !== null) {
    facts.push({
      label: "Primeira publicação",
      kind: "text",
      text: String(work.firstPublished),
    });
  }

  facts.push({ label: "Tipo", kind: "text", text: capitalizeFirst(work.type) });

  if (work.genres.length > 0) {
    facts.push({
      label: work.genres.length > 1 ? "Gêneros" : "Gênero",
      kind: "text",
      text: work.genres.map(capitalizeFirst).join(", "),
    });
  }

  return facts;
}

/**
 * Links de país: um por país das autorias (`work.countries`, ISO-2), resolvendo
 * o nome pelo `countryName` da autoria daquele código. Mantém a ordem de
 * `work.countries`. Países sem nome resolvido são omitidos.
 */
function countryFactLinks(work: WorkView): FactLink[] {
  const nameByCode = new Map<string, string>();
  for (const author of work.authors) {
    if (author.country && author.countryName) {
      nameByCode.set(author.country, author.countryName);
    }
  }
  const links: FactLink[] = [];
  for (const code of work.countries) {
    const name = nameByCode.get(code);
    if (name) links.push({ text: name, href: countryHref(name) });
  }
  return links;
}

/* ---------------------------------------------------------------- leituras */

function buildReadingLines(readings: ReadingView[]): ReadingLine[] {
  // Já vêm ordenadas por sequence do modelo; a primeira da ordem é a primeira
  // leitura, as demais são releituras — pela POSIÇÃO, não pelo campo `reread`.
  return readings.map((r, index) => ({
    year: r.year !== null ? { value: r.year, href: yearHref(r.year) } : null,
    undatedHref: r.year === null ? "/ano/sem-data" : null,
    role: index === 0 ? "primeira leitura" : "releitura",
    sequence: r.sequence,
  }));
}

function readingsHeading(count: number): string {
  if (count <= 1) return "Lido uma vez";
  if (count === 2) return "Lido duas vezes";
  return `Lido ${count} vezes`;
}

/* ------------------------------------------------------------------- temas */

function buildThemeChips(catalog: Catalog, work: WorkView): ThemeChip[] | null {
  if (work.themes.length === 0) return null;

  const chips = work.themes.map((theme) => {
    const count = themeWorkCount(catalog, theme);
    return {
      label: capitalizeFirst(theme),
      href: themeHref(theme),
      count: count >= CLOUD_MIN_WORKS ? count : null,
      _count: count,
    };
  });

  // Ordem: por nº de obras na estante (desc), empate pela ordem do caderno
  // (estável, já que `work.themes` preserva a ordem de origem).
  chips.sort((a, b) => b._count - a._count);

  return chips.map(({ label, href, count }) => ({ label, href, count }));
}

/**
 * Nº de obras na estante com um tema, agrupando variantes que diferem só por
 * caixa/acento (mesmo slug) — igual à nuvem do Atlas. Soma as contagens de
 * todas as variantes que colapsam no mesmo slug.
 */
function themeWorkCount(catalog: Catalog, theme: string): number {
  const slug = slugifyTheme(theme);
  let total = 0;
  for (const { key, count } of catalog.aggregates.worksByThemeDesc) {
    if (slugifyTheme(key) === slug) total += count;
  }
  return total;
}

/* ------------------------------------------------------------------ edição */

function buildEdition(work: WorkView): EditionBox | null {
  const e = work.edition;
  const lines: { label: string; value: string }[] = [];

  if (e.publisher) lines.push({ label: "Editora", value: e.publisher });
  if (e.year !== null) lines.push({ label: "Ano", value: String(e.year) });
  if (e.isbn13) lines.push({ label: "ISBN", value: e.isbn13 });

  if (lines.length === 0) return null;

  return { label: editionLabel(work), lines };
}

/**
 * Rótulo da caixa de edição (R6.2/6.3):
 *   - exact → "Edição lida";
 *   - representative em português → "Edição brasileira de referência";
 *   - representative nos demais idiomas → "Edição de referência".
 */
export function editionLabel(work: WorkView): string {
  if (work.edition.match === "exact") return "Edição lida";
  return work.edition.language === "português"
    ? "Edição brasileira de referência"
    : "Edição de referência";
}

/* ---------------------------------------------------------------- caderno */

function buildNotebook(readings: ReadingView[]): NotebookEntry[] {
  return readings
    .filter((r) => r.originalEntry.trim() !== "")
    .map((r) => ({
      when: r.year !== null ? `em ${r.year}` : `nº ${r.sequence} da lista`,
      text: r.originalEntry,
    }));
}

/* ------------------------------------------------------------------ util */

function cleanText(value: string | null | undefined): string | null {
  const t = (value ?? "").trim();
  return t === "" ? null : t;
}

/*
 * Recortes do Atlas, de Idioma, de País e de Tema (executa no build).
 *
 * Mesma fronteira de `home.ts` e `timeline.ts`: recebe o catálogo já modelado e
 * agregado (getCatalog()) e devolve tudo que as telas da S4 mostram, já pronto
 * para o layout. É aqui que moram as regras — as páginas `.astro` só iteram e
 * posicionam. Puro e sem dependências de Astro, para rodar sob `node --test`.
 *
 * Regras herdadas e fixadas:
 *   - o país de uma obra é o país da(s) AUTORIA(s); uma obra com autorias de
 *     países diferentes conta e aparece em cada um (handoff §6.5);
 *   - a ordem das lombadas e das grades é a ordem do caderno (sequence da
 *     primeira leitura da obra); faixas e grades têm UMA peça por OBRA;
 *   - temas que diferem só por caixa/acento (mesmo slug) são um tema só;
 *   - obras sem país ficam fora da vista por país, sem aviso (handoff §8).
 *
 * Recortes sem conteúdo voltam como `null`, para a página omiti-los.
 */
import type { Catalog } from "./catalog/index.ts";
import type { AuthorView, WorkView } from "./catalog/model.ts";
import {
  DEFAULT_RAIL_CAP,
  authorHref,
  slugifyTheme,
  themeHref,
  type AuthorPick,
} from "./home.ts";
import { languageColor, onGround } from "./language-color.ts";
import { fold } from "./search.ts";
import type { SortData } from "./grid-sort.ts";

export type { SortData } from "./grid-sort.ts";

/* ------------------------------------------------------------------ tipos */

/** Faixa pronta para o <YearBand>. */
export type BandData = {
  label: string;
  /** Ausente = faixa sem link (bloco "Outros países"). */
  href?: string;
  count: number;
  spines: { language: string }[];
};

/** Uma peça da grade de obras (uma por OBRA). */
export type GridWork = { work: WorkView; href: string; sort: SortData };

/** Um número grande (valor já formatado + rótulo no singular/plural certo). */
export type BigNumber = { value: string; label: string };

export type OthersBlock = {
  /** Faixa "Outros países" (sem href). */
  band: BandData;
  /** Um chip por país agrupado, por quantidade desc. */
  countries: { name: string; href: string; count: number }[];
};

export type AtlasByCountry = {
  bands: BandData[];
  others: OthersBlock | null;
};

export type ThemeCloudItem = {
  label: string;
  href: string;
  count: number;
  /** Degrau de tamanho: 1 (menor) .. 4 (maior). */
  tier: 1 | 2 | 3 | 4;
};

export type EraBar = {
  id: string;
  label: string;
  count: number;
  /** Largura da barra, relativa à maior época (0..100). */
  pct: number;
};

export type AtlasShared = {
  authors: AuthorPick[] | null;
  cloud: ThemeCloudItem[] | null;
  eras: EraBar[] | null;
};

export type LanguagePage = {
  slug: string;
  /** Nome para exibir ("Português"). */
  name: string;
  /** Chave do catálogo ("português"). */
  language: string;
  color: { bg: string; ink: string };
  numbers: BigNumber[];
  authors: AuthorPick[] | null;
  items: GridWork[];
};

export type CountryPage = {
  slug: string;
  name: string;
  dominantLanguage: string;
  /** Cor do nome do país, legível sobre --ground. */
  nameColor: string;
  /** Cor exata do idioma dominante (filete). */
  swatch: string;
  sharing: { name: string; href: string }[] | null;
  summary: string | null;
  numbers: BigNumber[];
  topAuthor: AuthorPick | null;
  items: GridWork[];
};

export type ThemePage = {
  slug: string;
  name: string;
  numbers: BigNumber[];
  items: GridWork[];
};

/* --------------------------------------------------------------- constantes */

/** Faixas individuais de país antes do bloco "Outros países" (handoff §6.5). */
export const COUNTRY_BANDS = 10;
/** Quantas autorias entram em "Quem ela mais lê". */
export const TOP_AUTHORS = 10;
/** Nuvem de temas: piso de obras e teto de itens. */
export const CLOUD_MIN_WORKS = 5;
export const CLOUD_LIMIT = 30;

/* ------------------------------------------------------------------ helpers */

const collator = new Intl.Collator("pt-BR");

function byText(a: string, b: string): number {
  return collator.compare(a, b);
}

export function languageHref(language: string): string {
  return `/idioma/${slugifyTheme(language)}`;
}

export function countryHref(name: string): string {
  return `/pais/${slugifyTheme(name)}`;
}

/** "segunda guerra" → "Segunda guerra". Só exibição; o dado não muda. */
export function capitalizeFirst(text: string): string {
  const first = text.charAt(0);
  return first.toLocaleUpperCase("pt-BR") + text.slice(1);
}

/** "1 leitura" / "N leituras". */
export function readingsLabel(n: number): string {
  return n === 1 ? "1 leitura" : `${n} leituras`;
}

function plural(n: number, one: string, many: string): string {
  return n === 1 ? one : many;
}

function bigNumber(n: number, one: string, many: string): BigNumber {
  return { value: String(n), label: plural(n, one, many) };
}

/** Ordem do caderno de uma obra: sequence da primeira leitura. */
export function firstSequence(work: WorkView): number {
  return work.readings[0]?.sequence ?? Number.MAX_SAFE_INTEGER;
}

/** Obras na ordem do caderno (desempate estável por slug). */
function inNotebookOrder(works: Iterable<WorkView>): WorkView[] {
  return [...works].sort(
    (a, b) => firstSequence(a) - firstSequence(b) || a.slug.localeCompare(b.slug),
  );
}

function spinesOf(works: WorkView[]): { language: string }[] {
  return works.map((w) => ({ language: w.language }));
}

/** Monta a peça de grade (destino da obra + dados de ordenação já dobrados). */
export function toGridWork(work: WorkView): GridWork {
  return {
    work,
    href: `/obra/${work.slug}`,
    sort: {
      seq: firstSequence(work),
      title: fold(work.title),
      author: fold(work.authors[0]?.name ?? ""),
      year: work.firstPublished,
    },
  };
}

function distinctAuthors(works: WorkView[]): Map<string, AuthorView> {
  const map = new Map<string, AuthorView>();
  for (const w of works) for (const a of w.authors) map.set(a.slug, a);
  return map;
}

/** Lança se dois nomes produzirem o mesmo slug (rotas estáticas ambíguas). */
function assertUniqueSlugs(kind: string, names: string[]): void {
  const seen = new Map<string, string>();
  for (const name of names) {
    const slug = slugifyTheme(name);
    const other = seen.get(slug);
    if (other !== undefined && other !== name) {
      throw new Error(
        `Colisão de slug de ${kind}: "${other}" e "${name}" → "${slug}".`,
      );
    }
    seen.set(slug, name);
  }
}

/* ----------------------------------------------------- índices (memoizados) */

type CountryEntry = {
  code: string;
  name: string;
  works: WorkView[];
  /** Idioma original mais frequente entre as obras do país. */
  dominant: string;
};

const countryCache = new WeakMap<Catalog, CountryEntry[]>();

/** Países com ao menos uma obra, em ordem de quantidade desc e nome. */
function countryIndex(catalog: Catalog): CountryEntry[] {
  const cached = countryCache.get(catalog);
  if (cached) return cached;

  const names = new Map<string, string>();
  for (const a of catalog.authors) {
    if (a.country && a.countryName && !names.has(a.country)) {
      names.set(a.country, a.countryName);
    }
  }

  const byCode = new Map<string, WorkView[]>();
  for (const work of catalog.works) {
    for (const code of work.countries) {
      const list = byCode.get(code) ?? [];
      list.push(work);
      byCode.set(code, list);
    }
  }

  const entries: CountryEntry[] = [...byCode.entries()].map(([code, works]) => {
    const ordered = inNotebookOrder(works);
    const langs = new Map<string, number>();
    for (const w of ordered) langs.set(w.language, (langs.get(w.language) ?? 0) + 1);
    const dominant = [...langs.entries()].sort(
      (a, b) => b[1] - a[1] || byText(a[0], b[0]),
    )[0]![0];
    return { code, name: names.get(code) ?? code, works: ordered, dominant };
  });

  entries.sort((a, b) => b.works.length - a.works.length || byText(a.name, b.name));
  countryCache.set(catalog, entries);
  return entries;
}

type ThemeEntry = { slug: string; label: string; works: WorkView[] };

const themeCache = new WeakMap<Catalog, ThemeEntry[]>();

/**
 * Temas agrupados por slug (variantes de caixa/acento viram um só), contados
 * por obra distinta. Rótulo = variante com mais obras; empate: a minúscula;
 * depois ordem pt-BR. Lista em quantidade desc e rótulo.
 */
function themeIndex(catalog: Catalog): ThemeEntry[] {
  const cached = themeCache.get(catalog);
  if (cached) return cached;

  type Acc = { works: Map<string, WorkView>; variants: Map<string, Set<string>> };
  const groups = new Map<string, Acc>();
  for (const work of catalog.works) {
    for (const theme of work.themes) {
      const slug = slugifyTheme(theme);
      if (slug === "") continue;
      const acc = groups.get(slug) ?? { works: new Map(), variants: new Map() };
      acc.works.set(work.slug, work);
      const v = acc.variants.get(theme) ?? new Set<string>();
      v.add(work.slug);
      acc.variants.set(theme, v);
      groups.set(slug, acc);
    }
  }

  const entries: ThemeEntry[] = [...groups.entries()].map(([slug, acc]) => {
    const label = [...acc.variants.entries()].sort((a, b) => {
      if (b[1].size !== a[1].size) return b[1].size - a[1].size;
      const aLower = a[0] === a[0].toLowerCase();
      const bLower = b[0] === b[0].toLowerCase();
      if (aLower !== bLower) return aLower ? -1 : 1;
      return byText(a[0], b[0]);
    })[0]![0];
    return { slug, label, works: inNotebookOrder(acc.works.values()) };
  });

  entries.sort((a, b) => b.works.length - a.works.length || byText(a.label, b.label));
  themeCache.set(catalog, entries);
  return entries;
}

/* ------------------------------------------------------- Atlas · por idioma */

/** Uma faixa por idioma original, por quantidade de obras (desc). */
export function buildAtlasByLanguage(catalog: Catalog): BandData[] {
  return catalog.aggregates.worksByLanguageDesc.map(({ key: language, count }) => {
    const works = inNotebookOrder(catalog.works.filter((w) => w.language === language));
    return {
      label: capitalizeFirst(language),
      href: languageHref(language),
      count,
      spines: spinesOf(works),
    };
  });
}

/* --------------------------------------------------------- Atlas · por país */

export function buildAtlasByCountry(catalog: Catalog): AtlasByCountry {
  const entries = countryIndex(catalog);

  const toBand = (e: CountryEntry): BandData => ({
    label: e.name,
    href: countryHref(e.name),
    count: e.works.length,
    spines: spinesOf(e.works),
  });

  let individual = entries.slice(0, COUNTRY_BANDS);
  let rest = entries.slice(COUNTRY_BANDS);
  // Agrupar um país só não economiza nada: ele vira a faixa seguinte.
  if (rest.length === 1) {
    individual = entries;
    rest = [];
  }

  if (rest.length === 0) return { bands: individual.map(toBand), others: null };

  const distinct = new Map<string, WorkView>();
  for (const e of rest) for (const w of e.works) distinct.set(w.slug, w);
  const works = inNotebookOrder(distinct.values());

  return {
    bands: individual.map(toBand),
    others: {
      band: { label: "Outros países", count: works.length, spines: spinesOf(works) },
      countries: rest.map((e) => ({
        name: e.name,
        href: countryHref(e.name),
        count: e.works.length,
      })),
    },
  };
}

/* ------------------------------------------------- blocos compartilhados */

/** As autorias com mais leituras; desempate pelo nome. Null sem autorias. */
export function topAuthors(
  catalog: Catalog,
  limit: number = TOP_AUTHORS,
): AuthorPick[] | null {
  const picks: AuthorPick[] = [];
  for (const [slug, readings] of catalog.aggregates.readingsByAuthor) {
    const author = catalog.authorsBySlug.get(slug);
    if (author) picks.push({ author, readings, href: authorHref(slug) });
  }
  if (picks.length === 0) return null;
  picks.sort((a, b) => b.readings - a.readings || byText(a.author.name, b.author.name));
  return picks.slice(0, limit);
}

/** Degrau de tamanho pela razão ao maior (R5.2). */
function tierFor(count: number, max: number): 1 | 2 | 3 | 4 {
  const ratio = count / max;
  if (ratio >= 0.6) return 4;
  if (ratio >= 0.3) return 3;
  if (ratio >= 0.15) return 2;
  return 1;
}

/** Nuvem de temas: os mais frequentes, exibidos em ordem alfabética. */
export function themeCloud(catalog: Catalog): ThemeCloudItem[] | null {
  const top = themeIndex(catalog)
    .filter((t) => t.works.length >= CLOUD_MIN_WORKS)
    .slice(0, CLOUD_LIMIT);
  if (top.length === 0) return null;
  const max = top[0]!.works.length;
  return top
    .map((t) => ({
      label: t.label,
      href: `/tema/${t.slug}`,
      count: t.works.length,
      tier: tierFor(t.works.length, max),
    }))
    .sort((a, b) => byText(a.label, b.label));
}

/** Épocas de `firstPublished`; cronológicas. Null se nenhuma obra tem ano. */
export function eras(catalog: Catalog): EraBar[] | null {
  const defs: { id: string; label: string; test: (y: number) => boolean; optional?: boolean }[] = [
    { id: "pre-1800", label: "antes de 1800", test: (y) => y < 1800, optional: true },
    { id: "xix", label: "séc. XIX", test: (y) => y >= 1800 && y < 1900 },
    { id: "xx", label: "séc. XX", test: (y) => y >= 1900 && y < 2000 },
    { id: "2000s", label: "2000s", test: (y) => y >= 2000 && y < 2010 },
    { id: "2010s", label: "2010s", test: (y) => y >= 2010 && y < 2020 },
    { id: "2020s", label: "2020s", test: (y) => y >= 2020 },
  ];

  const years = catalog.works
    .map((w) => w.firstPublished)
    .filter((y): y is number => y !== null);
  if (years.length === 0) return null;

  const counted = defs
    .map((d) => ({ d, count: years.filter(d.test).length }))
    .filter(({ d, count }) => !(d.optional && count === 0));
  const max = Math.max(...counted.map((c) => c.count));

  return counted.map(({ d, count }) => ({
    id: d.id,
    label: d.label,
    count,
    pct: max > 0 ? Math.round((count / max) * 100) : 0,
  }));
}

export function buildAtlasShared(catalog: Catalog): AtlasShared {
  return {
    authors: topAuthors(catalog),
    cloud: themeCloud(catalog),
    eras: eras(catalog),
  };
}

/* ---------------------------------------------------------------- Tema */

export function buildThemePages(catalog: Catalog): ThemePage[] {
  return themeIndex(catalog).map((t) => ({
    slug: t.slug,
    name: capitalizeFirst(t.label),
    numbers: [
      bigNumber(t.works.length, "obra", "obras"),
      bigNumber(distinctAuthors(t.works).size, "autoria", "autorias"),
      bigNumber(new Set(t.works.map((w) => w.language)).size, "idioma", "idiomas"),
    ],
    items: t.works.map(toGridWork),
  }));
}

/* -------------------------------------------------------------- Idioma */

function percentLabel(count: number, total: number): string {
  if (count === 0 || total === 0) return "0%";
  const pct = Math.round((count / total) * 100);
  return pct === 0 ? "<1%" : `${pct}%`;
}

export function buildLanguagePages(catalog: Catalog): LanguagePage[] {
  const languages = catalog.aggregates.worksByLanguageDesc.map((c) => c.key);
  assertUniqueSlugs("idioma", languages);
  const total = catalog.works.length;

  return languages.map((language) => {
    const works = inNotebookOrder(catalog.works.filter((w) => w.language === language));
    const authors = distinctAuthors(works);

    // Autorias por nº de obras NO idioma (desc), depois nome.
    const counts = new Map<string, number>();
    for (const w of works) for (const a of w.authors) counts.set(a.slug, (counts.get(a.slug) ?? 0) + 1);
    const ranked: AuthorPick[] = [...counts.entries()]
      .map(([slug, n]) => ({ author: authors.get(slug)!, readings: n, href: authorHref(slug) }))
      .sort((a, b) => b.readings - a.readings || byText(a.author.name, b.author.name));

    return {
      slug: slugifyTheme(language),
      name: capitalizeFirst(language),
      language,
      color: languageColor(language),
      numbers: [
        bigNumber(works.length, "obra", "obras"),
        { value: percentLabel(works.length, total), label: "da estante" },
        bigNumber(authors.size, "autoria", "autorias"),
      ],
      authors: ranked.length > 1 ? ranked.slice(0, DEFAULT_RAIL_CAP) : null,
      items: works.map(toGridWork),
    };
  });
}

/* --------------------------------------------------------------- País */

export function buildCountryPages(catalog: Catalog): CountryPage[] {
  const entries = countryIndex(catalog);
  assertUniqueSlugs("país", entries.map((e) => e.name));

  return entries.map((entry) => {
    const { bg } = languageColor(entry.dominant);

    const sharing = entries
      .filter((o) => o.code !== entry.code && o.dominant === entry.dominant)
      .map((o) => ({ name: o.name, href: countryHref(o.name) }));

    const authors = catalog.authors.filter((a) => a.country === entry.code && a.works.length > 0);

    // Destaque: máximo ÚNICO de leituras e ≥ 2.
    let topAuthor: AuthorPick | null = null;
    const ranked = authors
      .map((a) => ({ a, n: catalog.aggregates.readingsByAuthor.get(a.slug) ?? 0 }))
      .sort((x, y) => y.n - x.n || byText(x.a.name, y.a.name));
    const best = ranked[0];
    if (best && best.n >= 2 && (ranked[1]?.n ?? 0) < best.n) {
      topAuthor = { author: best.a, readings: best.n, href: authorHref(best.a.slug) };
    }

    return {
      slug: slugifyTheme(entry.name),
      name: entry.name,
      dominantLanguage: entry.dominant,
      nameColor: onGround(bg),
      swatch: bg,
      sharing: sharing.length ? sharing : null,
      summary: catalog.approvedSummaryByScope.get(`pais:${entry.code}`) ?? null,
      numbers: [
        bigNumber(entry.works.length, "obra", "obras"),
        bigNumber(authors.length, "autoria", "autorias"),
      ],
      topAuthor,
      items: entry.works.map(toGridWork),
    };
  });
}

// `themeHref` é reexportado para as páginas/componentes que montam links de tema.
export { themeHref };

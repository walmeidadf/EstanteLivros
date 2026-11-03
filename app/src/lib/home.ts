/*
 * Recortes da tela Início (executa no build).
 *
 * `buildHome()` recebe o catálogo já modelado e agregado (getCatalog()) e
 * devolve tudo que a página `/` mostra, já pronto para o layout. É aqui que
 * moram as regras de seleção do Início — a página `.astro` só itera e posiciona
 * (design §4). Puro e sem dependências de Astro, para rodar sob `node --test`.
 *
 * Regras herdadas e fixadas:
 *   - "ano atual" = o maior ano COM leitura (não o relógio do build), para a
 *     estante nunca abrir vazia em começo de ano (design §3.1/§11);
 *   - "quem sempre volta" = autorias com 3+ leituras (handoff §6.1);
 *   - 4 temas mais frequentes, teto de ~20 itens por carrossel (handoff §9/§12);
 *   - "lidos duas vezes" = releituras, uma peça por obra (nunca duplicada);
 *   - barras da linha do tempo só com anos conhecidos (sem "sem data").
 *
 * Seções que não têm conteúdo voltam como `null`, para a página omiti-las sem
 * espalhar condicionais (handoff §8: nada de "—" nem título vazio).
 */
import type { AuthorView, WorkView } from "./catalog/model.ts";
import type { Catalog } from "./catalog/index.ts";

/** Teto de itens visíveis num carrossel antes do cartão "ver todos" (handoff §9). */
export const DEFAULT_RAIL_CAP = 20;

/** Quantos carrosséis de tema o Início mostra (handoff §12.4). */
export const THEME_RAIL_COUNT = 4;

/** Corte de leituras para "quem sempre volta" (handoff §6.1). */
export const RECURRING_MIN_READINGS = 3;

/** Um item de capa: a obra e para onde ela leva. */
export type CaptionItem = {
  work: WorkView;
  /** Destino do item (página da obra, S5). */
  href: string;
};

/** Um carrossel de capas: título-link, itens (já cortados) e o total real. */
export type RailSection = {
  title: string;
  /** Destino do título e do cartão "ver todos". */
  href: string;
  items: CaptionItem[];
  /** Total de obras no recorte (N do "ver todos (N)"), antes do teto. */
  total: number;
};

/** Uma autoria em "quem sempre volta". */
export type AuthorPick = {
  author: AuthorView;
  readings: number;
  /** Destino do avatar (página da autoria, S5). */
  href: string;
};

/** Uma barra do mini-gráfico da linha do tempo. */
export type YearBar = {
  year: number;
  count: number;
  /** true no ano atual (destaque em --accent). */
  current: boolean;
};

export type HomeData = {
  /** "Em {ano atual}" — null quando nenhum ano tem leitura. */
  currentYear: RailSection | null;
  /** Ano usado no destaque (para o rótulo), ou null. */
  currentYearValue: number | null;
  /** "Quem sempre volta" — null quando ninguém atinge o corte. */
  recurringAuthors: AuthorPick[] | null;
  /** Carrosséis de tema (0..THEME_RAIL_COUNT). */
  themeRails: RailSection[];
  /** "Lidos duas vezes" — null quando não há releitura. */
  rereads: RailSection | null;
  /** Barras por ano conhecido, do mais antigo ao mais recente. */
  yearBars: YearBar[];
};

export function workHref(slug: string): string {
  return `/obra/${slug}`;
}

export function authorHref(slug: string): string {
  return `/autoria/${slug}`;
}

export function yearHref(year: number): string {
  return `/ano/${year}`;
}

export function themeHref(theme: string): string {
  return `/tema/${slugifyTheme(theme)}`;
}

/** Slug de um tema para a URL. Tolerante a acento, igual ao resto do app. */
export function slugifyTheme(theme: string): string {
  return theme
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

/** Monta todos os recortes do Início. */
export function buildHome(
  catalog: Catalog,
  railCap: number = DEFAULT_RAIL_CAP,
): HomeData {
  const currentYearValue = latestYearWithReading(catalog);

  return {
    currentYearValue,
    currentYear: buildCurrentYear(catalog, currentYearValue, railCap),
    recurringAuthors: buildRecurringAuthors(catalog),
    themeRails: buildThemeRails(catalog, railCap),
    rereads: buildRereads(catalog, railCap),
    yearBars: buildYearBars(catalog, currentYearValue),
  };
}

/** Maior ano com ao menos uma leitura, ou null se não houver nenhum. */
function latestYearWithReading(catalog: Catalog): number | null {
  const years = [...catalog.aggregates.readingsByYear.keys()];
  return years.length ? Math.max(...years) : null;
}

function buildCurrentYear(
  catalog: Catalog,
  year: number | null,
  railCap: number,
): RailSection | null {
  if (year === null) return null;

  // Obras com alguma leitura no ano, ordenadas pela sequence daquela leitura
  // (ordem do caderno). Uma obra relida no mesmo ano aparece uma vez.
  const inYear: { work: WorkView; sequence: number }[] = [];
  for (const work of catalog.works) {
    const reading = work.readings.find((r) => r.year === year);
    if (reading) inYear.push({ work, sequence: reading.sequence });
  }
  if (inYear.length === 0) return null;

  inYear.sort((a, b) => a.sequence - b.sequence);
  const items = inYear.map(({ work }) => ({ work, href: workHref(work.slug) }));

  return {
    title: `Em ${year}`,
    href: yearHref(year),
    items: items.slice(0, railCap),
    total: items.length,
  };
}

function buildRecurringAuthors(catalog: Catalog): AuthorPick[] | null {
  const picks: AuthorPick[] = [];
  for (const { key, count } of catalog.aggregates.readingsByAuthorDesc) {
    if (count < RECURRING_MIN_READINGS) break; // lista já é decrescente
    const author = catalog.authorsBySlug.get(key);
    if (!author) continue;
    picks.push({ author, readings: count, href: authorHref(author.slug) });
  }
  return picks.length ? picks : null;
}

function buildThemeRails(catalog: Catalog, railCap: number): RailSection[] {
  const topThemes = catalog.aggregates.worksByThemeDesc.slice(
    0,
    THEME_RAIL_COUNT,
  );

  const rails: RailSection[] = [];
  for (const { key: theme } of topThemes) {
    // Obras do tema, na ordem dos arquivos de obra (estável entre builds).
    const works = catalog.works.filter((w) => w.themes.includes(theme));
    if (works.length === 0) continue;
    const items = works.map((work) => ({ work, href: workHref(work.slug) }));
    rails.push({
      title: theme,
      href: themeHref(theme),
      items: items.slice(0, railCap),
      total: items.length,
    });
  }
  return rails;
}

function buildRereads(catalog: Catalog, railCap: number): RailSection | null {
  // Releituras: obras com mais de uma leitura, uma peça por obra.
  const works = catalog.works.filter((w) => w.reread);
  if (works.length === 0) return null;

  // Mais lidas primeiro; empate estável por título (pt-BR).
  const sorted = [...works].sort((a, b) => {
    if (b.readings.length !== a.readings.length) {
      return b.readings.length - a.readings.length;
    }
    return a.title.localeCompare(b.title, "pt-BR");
  });
  const items = sorted.map((work) => ({ work, href: workHref(work.slug) }));

  return {
    title: "Lidos duas vezes",
    href: "/linha-do-tempo",
    items: items.slice(0, railCap),
    total: items.length,
  };
}

function buildYearBars(catalog: Catalog, currentYear: number | null): YearBar[] {
  // Só anos conhecidos; do mais antigo ao mais recente (eixo do tempo).
  return [...catalog.aggregates.readingsByYear.entries()]
    .map(([year, count]) => ({ year, count, current: year === currentYear }))
    .sort((a, b) => a.year - b.year);
}

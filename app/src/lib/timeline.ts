/*
 * Recortes da linha do tempo, da tela Ano e de "sem data" (executa no build).
 *
 * Mesma fronteira do `home.ts`: recebe o catálogo já modelado e agregado
 * (getCatalog()) e devolve tudo que as três telas da S3 mostram, já pronto
 * para o layout. É aqui que moram as regras — as páginas `.astro` só iteram e
 * posicionam (design §4). Puro e sem dependências de Astro, para rodar sob
 * `node --test`.
 *
 * Regras herdadas e fixadas:
 *   - a linha do tempo é CRONOLÓGICA: faixas por ano, do mais recente ao mais
 *     antigo (não por quantidade, que é o `readingsByYearDesc` dos agregados);
 *   - uma lombada e uma peça de grade por LEITURA, não por obra — releitura
 *     conta em cada ano (modelo S1);
 *   - "ano atual" = o maior ano COM leitura (não o relógio), igual ao Início;
 *   - navegação anterior/próximo salta pelos anos que EXISTEM, não por ano ± 1;
 *   - resumo de ano só quando há summary `approved` de scope `ano:{ano}`;
 *   - só o ano existe: leitura sem ano mora em "Os primeiros da lista", pela
 *     sequence.
 *
 * Recortes que não têm conteúdo voltam como `null` (design §8).
 */
import type { WorkView } from "./catalog/model.ts";
import type { Catalog } from "./catalog/index.ts";

/** Uma lombada da faixa: só o idioma (a cor sai dele no componente Spine). */
export type BandSpine = { language: string };

/** Uma Faixa do ano pronta para a Linha do tempo. */
export type YearBandData = {
  year: number;
  /** Destino da faixa inteira. */
  href: string;
  /** Leituras do ano (releitura conta em cada ano). */
  count: number;
  /** 0..2 notas automáticas: principal + "N releituras". Nunca fixadas. */
  notes: string[];
  /** Uma lombada por leitura, na ordem do caderno. */
  spines: BandSpine[];
};

/** Um item de grade (tela Ano e Sem data). */
export type GridItem = {
  work: WorkView;
  /** Destino do item (página da obra, S5). */
  href: string;
  /** "nº N da lista" na tela Sem data; ausente na tela Ano. */
  undatedLabel?: string;
};

/** Um pedaço da barra de mix de idiomas do ano. */
export type LanguageSlice = {
  language: string;
  count: number;
  /** Percentual inteiro (0..100) para a largura da barra. */
  pct: number;
};

/** Tudo que a tela Ano mostra. */
export type YearData = {
  year: number;
  notes: string[];
  readings: number;
  languages: number;
  authors: number;
  rereads: number;
  mix: LanguageSlice[];
  /** Resumo aprovado, ou null (a seção some). */
  summary: string | null;
  /** Grade, ordem do caderno, uma peça por leitura. */
  items: GridItem[];
  /** Ano anterior existente, ou null (extremo). */
  prev: number | null;
  /** Próximo ano existente, ou null (extremo). */
  next: number | null;
};

/** "Os primeiros da lista", ou null quando não há leitura sem ano. */
export type UndatedData = {
  items: GridItem[];
} | null;

export function workHref(slug: string): string {
  return `/obra/${slug}`;
}

export function yearHref(year: number): string {
  return `/ano/${year}`;
}

/** Uma leitura de um ano, já resolvida à obra (uso interno). */
type YearReading = {
  work: WorkView;
  sequence: number;
  reread: boolean;
  language: string;
};

/** Anos com ao menos uma leitura, em ordem crescente. */
function knownYears(catalog: Catalog): number[] {
  return [...catalog.aggregates.readingsByYear.keys()].sort((a, b) => a - b);
}

/** Maior ano com leitura, ou null. Mesma regra do Início. */
function currentYear(catalog: Catalog): number | null {
  const years = knownYears(catalog);
  return years.length ? years[years.length - 1]! : null;
}

/**
 * Ano mais cheio (maior nº de leituras). Empate: o ano mais recente. Null se
 * não houver ano algum.
 */
function fullestYear(catalog: Catalog): number | null {
  let best: number | null = null;
  let bestCount = -1;
  for (const [year, count] of catalog.aggregates.readingsByYear) {
    if (count > bestCount || (count === bestCount && best !== null && year > best)) {
      best = year;
      bestCount = count;
    }
  }
  return best;
}

/** Leituras de um ano, resolvidas à obra, na ordem do caderno (sequence). */
function readingsInYear(catalog: Catalog, year: number): YearReading[] {
  const list: YearReading[] = [];
  for (const work of catalog.works) {
    for (const reading of work.readings) {
      if (reading.year === year) {
        list.push({
          work,
          sequence: reading.sequence,
          reread: reading.reread,
          language: work.language,
        });
      }
    }
  }
  list.sort((a, b) => a.sequence - b.sequence);
  return list;
}

/** Plural correto em pt-BR para a nota de releituras. */
function rereadNote(n: number): string {
  return n === 1 ? "1 releitura" : `${n} releituras`;
}

/**
 * Notas automáticas de um ano (design §4, R3). Principal: "em andamento" (ano
 * atual, prioridade) ou "o ano mais cheio da estante"; complementar: "N
 * releituras". Podem coexistir; podem ser nenhuma.
 */
function notesFor(
  year: number,
  rereadsInYear: number,
  current: number | null,
  fullest: number | null,
): string[] {
  const notes: string[] = [];
  if (year === current) {
    notes.push("em andamento");
  } else if (year === fullest) {
    notes.push("o ano mais cheio da estante");
  }
  if (rereadsInYear > 0) {
    notes.push(rereadNote(rereadsInYear));
  }
  return notes;
}

/** Faixas da linha do tempo, do ano mais recente ao mais antigo (R2, R3). */
export function buildTimeline(catalog: Catalog): YearBandData[] {
  const current = currentYear(catalog);
  const fullest = fullestYear(catalog);

  // Anos decrescentes (eixo cronológico), não por quantidade.
  const years = knownYears(catalog).reverse();

  return years.map((year) => {
    const readings = readingsInYear(catalog, year);
    const rereads = readings.filter((r) => r.reread).length;
    return {
      year,
      href: yearHref(year),
      count: readings.length,
      notes: notesFor(year, rereads, current, fullest),
      spines: readings.map((r) => ({ language: r.language })),
    };
  });
}

/** Dados da tela Ano (R5, R6, R7). Pressupõe um ano com ao menos uma leitura. */
export function buildYear(catalog: Catalog, year: number): YearData {
  const current = currentYear(catalog);
  const fullest = fullestYear(catalog);
  const readings = readingsInYear(catalog, year);

  const rereads = readings.filter((r) => r.reread).length;

  // Idiomas distintos e mix por idioma (desc, com percentual).
  const byLanguage = new Map<string, number>();
  for (const r of readings) {
    byLanguage.set(r.language, (byLanguage.get(r.language) ?? 0) + 1);
  }
  const total = readings.length;
  const mix: LanguageSlice[] = [...byLanguage.entries()]
    .map(([language, count]) => ({
      language,
      count,
      pct: total ? Math.round((count / total) * 100) : 0,
    }))
    .sort((a, b) => {
      if (b.count !== a.count) return b.count - a.count;
      return a.language.localeCompare(b.language, "pt-BR");
    });

  // Autorias distintas no ano (uma leitura pode ter várias autorias).
  const authorSlugs = new Set<string>();
  for (const r of readings) {
    for (const a of r.work.authors) authorSlugs.add(a.slug);
  }

  const years = knownYears(catalog);
  const idx = years.indexOf(year);
  const prev = idx > 0 ? years[idx - 1]! : null;
  const next = idx >= 0 && idx < years.length - 1 ? years[idx + 1]! : null;

  return {
    year,
    notes: notesFor(year, rereads, current, fullest),
    readings: readings.length,
    languages: byLanguage.size,
    authors: authorSlugs.size,
    rereads,
    mix,
    summary: catalog.approvedSummaryByScope.get(`ano:${year}`) ?? null,
    items: readings.map((r) => ({ work: r.work, href: workHref(r.work.slug) })),
    prev,
    next,
  };
}

/** "Os primeiros da lista" (R8): leituras sem ano, pela sequence. */
export function buildUndated(catalog: Catalog): UndatedData {
  const rows: { work: WorkView; sequence: number }[] = [];
  for (const work of catalog.works) {
    for (const reading of work.readings) {
      if (reading.year === null) {
        rows.push({ work, sequence: reading.sequence });
      }
    }
  }
  if (rows.length === 0) return null;

  rows.sort((a, b) => a.sequence - b.sequence);
  const items: GridItem[] = rows.map(({ work, sequence }) => ({
    work,
    href: workHref(work.slug),
    undatedLabel: `nº ${sequence} da lista`,
  }));
  return { items };
}

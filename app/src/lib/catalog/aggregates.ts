/*
 * Agregados (executa no build).
 *
 * Caminho de mão única, passo 3: agregar. Calcula uma vez as contagens que
 * quase toda tela pede, devolvendo para cada eixo tanto o mapa quanto a lista
 * já ordenada por quantidade (o design pede idiomas e países "por quantidade").
 *
 * Regras herdadas do modelo:
 *   - releitura conta no ano de CADA leitura (R5.5);
 *   - uma obra conta em CADA país das suas autorias (R5.6).
 */
import type { CatalogModel, WorkView } from "./model.ts";

export type Count<K> = { key: K; count: number };

export type Aggregates = {
  /** Leituras por ano (releitura conta em cada ano). Só anos conhecidos. */
  readingsByYear: Map<number, number>;
  readingsByYearDesc: Count<number>[];
  /** Leituras sem ano ("Os primeiros da lista"). */
  undatedCount: number;
  /** Obras por idioma original. */
  worksByLanguage: Map<string, number>;
  worksByLanguageDesc: Count<string>[];
  /** Obras por país da autoria (obra conta em cada país). */
  worksByCountry: Map<string, number>;
  worksByCountryDesc: Count<string>[];
  /** Leituras por autoria (base de "quem sempre volta"). */
  readingsByAuthor: Map<string, number>;
  readingsByAuthorDesc: Count<string>[];
  /** Obras por tema (base da nuvem de temas). */
  worksByTheme: Map<string, number>;
  worksByThemeDesc: Count<string>[];
};

export function buildAggregates(model: CatalogModel): Aggregates {
  const readingsByYear = new Map<number, number>();
  let undatedCount = 0;
  const worksByLanguage = new Map<string, number>();
  const worksByCountry = new Map<string, number>();
  const readingsByAuthor = new Map<string, number>();
  const worksByTheme = new Map<string, number>();

  for (const work of model.works) {
    inc(worksByLanguage, work.language);

    for (const country of work.countries) {
      inc(worksByCountry, country);
    }

    for (const theme of work.themes) {
      inc(worksByTheme, theme);
    }

    for (const reading of work.readings) {
      if (reading.year === null) {
        undatedCount += 1;
      } else {
        inc(readingsByYear, reading.year);
      }
    }

    // Leituras por autoria: cada leitura conta para cada autoria da obra.
    for (const author of work.authors) {
      incBy(readingsByAuthor, author.slug, countReadings(work));
    }
  }

  return {
    readingsByYear,
    readingsByYearDesc: toDesc(readingsByYear),
    undatedCount,
    worksByLanguage,
    worksByLanguageDesc: toDesc(worksByLanguage),
    worksByCountry,
    worksByCountryDesc: toDesc(worksByCountry),
    readingsByAuthor,
    readingsByAuthorDesc: toDesc(readingsByAuthor),
    worksByTheme,
    worksByThemeDesc: toDesc(worksByTheme),
  };
}

function countReadings(work: WorkView): number {
  return work.readings.length;
}

function inc<K>(map: Map<K, number>, key: K): void {
  map.set(key, (map.get(key) ?? 0) + 1);
}

function incBy<K>(map: Map<K, number>, key: K, by: number): void {
  if (by === 0) return;
  map.set(key, (map.get(key) ?? 0) + by);
}

/**
 * Lista ordenada por contagem decrescente. Empates: ordem estável por chave
 * (número crescente ou string em pt-BR), para builds reproduzíveis.
 */
function toDesc<K extends string | number>(map: Map<K, number>): Count<K>[] {
  return [...map.entries()]
    .map(([key, count]) => ({ key, count }))
    .sort((a, b) => {
      if (b.count !== a.count) return b.count - a.count;
      if (typeof a.key === "number" && typeof b.key === "number") {
        return a.key - b.key;
      }
      return String(a.key).localeCompare(String(b.key), "pt-BR");
    });
}

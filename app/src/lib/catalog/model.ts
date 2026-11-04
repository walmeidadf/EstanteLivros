/*
 * Modelo de domínio (executa no build).
 *
 * Caminho de mão única, passo 2: modelar. Transforma o catálogo cru em um
 * grafo tipado e navegável, aplicando aqui — uma vez, para todas as telas — as
 * regras de negócio:
 *   - releitura = UMA obra com várias leituras (nunca duplicada);
 *   - só o ANO existe; leitura sem ano é "sem data" e guarda a sequence;
 *   - a bio de uma autoria só aparece se houver summary approved;
 *   - o país de uma obra vem do país das autorias.
 *
 * Componentes e páginas consomem este modelo, não os JSON crus.
 */
import { languageColor, type LanguageColor } from "../language-color.ts";
import type { RawCatalog } from "./load.ts";
import type { Work as RawWork } from "./schema.ts";

export type ReadingView = {
  sequence: number;
  /** Ano da leitura, ou null quando "sem data" (ver `undated`). */
  year: number | null;
  reread: boolean;
  /** true quando não há ano: a leitura mora em "Os primeiros da lista". */
  undated: boolean;
  /** Como a leitura estava no caderno (tela Obra, "Como estava no caderno"). */
  originalEntry: string;
};

export type PhotoView = {
  /** Caminho do mestre relativo a catalog/media/ (ex.: authors/han-kang.jpg). */
  file: string;
  /** Crédito da foto (atribuição). Nulos quando a fonte não os informa. */
  author: string | null;
  license: string | null;
  sourceUrl: string | null;
};

/** Fonte citada de uma bio (mesmo summary aprovado que a origina). */
export type BioSource = {
  /** Rótulo para exibir (ex.: "Wikipédia (pt)"). */
  label: string;
  url: string | null;
};

export type AuthorView = {
  slug: string;
  name: string;
  country: string | null;
  countryName: string | null;
  languages: string[];
  primaryLanguage: string;
  /** Cor do idioma principal — usada no avatar. */
  color: LanguageColor;
  photo: PhotoView | null;
  /** Bio só quando há summary approved; senão null (a seção "Sobre" some). */
  bio: string | null;
  /** Fonte da bio (do mesmo summary aprovado); null quando não há bio. */
  bioSource: BioSource | null;
  /** Obras da autoria na estante. */
  works: WorkView[];
};

export type WorkView = {
  slug: string;
  title: string;
  originalTitle: string | null;
  originalTitleRomanized: string | null;
  language: string;
  /** Cor do idioma original — eixo visual de lombadas e capas. */
  color: LanguageColor;
  firstPublished: number | null;
  type: string;
  genres: string[];
  themes: string[];
  authors: AuthorView[];
  /** Países das autorias (ISO-2), sem repetição — base do Atlas por país. */
  countries: string[];
  readings: ReadingView[];
  /** true quando a obra foi lida mais de uma vez (selo "2×"). */
  reread: boolean;
  edition: RawWork["edition"];
  /** URL de origem da capa — PROVENIÊNCIA apenas; nunca usada como src. */
  coverSourceUrl: string | null;
  catalogerNote: string | null;
};

export type CatalogModel = {
  works: WorkView[];
  authors: AuthorView[];
  worksBySlug: Map<string, WorkView>;
  authorsBySlug: Map<string, AuthorView>;
  /**
   * Texto dos summaries APROVADOS, por scope completo (ex.: "ano:2024",
   * "autoria:han-kang", "pais:PT"). É a mesma fonte da bio de autoria; o
   * resumo de ano (tela Ano, S3) consulta "ano:{ano}" aqui, para não reler
   * disco nem reclassificar aprovação.
   */
  approvedSummaryByScope: Map<string, string>;
};

/** Monta o grafo tipado a partir do catálogo cru já validado. */
export function buildModel(raw: RawCatalog): CatalogModel {
  const countryNameByCode = new Map(
    raw.vocabularies.countries.map((c) => [c.code, c.name] as const),
  );

  // Summaries aprovados, indexados pelo scope completo. Do mesmo laço sai a
  // bio de autoria (scope "autoria:{slug}") e o resumo de ano ("ano:{ano}",
  // consumido pela S3). Não aprovados ficam de fora — a seção some.
  const approvedSummaryByScope = new Map<string, string>();
  const bioBySlug = new Map<string, string>();
  const bioSourceBySlug = new Map<string, BioSource>();
  for (const s of raw.summaries) {
    if (!s.approved) continue;
    approvedSummaryByScope.set(s.scope, s.text);
    if (s.scope.startsWith("autoria:")) {
      const slug = s.scope.slice("autoria:".length);
      bioBySlug.set(slug, s.text);
      // A fonte citada da bio vem do mesmo summary aprovado. Só guardamos
      // quando há rótulo de fonte; a URL pode faltar (vira link só com url).
      if (s.source) {
        bioSourceBySlug.set(slug, { label: s.source, url: s.sourceUrl });
      }
    }
  }

  // Leituras por obra (uma obra, várias leituras), ordenadas por sequence.
  const readingsByWork = new Map<string, ReadingView[]>();
  for (const r of raw.readings) {
    const list = readingsByWork.get(r.work) ?? [];
    list.push({
      sequence: r.sequence,
      year: r.year,
      reread: r.reread,
      undated: r.year === null,
      originalEntry: r.originalEntry,
    });
    readingsByWork.set(r.work, list);
  }
  for (const list of readingsByWork.values()) {
    list.sort((a, b) => a.sequence - b.sequence);
  }

  // Nós de autoria (sem obras ainda; ligadas no segundo passo).
  const authorViews = new Map<string, AuthorView>();
  for (const a of raw.authors) {
    authorViews.set(a.slug, {
      slug: a.slug,
      name: a.name,
      country: a.country,
      countryName: a.country ? (countryNameByCode.get(a.country) ?? null) : null,
      languages: a.languages,
      primaryLanguage: a.primaryLanguage,
      color: languageColor(a.primaryLanguage),
      photo: a.photo
        ? {
            file: a.photo.file,
            author: a.photo.author,
            license: a.photo.license,
            sourceUrl: a.photo.sourceUrl,
          }
        : null,
      bio: bioBySlug.get(a.slug) ?? null,
      bioSource: bioBySlug.has(a.slug)
        ? (bioSourceBySlug.get(a.slug) ?? null)
        : null,
      works: [],
    });
  }

  // Nós de obra, ligando as autorias resolvidas.
  const workViews = new Map<string, WorkView>();
  for (const w of raw.works) {
    const authors = w.authors
      .map((slug) => authorViews.get(slug))
      .filter((a): a is AuthorView => a !== undefined);

    const countries = uniq(
      authors
        .map((a) => a.country)
        .filter((c): c is string => c !== null),
    );

    const readings = readingsByWork.get(w.slug) ?? [];

    const view: WorkView = {
      slug: w.slug,
      title: w.title,
      originalTitle: w.originalTitle,
      originalTitleRomanized: w.originalTitleRomanized,
      language: w.language,
      color: languageColor(w.language),
      firstPublished: w.firstPublished,
      type: w.type,
      genres: w.genres,
      themes: w.themes,
      authors,
      countries,
      readings,
      reread: readings.length > 1,
      edition: w.edition,
      coverSourceUrl: w.cover ? w.cover.sourceUrl : null,
      catalogerNote: w.catalogerNote,
    };
    workViews.set(w.slug, view);
  }

  // Ligar obras às autorias (back-reference), na ordem dos arquivos de obra.
  for (const view of workViews.values()) {
    for (const author of view.authors) {
      author.works.push(view);
    }
  }

  return {
    works: [...workViews.values()],
    authors: [...authorViews.values()],
    worksBySlug: workViews,
    authorsBySlug: authorViews,
    approvedSummaryByScope,
  };
}

function uniq<T>(items: T[]): T[] {
  return [...new Set(items)];
}

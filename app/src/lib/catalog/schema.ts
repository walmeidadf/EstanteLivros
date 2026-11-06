/*
 * Esquemas Zod que espelham os JSON Schema reais de `catalog/schema/`.
 *
 * Fonte de verdade: os arquivos em catalog/schema/*.json. Este módulo é um
 * espelho fiel deles — campo a campo, mesmos nomes, mesmas restrições. NÃO
 * seguir o JSON "sugerido" do DESIGN_HANDOFF §7.3 (que está desatualizado:
 * fala em CSV e em `bio` dentro da autoria). O modelo real é:
 *   - work.cover é objeto { sourceUrl, source } OU null (nunca string);
 *   - author.photo é objeto OU null; author.country é ISO-2 OU null;
 *   - NÃO há `bio` na autoria — a bio vive em summaries.json;
 *   - reading.year pode ser null; existem sequence e reread;
 *   - a bio é um summary com scope "autoria:{slug}" e approved.
 *
 * Os tipos TypeScript a jusante derivam destes esquemas (z.infer), de modo que
 * o código tipado nasce da validação, não à parte dela.
 */
import { z } from "zod";

/* ---- primitivas compartilhadas (iguais aos $defs dos JSON Schema) ---- */

const slug = z
  .string()
  .regex(/^[a-z0-9]+(-[a-z0-9]+)*$/)
  .max(80);

const text = z.string().min(1);
const optionalText = z.string().min(1).nullable();
const textList = z.array(z.string().min(1));
const optionalYear = z.number().int().min(1000).max(2100).nullable();
const isoDate = z.string().regex(/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/);
const httpUrl = z.string().regex(/^https?:\/\//);

/* ---- Obra (work.schema.json) ---- */

export const workSchema = z
  .object({
    slug,
    title: text,
    originalTitle: optionalText,
    originalTitleRomanized: optionalText,
    authors: z.array(slug).min(1),
    language: text,
    firstPublished: optionalYear,
    type: text,
    genres: textList,
    themes: textList,
    // Temas originais, só para registro (F2.3). Aditivo e opcional; o app não
    // os expõe em nenhuma tela.
    tags: textList.optional(),
    edition: z
      .object({
        title: optionalText,
        language: optionalText,
        publisher: optionalText,
        year: optionalYear,
        isbn13: z
          .string()
          .regex(/^97[89][0-9]{10}$/)
          .nullable(),
        isbn10: z
          .string()
          .regex(/^[0-9]{9}[0-9X]$/)
          .nullable(),
        format: optionalText,
        match: z.enum(["exact", "representative"]),
      })
      .strict(),
    // cover: objeto OU null — NUNCA string.
    // Campos de enriquecimento (file/license/credit/focus/display) são aditivos
    // e opcionais; obras ainda não enriquecidas trazem só sourceUrl/source.
    cover: z
      .object({
        sourceUrl: httpUrl,
        source: optionalText,
        file: z
          .string()
          .regex(/^covers\/[a-z0-9]+(-[a-z0-9]+)*\.(jpg|png|webp|gif)$/)
          .nullish(),
        license: optionalText.optional(),
        credit: optionalText.optional(),
        focus: z.enum(["top", "center", "bottom"]).nullish(),
        display: z.literal("typographic").nullish(),
      })
      .strict()
      .nullable(),
    catalogerNote: optionalText,
    confidence: z.enum(["high", "medium", "low"]),
    references: z.array(
      z
        .object({
          provider: z.enum([
            "literal",
            "openlibrary",
            "google_books",
            "wikidata",
            "web",
          ]),
          id: optionalText,
          url: httpUrl.nullable(),
          fields: optionalText,
        })
        .strict(),
    ),
    legacyId: z.string().min(1).nullable(),
    audit: z
      .object({
        validationStatus: optionalText,
        sourceConflicts: optionalText,
        validatedAt: isoDate.nullable(),
      })
      .strict(),
  })
  .strict();

/* ---- Autoria (author.schema.json) — SEM campo `bio` ---- */

export const authorSchema = z
  .object({
    slug,
    name: text,
    aliases: z.array(z.string().min(1)),
    country: z
      .string()
      .regex(/^[A-Z]{2}$/)
      .nullable(),
    countrySource: z
      .enum(["wikidata-citizenship", "wikidata-birthplace", "override"])
      .nullable(),
    languages: z.array(z.string().min(1)).min(1),
    primaryLanguage: text,
    wikidata: z
      .object({
        id: z
          .string()
          .regex(/^Q[0-9]+$/)
          .nullable(),
        status: z.enum([
          "confirmed",
          "probable",
          "manual",
          "ambiguous",
          "not_found",
          "none",
        ]),
        evidence: optionalText,
        rulesVersion: z.number().int().min(1),
      })
      .strict()
      .nullable(),
    // photo: objeto OU null.
    photo: z
      .object({
        file: z.string().regex(/^authors\/[a-z0-9]+(-[a-z0-9]+)*\.(jpg|png|webp|gif)$/),
        license: optionalText,
        author: optionalText,
        sourceUrl: httpUrl,
        source: z.enum(["commons", "wikipedia", "serpapi", "tavily", "manual"]),
      })
      .strict()
      .nullable(),
    references: z.array(
      z
        .object({
          provider: z.string().min(1),
          id: z.string().min(1).nullable(),
          url: httpUrl.nullable(),
        })
        .strict(),
    ),
  })
  .strict();

/* ---- Leituras (readings.schema.json) ---- */

export const readingSchema = z
  .object({
    sequence: z.number().int().min(1),
    year: optionalYear,
    work: slug,
    reread: z.boolean(),
    originalEntry: text,
    notes: z.string().min(1).nullable(),
  })
  .strict();

export const readingsFileSchema = z
  .object({ readings: z.array(readingSchema) })
  .strict();

/* ---- Resumos (summaries.schema.json) — a bio vive aqui ---- */

export const summaryScope = z
  .string()
  .regex(/^(autoria:[a-z0-9]+(-[a-z0-9]+)*|ano:[0-9]{4}|pais:[A-Z]{2})$/);

export const summarySchema = z
  .object({
    scope: summaryScope,
    text: z.string(),
    approved: z.boolean(),
    updatedAt: isoDate,
    source: z.string().min(1).nullable(),
    sourceUrl: httpUrl.nullable(),
    sourceLanguage: z
      .string()
      .regex(/^[a-z]{2,3}$/)
      .nullable(),
    model: z.string().min(1).nullable(),
    promptVersion: z.string().min(1).nullable(),
    editedBy: z.enum(["human"]).nullable(),
  })
  .strict();

export const summariesFileSchema = z
  .object({ summaries: z.array(summarySchema) })
  .strict();

/* ---- Vocabulários (vocabularies.schema.json) ---- */

const vocabList = z.array(z.string().min(1));

export const vocabulariesSchema = z
  .object({
    languages: vocabList,
    workTypes: vocabList,
    genres: vocabList,
    themes: vocabList,
    countries: z.array(
      z
        .object({
          code: z.string().regex(/^[A-Z]{2}$/),
          name: z.string().min(1),
          languages: z.array(z.string().min(1)),
        })
        .strict(),
    ),
  })
  .strict();

/* ---- tipos derivados ---- */

export type Work = z.infer<typeof workSchema>;
export type Author = z.infer<typeof authorSchema>;
export type Reading = z.infer<typeof readingSchema>;
export type Summary = z.infer<typeof summarySchema>;
export type Vocabularies = z.infer<typeof vocabulariesSchema>;

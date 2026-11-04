/*
 * Utilidades de texto para os componentes visuais.
 *
 * - `initials`: iniciais de um nome, para o avatar de iniciais.
 * - `detectScript`: detecta o alfabeto de um texto (para escolher a fonte Noto
 *   e o `dir`), olhando as faixas Unicode. Usado no título original não latino.
 *
 * Puro — roda sob node --test.
 */
import { fold } from "./search.ts";

export type Script =
  | "latin"
  | "cyrillic"
  | "hebrew"
  | "arabic"
  | "cjk"
  | "other";

/** `lang` BCP-47 de cada idioma original do catálogo (nome pt-BR → tag). */
const LANGUAGE_TAGS: Readonly<Record<string, string>> = {
  português: "pt",
  inglês: "en",
  espanhol: "es",
  francês: "fr",
  italiano: "it",
  russo: "ru",
  japonês: "ja",
  alemão: "de",
  hebraico: "he",
  coreano: "ko",
  norueguês: "no",
  catalão: "ca",
  tcheco: "cs",
  árabe: "ar",
  holandês: "nl",
};

/** Idiomas cujo alfabeto nativo não é o latino. */
const NON_LATIN_LANGUAGES = new Set(["coreano", "japonês", "hebraico", "russo", "árabe"]);

/**
 * `lang` de um TÍTULO ORIGINAL: a tag do idioma da obra, exceto quando o título
 * está em alfabeto latino num idioma de outro alfabeto (ex.: "Nemureru Bijo",
 * romanização de uma obra japonesa) — aí marcar `ja` seria errado e o atributo
 * é omitido.
 */
export function originalTitleLang(language: string, text: string): string | undefined {
  if (NON_LATIN_LANGUAGES.has(language) && detectScript(text) === "latin") {
    return undefined;
  }
  return languageTag(language);
}

/**
 * Tag `lang` do idioma original (nome pt-BR, como no catálogo). Idioma sem
 * tag conhecida devolve `undefined`: o atributo some, nunca é inventado.
 */
export function languageTag(language: string): string | undefined {
  return LANGUAGE_TAGS[language];
}

/** Apresentação de um título original pronto para o HTML. */
export type OriginalTitlePresentation = {
  /** O próprio texto do título original. */
  text: string;
  /** `lang` do atributo HTML; ausente em romanização de idioma não latino. */
  lang?: string;
  /** `dir` do atributo HTML (rtl para hebraico/árabe). */
  dir: "ltr" | "rtl";
  /** Custom property de fonte Noto, ou ausente (fonte padrão). */
  font?: string;
};

/**
 * Decide se, e como, mostrar o título ORIGINAL de uma obra (telas Obra e as
 * grades/carrosséis). Devolve `null` quando não há original ou quando ele é
 * igual ao título pt-BR (comparando sem caixa e sem acento, via `fold`). É a
 * regra única: `CoverCaption` e a página da Obra a consomem, para o `lang`,
 * o `dir` e a fonte Noto nunca divergirem.
 */
export function originalTitlePresentation(
  language: string,
  title: string,
  original: string | null | undefined,
): OriginalTitlePresentation | null {
  const text = (original ?? "").trim();
  if (text === "") return null;
  if (fold(text) === fold(title.trim())) return null;

  const script = detectScript(text);
  const dir = scriptDir(script);
  const lang = originalTitleLang(language, text);
  const font = originalTitleFont(language, script);
  return font ? { text, lang, dir, font } : { text, lang, dir };
}

/**
 * Fonte Noto para o título original pelo script (e pelo idioma, que decide
 * coreano vs japonês dentro do CJK). Devolve `undefined` para latim/cirílico
 * (a fonte padrão serve).
 */
export function originalTitleFont(
  language: string,
  script: Script,
): string | undefined {
  if (script === "cjk") {
    return language === "coreano"
      ? "var(--font-serif-kr)"
      : "var(--font-serif-jp)";
  }
  if (script === "hebrew") return "var(--font-serif-hebrew)";
  return undefined;
}

/**
 * Iniciais de um nome: primeira letra do primeiro e do último nome
 * significativos. "Han Kang" → "HK"; "Clarice Lispector" → "CL";
 * "Platão" → "P". Ignora partículas curtas (de, da, e, von…).
 */
export function initials(name: string): string {
  const parts = name
    .trim()
    .split(/\s+/)
    .filter((p) => p.length > 0 && !PARTICLES.has(p.toLowerCase()));
  if (parts.length === 0) return "";
  const first = firstLetter(parts[0]!);
  if (parts.length === 1) return first.toUpperCase();
  const last = firstLetter(parts[parts.length - 1]!);
  return (first + last).toUpperCase();
}

const PARTICLES = new Set([
  "de", "da", "do", "das", "dos", "e", "di", "del", "della", "van", "von",
  "la", "le", "el", "bin", "al",
]);

function firstLetter(word: string): string {
  // Primeiro caractere que seja letra (pula aspas, parênteses etc.).
  for (const ch of word) {
    if (/\p{L}/u.test(ch)) return ch;
  }
  return word.charAt(0);
}

/**
 * Detecta o script predominante de um texto pelas faixas Unicode.
 * Serve para escolher a fonte Noto e decidir `dir` no título original.
 */
export function detectScript(text: string): Script {
  if (/[\u0590-\u05FF]/.test(text)) return "hebrew";
  if (/[\u0600-\u06FF]/.test(text)) return "arabic";
  if (/[\u0400-\u04FF]/.test(text)) return "cyrillic";
  // CJK: Hangul, Hiragana, Katakana, ideogramas.
  if (/[\uAC00-\uD7AF\u3040-\u30FF\u3400-\u4DBF\u4E00-\u9FFF]/.test(text)) {
    return "cjk";
  }
  if (/\p{Script=Latin}/u.test(text)) return "latin";
  return "other";
}

/** `dir` apropriado para o script (hebraico e árabe são RTL). */
export function scriptDir(script: Script): "ltr" | "rtl" {
  return script === "hebrew" || script === "arabic" ? "rtl" : "ltr";
}

/**
 * `lang` BCP-47 aproximado a partir do script, para o atributo HTML.
 * Não distingue línguas dentro do mesmo script (ex.: ja vs zh): usamos o uso
 * do catálogo, onde o CJK dos títulos é japonês ou coreano — resolvido pelo
 * idioma da obra no componente, não aqui. Aqui devolvemos só o fallback.
 */
export function scriptToken(script: Script): string {
  switch (script) {
    case "hebrew":
      return "he";
    case "arabic":
      return "ar";
    case "cyrillic":
      return "ru";
    default:
      return "";
  }
}

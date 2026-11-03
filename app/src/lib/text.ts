/*
 * Utilidades de texto para os componentes visuais.
 *
 * - `initials`: iniciais de um nome, para o avatar de iniciais.
 * - `detectScript`: detecta o alfabeto de um texto (para escolher a fonte Noto
 *   e o `dir`), olhando as faixas Unicode. Usado no título original não latino.
 *
 * Puro e sem dependências — roda sob node --test.
 */

export type Script = "latin" | "cyrillic" | "hebrew" | "cjk" | "other";

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
  if (/[\u0400-\u04FF]/.test(text)) return "cyrillic";
  // CJK: Hangul, Hiragana, Katakana, ideogramas.
  if (/[\uAC00-\uD7AF\u3040-\u30FF\u3400-\u4DBF\u4E00-\u9FFF]/.test(text)) {
    return "cjk";
  }
  if (/\p{Script=Latin}/u.test(text)) return "latin";
  return "other";
}

/** `dir` apropriado para o script (hebraico é RTL). */
export function scriptDir(script: Script): "ltr" | "rtl" {
  return script === "hebrew" ? "rtl" : "ltr";
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
    case "cyrillic":
      return "ru";
    default:
      return "";
  }
}

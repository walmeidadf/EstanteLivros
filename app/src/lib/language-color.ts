/*
 * Cor por idioma original — o sistema de cor central do design (handoff §3.2).
 *
 * A cor do idioma original aparece em tudo: lombadas, capas tipográficas,
 * avatares de iniciais, pontos/lombadas do Atlas e cabeçalho da página de
 * idioma. Este módulo é a única fonte dessa cor.
 *
 * Idiomas sem cor própria caem em "outros" (OTHER), sem erro — é assim que o
 * design trata idiomas novos até ganharem cor.
 */

export type LanguageColor = {
  /** Cor de fundo na cor do idioma. */
  bg: string;
  /** Cor do texto sobre esse fundo (coluna "Texto" de §3.2). */
  ink: string;
};

/** Mapa idioma (nome pt-BR, como no catálogo) → par de cores de §3.2. */
const LANGUAGE_COLORS: Readonly<Record<string, LanguageColor>> = {
  português: { bg: "#C89B3C", ink: "#1A1408" },
  inglês: { bg: "#2F5D9E", ink: "#F4EFE6" },
  espanhol: { bg: "#A8432C", ink: "#F7EDE6" },
  francês: { bg: "#6B4F9A", ink: "#F3EEF8" },
  italiano: { bg: "#3F7A5C", ink: "#F2F0E8" },
  russo: { bg: "#7E2433", ink: "#F6E9EB" },
  japonês: { bg: "#E8DFCB", ink: "#2A2418" },
  alemão: { bg: "#5A5A5A", ink: "#F2F2F2" },
  hebraico: { bg: "#2A7F86", ink: "#EEF7F7" },
  coreano: { bg: "#E3A9B0", ink: "#2A1418" },
};

/** Fallback "outros" (§3.2) para qualquer idioma sem cor própria. */
export const OTHER_LANGUAGE_COLOR: LanguageColor = {
  bg: "#4B5E55",
  ink: "#EDE6D6",
};

/**
 * Devolve o par de cores do idioma. Idioma desconhecido cai em "outros".
 * @param language nome do idioma em pt-BR, como no catálogo.
 */
export function languageColor(language: string): LanguageColor {
  return LANGUAGE_COLORS[language] ?? OTHER_LANGUAGE_COLOR;
}

/**
 * Emite as custom properties `--lang-bg`/`--lang-ink` como string de `style`,
 * para compor a cor do idioma em CSS (ex.: `style={languageColorVars(lang)}`).
 */
export function languageColorVars(language: string): string {
  const { bg, ink } = languageColor(language);
  return `--lang-bg:${bg};--lang-ink:${ink};`;
}

/** Lista dos idiomas que têm cor própria (os demais caem em "outros"). */
export function languagesWithOwnColor(): string[] {
  return Object.keys(LANGUAGE_COLORS);
}

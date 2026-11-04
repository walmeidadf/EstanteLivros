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

/* ---- Legibilidade sobre o fundo escuro (S4, design §4.3) ---- */

/** Espelha o token `--ground` (tokens.css). */
const GROUND_HEX = "#0E1714";
/** Espelha o token `--title` (tokens.css): destino do clareamento. */
const TITLE_HEX = "#F4EBD8";

function parseHex(hex: string): [number, number, number] {
  const h = hex.replace("#", "");
  return [
    parseInt(h.slice(0, 2), 16),
    parseInt(h.slice(2, 4), 16),
    parseInt(h.slice(4, 6), 16),
  ];
}

function toHex([r, g, b]: [number, number, number]): string {
  const part = (n: number) =>
    Math.max(0, Math.min(255, Math.round(n)))
      .toString(16)
      .padStart(2, "0");
  return `#${part(r)}${part(g)}${part(b)}`.toUpperCase();
}

function luminance(hex: string): number {
  const lin = parseHex(hex).map((v) => {
    const c = v / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  }) as [number, number, number];
  return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2];
}

/** Razão de contraste WCAG entre duas cores `#RRGGBB` (1..21). */
export function contrastRatio(hexA: string, hexB: string): number {
  const [hi, lo] = [luminance(hexA), luminance(hexB)].sort((a, b) => b - a);
  return (hi! + 0.05) / (lo! + 0.05);
}

/**
 * Cor legível como TEXTO sobre `--ground`: devolve a própria cor se já passa em
 * `min` (padrão 4.5:1); senão a mistura com `--title` em passos de 5% até
 * passar, preservando a matiz o quanto possível.
 */
export function onGround(hex: string, min = 4.5): string {
  const base = hex.toUpperCase();
  if (contrastRatio(base, GROUND_HEX) >= min) return base;
  const from = parseHex(base);
  const to = parseHex(TITLE_HEX);
  for (let step = 1; step <= 20; step++) {
    const t = step / 20;
    const mixed = toHex([
      from[0] + (to[0] - from[0]) * t,
      from[1] + (to[1] - from[1]) * t,
      from[2] + (to[2] - from[2]) * t,
    ]);
    if (contrastRatio(mixed, GROUND_HEX) >= min) return mixed;
  }
  return TITLE_HEX;
}

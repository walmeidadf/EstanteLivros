/*
 * Qual capa mostrar numa obra (regra pura, testável com node --test).
 *
 * O catálogo guarda três estados (DATA_MODEL, "cover"):
 *   - `file` presente           → capa real escolhida (mestre local);
 *   - `display: "typographic"`  → revisada, fica a capa tipográfica;
 *   - nenhum dos dois           → ainda não revisada: tipográfica (padrão seguro).
 *
 * A `sourceUrl` é só proveniência e nunca entra aqui (R6.4 da S1, R7.4).
 */

export type CoverFocus = "top" | "center" | "bottom";
export type CoverDisplay = "typographic";

/** Subconjunto do `cover` do catálogo que esta regra lê. */
export type RawCoverFields = {
  file?: string | null;
  focus?: CoverFocus | null;
  display?: CoverDisplay | null;
} | null;

/** Campos resolvidos que a WorkView carrega. */
export type CoverFields = {
  /** `covers/{slug}.{ext}` ou null quando não há mestre local. */
  coverFile: string | null;
  /** Enquadramento do corte 2:3 no build (padrão: centro). */
  coverFocus: CoverFocus;
  /** "typographic" quando a Lila revisou e escolheu a tipográfica. */
  coverDisplay: CoverDisplay | null;
};

export function coverFields(cover: RawCoverFields): CoverFields {
  return {
    coverFile: cover?.file ?? null,
    coverFocus: cover?.focus ?? "center",
    coverDisplay: cover?.display ?? null,
  };
}

/**
 * A capa real a derivar, ou null para cair na capa tipográfica. A escolha de
 * manter a tipográfica vence um mestre que ainda esteja no catálogo.
 */
export function localCover(
  fields: CoverFields,
): { file: string; focus: CoverFocus } | null {
  if (!fields.coverFile || fields.coverDisplay === "typographic") return null;
  return { file: fields.coverFile, focus: fields.coverFocus };
}

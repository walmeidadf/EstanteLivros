/*
 * Derivação de imagens no build (R6).
 *
 * Os mestres vivem em catalog/media/ (fora de app/src): fotos de autoria em
 * authors/ e capas de obra em covers/. Usamos o pipeline de imagem do Astro
 * (astro:assets → sharp) sobre eles via import.meta.glob, sem copiar o
 * diretório para dentro do app. O `src` renderizado é SEMPRE o derivado local
 * gerado no build; a `cover.sourceUrl` do catálogo é só proveniência e NUNCA
 * vira src (R6.4).
 *
 * Este módulo roda apenas no contexto do Astro (import.meta.glob é do Vite),
 * então ele importa de "astro:assets". Não é exercitado pelo node --test.
 */
import { getImage } from "astro:assets";
import {
  localCover,
  type CoverFields,
  type CoverFocus,
} from "./cover-selection.ts";

/**
 * Mapa de todos os mestres de foto de autoria, resolvidos como ImageMetadata
 * pelo Astro. A chave é o nome do arquivo (ex.: "han-kang.jpg").
 *
 * O caminho é relativo a este arquivo: src/lib → ../../.. → raiz do repo →
 * catalog/media/authors.
 */
const authorMasters = import.meta.glob<{ default: ImageMetadata }>(
  "../../../catalog/media/authors/*.{jpg,png,webp,gif}",
  { eager: true },
);

/** Índice por nome de arquivo (slug.ext) → ImageMetadata. */
const authorMasterByFile = new Map<string, ImageMetadata>();
for (const [path, mod] of Object.entries(authorMasters)) {
  const file = path.split("/").pop();
  if (file) authorMasterByFile.set(file, mod.default);
}

/**
 * Mapa dos mestres de capa de obra (catalog/media/covers). Enquanto nenhuma
 * capa foi escolhida a pasta só tem .gitkeep e o mapa fica vazio.
 */
const coverMasters = import.meta.glob<{ default: ImageMetadata }>(
  "../../../catalog/media/covers/*.{jpg,png,webp,gif}",
  { eager: true },
);

/** Índice por nome de arquivo (slug.ext) → ImageMetadata. */
const coverMasterByFile = new Map<string, ImageMetadata>();
for (const [path, mod] of Object.entries(coverMasters)) {
  const file = path.split("/").pop();
  if (file) coverMasterByFile.set(file, mod.default);
}

export type DerivedImage = {
  /** src do derivado AVIF (formato preferido). */
  src: string;
  /** srcset com os tamanhos gerados, para telas de densidades diferentes. */
  srcset: string;
  width: number;
  height: number;
};

/** Proporções suportadas: 2:3 (capa/retrato) e 1:1 (avatar circular). */
export type Aspect = "2:3" | "1:1";

/** Larguras padrão (incluem o dobro para telas retina). */
const AVATAR_WIDTHS = [64, 128, 256] as const;
const COVER_WIDTHS = [104, 136, 272] as const;
/**
 * Capa de obra: 104 (carrossel) e 136 (destaque/grade no desktop) em 1x, 2x e
 * 3x (408 px, o Samsung da Lila). O `sizes` do <img> escolhe entre elas.
 */
const WORK_COVER_WIDTHS = [104, 136, 272, 408] as const;

function heightFor(width: number, aspect: Aspect): number {
  return aspect === "1:1" ? width : Math.round((width * 3) / 2);
}

/**
 * Deriva a foto de uma autoria a partir do seu `photo.file`
 * (ex.: "authors/han-kang.jpg"). Corte central, AVIF, na proporção pedida.
 * Devolve `null` quando não há mestre local — o chamador cai no avatar.
 *
 * `aspect` 1:1 serve ao avatar circular; 2:3 serve a retratos/capas.
 */
export async function deriveAuthorPhoto(
  photoFile: string,
  aspect: Aspect = "1:1",
  widths: readonly number[] = aspect === "1:1" ? AVATAR_WIDTHS : COVER_WIDTHS,
): Promise<DerivedImage | null> {
  const fileName = photoFile.replace(/^authors\//, "");
  const master = authorMasterByFile.get(fileName);
  if (!master) return null;

  const largest = Math.max(...widths);
  const image = await getImage({
    src: master,
    width: largest,
    height: heightFor(largest, aspect),
    format: "avif",
    fit: "cover",
    position: "center",
  });

  const srcset = await buildSrcset(master, widths, aspect);
  return {
    src: image.src,
    srcset,
    width: largest,
    height: heightFor(largest, aspect),
  };
}

async function buildSrcset(
  master: ImageMetadata,
  widths: readonly number[],
  aspect: Aspect,
  position: CoverFocus = "center",
): Promise<string> {
  const parts: string[] = [];
  for (const w of widths) {
    const img = await getImage({
      src: master,
      width: w,
      height: heightFor(w, aspect),
      format: "avif",
      fit: "cover",
      position,
    });
    parts.push(`${img.src} ${w}w`);
  }
  return parts.join(", ");
}

/**
 * Deriva a capa de uma obra a partir do seu `cover.file` (ex.:
 * "covers/a-vegetariana-han-kang.jpg"). Sempre 2:3, AVIF, com o corte no
 * `focus` (padrão: centro). O mestre nunca é recortado em disco: só o derivado
 * do build. Larguras maiores que o mestre são descartadas (sem ampliar).
 * Devolve `null` quando não há mestre local; o chamador cai na tipográfica.
 */
export async function deriveWorkCover(
  coverFile: string,
  focus: CoverFocus = "center",
  widths: readonly number[] = WORK_COVER_WIDTHS,
): Promise<DerivedImage | null> {
  const master = coverMasterByFile.get(coverFile.replace(/^covers\//, ""));
  if (!master) return null;

  const fitting = widths.filter((w) => w <= master.width);
  const usable = fitting.length > 0 ? fitting : [Math.min(...widths)];
  const largest = Math.max(...usable);
  const image = await getImage({
    src: master,
    width: largest,
    height: heightFor(largest, "2:3"),
    format: "avif",
    fit: "cover",
    position: focus,
  });
  return {
    src: image.src,
    srcset: await buildSrcset(master, usable, "2:3", focus),
    width: largest,
    height: heightFor(largest, "2:3"),
  };
}

/**
 * Capa derivada de uma obra (WorkView), ou null para a capa tipográfica. Aplica
 * a regra de cover-selection.ts: "fica tipográfica" vence um mestre existente.
 */
export async function deriveCoverOf(
  work: CoverFields,
): Promise<DerivedImage | null> {
  const chosen = localCover(work);
  return chosen ? deriveWorkCover(chosen.file, chosen.focus) : null;
}

/** true quando existe mestre local para a capa da obra (sem derivar). */
export function hasWorkCover(coverFile: string): boolean {
  return coverMasterByFile.has(coverFile.replace(/^covers\//, ""));
}

/** true quando existe mestre local para a foto (sem derivar). */
export function hasAuthorMaster(photoFile: string): boolean {
  return authorMasterByFile.has(photoFile.replace(/^authors\//, ""));
}

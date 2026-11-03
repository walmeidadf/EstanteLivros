/*
 * Derivação de imagens no build (R6).
 *
 * Os mestres vivem em catalog/media/ (fora de app/src). Usamos o pipeline de
 * imagem do Astro (astro:assets → sharp) sobre eles via import.meta.glob, sem
 * copiar o diretório para dentro do app. O `src` renderizado é SEMPRE o
 * derivado local gerado no build; a `cover.sourceUrl` do catálogo é só
 * proveniência e NUNCA vira src (R6.4).
 *
 * Este módulo roda apenas no contexto do Astro (import.meta.glob é do Vite),
 * então ele importa de "astro:assets". Não é exercitado pelo node --test.
 */
import { getImage } from "astro:assets";

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
): Promise<string> {
  const parts: string[] = [];
  for (const w of widths) {
    const img = await getImage({
      src: master,
      width: w,
      height: heightFor(w, aspect),
      format: "avif",
      fit: "cover",
      position: "center",
    });
    parts.push(`${img.src} ${w}w`);
  }
  return parts.join(", ");
}

/** true quando existe mestre local para a foto (sem derivar). */
export function hasAuthorMaster(photoFile: string): boolean {
  return authorMasterByFile.has(photoFile.replace(/^authors\//, ""));
}

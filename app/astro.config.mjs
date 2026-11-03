// @ts-check
import { defineConfig } from "astro/config";
import { fileURLToPath } from "node:url";

// O catálogo (fonte de verdade) vive um nível acima de app/. O app só lê.
const catalogDir = fileURLToPath(new URL("../catalog", import.meta.url));

// https://astro.build/config
export default defineConfig({
  output: "static",
  // Endereço de produção (subdomínio, app na raiz). `base` fica implícito em
  // "/" — sem prefixo de subcaminho, para links, imagens, service worker (S6)
  // e manifest viverem na raiz.
  site: "https://liliane.prateleira.site",
  // Sem adaptador de servidor: tudo é HTML estático.
  vite: {
    resolve: {
      alias: {
        "@": fileURLToPath(new URL("./src", import.meta.url)),
      },
    },
    // Permite que o Vite leia os mestres de imagem fora de app/ (catalog/media/).
    server: {
      fs: {
        allow: [fileURLToPath(new URL(".", import.meta.url)), catalogDir],
      },
    },
  },
});

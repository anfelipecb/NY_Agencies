import { defineConfig } from "vite";

export default defineConfig({
  base: process.env.PAGES_BASE ?? "/",
  root: "web",
  build: {
    outDir: "../dist",
    emptyOutDir: true,
  },
});

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The renderer is a plain SPA. We use a relative base so the built assets
// load correctly when Electron serves them from the local filesystem
// (file://) in production.
export default defineConfig({
  base: "./",
  plugins: [react()],
  root: ".",
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    strictPort: true,
  },
});

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// App 100% estatico: todo o calculo roda no navegador (inclusive em Web Worker).
// `base` relativa para funcionar tanto em dominio proprio quanto em GitHub Pages.
export default defineConfig({
  base: "./",
  plugins: [react()],
});

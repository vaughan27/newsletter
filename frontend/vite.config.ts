import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

// Dev  (`npm run dev`):   app at "/",            API at "/api"            (proxied to FastAPI :8000)
// Prod (`npm run build`): app at "/newsletter/", API at "/newsletter-api" (nginx -> FastAPI)
// Override either with VITE_BASE_PATH / VITE_API_BASE in a .env file if the nginx paths differ.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, ".", "VITE_");
  const prod = mode === "production";
  const base = env.VITE_BASE_PATH ?? (prod ? "/newsletter/" : "/");
  const apiBase = (env.VITE_API_BASE ?? (prod ? "/newsletter-api" : "/api")).replace(/\/$/, "");

  return {
    base,
    plugins: [react()],
    define: { __API_BASE__: JSON.stringify(apiBase) },
    server: {
      port: 5181,
      proxy: {
        "/api": { target: "http://localhost:8010", changeOrigin: false },
      },
    },
  };
});

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// In dev the browser talks only to Vite (port 5173); /api is proxied to FastAPI.
// That keeps everything same-origin, so the anonymous visitor cookie just works.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5181,
    proxy: {
      "/api": { target: "http://localhost:8010", changeOrigin: false },
    },
  },
});

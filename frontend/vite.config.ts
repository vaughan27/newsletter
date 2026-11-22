import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  base: "/newsletter/",
  plugins: [react()],
  server: {
    port: 5181,
    proxy: {
      "/newsletter-api": {
        target: "http://localhost:8010",
        changeOrigin: false,
        rewrite: (path) => path.replace(/^\/newsletter-api/, "/api"),
      },
    },
  },
});
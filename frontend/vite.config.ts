import { readFileSync } from "fs";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

const version = readFileSync("../VERSION", "utf-8").trim();

export default defineConfig({
  plugins: [react(), tailwindcss()],
  define: {
    __APP_VERSION__: JSON.stringify(version),
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes("node_modules/react/") || id.includes("node_modules/react-dom/") || id.includes("node_modules/react-router")) {
            return "react";
          }
          if (id.includes("node_modules/echarts")) {
            return "echarts";
          }
          if (id.includes("node_modules/react-markdown") || id.includes("node_modules/remark-gfm")) {
            return "markdown";
          }
          if (id.includes("node_modules/framer-motion")) {
            return "motion";
          }
        },
      },
    },
  },
  server: {
    port: 3000,
    proxy: {
      "/api/conversations/ws": {
        target: "http://127.0.0.1:8000",
        ws: true,
        changeOrigin: true,
      },
      "/api/huddle/ws": {
        target: "http://127.0.0.1:8000",
        ws: true,
        changeOrigin: true,
      },
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});

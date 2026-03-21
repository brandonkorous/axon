import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 3000,
    proxy: {
      "/api": "http://localhost:8000",
      "/api/conversations/ws": {
        target: "ws://localhost:8000",
        ws: true,
      },
      "/api/boardroom/ws": {
        target: "ws://localhost:8000",
        ws: true,
      },
    },
  },
});

import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

export default defineConfig(({ mode }) => {
  const fileEnv = loadEnv(mode, repoRoot, "");
  const env = { ...fileEnv, ...process.env };
  const backendPort = (env.BACKEND_PORT || "8000").trim();
  const target = `http://127.0.0.1:${backendPort}`;

  return {
    plugins: [react()],
    server: {
      // Слушаем все интерфейсы (0.0.0.0 / ::), чтобы и http://127.0.0.1:5173,
      // и http://localhost:5173 открывались одинаково на разных ОС.
      host: true,
      port: 5173,
      strictPort: true,
      proxy: {
        "/api": target,
        "/health": target,
      },
    },
  };
});

import { execSync } from "node:child_process";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

function gitValue(command: string, fallback: string): string {
  try {
    return execSync(command, { encoding: "utf8" }).trim();
  } catch {
    return fallback;
  }
}

const workingTreeIsDirty = gitValue("git status --short", "dirty").length > 0;
const buildCommit = workingTreeIsDirty
  ? "local-pending"
  : gitValue("git rev-parse --short HEAD", "local-pending");
const buildMessage = workingTreeIsDirty
  ? "Heat and Hot Water implementation"
  : gitValue("git log -1 --pretty=%s", "local implementation");

export default defineConfig({
  plugins: [react()],
  define: {
    __BUILD_COMMIT__: JSON.stringify(
      buildCommit,
    ),
    __BUILD_MESSAGE__: JSON.stringify(
      buildMessage,
    ),
    __BUILD_DATE__: JSON.stringify(new Date().toISOString().slice(0, 10)),
  },
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8000",
      "/health": "http://127.0.0.1:8000",
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts",
    coverage: {
      provider: "v8",
      reporter: ["text", "json-summary", "html"],
      include: ["src/**/*.{ts,tsx}"],
      exclude: ["src/main.tsx", "src/test/**"],
      thresholds: {
        lines: 60,
        functions: 60,
        branches: 60,
        statements: 60,
      },
    },
  },
});


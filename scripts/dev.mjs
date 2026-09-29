/**
 * Cross-platform dev launcher — starts backend then frontend.
 * Usage: node scripts/dev.mjs
 */
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const isWin = process.platform === "win32";

const backendPy = path.join(root, "backend", ".venv", isWin ? "Scripts/python.exe" : "bin/python");
const uvicornArgs = ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"];

console.log("DataForge Analytics — starting backend + frontend\n");

const backend = spawn(backendPy, uvicornArgs, {
  cwd: path.join(root, "backend"),
  stdio: "inherit",
  shell: isWin,
});

setTimeout(() => {
  const npm = isWin ? "npm.cmd" : "npm";
  const frontend = spawn(npm, ["run", "dev"], {
    cwd: path.join(root, "frontend"),
    stdio: "inherit",
    shell: isWin,
  });
  frontend.on("exit", (code) => process.exit(code ?? 0));
}, 2000);

backend.on("exit", (code) => process.exit(code ?? 0));

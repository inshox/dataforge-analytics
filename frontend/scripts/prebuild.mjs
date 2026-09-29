/**
 * Clears stale Next.js build lock (left when dev/build process is killed).
 */
import { existsSync, rmSync } from "node:fs";
import { join } from "node:path";

const lock = join(process.cwd(), ".next", "lock");
if (existsSync(lock)) {
  try {
    rmSync(lock, { force: true });
    console.log("Removed stale .next/lock");
  } catch {
    console.warn("Could not remove .next/lock — stop other `next dev` / `next build` processes first.");
  }
}

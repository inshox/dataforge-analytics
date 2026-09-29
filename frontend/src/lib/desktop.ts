/** Tauri desktop helpers (no-op in browser dev). */

export const APP_VERSION = process.env.NEXT_PUBLIC_APP_VERSION ?? "1.0.0";

export async function isTauri(): Promise<boolean> {
  try {
    const { isTauri: check } = await import("@tauri-apps/api/core");
    return check();
  } catch {
    return false;
  }
}

export async function openLogsFolder(): Promise<void> {
  if (!(await isTauri())) {
    console.warn("[DataForge] openLogsFolder only available in desktop app");
    return;
  }
  const { invoke } = await import("@tauri-apps/api/core");
  await invoke("open_logs_folder");
}

export async function getDesktopPaths(): Promise<{
  data_directory: string;
  log_file: string;
  backend_port?: number;
} | null> {
  if (!(await isTauri())) return null;
  const { invoke } = await import("@tauri-apps/api/core");
  return invoke("get_app_paths");
}

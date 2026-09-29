//! Tauri application — spawns local FastAPI backend on startup.

use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::thread;
use std::time::Duration;
use tauri::Manager;

struct BackendProcess(Mutex<Option<Child>>);

fn app_data_dir() -> PathBuf {
    if let Ok(dir) = std::env::var("DATAFORGE_DATA_DIR") {
        return PathBuf::from(dir);
    }
    dirs::data_dir()
        .unwrap_or_else(|| PathBuf::from("."))
        .join("DataForge Analytics")
}

fn dev_backend_dir() -> Option<PathBuf> {
    let dev = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../backend");
    if dev.join("app").join("main.py").exists() {
        Some(dev)
    } else {
        None
    }
}

fn installed_backend_dir() -> Option<PathBuf> {
    std::env::current_exe().ok().and_then(|exe| {
        let mut p = exe.parent()?.to_path_buf();
        for _ in 0..6 {
            let bundled = p.join("resources").join("backend-pack");
            if bundled.join("app").join("main.py").exists() {
                return Some(bundled);
            }
            let candidate = p.join("backend-pack");
            if candidate.join("app").join("main.py").exists() {
                return Some(candidate);
            }
            if !p.pop() {
                break;
            }
        }
        None
    })
}

fn resolve_backend_dir(resource_dir: Option<&Path>) -> Option<PathBuf> {
    if let Some(r) = resource_dir {
        for candidate in [r.join("backend-pack"), r.to_path_buf()] {
            if candidate.join("app").join("main.py").exists() {
                return Some(candidate);
            }
        }
    }
    installed_backend_dir().or_else(dev_backend_dir)
}

fn find_listen_port(host: &str, preferred: u16) -> u16 {
    for port in preferred..preferred.saturating_add(10) {
        if std::net::TcpListener::bind((host, port)).is_ok() {
            return port;
        }
    }
    preferred
}

fn python_executable(backend_dir: &Path, port: u16) -> (PathBuf, Vec<String>) {
    #[cfg(windows)]
    let venv_py = backend_dir.join(".venv").join("Scripts").join("python.exe");
    #[cfg(not(windows))]
    let venv_py = backend_dir.join(".venv").join("bin").join("python3");

    let uvicorn_args = vec![
        "-m".into(),
        "uvicorn".into(),
        "app.main:app".into(),
        "--host".into(),
        "127.0.0.1".into(),
        "--port".into(),
        port.to_string(),
    ];

    if venv_py.is_file() {
        return (venv_py, uvicorn_args);
    }

    #[cfg(windows)]
    {
        (
            PathBuf::from("py"),
            std::iter::once("-3.12".into())
                .chain(uvicorn_args)
                .collect(),
        )
    }
    #[cfg(not(windows))]
    {
        (PathBuf::from("python3"), uvicorn_args)
    }
}

fn configure_backend_cmd(cmd: &mut Command) {
    #[cfg(windows)]
    {
        #[cfg(not(debug_assertions))]
        {
            use std::os::windows::process::CommandExt;
            const CREATE_NO_WINDOW: u32 = 0x0800_0000;
            cmd.creation_flags(CREATE_NO_WINDOW);
        }
    }
}

fn spawn_backend(resource_dir: Option<PathBuf>) -> Option<Child> {
    let data_dir = app_data_dir();
    std::fs::create_dir_all(&data_dir).ok()?;
    let log_dir = data_dir.join("logs");
    std::fs::create_dir_all(&log_dir).ok()?;

    let db_path = data_dir.join("dataforge.db");
    let db_url = format!(
        "sqlite+aiosqlite:///{}",
        db_path.to_string_lossy().replace('\\', "/")
    );

    let backend_dir = resolve_backend_dir(resource_dir.as_deref())?;
    let port = find_listen_port("127.0.0.1", 8000);
    let (python, args) = python_executable(&backend_dir, port);

    let mut cmd = Command::new(&python);
    cmd.args(&args)
        .current_dir(&backend_dir)
        .env("DATAFORGE_DATA_DIR", data_dir.to_string_lossy().to_string())
        .env("DATABASE_URL", db_url)
        .env("PORT", port.to_string())
        .stdout(Stdio::null())
        .stderr(Stdio::null());

    configure_backend_cmd(&mut cmd);

    match cmd.spawn() {
        Ok(child) => Some(child),
        Err(e) => {
            eprintln!("[DataForge] Failed to spawn backend: {e}");
            None
        }
    }
}

fn kill_backend(state: &BackendProcess) {
    if let Ok(mut guard) = state.0.lock() {
        if let Some(mut child) = guard.take() {
            let _ = child.kill();
            let _ = child.wait();
        }
    }
}

#[tauri::command]
fn open_logs_folder() -> Result<(), String> {
    let dir = app_data_dir().join("logs");
    std::fs::create_dir_all(&dir).map_err(|e| e.to_string())?;
    open::that(&dir).map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
fn get_app_paths() -> Result<serde_json::Value, String> {
    let data_dir = app_data_dir();
    let log_file = data_dir.join("logs").join("backend.log");
    let port_file = data_dir.join("backend.port");
    let backend_port = std::fs::read_to_string(&port_file)
        .ok()
        .and_then(|s| s.trim().parse::<u16>().ok())
        .unwrap_or(8000);
    Ok(serde_json::json!({
        "data_directory": data_dir.to_string_lossy(),
        "log_file": log_file.to_string_lossy(),
        "backend_port": backend_port,
    }))
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![open_logs_folder, get_app_paths])
        .setup(|app| {
            let resource_dir = app.path().resource_dir().ok();
            let child = spawn_backend(resource_dir);
            let backend = BackendProcess(Mutex::new(child));
            app.manage(backend);

            // Staggered retry if first spawn failed (e.g. port briefly busy)
            let handle = app.handle().clone();
            thread::spawn(move || {
                for _ in 0..5 {
                    thread::sleep(Duration::from_secs(2));
                    if let Some(state) = handle.try_state::<BackendProcess>() {
                        let needs_spawn = state.0.lock().map(|g| g.is_none()).unwrap_or(true);
                        if needs_spawn {
                            if let Some(child) = spawn_backend(None) {
                                if let Ok(mut guard) = state.0.lock() {
                                    *guard = Some(child);
                                }
                            }
                        } else {
                            break;
                        }
                    }
                }
            });

            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event {
                if let Some(state) = window.app_handle().try_state::<BackendProcess>() {
                    kill_backend(&state);
                }
            }
        })
        .build(tauri::generate_context!())
        .expect("error while running tauri application")
        .run(|app_handle, event| {
            if let tauri::RunEvent::Exit = event {
                if let Some(state) = app_handle.try_state::<BackendProcess>() {
                    kill_backend(&state);
                }
            }
        });
}

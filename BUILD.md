# DataForge Analytics — build desktop

## Wymagania (Windows)

1. **Node.js** 18+
2. **Python 3.12** (`py -3.12`)
3. **Rust** — [https://rustup.rs](https://rustup.rs)
4. **Visual Studio Build Tools** — workload „Desktop development with C++” (linker MSVC dla Rust i opcjonalnie Python)

## Dev (okno natywne)

```powershell
cd C:\Users\SEBAS\Projects\DataForgeAnalytics\frontend
npm install
npm run tauri:dev
```

Backend startuje automatycznie. Przy pierwszym uruchomieniu API tworzy **dataset demo** (16 wierszy sprzedaży).

## Produkcja — instalator `.exe`

```powershell
cd C:\Users\SEBAS\Projects\DataForgeAnalytics\frontend
npm install
npm run tauri:build
```

> Używaj `npm run tauri:build` (nie samo `tauri build`) — najpierw pakuje backend do `build/backend-pack`.

Skrypt `tauri:build`:

1. `scripts/pack-backend.ps1` — kopiuje backend + tworzy `.venv` w `src-tauri/resources/backend-pack`
2. `next build` (static export)
3. `tauri build` — NSIS installer

### Gdzie jest instalator?

```
frontend\src-tauri\target\release\bundle\nsis\
  DataForge Analytics_1.0.0_x64-setup.exe
```

Aplikacja po instalacji:

- Uruchamia **wbudowany Python** z `backend-pack/.venv` (nie wymaga osobnej instalacji Pythona u użytkownika)
- Zapisuje dane w `%APPDATA%\DataForge Analytics\`
- Seeduje demo dataset przy pierwszym starcie (pusta baza)

## macOS — `.dmg`

Buduj **na Macu**:

```bash
cd frontend
npm install
npm run tauri:build
```

Artefakt: `src-tauri/target/release/bundle/dmg/*.dmg`

## Rozwiązywanie problemów

| Problem | Rozwiązanie |
|---------|-------------|
| `npm run build` wisi po `Environments: .env.local` | Zatrzymaj wszystkie `next dev` / `next build` (Menedżer zadań → Node.js), usuń `frontend/.next`, uruchom build ponownie. `prebuild` usuwa stale `.next/lock`. |
| `link.exe not found` | Zainstaluj VS Build Tools + C++ |
| `duckdb` build failed | Użyj Python **3.12**, nie 3.14 |
| Backend offline w UI | Poczekaj 3–5 s po starcie; sprawdź `http://127.0.0.1:8000/health` |
| Brak ikon Tauri | `npm run tauri:icon` w folderze `frontend` |

> **Nie** pakuj backendu do `frontend/src-tauri/resources/backend-pack` — użyj `build/backend-pack` (skrypt `pack-backend.ps1`), inaczej Next.js skanuje tysiące plików `.venv` i build może trwać bardzo długo lub się zawiesić.

## Wyłączenie demo przy starcie

W `backend/.env`:

```
SEED_DEMO_ON_STARTUP=false
```

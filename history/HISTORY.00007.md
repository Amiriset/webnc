# Summary 00007

## Goal

- Build a Norton Commander-like web file manager with FastAPI backend and React frontend, running on Windows without Node.js — positioned as a local-first, keyboard-driven admin utility with remote-administration potential and three-layer security (TLS 1.3, zero-knowledge session auth, extensible AuthProvider interface).

## Constraints & Preferences
- Node.js not installed; frontend must be a single `index.html` with React + Babel standalone served locally
- Python 3.9 via `py` launcher, not `python`
- Full filesystem access (multi-drive C:\ through any drive letter) — no sandbox
- Classic NC retro look: blue background, cyan/white/yellow colors, double-panel layout, Fn bar, keyboard-driven
- All scripts (React, ReactDOM, Babel) served locally from the backend, not from CDN (CORS issues with `file://`)
- Table data must use semantic `<table>` HTML
- Ctrl+R/Ctrl+U/Ctrl+O cannot be reliably overridden as shortcuts (browser intercepts them)
- PowerShell 5.1 on user system — `-SkipCertificateCheck` not available, `Invoke-WebRequest` needs workarounds
- `openssl` CLI not installed on user system; SSL cert generation via Python `cryptography` library
- `auth_provider: set[str]` type hint syntax not supported in Python 3.9 (use `set` without generic)

## Progress
### Done
- Backend: FastAPI server (`nc_server.py`) with all CRUD endpoints (list, view, copy, move, rename, mkdir, delete, batch‑delete, search, info, disk, drives, health, sysinfo, compare, tree, archive)
- Backend: `/api/archive/list` — lists ZIP (with optional password) and TAR archive contents; parent `..` entry; path normalisation to URL format
- Backend: Sandbox removed; `safe_path` converts URL paths like `/C/Users/foo` to Windows absolute paths for any drive
- Backend: PermissionError handling — skips inaccessible items instead of failing; all `except` blocks log warnings
- Backend: sort_by="unsorted" support; filter query param on `/api/list` (fnmatch pattern); `/api/info` uses `iterdir()` not `rglob()` for directory stats
- Backend: All blocking FS calls wrapped in `asyncio.to_thread()`; owner info via Win32 API (`GetNamedSecurityInfoW` + `LookupAccountSidW`)
- Backend: Comprehensive logging — `logger.info()` on each API call, `logger.warning()` on swallowed exceptions, `logger.exception()` on caught errors; `RotatingFileHandler` (5 MB × 3 backups, UTF‑8, `if not logger.handlers` guard for reload)
- Backend: **TLS 1.3** — RSA‑4096 self-signed cert via `cryptography` (no `openssl`); `_gen_self_signed_cert()` with SAN for `localhost`, `127.0.0.1`, `::1`; `_create_ssl_context()` sets `minimum_version=TLSv1_3`, `OP_NO_COMPRESSION`, `OP_CIPHER_SERVER_PREFERENCE`; uvicorn monkey‑patched via `uvicorn.config.create_ssl_context`
- Backend: **Auth Provider Interface** — `AuthProvider(ABC)` with `authenticate(request) -> Optional[UserInfo]` and `authorize(user, permission) -> bool`; `UserInfo` dataclass (`username`, `roles`); `ConsoleTokenProvider` (SHA‑256 handshake, nonce, timestamp, `secrets.compare_digest`, replay protection); `SessionAuthMiddleware` calls `_auth_provider.authenticate()`; `/api/health` excluded; `app.state.modules` module registry; `--auth console-token` CLI arg
- Backend: **Directory Sync** — `POST /api/sync/plan` (recursive compare), `POST /api/sync/execute` (file copies / deletes by action list); `_do_sync` walks both trees, returns status `only_left`/`only_right`/`different`/`same`; `_do_sync_execute` handles `copy_left_to_right`, `copy_right_to_left`, `delete_left`, `delete_right`
- Backend: SSL default ON — `--insecure` flag (opt‑out) replaces `--ssl`; `--reload` opt‑in (default off); `sys.modules["nc_server"] = sys.modules["__main__"]` prevents double module init
- Frontend: Two-panel layout with keyboard navigation (arrows, Enter, Tab, Insert, Home/End, PgUp/PgDn); F3 (view), F4 (info), F5 (copy), F6 (move/rename), F7 (mkdir), F8 (delete/batch‑delete) with modals; Alt+F1/F2 drive switching; sort per‑panel with asc/desc; Brief/Full/Quick/Info/Tree view modes; Info view (opposite panel summary + disk); Tree view (expandable, lazy‑load from `/api/tree`)
- Frontend: Filter (fnmatch InputDialog, `[*.txt]` indicator in path bar); History (last 50, dialog with ↑↓/Enter); Select Group (+), Deselect Group (−), Invert Selection (*); Per‑panel On/Off toggle
- Frontend: Compare Directories dialog — 4 tabs (Different/Only Left/Only Right/Same), click to navigate
- Frontend: **Auth handshake** — token from URL fragment `#token=...` or `prompt()`; `_signHeaders()` via Web Crypto API `crypto.subtle.digest("SHA‑256")`; `api()` signs every request with `X-NC-Nonce`, `X-NC-Timestamp`, `X-NC-Signature`; 401 → clear session, reload
- Frontend: `manage_server.ps1` — `-Insecure` instead of `-UseSSL`; `Test-Health` uses `ServicePointManager.ServerCertificateValidationCallback` for PS 5.1 self‑signed bypass; `$Scheme` defaults to `https`; health‑check loop with auto‑restart; PID file tracking
- Frontend: `run.bat` — default = HTTPS; `run --insecure` = HTTP; removed `--ssl` alias
- Frontend: Configuration dialog (Options → Configuration...) — default view mode, sort, hidden files, confirm delete/overwrite, font size; stored in `localStorage` under `nc_config`; global `_ncConfig.showHidden` for `apiList()`
- Frontend: Help dialog (F1) — comprehensive key bindings reference; F2 toggles Left menu; F10 shows Quit confirmation; Compressed File dialog (Left/Right → Compressed File) with password retry; status bar `F1-F8`; top menu bar with dropdowns and mouse hover‑switch
- README.md rewritten: three‑layer security architecture, AuthProvider interface, CLI reference, updated Roadmap

### In Progress
- Frontend: **SyncDialog** — "Synchronize Directories" menu item (Commands → Synchronize Directories); dialog with comparison results, checkboxes, action buttons (Copy →, Copy ←, Delete), Execute button

### Blocked
- Ctrl+O cannot be intercepted in Chrome/Edge (browser-level shortcut); capture-phase listener is best-effort, menu always works

## Key Decisions
- Use `py` launcher instead of `python` (the only way to run Python on this system)
- Serve all JS locally (React, ReactDOM, Babel) from the backend instead of CDN because `file://` blocks CORS
- Multi-drive path format: `/C/Users/...` → Windows `C:\Users\...`; `/C/` for drive root
- Use cdnjs instead of unpkg for downloading React/Babel because unpkg redirects broke `urlretrieve`
- Drive switching via Alt+F1 (left panel) and Alt+F2 (right panel) — classic NC convention
- Use `<table>` elements for file listing (semantic HTML)
- All blocking FS operations wrapped in `asyncio.to_thread()` — avoids event loop blocking
- Directory stats use `iterdir()` (immediate children) not `rglob()` (recursive)
- Logging: file + stderr via `RotatingFileHandler`; `if not logger.handlers` guard for reload; format `%(asctime)s | %(levelname)-8s | %(message)s`
- Config: `localStorage` under `nc_config`; global `_ncConfig.showHidden` for `apiList()`; initial fetch uses config defaults for sort/view
- **SSL default ON** — replaced `--ssl` with `--insecure` (opt‑out); cert auto‑generated via `cryptography` (no `openssl`); `--reload` opt‑in (default off); `sys.modules["nc_server"] = sys.modules["__main__"]` prevents double module init
- **AuthProvider interface** — `AuthProvider(ABC)` with `authenticate()` / `authorize()`; `UserInfo` dataclass; `ConsoleTokenProvider` default; `--auth console-token` CLI arg; middleware calls provider, sets `request.state.user_info`; `/api/health` excluded; module registry on `app.state.modules`
- **Directory Sync** — two endpoints: `/api/sync/plan` (recursive compare), `/api/sync/execute` (batch copy/delete); actions: `copy_left_to_right`, `copy_right_to_left`, `delete_left`, `delete_right`
- Archive passwords: stateful retry in `handleCompressedFile` — first try without password, on 401 show InputDialog, recurse with password
- `run.bat` passes `%2` for extra args (e.g. `run restart --insecure`)
- `Test-Health` in PS 5.1 uses `ServicePointManager.ServerCertificateValidationCallback` for self‑signed cert bypass (no `-SkipCertificateCheck` in PS 5.1)

## Next Steps
- Frontend: SyncDialog component — comparison table with checkboxes, action buttons (Copy →, Copy ←, Delete), Execute button
- Consider remaining disabled menu items: Find file panel, Link, Terminal Emulation
- Add file extraction/viewing for archive entries (currently only listing)
- AD/Kerberos auth provider (`--auth ad`)
- JWT auth provider for automation
- Role-based access control (RBAC) per module
- Background file operations with progress/cancel
- FTP/SFTP provider via abstracted `VfsProvider` layer

## Critical Context
- Run backend: `py nc_server.py` (SSL default) or `py nc_server.py --insecure` (HTTP); add `--reload` for dev
- Frontend at `https://localhost:8000/` — accepts self-signed cert, paste token from console
- Auth token: `secrets.token_hex(32)` = 256 bits; printed once to console/log; token never transmitted (SHA‑256 handshake); nonce + 5‑minute timestamp + replay protection
- PowerShell 5.1 health check uses `ServicePointManager.ServerCertificateValidationCallback` for self‑signed cert; PS 7+ uses `-SkipCertificateCheck`
- `run monitor` now works correctly — health check returns 200, no more restart loops
- `run --insecure` for HTTP (debugging only, no encryption)
- Directory sync: `POST /api/sync/plan` returns recursive diff with `status` field; `POST /api/sync/execute` takes `actions[{name, action}]`
- Port 8000 must be free before starting; use `taskkill /F /PID <pid>` or `Get-Process | Stop-Process -Force` to clear stale processes
- Old processes sometimes linger on port 8000; check with `netstat -ano | findstr :8000`
- Babel standalone transpiles JSX+ES6 in browser; `index.html` uses `React.createElement` (`h()`) calls
- Total paren count in `index.html`: 1813/1813 balanced
- Configuration saved to `localStorage` key `nc_config`; read at startup via `loadConfig()`/`saveConfig()`

## Relevant Files
- `E:\Projects\WebNC\nc_server.py` — FastAPI backend: all endpoints, TLS 1.3 monkey‑patch, AuthProvider interface (`AuthProvider`, `UserInfo`, `ConsoleTokenProvider`), `SessionAuthMiddleware`, module registry, Directory Sync (`/api/sync/plan`, `/api/sync/execute`), cert generation via `cryptography`, entry point with `--insecure`/`--auth`/`--reload`/`--cert`/`--key`
- `E:\Projects\WebNC\index.html` — Frontend: all components (Panel, CompareDialog, SyncDialog placeholder, ConfigDialog, HelpDialog, ArchiveDialog, SearchDialog, SysInfoDialog, HistoryDialog, DriveDialog), menu system, sort/filter/view/selection state, tree expand/collapse, password retry for archives, auth handshake (`_signHeaders()`, `_ncToken`, sessionStorage), `_ncConfig` global, `isArchive()` helper
- `E:\Projects\WebNC\manage_server.ps1` — PowerShell script: start/stop/restart/status/monitor; `-Insecure`/`-HostAddr`/`-Port` params; `Test-Health` with PS 5.1 cert bypass via `ServicePointManager.ServerCertificateValidationCallback`; PID file tracking
- `E:\Projects\WebNC\run.bat` — CMD wrapper: `run` = HTTPS (default), `run --insecure` = HTTP, `run stop`, `run restart`, `run restart --insecure`
- `E:\Projects\WebNC\nc_server.log` — rotating log file (5 MB × 3 backups)
- `E:\Projects\WebNC\nc_server.crt` / `nc_server.key` — auto‑generated self‑signed RSA‑4096 cert (SAN: localhost, 127.0.0.1, ::1)
- `E:\Projects\WebNC\requirements.txt` — Python deps (fastapi, uvicorn, aiofiles, python‑multipart, cryptography)
- `E:\Projects\WebNC\README.md` — updated with three‑layer security, CLI args, AuthProvider architecture, roadmap
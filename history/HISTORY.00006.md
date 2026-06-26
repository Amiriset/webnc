# Summary 00006

## Goal

- Build a Norton Commander-like web file manager with FastAPI backend and React frontend, running on Windows without Node.js — positioned as a local-first, keyboard-driven admin utility with remote-administration potential.

## Constraints & Preferences
- Node.js not installed; frontend must work via CDN-loaded React + Babel standalone in a single `index.html`
- Python 3.9 available via `py` launcher, not via `python` command
- Full filesystem access (C:\ root, multi-drive) — no sandbox
- Classic NC retro look: blue background, cyan/white/yellow colors, double-panel layout, Fn bar, keyboard-driven
- All scripts (React, ReactDOM, Babel) served locally from the backend, not from CDN (CORS issues with `file://`)
- Table data must use semantic `<table>` HTML, not `<div>`-based flexbox mimicking tables
- UI should not feel cramped — needs adequate padding/spacing
- Ctrl+R/Ctrl+U/Ctrl+O cannot be reliably overridden as shortcuts (browser intercepts them even with `capture: true`)

## Progress
### Done
- Backend: FastAPI server (`nc_server.py`) with full CRUD endpoints (list, view, copy, move, rename, mkdir, delete, batch-delete, search, info, disk, drives, health, sysinfo, compare, tree, archive)
- Backend: `/api/archive/list` — lists contents of ZIP (with optional password) and TAR archives; parent `..` entry; path normalization to URL format
- Backend: Sandbox removed; `safe_path` converts URL paths like `/C/Users/foo` to Windows absolute paths for any drive
- Backend: PermissionError handling — skips inaccessible items instead of failing entirely; all `except` blocks now log warnings
- Backend: sort_by="unsorted" support — skips sorting, returns filesystem order
- Backend: filter query param on `/api/list` (fnmatch pattern); `/api/info` uses `iterdir()` not `rglob()` for directory stats (instant on C:\)
- Backend: All blocking FS calls wrapped in `asyncio.to_thread()` — prevents event loop blocking
- Backend: Owner info via Win32 API (`GetNamedSecurityInfoW` + `LookupAccountSidW`)
- Backend: Comprehensive logging — `logger.info()` on every API call, `logger.warning()` on all silent exception swallows, `logger.exception()` on caught errors; no bare `except: pass` remains
- Backend: **File logging** — `RotatingFileHandler` added; writes to `nc_server.log` (5 MB rotation, 3 backups, UTF-8); `if not logger.handlers` guard for `--reload` safety
- Backend: SSL support via `__main__` entry point — `argparse` with `--host` (default `127.0.0.1`), `--port`, `--ssl`, `--cert`, `--key`, `--no-reload`; auto-generates self-signed cert with `openssl` if `--ssl` passed; prints warning when binding `0.0.0.0` without SSL
- Backend: Fixed duplicate `from pathlib import Path` import; added `import sys`, `import zipfile` at top level
- Frontend: Two-panel layout with keyboard navigation (arrows, Enter, Tab, Insert, Home/End, PgUp/PgDn)
- Frontend: F3 (view), F4 (info), F5 (copy), F6 (move/rename), F7 (mkdir), F8 (delete/batch-delete) with modals
- Frontend: Alt+F1/F2 drive switching with DriveDialog; `toWinPath` helper; status bar
- Frontend: Sort options per-panel (handleSort with `[X]` indicator, toggle asc/desc)
- Frontend: Brief, Full, Quick view, Info, Tree view modes per panel
- Frontend: Info view mode — directory summary + disk info about the OPPOSITE panel; updates dynamically as cursor moves
- Frontend: Tree view mode — expandable directory tree with `[+]`/`[-]` click indicators, lazy-loading from `/api/tree`
- Frontend: Filter... — InputDialog for fnmatch pattern, `[*.txt]` indicator in path bar, persistent across navigation
- Frontend: Directory Information menu items → shows `/api/info` results in InfoDialog; title changes to "Directory Info" for dirs; Owner row (DOMAIN\Username)
- Frontend: System Information dialog (Commands menu)
- Frontend: Compare Directories dialog — 4 tabs (Different/Only Left/Only Right/Same), color-coded, click to navigate
- Frontend: History — per-panel path tracking (last 50 unique), dialog with ↑↓/Enter navigation
- Frontend: Select Group (+), Deselect Group (−), Invert Selection (*)
- Frontend: Per-panel On/Off — Left/Right menu toggles individual panel; Commands → Panels On/Off toggles both
- Frontend: `manage_server.ps1` with start/stop/restart/status/monitor; health-check loop with auto-restart; PID file tracking
- Frontend: `run.bat` — cmd wrapper for manage_server.ps1
- Frontend: **Configuration dialog** (Options → Configuration..., Commands → Configuration) — settings: default view mode, default sort by/direction, show hidden files, confirm delete/overwrite, font size; stored in `localStorage` under `nc_config`; `_ncConfig.showHidden` global for `apiList()`; applies on startup
- Frontend: **Help dialog (F1)** — comprehensive key bindings reference (Navigation, Function Keys F1-F10, Selection, Panels, View Modes, Commands, Sort, File Operations, Tips); closes on Esc/Enter/F1
- Frontend: **F2 toggles Left menu**; **F10 shows Quit confirmation** (calls `window.close()`)
- Frontend: **Compressed File dialog** (Left/Right → Compressed File) — lists archive contents in table (Name/Size/Packed/Modified); ↑↓/Esc; `isArchive()` helper; if password required → InputDialog for retry with password; title shows `🔐` when password used
- Frontend: `apiArchiveList(p, pw)` helper; `handleCompressedFile(side, password?)` with password retry loop
- Frontend: Status bar hint updated from `F3-F8` to `F1-F8`
- Frontend: Updated `manage_server.ps1` — added `-HostAddr` (default `127.0.0.1`), `-UseSSL` switch; health check uses `-SkipCertificateCheck`; `$Scheme` for https URLs
- Frontend: Updated `run.bat` — `run --ssl` starts with HTTPS
- Top menu bar: functional dropdown menus for Left, Files, Commands, Options, Right; mouse navigation with hover-switch; click-outside closes
- Backend: Pydantic models for request validation; compare, sysinfo, tree, archive endpoints
- README.md rewritten: positioned as local-first admin utility; security warning; `--host 127.0.0.1` in Quick Start; Roadmap

### In Progress
- (none)

### Blocked
- Ctrl+O cannot be intercepted in Chrome/Edge (browser-level shortcut); capture-phase listener is best-effort, menu always works

## Key Decisions
- Use `py` launcher instead of `python` (the only way to run Python on this system)
- Serve all JS locally (React, ReactDOM, Babel) from the backend instead of CDN because `file://` protocol blocks CORS
- Multi-drive path format: `/C/Users/...` → Windows `C:\Users\...`; `/C/` for drive root
- Use cdnjs instead of unpkg for downloading React/Babel because unpkg redirects broke `urlretrieve`
- Drive switching via Alt+F1 (left panel) and Alt+F2 (right panel) — classic NC convention
- Use `<table>` elements for file listing (semantic HTML)
- All blocking FS operations wrapped in `asyncio.to_thread()` — avoids event loop blocking
- Directory stats use `iterdir()` (immediate children) not `rglob()` (recursive)
- Logging: file + stderr via `RotatingFileHandler`; `if not logger.handlers` guard for `--reload`; format `%(asctime)s | %(levelname)-8s | %(message)s`
- Config: `localStorage` under `nc_config`; global `_ncConfig.showHidden` for `apiList()`; initial fetch uses config defaults for sort/view
- SSL: auto-generate self-signed cert via `openssl` CLI; `--ssl` flag; default host changed from `0.0.0.0` to `127.0.0.1` for security
- Archive passwords: stateful retry in `handleCompressedFile` — first try without password, on 401 show InputDialog, recurse with password
- `run.bat` passes `%2` for extra args (e.g. `run restart --ssl`)

## Next Steps
- Consider remaining disabled menu items: Find file panel, Link, Synchronize Directories, Terminal Emulation
- Add file extraction/viewing for archive entries (currently only listing)
- Add authentication, audit log, restricted mode for remote administration use case
- FTP/SFTP, ZIP/TAR providers via abstracted `VfsProvider` layer
- Background file operations with progress/cancel

## Critical Context
- Run backend: `py -m uvicorn nc_server:app --host 127.0.0.1 --port 8000` or use `run.bat` / `manage_server.ps1 start`; add `--ssl` for HTTPS
- Frontend at `http://localhost:8000/` — the backend serves `index.html` and all JS files
- Port mismatch: `const API = "http://localhost:8000"` will fail if server on wrong port
- Drive paths use uppercase letters: `/C/`, `/D/`, `/E/` etc.
- Babel standalone transpiles JSX+ES6 in browser; `index.html` uses explicit `React.createElement` (`h()`) calls
- Total paren count in `index.html`: 1776/1776 balanced
- SSL cert auto-generated to `nc_server.crt` / `nc_server.key` on first `--ssl` run via `openssl req -x509 -newkey rsa:2048 -days 3650 -subj "/CN=localhost"`
- Archive endpoint returns 401 "Password required or incorrect" on wrong/missing password; TAR has no password support
- Configuration saved to `localStorage` key `nc_config`; read at startup via `loadConfig()`/`saveConfig()`
- `apiList()` reads global `_ncConfig.showHidden` which is synced from config state on save and initial load
- If page shows blank, check browser console for errors — most common: port mismatch, missing parens in script, cached stale scripts
- Search results from `/C/` root; pattern supports glob (`*.txt`) and regex; max_results=200
- Tree view loads root from drive letter of current panel; `[+]`/`[-]` click handlers
- Info view shows data about OPPOSITE panel's directory (per NC spec)
- Monitor with `run monitor` for health-check loop with auto-restart
- Old processes sometimes linger on port 8000; use `taskkill /F /PID <pid>` or `Get-Process ... | Stop-Process -Force` to clear

## Relevant Files
- `E:\Projects\WebNC\nc_server.py` — FastAPI backend (all endpoints including sysinfo, compare, tree, archive, file owner; all blocking I/O in `asyncio.to_thread()`; comprehensive logging with file + stderr handlers; SSL entry point with `argparse`; `_gen_self_signed_cert()`)
- `E:\Projects\WebNC\index.html` — CDN-based frontend (all components: Panel with Brief/Full/Quick/Info/Tree modes, ConfigDialog, HelpDialog, ArchiveDialog, SearchDialog, SysInfoDialog, CompareDialog, HistoryDialog; menu system; sort/filter/view/selection state; tree expand/collapse; password retry for archives; `_ncConfig` global; `isArchive()` helper)
- `E:\Projects\WebNC\manage_server.ps1` — PowerShell script with start/stop/restart/status/monitor; `-HostAddr` (default 127.0.0.1), `-UseSSL` switch; `-SkipCertificateCheck` in health check
- `E:\Projects\WebNC\run.bat` — cmd wrapper: `run` = start, `run --ssl` = HTTPS, `run stop`, `run restart`, `run restart --ssl`
- `E:\Projects\WebNC\nc_server.log` — rotating log file (5 MB × 3 backups) written alongside the script
- `E:\Projects\WebNC\nc_server.crt` / `nc_server.key` — auto-generated self-signed SSL cert (created on first `--ssl` run)
- `E:\Projects\WebNC\react.production.min.js` — React 18 UMD (from cdnjs)
- `E:\Projects\WebNC\react-dom.production.min.js` — ReactDOM 18 UMD (from cdnjs)
- `E:\Projects\WebNC\babel.min.js` — Babel standalone 7.23.4 (from cdnjs)
- `E:\Projects\WebNC\requirements.txt` — Python deps (fastapi, uvicorn, aiofiles, python-multipart)
- `E:\Projects\WebNC\README.md` — Project documentation with usage, features, API reference, roadmap
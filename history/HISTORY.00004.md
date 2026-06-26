# Summary 00004

## Goal

- Build a Norton Commander-like web file manager with FastAPI backend and React frontend, running on Windows without Node.js.

## Constraints & Preferences
- Node.js not installed; frontend must work via CDN-loaded React + Babel standalone in a single `index.html`
- Python 3.9 available via `py` launcher, not via `python` command
- Full filesystem access (C:\ root, multi-drive) — no sandbox
- Classic NC retro look: blue background, cyan/white/yellow colors, double-panel layout, Fn bar, keyboard-driven
- All scripts (React, ReactDOM, Babel) served locally from the backend, not from CDN (CORS issues with `file://`)
- Table data must use semantic `<table>` HTML, not `<div>`-based flexbox mimicking tables
- UI should not feel cramped — needs adequate padding/spacing
- Ctrl+R/Ctrl+U cannot be used as shortcuts (browser intercepts them)

## Progress
### Done
- Backend: FastAPI server (`nc_server.py`) with full CRUD endpoints (list, view, copy, move, rename, mkdir, delete, batch-delete, search, info, disk, drives, health, sysinfo, compare)
- Backend: sandbox removed; `safe_path` converts URL paths like `/C/Users/foo` to Windows absolute paths for any drive
- Backend: `/api/search` endpoint with glob/regex pattern matching; supports `*`, `?` wildcards via regex fallback
- Backend: `/api/drives` endpoint with volume labels via `GetVolumeInformationW` (ctypes), filters only available drives
- Backend: `PermissionError` handling — skips inaccessible items instead of failing entirely
- Backend: added `sort_by="unsorted"` support — skips sorting, returns filesystem order
- Backend: `/api/list` now supports `filter` query param (fnmatch pattern); `/api/info` uses `iterdir()` not `rglob()` for directory stats (instant on C:\)
- Backend: **all blocking FS calls wrapped in `asyncio.to_thread()`** — prevents event loop blocking, server no longer hangs on slow drives/large dirs
- Backend: `get_file_owner()` via Win32 API (`GetNamedSecurityInfoW` + `LookupAccountSidW`) → `owner: "DOMAIN\Username"` in `/api/info` response
- Backend: `/api/sysinfo` returns OS, hostname, CPU, architecture, uptime, RAM (GlobalMemoryStatusEx), all drives with usage
- Backend: `/api/compare` compares two directories (by name, size, date) → returns only_left, only_right, different, same with `path` for navigation
- Frontend: two-panel layout with keyboard navigation (arrows, Enter, Tab, Insert, Home/End, PgUp/PgDn)
- Frontend: F3 (view), F4 (info), F5 (copy), F6 (move/rename), F7 (mkdir), F8 (delete/batch-delete) with modals
- Frontend: Alt+F1/F2 drive switching with `DriveDialog` (lists drives with labels, arrow/letter-key selection)
- Frontend: `toWinPath` helper to display paths as `C:\Users\...`; status bar with hints
- Frontend: React 18.2.0 + Babel standalone 7.23.4 downloaded from cdnjs, served locally as static files
- Frontend: Sort options per-panel (`handleSort` with `[X]` indicator, toggle asc/desc)
- Frontend: **Brief view mode** (multi-column CSS, column-width: 120px), **Quick view mode** (shows preview of opposite panel's selection — text content for files <64KB, info otherwise)
- Frontend: **Filter...** (InputDialog for fnmatch pattern, filter indicator `[*.txt]` in path bar, persistent across navigation)
- Frontend: **Directory Information** menu items enabled → shows `/api/info` results in InfoDialog; title changes to "Directory Info" for dirs
- Frontend: **Owner** row in InfoDialog (DOMAIN\Username from backend, fallback to uid:gid)
- Frontend: **System Information** dialog (Commands menu) — OS, hostname, CPU, arch, uptime, RAM, drives table
- Frontend: **Compare Directories** dialog (Commands menu) — 4 tabs (Different/Only Left/Only Right/Same), color-coded, click to navigate
- Frontend: **History** (Commands menu) — per-panel path tracking (last 50 unique), dialog with ↑↓/Enter navigation
- Frontend: **Panels On/Off** — Ctrl+O or menu toggles panels visibility; shows "Panels Off (Ctrl+O)" placeholder
- Frontend: **manage_server.ps1** — unified script with start/stop/restart/status/monitor commands; health-check loop with auto-restart; PID file tracking
- Frontend: **run.bat** — cmd wrapper for `manage_server.ps1` (`run` = start, `run stop`, `run status`, `run monitor`)
- Backend: **CompareRequest** model added; all endpoints now use Pydantic models for request validation
- Top menu bar: functional dropdown menus for Left, Files, Commands, Options, Right; mouse navigation with hover-switch; click-outside closes

### In Progress
- (none)

### Blocked
- (none)

## Key Decisions
- Use `py` launcher instead of `python` (the only way to run Python on this system)
- Serve all JS locally (React, ReactDOM, Babel) from the backend instead of CDN because `file://` protocol blocks CORS
- Multi-drive path format: `/C/Users/...` → Windows `C:\Users\...`; `/C/` for drive root
- Use cdnjs instead of unpkg for downloading React/Babel because unpkg redirects broke `urlretrieve`
- Drive switching via Alt+F1 (left panel) and Alt+F2 (right panel) — classic NC convention
- Use `<table>` elements for file listing (semantic HTML) — user explicitly requested over `<div>`-based layouts
- Menu-driven features replace keyboard shortcuts for refresh (Re-read) and swap panels — Ctrl+R/U intercepted by browser
- Per-panel state for sort field/direction and view mode (Brief/Full/Quick) — mirrors classic NC behavior
- `fetchDir` accepts optional `optBy/optDir/optFilter` params to avoid stale closure issues when state changes before React update
- All blocking FS operations wrapped in `asyncio.to_thread()` — avoids event loop blocking (root cause of hangs)
- Owner info fetched via ctypes Win32 API only in `/api/info` (not in directory listing) to avoid performance hit
- Directory stats use `iterdir()` (immediate children) not `rglob()` (recursive) — instant even on system roots
- Server management via PowerShell script (`manage_server.ps1`) with health-loop monitor; start via `Start-Process` to detach from terminal

## Next Steps
- Consider implementing remaining disabled menu items: Info (view mode), Tree, Compressed File, Find file panel, Link, Synchronize Directories, Terminal Emulation, Configuration
- Consider adding file selection (copy/move with selections), drag-and-drop upload
- Test edge cases: very large directories (>10K files), network drives, permissions errors
- Consider per-panel On/Off toggle (currently both panels toggle together)

## Critical Context
- Run backend: `py -m uvicorn nc_server:app --host 0.0.0.0 --port 8000` or use `run.bat` / `manage_server.ps1 start`
- Frontend at `http://localhost:8000/` — the backend serves `index.html` and all JS files
- **Port mismatch issue**: If server starts on wrong port, frontend with `const API = "http://localhost:8000"` will fail — always use `--port 8000`
- Drive paths use uppercase letters: `/C/`, `/D/`, `/E/` etc.
- Babel standalone transpiles JSX+ES6 in the browser; `index.html` uses explicit `React.createElement` (`h()`) calls, not JSX syntax
- The `norton-commander.jsx` file is the Vite version with real JSX imports; `index.html` is the CDN version with `h()` calls
- If page shows blank, check browser console for errors — most common causes: port mismatch, missing parens in script, cached stale scripts
- Total paren count in index.html is 1170/1170 balanced
- Server hangs (event loop blocking) fixed by wrapping all FS calls in `asyncio.to_thread()` — monitor with `run monitor`
- Search results search from `/C/` root; pattern supports glob (`*.txt`) and regex; max_results=200; clicking a result navigates to parent dir
- Quick view fetches `/api/info` + `/api/view` (for files <64KB) for the opposite panel's selected item

## Relevant Files
- `E:\Projects\WebNC\nc_server.py` — FastAPI backend (all endpoints including sysinfo, compare, file owner; all blocking I/O in `asyncio.to_thread()`)
- `E:\Projects\WebNC\index.html` — CDN-based frontend (all components: Panel with Brief/Full/Quick modes, SearchDialog, SysInfoDialog, CompareDialog, HistoryDialog, menu system, sort/filter/view state, preview logic, panels toggle)
- `E:\Projects\WebNC\norton-commander.jsx` — Vite-based React component (not used without Node)
- `E:\Projects\WebNC\manage_server.ps1` — PowerShell script for start/stop/restart/status/monitor; health-check loop with auto-restart
- `E:\Projects\WebNC\run.bat` — cmd wrapper: `run` = start, `run stop`, `run status`, `run monitor`
- `E:\Projects\WebNC\react.production.min.js` — React 18 UMD (downloaded from cdnjs)
- `E:\Projects\WebNC\react-dom.production.min.js` — ReactDOM 18 UMD (downloaded from cdnjs)
- `E:\Projects\WebNC\babel.min.js` — Babel standalone 7.23.4 (downloaded from cdnjs)
- `E:\Projects\WebNC\requirements.txt` — Python deps (fastapi, uvicorn, aiofiles, python-multipart)
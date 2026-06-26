# Summary 00009

## Goal

- Build a Norton Commander-like web file manager with FastAPI backend and React frontend, running on Windows without Node.js, positioned as a local-first keyboard-driven admin utility with remote-administration potential.

## Constraints & Preferences
- Node.js not installed; frontend via native ESM modules (no Babel, no CDN, no JSX)
- Python 3.9 via `py` launcher (not `python`)
- Full filesystem access (C:\ root, multi-drive) — no sandbox
- Classic NC retro look: blue background, cyan/white/yellow colors, double-panel layout, Fn bar, keyboard-driven
- All scripts served locally from backend (CORS issues with `file://`)

## Progress
### Done
- Backend: FastAPI server (`webnc/` package) with full CRUD, search, drives, info, compare, sysinfo, tree, sync, archive endpoints; all blocking FS calls wrapped in `asyncio.to_thread()`
- Backend: comprehensive logging (every API call logged, no bare `except: pass`)
- Backend: sync endpoints with `subdirs`, `by_content`, `ignore_date`, `asymmetric`, `filter` fields; `_compare_content` helper; `suggested` field for auto-marking
- Backend: session auth with SHA-256 token handshake (`_signHeaders` + `SessionAuthMiddleware`)
- Backend: file owner via Win32 API (`GetNamedSecurityInfoW` + `LookupAccountSidW`)
- Backend: `_do_sync` now includes `left`/`right` sub-objects with `size`/`modified_ts` for `only_left`/`only_right` items (fixes frontend size/date display)
- Frontend: fully refactored from monolithic `index.html` to modular ESM structure:
  - `index.html` (22 lines) — loads React UMD + `<script type="module">` entry
  - `frontend/app.js` — NortonCommander main component
  - `frontend/lib/` — `api.js`, `utils.js`, `styles.js`, `config.js`
  - `frontend/components/Panel.js` — Panel + briefListing
  - `frontend/dialogs/` — 12 dialog modules + barrel export `index.js`
- Frontend: two-panel layout, keyboard nav, F-key modals, Alt+F1/F2 drives, sort, view modes (Brief/Full/Quick/Info/Tree), filter, select/invert, per-panel On/Off, history, compare, sysinfo, config, help
- Frontend: SyncDialog — two-phase layout (setup → results), show-filter toggles (→ = ≠ ←), per-row action cycling, info bar, bottom buttons
- Frontend: SyncDialog "trapped user" bug fixed — Re-compare/Close buttons visible even when compare returns zero files
- Frontend: `manage_server.ps1` — start/stop/restart/status/monitor
- Frontend: `run.bat` — cmd wrapper for `manage_server.ps1`
- Frontend: `run.bat` monitor mode (SSL, cert `nc_server.crt`)
- README.md rewritten with local-first positioning, security warning, roadmap
- Backend: `webnc/api/static.py` updated — added `/frontend/{rest:path}` route with explicit `text/javascript` MIME for ES modules, serves nested `frontend/` directory

### In Progress
- (none)

### Blocked
- Ctrl+O cannot be intercepted in Chrome/Edge (browser-level shortcut); capture-phase listener is best-effort, menu always works

## Key Decisions
- Use `py` launcher instead of `python`
- Serve all JS locally from backend (CORS with `file://`)
- Multi-drive path format: `/C/Users/...` → Windows `C:\Users\...`
- Frontend modular structure: `index.html` loads React UMD scripts, then `type="module"` imports `frontend/app.js` which imports all other modules
- Each module defines `const h = React.createElement` locally for `h()` syntax (no JSX, no Babel)
- Sync dialog redesigned to match Total Commander workflow: two-phase (setup → compare → results), show-filter toggles instead of tabs, per-row action cycling, info bar with counts
- `_do_sync` returns `suggested` field for auto-marking only_left/only_right items in frontend
- `handleSync` opens setup without API call; `handleSyncCompare` triggered by dialog Compare button
- All blocking FS operations wrapped in `asyncio.to_thread()`

## Next Steps
- Test ESLint/prettier or syntax validation for all modules
- Consider remaining disabled menu items: Find file panel, Link, Terminal Emulation, EGA Lines, etc.
- Consider FTP/SFTP, ZIP/TAR providers via abstracted `VfsProvider` layer
- Background file operations with progress/cancel
- Authentication, audit log, restricted mode for remote administration

## Critical Context
- Run backend: `py -m uvicorn webnc.main:app --host 127.0.0.1 --port 8000` or `run.bat` / `manage_server.ps1 start`
- Frontend at `http://localhost:8000/` — backend serves `index.html` and all JS from `frontend/` directory
- ESM modules require `text/javascript` MIME type; static router explicitly sets it for `.js` files
- React loaded from bundled UMD files: `react.production.min.js` + `react-dom.production.min.js` (at project root)
- Port 8000 in use → monitor fallback: `run.bat monitor` with SSL; force-kill with `taskkill /F /PID <pid>` then `Get-Process python | Stop-Process`
- Sync flow: open Commands → Synchronize Directories → setup mode (set filter/options) → [Compare] → results (click files to set direction) → [Synchronize]
- Sync API: `POST /api/sync/plan`; `POST /api/sync/execute` with `{left, right, actions: [{name, action}]}`
- `app.js:515 Uncaught SyntaxError: missing ) after argument list` — reported error, may be due to nested template literal at line 472 or other structural issue; needs investigation
- Current server hangs frequently on Windows; monitor auto-restarts every 15s

## Relevant Files
- `E:\Projects\WebNC\index.html` — entry point (22 lines, no Babel)
- `E:\Projects\WebNC\frontend/app.js` — NortonCommander main component (516 lines)
- `E:\Projects\WebNC\frontend/lib/` — `api.js`, `utils.js`, `styles.js`, `config.js`
- `E:\Projects\WebNC\frontend/components/Panel.js` — Panel + briefListing
- `E:\Projects\WebNC\frontend/dialogs/` — 12 dialog modules + `index.js` barrel export
- `E:\Projects\WebNC\webnc\api\sync.py` — sync endpoints with all options
- `E:\Projects\WebNC\webnc\api\static.py` — static file serving (frontend + root .js)
- `E:\Projects\WebNC\webnc\main.py` — FastAPI app factory, auth setup, router registration
- `E:\Projects\WebNC\webnc\security\middleware.py` — `SessionAuthMiddleware`
- `E:\Projects\WebNC\webnc\security\console_token.py` — `ConsoleTokenProvider` (SHA-256 handshake)
- `E:\Projects\WebNC\manage_server.ps1` — start/stop/restart/status/monitor
- `E:\Projects\WebNC\run.bat` — cmd wrapper for manage_server.ps1
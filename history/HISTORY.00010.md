# Summary 00010

## Goal

- Build a Norton Commander-like web file manager with FastAPI backend and React frontend, running on Windows without Node.js.

## Constraints & Preferences
- Node.js not installed; frontend via native ESM modules (no JSX, no Babel)
- Python 3.9 via `py` launcher (not `python`)
- Full filesystem access (C:\ root, multi-drive)
- Classic NC retro look: blue background, cyan/white/yellow colors, keyboard-driven
- All scripts served locally from backend (CORS issues with `file://`)

## Progress
### Done
- Backend: FastAPI server (`webnc/` package) with full CRUD, search, drives, info, compare, sysinfo, tree, sync, archive endpoints
- Backend: session auth with SHA-256 token handshake (`_signHeaders` + `SessionAuthMiddleware`)
- Backend: `/api/drives` and `/api/disk` exempted from auth in `SessionAuthMiddleware` (non-sensitive data — drive letters, free space)
- Backend: file owner via Win32 API; sync endpoints with `subdirs`, `by_content`, `ignore_date`, `asymmetric`, `filter` fields
- Backend: comprehensive logging (every API call logged, no bare `except: pass`)
- Frontend: fully refactored from monolithic `index.html` to modular ESM structure:
  - `index.html` (22 lines) → loads React UMD + `<script type="module">` entry
  - `frontend/app.js` — NortonCommander main component (516 lines)
  - `frontend/lib/` — `api.js`, `utils.js`, `styles.js`, `config.js`
  - `frontend/components/Panel.js` — Panel + briefListing
  - `frontend/dialogs/` — 12 dialog modules + barrel export `index.js`
- Frontend: two-panel layout, keyboard nav, F-key modals, Alt+F1/F2 drives, sort, view modes (Brief/Full/Quick/Info/Tree), filter, select/invert, per-panel On/Off, history, compare, sysinfo, config, help
- Frontend: SyncDialog — two-phase layout (setup → results), show-filter toggles, per-row action cycling, info bar
- Frontend: `loginDlg` and `syncDlg` added to keyboard handler `useEffect` dependency array (fixes stale closure)
- Frontend: syntax error fixed — line 471 `})))),` → `}))))),` (added missing `)` to close `["Left",...].map((name) => ...)` expression), resolves `SyntaxError: missing ) after argument list` on line 515
- `manage_server.ps1` — start/stop/restart/status/monitor
- `run.bat` — cmd wrapper for `manage_server.ps1`
- README.md rewritten with local-first positioning, security warning, roadmap

### In Progress
- Root-causing server hangs on Windows that force monitor mode to auto-restart every 15s — identified that `Path.exists()`, `.is_dir()`, `.stat()`, `.resolve()`, `.iterdir()` calls in `async def` API handlers run directly on the asyncio event loop (NOT wrapped in `asyncio.to_thread()`); when user accesses a problematic path (CD-ROM, network drive, disconnected USB), these block for 30+ seconds freezing ALL handlers including `/api/health`, causing the monitor to kill and restart

### Blocked
- Ctrl+O cannot be intercepted in Chrome/Edge (browser-level shortcut); capture-phase listener is best-effort

## Key Decisions
- Use `py` launcher instead of `python`
- Serve all JS locally from backend (avoids CORS with `file://`)
- Multi-drive path format: `/C/Users/...` → Windows `C:\Users\...`
- Frontend modular structure: `index.html` loads React UMD scripts, then `type="module"` imports `frontend/app.js` which imports all other modules
- Each module defines `const h = React.createElement` locally for `h()` syntax (no JSX, no Babel)
- Token persistence to disk rejected by user for security reasons
- `/api/drives` and `/api/disk` exempt from auth — drive listing and disk usage are not sensitive data
- All blocking FS operations MUST be wrapped in `asyncio.to_thread()` to avoid event loop blocking; any raw `Path.exists()/.is_dir()/.stat()` in an `async def` handler is a potential hang

## Next Steps
- Wrap all blocking `Path.exists()`, `.is_dir()`, `.stat()`, `.resolve()`, `.iterdir()` calls in `async def` handlers into `await asyncio.to_thread(...)` — particularly in `webnc/api/files.py` (lines 150, 153, 180, 215, 235, 262, 393, 440, 511, 525, 536-541, 593)
- Check other API modules (`compare.py`, `system.py`, `archive.py`) for similar event-loop-blocking calls
- Consider adding timeouts to `asyncio.to_thread()` calls as second line of defense

## Critical Context
- Run backend: `py -m uvicorn webnc.main:app --host 127.0.0.1 --port 8000` or `run.bat`
- Frontend at `http://localhost:8000/` (backend serves `index.html` and all JS)
- ESM modules require `text/javascript` MIME type — static router explicitly sets it
- React loaded from bundled UMD files (`react.production.min.js` + `react-dom.production.min.js`)
- Monitor mode (`run.bat monitor`) auto-restarts server every 15s when health check fails; root cause of restarts is blocking filesystem calls on the event loop
- Auth token is ephemeral — regenerated on every server start (no persistence)
- On server restart, old token in browser becomes invalid; next API call returns 401 → `logout()` → login dialog appears
- Parens in `app.js` are balanced (O=0 verified after syntax fix)

## Relevant Files
- `E:\Projects\WebNC\webnc\api\files.py` — main filesystem API handlers; contains ~30 blocking `Path.exists()/.is_dir()/.stat()` calls on the event loop that cause server hangs
- `E:\Projects\WebNC\webnc\api\drives.py` — `_do_list_drives` iterates all 26 drives via `shutil.disk_usage()` (wrapped in thread pool, but can still exhaust pool if too many hang)
- `E:\Projects\WebNC\webnc\security\middleware.py` — `SessionAuthMiddleware` exempts `/api/drives` and `/api/disk`
- `E:\Projects\WebNC\webnc\security\console_token.py` — `ConsoleTokenProvider` (SHA-256 handshake, ephemeral token)
- `E:\Projects\WebNC\frontend\app.js` — NortonCommander main component (516 lines)
- `E:\Projects\WebNC\frontend\dialogs\DriveDialog.js` — drive selection dialog
- `E:\Projects\WebNC\manage_server.ps1` — monitor mode checks health every 15s, restarts on failure
- `E:\Projects\WebNC\nc_server.py` — thin shim importing `webnc.main`

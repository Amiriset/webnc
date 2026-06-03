# Summary 00008

## Goal

- Build a Norton Commander-like web file manager with FastAPI backend and React frontend, running on Windows without Node.js, positioned as a local-first keyboard-driven admin utility with remote-administration potential. Synchronize Directories dialog redesigned to match Total Commander workflow.

## Constraints & Preferences
- Node.js not installed; frontend works via CDN-loaded React + Babel standalone in single `index.html`
- Python 3.9 via `py` launcher (not `python`)
- Full filesystem access (C:\ root, multi-drive) — no sandbox
- Classic NC retro look: blue background, cyan/white/yellow colors, double-panel layout, Fn bar, keyboard-driven
- All scripts served locally from backend (CORS issues with `file://`)
- Table data uses semantic `<table>` HTML

## Progress
### Done
- Backend: FastAPI server (`nc_server.py` → refactored to `webnc/` package) with full CRUD, search, drives, info, compare, sysinfo, tree, sync, archive endpoints
- Backend: all blocking FS calls wrapped in `asyncio.to_thread()`
- Backend: comprehensive logging (every API call logged, no bare `except: pass`)
- Backend: sync endpoints updated — `SyncRequest` model now has `subdirs`, `by_content`, `ignore_date`, `asymmetric`, `filter` fields; `_do_sync` uses all options; `_compare_content` helper for by_content mode; items have `suggested` field for auto-marking
- Frontend: two-panel layout, keyboard nav, F-key modals, Alt+F1/F2 drives, sort, view modes (Brief/Full/Quick/Info/Tree), filter, select/invert, per-panel On/Off, history, compare, sysinfo, config, help
- Frontend: SyncDialog completely redesigned to match Total Commander layout:
  - **Two-phase dialog**: Setup (paths, filter input, checkboxes for Subdirs/By content/Ignore date/Asymmetric, [Compare] button) → Results (file list with show-filter toggles)
  - **Show-filter toggles**: → = ≠ ← — independent toggle buttons, filter file list by action type
  - **Per-row action cycling**: click file to cycle through available directions per status:
    - `different`: `null → copy_left_to_right → copy_right_to_left → null`
    - `only_left`: `copy_left_to_right ↔ null`
    - `only_right`: `asymmetric ? delete_right : copy_right_to_left ↔ null`
    - `same`: not clickable
  - **Info bar**: Total, Same, Diff, L-only, R-only counts
  - **Bottom buttons**: Re-compare, Mark All, Synchronize, Close
  - **Fixed "only Cancel works" bugs**: auto-detect best tab, same-items non-clickable, Enter key guard (`actions.length > 0`), guard against null `syncPlan`, empty actions guard in `syncExecute`
- Frontend: parent handlers updated — `handleSync` opens setup mode (no API call), `handleSyncCompare` sends options + auto-marks suggested items, `syncToggleItem` simplified to `(path, action)` cycling, `syncSetAll` uses `item.suggested`, `syncDefaultAction`/`syncSetDirection` removed
- Frontend: `manage_server.ps1` — start/stop/restart/status/monitor
- Frontend: `run.bat` — cmd wrapper for `manage_server.ps1`
- Backend: `webnc/` package structure — `main.py` (app factory), `api/` (files, drives, system, compare, sync, archive, static), `models/` (sync, compare, files, auth, state), `vfs/` (paths), `security/` (auth providers, middleware), `services/`, `frontend/`, `logging_config.py`, `config.py`
- Backend: session auth with SHA-256 token handshake (`_signHeaders` + `SessionAuthMiddleware`)
- Backend: file owner via Win32 API (`GetNamedSecurityInfoW` + `LookupAccountSidW`)
- README.md rewritten with local-first positioning, security warning, roadmap

### In Progress
- (none)

### Blocked
- Ctrl+O cannot be intercepted in Chrome/Edge (browser-level shortcut); capture-phase listener is best-effort, menu always works

## Key Decisions
- Use `py` launcher instead of `python`
- Serve all JS locally from backend (CORS with `file://`)
- Multi-drive path format: `/C/Users/...` → Windows `C:\Users\...`
- Sync dialog redesigned to match Total Commander workflow: two-phase (setup → compare → results), show-filter toggles instead of tabs, per-row action cycling, info bar with counts
- `_do_sync` returns `suggested` field for auto-marking only_left/only_right items in frontend
- `handleSync` opens setup without API call; `handleSyncCompare` triggered by dialog Compare button
- All blocking FS operations wrapped in `asyncio.to_thread()`
- Logging: every API call logged at INFO; all silent exception blocks upgraded to `logger.warning()` or `logger.exception()`

## Next Steps
- Verify sync dialog works end-to-end (frontend → backend → filesystem)
- Consider remaining disabled menu items: Find file panel, Link, Terminal Emulation, EGA Lines, etc.
- Consider FTPSFTP, ZIP/TAR providers via abstracted `VfsProvider` layer
- Background file operations with progress/cancel
- Authentication, audit log, restricted mode for remote administration

## Critical Context
- Run backend: `py -m uvicorn nc_server:app --host 127.0.0.1 --port 8000` or `run.bat` / `manage_server.ps1 start`
- Frontend at `http://localhost:8000/` — backend serves `index.html` and all JS
- Port mismatch causes fetch failures — always use `--port 8000`
- Sync flow: open Commands → Synchronize Directories → setup mode (set filter/options) → [Compare] → results (click files to set direction) → [Synchronize]
- Sync API: `POST /api/sync/plan` with `{left, right, subdirs, by_content, ignore_date, asymmetric, filter}`; `POST /api/sync/execute` with `{left, right, actions: [{name, action}]}`
- Only `copy_left_to_right` / `copy_right_to_left` actions are exposed in UI; `delete_left`/`delete_right` only for asymmetric only_right items
- Babel standalone transpiles JSX+ES6 in browser; `index.html` uses `React.createElement` (`h()`), not JSX
- Project refactored from monolithic `nc_server.py` into `webnc/` package; `nc_server.py` is now a thin shim importing from `webnc.main`

## Relevant Files
- `E:\Projects\WebNC\webnc\api\sync.py` — sync endpoints with all options (subdirs, by_content, ignore_date, asymmetric, filter)
- `E:\Projects\WebNC\webnc\models\sync.py` — SyncRequest (with new fields), SyncAction, SyncExecuteRequest
- `E:\Projects\WebNC\index.html` — SyncDialog component (lines 323–431+), parent handlers (handleSync, handleSyncCompare, syncToggleItem, syncSetAll, syncExecute)
- `E:\Projects\WebNC\webnc\main.py` — FastAPI app factory, auth setup, router registration
- `E:\Projects\WebNC\nc_server.py` — thin shim importing from `webnc.main`
- `E:\Projects\WebNC\manage_server.ps1` — start/stop/restart/status/monitor

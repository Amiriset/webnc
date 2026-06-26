# Summary 00001

## Goal

- Build a Norton Commander-like web file manager with FastAPI backend and React frontend, running on Windows without Node.js.

## Constraints & Preferences
- Node.js not installed; frontend must work via CDN-loaded React + Babel standalone in a single `index.html`
- Python 3.9 available via `py` launcher, not via `python` command
- Full filesystem access (C:\ root, multi-drive) — no sandbox
- Classic NC retro look: blue background, cyan/white/yellow colors, double-panel layout, Fn bar, keyboard-driven
- All scripts (React, ReactDOM, Babel) served locally from the backend, not from CDN (CORS issues with `file://`)

## Progress
### Done
- Backend: FastAPI server (`nc_server.py`) with full CRUD endpoints (list, view, copy, move, rename, mkdir, delete, batch-delete, search, info, disk, drives, health)
- Backend: sandbox removed; `safe_path` now converts URL paths like `/C/Users/foo` to Windows absolute paths for any drive
- Backend: `/api/drives` endpoint with volume labels via `GetVolumeInformationW` (ctypes), filters only available drives
- Backend: `PermissionError` handling — skips inaccessible items instead of failing entirely
- Frontend: two-panel layout with keyboard navigation (arrows, Enter, Tab, Insert, Home/End, PgUp/PgDn)
- Frontend: F3 (view), F4 (info), F5 (copy), F6 (move/rename), F7 (mkdir), F8 (delete/batch-delete) with modals
- Frontend: Alt+F1/F2 drive switching with `DriveDialog` (lists drives with labels, arrow/letter-key selection)
- Frontend: `toWinPath` helper to display paths as `C:\Users\...`; status bar with Alt+F1/F2 hint
- Frontend: React 18.2.0 + Babel standalone 7.23.4 downloaded from cdnjs, served locally as static files

### In Progress
- (none)

### Blocked
- (none)

## Key Decisions
- Use `py` launcher instead of `python` (the only way to run Python on this system)
- Serve all JS locally (React, ReactDOM, Babel) from the backend instead of unpkg CDN because `file://` protocol blocks CORS
- Multi-drive path format: `/C/Users/...` → Windows `C:\Users\...`; `/C/` for drive root
- Use cdnjs instead of unpkg for downloading React/Babel because unpkg redirects broke `urlretrieve`
- Drive switching via Alt+F1 (left panel) and Alt+F2 (right panel) — classic NC convention

## Next Steps
- Test the full flow: open `http://localhost:8000/`, navigate drives with Alt+F1/F2, verify F3-F8 operations
- Optionally implement remaining unimplemented features: Brief mode, Ctrl+R (refresh), Ctrl+U (swap panels), Ctrl+O (hide panels), tree view, etc.

## Critical Context
- Run backend: `py nc_server.py` (listens on port 8000)
- Frontend at `http://localhost:8000/` — the backend serves `index.html` and all JS files
- Drive paths use uppercase letters: `/C/`, `/D/`, `/E/` etc.
- Babel standalone transpiles JSX+ES6 in the browser; `index.html` uses explicit `React.createElement` (`h()`) calls, not JSX syntax
- The `norton-commander.jsx` file is the Vite version with real JSX imports; `index.html` is the CDN version with `h()` calls
- If page shows blank, check browser console for errors (cached scripts, Babel failures, etc.)

## Relevant Files
- `E:\Projects\WebNC\nc_server.py` — FastAPI backend (all endpoints, path helpers, static file serving)
- `E:\Projects\WebNC\index.html` — CDN-based frontend (React+DOM+Babel from local files, all components inline)
- `E:\Projects\WebNC\norton-commander.jsx` — Vite-based React component (imports, JSX syntax, not used without Node)
- `E:\Projects\WebNC\react.production.min.js` — React 18 UMD (downloaded from cdnjs)
- `E:\Projects\WebNC\react-dom.production.min.js` — ReactDOM 18 UMD (downloaded from cdnjs)
- `E:\Projects\WebNC\babel.min.js` — Babel standalone 7.23.4 (downloaded from cdnjs)
- `E:\Projects\WebNC\requirements.txt` — Python deps (fastapi, uvicorn, aiofiles, python-multipart)

---

## Internal Milestone 001
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

---

## Internal Milestone 002
- Build a Norton Commander-like web file manager with FastAPI backend and React frontend, running on Windows without Node.js.

## Constraints & Preferences
- Node.js not installed; frontend must work via CDN-loaded React + Babel standalone in a single `index.html`
- Python 3.9 available via `py` launcher, not via `python` command
- Full filesystem access (C:\ root, multi-drive) — no sandbox
- Classic NC retro look: blue background, cyan/white/yellow colors, double-panel layout, Fn bar, keyboard-driven
- All scripts (React, ReactDOM, Babel) served locally from the backend, not from CDN (CORS issues with `file://`)
- Table data must use semantic `<table>` HTML, not `<div>`-based flexbox mimicking tables
- UI should not feel cramped ("все слитно") — needs adequate padding/spacing

## Progress
### Done
- Backend: FastAPI server (`nc_server.py`) with full CRUD endpoints (list, view, copy, move, rename, mkdir, delete, batch-delete, search, info, disk, drives, health)
- Backend: sandbox removed; `safe_path` converts URL paths like `/C/Users/foo` to Windows absolute paths for any drive
- Backend: `/api/drives` endpoint with volume labels via `GetVolumeInformationW` (ctypes), filters only available drives
- Backend: `PermissionError` handling — skips inaccessible items instead of failing entirely
- Frontend: two-panel layout with keyboard navigation (arrows, Enter, Tab, Insert, Home/End, PgUp/PgDn)
- Frontend: F3 (view), F4 (info), F5 (copy), F6 (move/rename), F7 (mkdir), F8 (delete/batch-delete) with modals
- Frontend: Alt+F1/F2 drive switching with `DriveDialog` (lists drives with labels, arrow/letter-key selection)
- Frontend: `toWinPath` helper to display paths as `C:\Users\...`; status bar with Alt+F1/F2 hint
- Frontend: React 18.2.0 + Babel standalone 7.23.4 downloaded from cdnjs, served locally as static files
- **Paren balance fix**: Missing `)` on `index.html` line 96 (DriveDialog closing `")));` → `"))));`) — was causing script-wide syntax error → blank page
- **Panel → `<table>` rewrite**: Panel component now uses real `<table>`, `<thead>`, `<tbody>`, `<tr>`, `<td>` instead of `<div>` flexbox for file listing; scrollIntoView uses `querySelector([data-idx])` instead of `children[selectedIdx]`
- **Spacing improvements**: increased padding on title bar (`3px 10px`), command line (`3px 8px`), status bar (`2px 10px`), Fn buttons (`4px 2px`); added `gap: "4px"` between panels

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
- Use `<table>` elements for file listing (semantic HTML, better accessibility) — user explicitly requested this over `<div>`-based layouts

## Next Steps
- Test the full flow: open `http://localhost:8000/`, navigate drives with Alt+F1/F2, verify all keyboard shortcuts and modal operations
- Verify the "UI disappears on Alt+F1/F2" report is resolved by the paren balance fix
- Consider adding remaining unimplemented features: Brief mode, Ctrl+R (refresh), Ctrl+U (swap panels), Ctrl+O (hide panels), tree view, etc.

## Critical Context
- Run backend: `py nc_server.py` (listens on port 8000)
- Frontend at `http://localhost:8000/` — the backend serves `index.html` and all JS files
- **Port mismatch issue**: If server starts on wrong port (e.g. 8080), frontend with `const API = "http://localhost:8000"` will fail — always use `--port 8000`
- Drive paths use uppercase letters: `/C/`, `/D/`, `/E/` etc.
- Babel standalone transpiles JSX+ES6 in the browser; `index.html` uses explicit `React.createElement` (`h()`) calls, not JSX syntax
- The `norton-commander.jsx` file is the Vite version with real JSX imports; `index.html` is the CDN version with `h()` calls
- If page shows blank, check browser console for errors — most common causes: port mismatch, missing parens in script, cached stale scripts
- Total paren count must be exactly balanced (currently 606/606)

## Relevant Files
- `E:\Projects\WebNC\nc_server.py` — FastAPI backend (all endpoints, path helpers, static file serving)
- `E:\Projects\WebNC\index.html` — CDN-based frontend (React+DOM+Babel from local files, all components inline)
- `E:\Projects\WebNC\norton-commander.jsx` — Vite-based React component (imports, JSX syntax, not used without Node)
- `E:\Projects\WebNC\react.production.min.js` — React 18 UMD (downloaded from cdnjs)
- `E:\Projects\WebNC\react-dom.production.min.js` — ReactDOM 18 UMD (downloaded from cdnjs)
- `E:\Projects\WebNC\babel.min.js` — Babel standalone 7.23.4 (downloaded from cdnjs)
- `E:\Projects\WebNC\requirements.txt` — Python deps (fastapi, uvicorn, aiofiles, python-multipart)

---

## Internal Milestone 003
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
- Backend: FastAPI server (`nc_server.py`) with full CRUD endpoints (list, view, copy, move, rename, mkdir, delete, batch-delete, search, info, disk, drives, health)
- Backend: sandbox removed; `safe_path` converts URL paths like `/C/Users/foo` to Windows absolute paths for any drive
- Backend: `/api/search` endpoint with glob/regex pattern matching; supports `*`, `?` wildcards via regex fallback
- Backend: `/api/drives` endpoint with volume labels via `GetVolumeInformationW` (ctypes), filters only available drives
- Backend: `PermissionError` handling — skips inaccessible items instead of failing entirely
- Backend: added `sort_by="unsorted"` support — skips sorting, returns filesystem order
- Frontend: two-panel layout with keyboard navigation (arrows, Enter, Tab, Insert, Home/End, PgUp/PgDn)
- Frontend: F3 (view), F4 (info), F5 (copy), F6 (move/rename), F7 (mkdir), F8 (delete/batch-delete) with modals
- Frontend: Alt+F1/F2 drive switching with `DriveDialog` (lists drives with labels, arrow/letter-key selection)
- Frontend: `toWinPath` helper to display paths as `C:\Users\...`; status bar with hints
- Frontend: React 18.2.0 + Babel standalone 7.23.4 downloaded from cdnjs, served locally as static files
- **Paren balance fix**: Missing `)` on DriveDialog closing — was causing script-wide syntax error → blank page
- **Panel → `<table>` rewrite**: Panel uses real `<table>`, `<thead>`, `<tbody>`, `<tr>`, `<td>`; scrollIntoView uses `querySelector([data-idx])`
- **Spacing improvements**: increased padding on title bar, command line, status bar, Fn buttons; added `gap: "4px"` between panels
- **Date format fix**: changed from `MM-DD HH:MM` to `YYYY-MM-DD HH:MM` (added year); date column width 90→140px, added `white-space: nowrap`
- **Top menu bar**: functional dropdown menus for Left, Files, Commands, Options, Right; mouse navigation with hover-switch; click-outside closes
- **Menu structure**: Left/Right menus match real NC5 (Brief/Full/Info/Tree/Quick view/Compressed File/Find file panel/Directory information/Link/On/Off; Name/Extension/Time/Size/Unsorted; Re-read/Filter/Drive); Commands matches real NC5 (NDC tree/Find File/History/EGA Lines/System Information; Swap panels/Panels On/Off/Compare Directories/Synchronize Directories; Terminal Emulation; Menu File Edit/Extension File edit/Editors; Configuration)
- **Find File (F9)**: `SearchDialog` component with pattern input, results list, ↑↓ navigation, Enter to open; uses `/api/search`; Esc to close
- **Search bug fix**: `setSearched(true)` was missing — dialog always showed hint instead of results
- **Sort options**: per-panel sort state (`leftSortBy/leftSortDir`, `rightSortBy/rightSortDir`); clickable menu items with `[X]` indicator; repeated click toggles asc/desc; `handleSort` passes sort params directly to `fetchDir`
- **Sort bug fix**: initial `useEffect` changed to `[]` deps to prevent re-fetch to `/C/` on sort change; `fetchDir` accepts optional `optBy/optDir` params to bypass stale closure
- **Brief view mode**: per-panel state (`leftViewMode`, `rightViewMode`); multi-column layout via CSS `column-width: 120px`; loading/error states handled; only filenames displayed (no size/date); ↑↓ navigation works in DOM order

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
- Per-panel state for sort field/direction and view mode (Brief/Full) — mirrors classic NC behavior
- `fetchDir` accepts optional `optBy/optDir` params to avoid stale closure issues when sort changes before React state update

## Next Steps
- Test all menu items: Left (View modes, Sort options, Re-read, Drive), Files (F3-F8), Commands (Find File, Swap panels), Options
- Verify Brief mode loads correctly with loading/error states
- Consider implementing remaining disabled menu items: Filter, On/Off (panel toggle), System Information, Search refinement, etc.
- Consider adding keyboard navigation for menus (arrow keys, Enter, Escape)

## Critical Context
- Run backend: `py -m uvicorn nc_server:app --host 0.0.0.0 --port 8000` or `py nc_server.py` (listens on port 8000)
- Frontend at `http://localhost:8000/` — the backend serves `index.html` and all JS files
- **Port mismatch issue**: If server starts on wrong port, frontend with `const API = "http://localhost:8000"` will fail — always use `--port 8000`
- Drive paths use uppercase letters: `/C/`, `/D/`, `/E/` etc.
- Babel standalone transpiles JSX+ES6 in the browser; `index.html` uses explicit `React.createElement` (`h()`) calls, not JSX syntax
- The `norton-commander.jsx` file is the Vite version with real JSX imports; `index.html` is the CDN version with `h()` calls
- If page shows blank, check browser console for errors — most common causes: port mismatch, missing parens in script, cached stale scripts
- Total paren count in index.html is currently 836/836 balanced
- Search results search from `/C/` root; pattern supports glob (`*.txt`) and regex; max_results=200; clicking a result navigates to parent dir
- Brief mode uses `column-width: 120px` CSS columns; DOM order is top-to-bottom per column; data-idx attribute used for scrollIntoView

## Relevant Files
- `E:\Projects\WebNC\nc_server.py` — FastAPI backend (all endpoints, path helpers, static file serving); includes search, unsorted sort support
- `E:\Projects\WebNC\index.html` — CDN-based frontend (React+DOM+Babel from local files, all components inline: SearchDialog, briefListing, Panel with viewMode, menu system with openMenu state, sort/view state)
- `E:\Projects\WebNC\norton-commander.jsx` — Vite-based React component (imports, JSX syntax, not used without Node)
- `E:\Projects\WebNC\react.production.min.js` — React 18 UMD (downloaded from cdnjs)
- `E:\Projects\WebNC\react-dom.production.min.js` — ReactDOM 18 UMD (downloaded from cdnjs)
- `E:\Projects\WebNC\babel.min.js` — Babel standalone 7.23.4 (downloaded from cdnjs)
- `E:\Projects\WebNC\requirements.txt` — Python deps (fastapi, uvicorn, aiofiles, python-multipart)

---

## Goal 004
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

---

## Internal Milestone 005
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
- Backend: FastAPI server (`nc_server.py`) with full CRUD endpoints (list, view, copy, move, rename, mkdir, delete, batch-delete, search, info, disk, drives, health, sysinfo, compare, tree)
- Backend: sandbox removed; `safe_path` converts URL paths like `/C/Users/foo` to Windows absolute paths for any drive
- Backend: `/api/search` endpoint with glob/regex pattern matching; supports `*`, `?` wildcards via regex fallback
- Backend: `/api/drives` endpoint with volume labels via `GetVolumeInformationW` (ctypes), filters only available drives
- Backend: `PermissionError` handling — skips inaccessible items instead of failing entirely; all `except` blocks now log warnings
- Backend: added `sort_by="unsorted"` support — skips sorting, returns filesystem order
- Backend: `/api/list` now supports `filter` query param (fnmatch pattern); `/api/info` uses `iterdir()` not `rglob()` for directory stats (instant on C:\)
- Backend: **all blocking FS calls wrapped in `asyncio.to_thread()`** — prevents event loop blocking, server no longer hangs on slow drives/large dirs
- Backend: `get_file_owner()` via Win32 API (`GetNamedSecurityInfoW` + `LookupAccountSidW`) → `owner: "DOMAIN\Username"` in `/api/info` response
- Backend: `/api/sysinfo` returns OS, hostname, CPU, architecture, uptime, RAM (GlobalMemoryStatusEx), all drives with usage
- Backend: `/api/compare` compares two directories (by name, size, date) → returns only_left, only_right, different, same with `path` for navigation
- Backend: `/api/tree` returns immediate subdirectories for tree view (lazy-loaded)
- Backend: **comprehensive logging** added — `import logging` with `logger.info()` on every API call (with params), `logger.warning()` on all silent exception swallows, `logger.exception()` on caught errors; no bare `except: pass` remains
- Frontend: two-panel layout with keyboard navigation (arrows, Enter, Tab, Insert, Home/End, PgUp/PgDn)
- Frontend: F3 (view), F4 (info), F5 (copy), F6 (move/rename), F7 (mkdir), F8 (delete/batch-delete) with modals
- Frontend: Alt+F1/F2 drive switching with `DriveDialog` (lists drives with labels, arrow/letter-key selection)
- Frontend: `toWinPath` helper to display paths as `C:\Users\...`; status bar with hints
- Frontend: React 18.2.0 + Babel standalone 7.23.4 downloaded from cdnjs, served locally as static files
- Frontend: Sort options per-panel (`handleSort` with `[X]` indicator, toggle asc/desc)
- Frontend: Brief, Full, Quick view, **Info**, **Tree** view modes per panel
- Frontend: **Info view mode** (Left/Right → Info) — shows directory summary + disk info about the OPPOSITE panel; updates dynamically when cursor moves
- Frontend: **Tree view mode** (Left/Right → Tree) — expandable directory tree with `[+]`/`[-]` indicators (click to toggle), lazy-loading from `/api/tree`, opposite panel follows cursor
- Frontend: **Filter...** (InputDialog for fnmatch pattern, filter indicator `[*.txt]` in path bar, persistent across navigation)
- Frontend: **Directory Information** menu items enabled → shows `/api/info` results in InfoDialog; title changes to "Directory Info" for dirs
- Frontend: **Owner** row in InfoDialog (DOMAIN\Username from backend, fallback to uid:gid)
- Frontend: **System Information** dialog (Commands menu) — OS, hostname, CPU, arch, uptime, RAM, drives table
- Frontend: **Compare Directories** dialog (Commands menu) — 4 tabs (Different/Only Left/Only Right/Same), color-coded, click to navigate
- Frontend: **History** (Commands menu) — per-panel path tracking (last 50 unique), dialog with ↑↓/Enter navigation
- Frontend: **Select Group (+)** — InputDialog for fnmatch pattern, adds to selection
- Frontend: **Deselect Group (−)** — InputDialog for fnmatch pattern, removes from selection
- Frontend: **Invert Selection (*)** — toggles all non-parent items
- Frontend: **Per-panel On/Off** — `leftPanelVisible`/`rightPanelVisible` states; Left/Right menu toggles individual panel; Commands → Panels On/Off toggles both
- Frontend: **Panels On/Off** — `{ capture: true }` listener on `document` for Ctrl+O (best-effort; browser may still intercept); menu always works
- Frontend: **manage_server.ps1** — unified script with start/stop/restart/status/monitor commands; health-check loop with auto-restart; PID file tracking
- Frontend: **run.bat** — cmd wrapper for `manage_server.ps1` (`run` = start, `run stop`, `run status`, `run monitor`)
- Top menu bar: functional dropdown menus for Left, Files, Commands, Options, Right; mouse navigation with hover-switch; click-outside closes
- Backend: **CompareRequest** model added; all endpoints now use Pydantic models for request validation
- Backend: `/api/info` now includes `disk_total`, `disk_free`, `disk_used`, `disk_percent_used`
- **README.md** rewritten: positioned as local-first admin utility; security warning; `--host 127.0.0.1` in Quick Start with LAN section; Roadmap (FTP/SFTP, archives, auth, audit, restricted mode)

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
- Use `<table>` elements for file listing (semantic HTML) — user explicitly requested over `<div>`-based layouts
- Menu-driven features replace keyboard shortcuts for refresh (Re-read) and swap panels — Ctrl+R/U intercepted by browser
- Per-panel state for sort field/direction and view mode (Brief/Full/Quick/Info/Tree) — mirrors classic NC behavior
- `fetchDir` accepts optional `optBy/optDir/optFilter` params to avoid stale closure issues when state changes before React update
- All blocking FS operations wrapped in `asyncio.to_thread()` — avoids event loop blocking (root cause of hangs)
- Owner info fetched via ctypes Win32 API only in `/api/info` (not in directory listing) to avoid performance hit
- Directory stats use `iterdir()` (immediate children) not `rglob()` (recursive) — instant even on system roots
- Server management via PowerShell script (`manage_server.ps1`) with health-loop monitor; start via `Start-Process` to detach from terminal
- Tree view uses `[+]`/`[-]` click separators (not double-click) to avoid browser click/dblclick event conflicts
- Logging: every API call logged with params at `INFO` level; all silent exception blocks upgraded to `logger.warning()` or `logger.exception()`
- Project positioned as "browser-hosted utility software" — NC UX + browser + local-first + Windows-native + zero-build + full FS access (an empty intersection in the tooling ecosystem)

## Next Steps
- Consider implementing remaining disabled menu items: Compressed File, Find file panel, Link, Synchronize Directories, Terminal Emulation, Configuration
- Consider tree view entering at current directory (not always root)
- Add authentication, audit log, restricted mode for remote administration use case
- FTP/SFTP, ZIP/TAR providers via abstracted `VfsProvider` layer
- Background file operations with progress/cancel

## Critical Context
- Run backend: `py -m uvicorn nc_server:app --host 127.0.0.1 --port 8000` or use `run.bat` / `manage_server.ps1 start`
- Frontend at `http://localhost:8000/` — the backend serves `index.html` and all JS files
- **Port mismatch issue**: If server starts on wrong port, frontend with `const API = "http://localhost:8000"` will fail — always use `--port 8000`
- Drive paths use uppercase letters: `/C/`, `/D/`, `/E/` etc.
- Babel standalone transpiles JSX+ES6 in the browser; `index.html` uses explicit `React.createElement` (`h()`) calls, not JSX syntax
- If page shows blank, check browser console for errors — most common causes: port mismatch, missing parens in script, cached stale scripts
- Total paren count in index.html is 1494/1494 balanced
- Server hangs (event loop blocking) fixed by wrapping all FS calls in `asyncio.to_thread()` — monitor with `run monitor`
- Search results search from `/C/` root; pattern supports glob (`*.txt`) and regex; max_results=200; clicking a result navigates to parent dir
- Quick view fetches `/api/info` + `/api/view` (for files <64KB) for the opposite panel's selected item
- Tree view loads root from drive letter of current panel; `[+]`/`[-]` separate click handlers (expand vs navigate); arrow keys update opposite panel cursor-follow
- Info view shows data about OPPOSITE panel's directory (per NC spec), not current panel's selected item

## Relevant Files
- `E:\Projects\WebNC\nc_server.py` — FastAPI backend (all endpoints including sysinfo, compare, tree, file owner; all blocking I/O in `asyncio.to_thread()`; comprehensive logging with `logger.info()`/`logger.warning()`)
- `E:\Projects\WebNC\index.html` — CDN-based frontend (all components: Panel with Brief/Full/Quick/Info/Tree modes, SearchDialog, SysInfoDialog, CompareDialog, HistoryDialog, menu system, sort/filter/view state, per-panel On/Off, select/deselect/invert, tree expand/collapse)
- `E:\Projects\WebNC\norton-commander.jsx` — Vite-based React component (not used without Node)
- `E:\Projects\WebNC\manage_server.ps1` — PowerShell script for start/stop/restart/status/monitor; health-check loop with auto-restart
- `E:\Projects\WebNC\run.bat` — cmd wrapper: `run` = start, `run stop`, `run status`, `run monitor`
- `E:\Projects\WebNC\react.production.min.js` — React 18 UMD (downloaded from cdnjs)
- `E:\Projects\WebNC\react-dom.production.min.js` — ReactDOM 18 UMD (downloaded from cdnjs)
- `E:\Projects\WebNC\babel.min.js` — Babel standalone 7.23.4 (downloaded from cdnjs)
- `E:\Projects\WebNC\requirements.txt` — Python deps (fastapi, uvicorn, aiofiles, python-multipart)
- `E:\Projects\WebNC\README.md` — Project documentation with usage, features, API reference, roadmap

---

## Internal Milestone 006
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

---

## Internal Milestone 007
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

---

## Internal Milestone 008
Build a Norton Commander-like web file manager with FastAPI backend and React frontend, running on Windows without Node.js, positioned as a local-first keyboard-driven admin utility with remote-administration potential. Synchronize Directories dialog redesigned to match Total Commander workflow.

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

---

## Internal Milestone 009
Build a Norton Commander-like web file manager with FastAPI backend and React frontend, running on Windows without Node.js, positioned as a local-first keyboard-driven admin utility with remote-administration potential.

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

---

## Internal Milestone  010
Build a Norton Commander-like web file manager with FastAPI backend and React frontend, running on Windows without Node.js.

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

--------

## Internal Milestone 011
- Fix 8 frontend endpoints that expect data but receive `{operation_id, status: "QUEUED"}`; add per-operation retry/timeout config with frontend UI.

## Constraints & Preferences
- All FS I/O runs in thread pool (event loop blocking already solved)
- Smart retry: `PermissionError`, `FileNotFoundError` → no retry; transient `OSError` → retry
- Config file must be read-write (not hardcoded), saved as `config.json` in project root
- Timeout/retry settings in a separate TimeoutsDialog (not inlined in ConfigDialog)
- SyncDialog shows dual-pane left/right layout (TC-style)

## Progress
### Done
- Frontend: `pollOperation(opId, timeout, interval)` in api.js — polls `GET /api/operation/{id}` every `interval` ms, respects per-operation timeout
- Frontend: `apiGetConfig()`, `apiSetConfig()` in api.js
- Frontend: 5 typed functions (`apiCopy`, `apiMove`, `apiBatchDelete`, `apiSearch`, `apiArchiveList`) and 3 handlers (`handleCompare`, `handleSyncCompare`, `syncExecute`) all pass `poll?.timeout` / `poll?.interval` from backend response
- Frontend: `TimeoutsDialog.js` — standalone dialog with table (Operation | Retries | Timeout s | Interval ms) for all 8 operations, Save → `PUT /api/config`
- Frontend: `SyncDialog` redesigned to dual-pane left/right layout (900px wide, columns: Name flex:1 / Size 65px / Date 125px / Status 24px)
- Frontend: Sync `different` action cycle fixed — `null` moved to end so first click selects `copy_left_to_right` (was dead-click)
- Frontend: Sync rows with an action assigned get `background: #002266` highlight
- Frontend: ConfigDialog reverted to original (only UI prefs like view/sort/font, no operation settings)
- Frontend: Menu items — Commands/Options both have "Configuration..." and "Timeouts..." entries
- Frontend: Esc handler and dialog exclusion list include `timeoutsDlg`
- Backend: `webnc/config_manager.py` — `ConfigManager` class with JSON read/write, thread-safe lock, atomic save via `.tmp` + replace, defaults for copy/move/batch_delete/search/compare/sync_plan/sync_execute/archive_list
- Backend: `webnc/api/config_api.py` — `GET /api/config`, `PUT /api/config`
- Backend: `main.py` — `config_manager = ConfigManager()`, `config_router` mounted
- Backend: `base.py` — `__post_init__()` reads `max_retries` from config; `get_poll_config()` returns `{timeout, interval}`; `op_config_key` ClassVar; `run()` has `max_retries==0` fast-path, cancel check, no-FAILED-result fallthrough bug fixed; `should_retry()` with `_is_non_retriable()` for `PermissionError`, `FileNotFoundError`, `FileExistsError`, `NotADirectoryError`, `IsADirectoryError`, `BlockingIOError`, `InterruptedError`
- Backend: All 8 queue operations have `op_config_key` set
- Backend: All 8 API handlers now include `"poll": op.get_poll_config()` in response
- Backend: Smart `should_retry()` overrides — `CopyOperation`, `MoveOperation`, `BatchDeleteOperation`, `CompareOperation`, `SyncExecuteOperation` (via `_is_non_retriable`); `ArchiveListOperation` (+ `BadZipFile`, `ReadError`, `PasswordRequiredException`, `ExtractError`)
- `config.json` created in project root with defaults

### In Progress
- (none)

### Blocked
- (none)

## Key Decisions
- Polling in frontend (not backend synchronous wait) — preserves non-blocking thread pool execution
- Per-operation poll timeout/interval sent from backend via `poll` field in `add_operation()` response — frontend passes to `pollOperation()`
- Timeouts in separate dialog from UI config — keeps ConfigDialog focused on user preferences
- Operation retry config in backend JSON file (not hardcoded) — allows live editing via API
- `_is_non_retriable` as static method in base class, overridden per operation class — avoids code duplication
- Sync action cycle changed: `different: ["copy_left_to_right", "copy_right_to_left", null]` — first click now selects an action instead of no-op

## Next Steps
- (none — everything requested is implemented)

## Critical Context
- `__post_init__()` in AbstractOperation lazy-imports `config_manager` from `webnc.main` — safe: no circular import at runtime
- Backend `max_retries` for an operation is set ONCE at construction time, not re-read on retry — intentional
- SyncExecuteOperation expects `actions[i].name` to be the relative file path (not just filename)
- `config.json` is auto-created on first `ConfigManager()` instantiation via `_merge_defaults()` + `save()`

## Relevant Files
- `frontend/lib/api.js`: `pollOperation`, `apiGetConfig`, `apiSetConfig`, 5 typed API functions
- `frontend/app.js`: imports `pollOperation`/`TimeoutsDialog`, 3 polled handlers, menu items, `timeoutsDlg` state/render
- `frontend/dialogs/TimeoutsDialog.js`: operation retry/timeout config table
- `frontend/dialogs/SyncDialog.js`: dual-pane layout, action cycle fix, row highlight
- `frontend/dialogs/ConfigDialog.js`: reverted to original (UI prefs only)
- `frontend/dialogs/index.js`: exports `TimeoutsDialog`
- `webnc/config_manager.py`: `ConfigManager` class, `OPERATION_DEFAULTS`, thread-safe read/write
- `webnc/api/config_api.py`: `GET /api/config`, `PUT /api/config`
- `webnc/api/files.py`, `compare.py`, `sync.py`, `archive.py`: all 8 handlers include `"poll"` in response
- `webnc/operations/base.py`: `__post_init__`, `get_poll_config`, `op_config_key`, refactored `run()`, `should_retry`/`_is_non_retriable`
- `webnc/operations/files.py`, `compare.py`, `syncop.py`, `archive.py`: `op_config_key` and `should_retry()` overrides
- `webnc/main.py`: `config_manager = ConfigManager()`, `config_router`
- `config.json` (project root): auto-generated per-operation defaults

---

## Internal Milestone 012
- Implement per-operation retry/timeout config with frontend UI, CSS refactoring, Find File panel mode, and in-browser file editor.

## Constraints & Preferences
- All FS I/O runs in thread pool (event loop blocking already solved)
- Smart retry: `PermissionError`, `FileNotFoundError` → no retry; transient `OSError` → retry
- Config file must be read-write, saved as `config.json` in project root
- Styles extracted to `frontend/nc.css` with semantic classes (`.filename`, `.directory`, `.filesize`, `.datetime`, `.selected`, `.overlay`, `.dialog`, etc.)
- Selected/highlighted rows use yellow (`#554400`) background consistently
- Find File panel is a panel `viewMode: "search"` (not a dialog), results populate opposite panel
- F4 opens in-browser editor for files, Info for directories
- Editor uses `<textarea>` + Ctrl+S + Save/Cancel buttons

## Progress
### Done
- CSS refactoring: all inline overlay/dialog styles replaced with `.overlay`/`.dialog`/`.title-bar`/`.scroll-y`/`.footer-bar` classes
- Semantic column classes: `.filename`, `.directory`, `.filesize`, `.datetime`, `.status-icon`
- Utility classes: `.flex`, `.flex-1`, `.flex-col`, `.flex-shrink0`, `.text-yellow`, `.text-cyan`, `.text-red`, `.text-center`, `.text-right`, `.gap-*`, `.bor-bot-*`, `.fs-*`, `.mono`
- Yellow selection: `background: #554400` for SyncDialog rows with action (`.file-row.selected`)
- Panel styles: `.panel-border-active`, `.panel-header-active`, `.panel-row`, `.panel-row-current`
- `frontend/nc.css` — comprehensive NC theme stylesheet
- `index.html` — inline `<style>` removed, replaced with `<link rel="stylesheet" href="frontend/nc.css">`
- `frontend/styles.js` — no longer imported by any file, kept as legacy reference
- Find File panel (`viewMode: "search"`): new branch in Panel.js with Name/Path/Size/Date columns
- `app.js` — `handleSearchResults()`, `leftSearchQuery`/`rightSearchQuery` state, F9 search populates opposite panel
- `SearchDialog` — `onResults` callback sends results to panel on search completion
- Left/Right/Files menus — "Find file panel" entries active with `[X]` checkbox when panel in search mode
- Navigating from search mode resets viewMode to `"full"` and refreshes directory listing
- Editor: `POST /api/edit` endpoint (`webnc/api/files.py`), `WriteOperation` (`webnc/operations/files.py`), `EditRequest` model
- `frontend/dialogs/EditorDialog.js` — textarea + Ctrl+S + dirty flag + Save/Cancel
- F4 handler: files → fetch content via `apiView` → open EditorDialog; dirs → show Info (unchanged)
- Fn bar: F4 label changed from "Info" to "Edit"
- `EditorDialog` exported from `dialogs/index.js`, wired in `app.js` with `handleEditorSave`
- Unused imports cleaned up (`MONO`, `btnStyle`) across all dialog files
- Backend: `ConfigManager` class with JSON read/write, thread-safe lock, atomic save
- Backend: `GET /api/config`, `PUT /api/config` endpoints
- Backend: 8 queue operations with `op_config_key`, `should_retry()` overrides, `get_poll_config()` in all API handlers
- Frontend: `pollOperation()` in api.js, `TimeoutsDialog`, 5 polled API functions
- SyncDialog: dual-pane layout, action cycle fix (`different` cycle ends with `null`), row highlight
- `config.json` auto-created in project root
- README.md fully updated with project structure, API endpoints, features, roadmap

### In Progress
- (none)

### Blocked
- (none)

## Key Decisions
- Polling in frontend (not backend synchronous wait) — preserves non-blocking thread pool
- Per-operation poll timeout/interval sent from backend via `poll` field — frontend passes to `pollOperation()`
- Timeouts in separate dialog from UI config — keeps ConfigDialog focused on user preferences
- Operation retry config in JSON file (not hardcoded) — allows live editing via API
- Search results go to opposite panel as `viewMode: "search"` — reuses Panel infrastructure, no separate dialog
- Navigating from search mode switches panel back to `"full"` and re-fetches directory via `fetchDir`
- F4: Editor for files, Info for dirs — matches TC convention while keeping Info accessible
- Editor: `<textarea>` (not CodeMirror) — pragmatic first step, can be upgraded later
- CSS extracted to static file with semantic classes — reduces inline style duplication and enables consistent theme

## Next Steps
- Fullscreen mode (EGA Lines) — `requestFullscreen()` toggle in menu
- Keyboard shortcut config — JSON mapping in `config.json`, frontend reads instead of hardcoded switch
- Command input — `/api/exec` endpoint + cmdline execution from existing `>` input bar
- Symlink support — `/api/link` → `os.symlink()` in thread pool

## Critical Context
- `__post_init__()` in AbstractOperation lazy-imports `config_manager` from `webnc.main` — safe: no circular import at runtime
- Backend `max_retries` for an operation is set ONCE at construction time, not re-read on retry — intentional
- `config.json` is auto-created on first `ConfigManager()` instantiation via `_merge_defaults()` + `save()`
- CSS classes defined in `nc.css` are referenced via `className` in `React.createElement()` — all 13 dialog files updated
- Search results replace panel `items` in `app.js`; `handleViewMode` re-fetches directory when leaving search mode
- Editor `POST /api/edit` is a synchronous operation (not queued) — runs via `queue.run_sync()`
- `MONO` font family is now set by CSS (`.mono` class or `nc-btn`/`nc-input`/`dialog` rules) — no longer imported per-file

## Relevant Files
- `frontend/nc.css` — NC theme: layout, colors, typography, `.overlay`, `.dialog`, `.file-row`, `.filename`, `.filesize`, `.datetime`, `.status-icon`, `.nc-btn`, `.nc-input`, `.nc-num`, `.nc-table`, panel classes, scrollbar
- `index.html` — `<link rel="stylesheet" href="frontend/nc.css">`
- `frontend/components/Panel.js` — `viewMode === "search"` branch, `searchQuery` prop, search header/footer
- `frontend/app.js` — `handleSearchResults`, `leftSearchQuery`/`rightSearchQuery`, `handleEditorSave`, `editorDlg` state, F4 → editor/files info/dirs, Fn bar "Edit", menu items, dialog exclusion list
- `frontend/dialogs/SearchDialog.js` — `onResults` prop, fires on search completion
- `frontend/dialogs/EditorDialog.js` — textarea editor with Ctrl+S, dirty flag, Save/Cancel
- `frontend/dialogs/CompareDialog.js` — refactored to CSS classes (`.overlay`, `.dialog`, `.title-bar`, `.filename`, `.filesize`, etc.)
- `frontend/dialogs/SimpleDialogs.js` — refactored (FileViewer, Confirm, Input)
- `frontend/dialogs/DriveDialog.js`, `InfoDialog.js`, `HistoryDialog.js`, `HelpDialog.js`, `LoginDialog.js`, `ArchiveDialog.js`, `SysInfoDialog.js`, `ConfigDialog.js`, `TimeoutsDialog.js` — all refactored to CSS classes
- `frontend/dialogs/SyncDialog.js` — CSS classes for rows, `.file-row.selected` yellow background, dual-pane layout
- `frontend/dialogs/index.js` — exports `EditorDialog`
- `frontend/lib/api.js` — `api()` function, `pollOperation`, typed endpoints
- `webnc/api/files.py` — `POST /api/edit` endpoint with `EditRequest`
- `webnc/operations/files.py` — `WriteOperation` (write_text via thread pool)
- `webnc/models/files.py` — `EditRequest { path, content }`
- `webnc/config_manager.py` — `ConfigManager`, thread-safe JSON read/write
- `webnc/api/config_api.py` — `GET /api/config`, `PUT /api/config`
- `webnc/main.py` — mounts all routers, creates `ConfigManager`
- `config.json` — auto-generated per-operation defaults

---

## Internal Milestone 013
- Implement fullscreen mode, keyboard config, command input, project restructuring, and cleanup of dead files.

## Constraints & Preferences
- Command output should appear in the terminal area below panels (not status bar)
- Terminal area should expand when panels are hidden (Ctrl+O)
- Keyboard bindings stored in `config.json` → `keybindings` section
- Command exec security: allow/deny lists in `config.json`
- Russian text from cmd.exe (cp866) must be decoded to Unicode
- Exec decoding fallback: utf-8 → cp866 → cp1251 → cp437 → latin-1
- `max_edit_size` in config.json (default 1MB) — refuse to open larger files in editor
- All "Norton Commander" references replaced with "WebNC"
- Project restructured: client/, bin/, logs/, config/
- Dead files must be removed

## Progress
### Done
- Fullscreen toggle via `document.documentElement.requestFullscreen()` — F11, Commands → EGA Lines, Options → Fullscreen, `fullscreenchange` listener
- Keyboard config: `keybindings` in `config.json`, `apiGetConfig` fetch on mount, ACTION dispatch map replaces hardcoded `switch(e.key)`, tree mode keys stay hardcoded
- Command input: `POST /api/exec` (`webnc/api/exec.py`) with `asyncio.create_subprocess_shell`, 30s timeout, command allow/deny checks
- `cmdHistory` state + `handleCmdEnter` pushes to history
- Terminal output area below panels (scrollable, `termRef`, auto-scroll on new output)
- When both panels hidden → terminal fills `flex: 1 1 0%`, panels section becomes `null`
- `_decode()` function for cp866/cp1251/utf-8 fallback decoding
- `max_edit_size` config (default 1048576) in `config.json` → `editor`
- `GET /api/view?for_edit=true` checks file size → 413 if too large, `apiView(p, forEdit=true)` in frontend
- "Norton Commander" replaced with "WebNC" in all source files (README, index.html, app.js, nc.css, HelpDialog, main.py, run.bat, nc_server.py)
- `nc_server.py` → `webnc_server.py` (file rename + all refs in main.py, README, manage_server.ps1)
- `nc_server.crt`/`.key` → `webnc_server.crt`/`.key` in `webnc/security/tls.py`
- `nc_server.log` → `webnc_server.log` in `webnc/logging_config.py` + `getLogger("webnc_server")`
- Dead files removed: `babel.min.js`, `norton-commander.jsx`, `src/`, `package.json`, `vite.config.js`, `cookies`, `nc_server.token`, `frontend/lib/styles.js`
- Project restructured: `index.html` → `client/`, HTML paths → `css/nc.css`/`js/app.js`; `config.json` → `config/`; `run.bat`/`manage_server.ps1` → `bin/`; logs → `logs/`
- `static.py` rewritten — serves `/` (client/index.html), `/css/{rest}`, `/js/{rest}`
- `config_manager.py` → `CONFIG_FILE = PROJECT_ROOT / "config" / "config.json"`
- `README.md` roadmap updated with actual status (`[x]` for implemented features)

### In Progress
- (none)

### Blocked
- (none)

## Key Decisions
- Command output goes to scrollable terminal area (not status bar) — matches NC behavior
- Terminal fills full space when both panels hidden — replaces "Panels Off" placeholder
- Keyboard dispatch uses ACTION lookup map (not switch) — enables config-driven remapping
- Exec encoding uses fallback chain (utf-8 → cp866 → cp1251 → cp437 → latin-1) — handles Russian Windows console
- `max_edit_size` checked on `GET /api/view?for_edit=true` (not on save) — prevents loading huge files into editor
- Static serving uses explicit `/css/` and `/js/` routes (not catch-all) — avoids conflicts with API routes
- Project root directory contains only `webnc/`, `webnc_server.py`, `config/`, `client/`, `bin/`, `logs/`, `README.md`, `requirements.txt`, `History.md`, `LICENSE`, `.gitignore`

## Next Steps
- Symbolic links (`/api/link`)
- Extension-to-action associations
- Command history up/down arrow navigation
- Configurable exec timeout in `config.json`
- NDC Tree dialog

## Critical Context
- `_decode()` in `webnc/api/exec.py` tries utf-8 first, then cp866 (OEM), then cp1251 (ANSI), then cp437, then latin-1 — last resort falls back to utf-8 `errors="replace"`
- Keyboard handler deps no longer include `setSelected`/`setIdx` (not defined at component level) — fixed to `setLeftSelected`/`setRightSelected`/`setLeftIdx`/`setRightIdx`
- `bothVisible` is `leftPanelVisible || rightPanelVisible` (OR) — panels section hidden only when BOTH panels off
- Backend `safe_path()` converts `/C/...` virtual paths to `C:\...` real paths — used for exec `cwd`
- `config_manager.py` now reads from `config/config.json` — must exist before first `ConfigManager()` instantiation
- `gen_self_signed_cert()` in `webnc/security/tls.py` generates `webnc_server.crt`/`.key` — reuses existing files if present
- RotatingFileHandler in `logging_config.py` writes to `logs/webnc_server.log` — dir is `webnc/` parent project root + `logs/`

## Relevant Files
- `webnc/api/exec.py` — `POST /api/exec`, `_decode()`, command allow/deny checks
- `webnc/api/files.py` — `_check_edit_size()`, `GET /api/view?for_edit=true`
- `webnc/api/static.py` — static file serving for client/css/, client/js/, client/index.html
- `webnc/security/tls.py` — `gen_self_signed_cert()` → `webnc_server.crt`/`.key`
- `webnc/logging_config.py` — logger name `webnc_server`, log file `logs/webnc_server.log`
- `webnc/config_manager.py` — `CONFIG_FILE = config/config.json`, `EDITOR_DEFAULTS`, `EXEC_DEFAULTS`, `get_max_edit_size()`, `get_exec_allowed()`, `get_exec_denied()`
- `frontend/app.js` — `cmdHistory`, `handleCmdEnter`, `termRef`, `toggleFullscreen`, `keyBindings` state, keyboard ACTION map, `apiView(path, true)` for edit
- `frontend/lib/api.js` — `apiExec()`, `apiView(p, forEdit)`
- `client/index.html` — paths: `css/nc.css`, `js/react.*.min.js`, `./js/app.js`
- `config/config.json` — `keybindings`, `exec`, `editor` sections
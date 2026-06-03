# Summary 00003

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
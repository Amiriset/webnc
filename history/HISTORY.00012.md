# Summary 00012

## Goal

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

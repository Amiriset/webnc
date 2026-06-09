## Goal
Complete Phase 1 features (NDC Tree Dialog), fix Windows connection-reset crash, add `.`/`..` navigation in error states, and refactor into layered architecture (API → Service → VFS → FS).

## Constraints & Preferences
- Windows `ProactorEventLoop` required for `asyncio.create_subprocess_shell`
- `ConnectionResetError` from client disconnects silently swallowed — `asyncio` logger set to `CRITICAL`
- `.` entry navigates to drive root, shows `[. ]` / `ROOT`; `..` shows `↑..` / `UP--DIR`
- Service layer (`FileService` ABC) allows future Linux/Mac implementations

## Progress
### Done
- **NDC Tree Dialog** (Phase 1.8): `client/js/dialogs/TreeDialog.js` — full-screen directory tree, lazy-loads via `apiTree`, arrow-key navigation, Enter expand→select, double-click navigates both panels. Menu `Commands → NDC tree` (no longer disabled).
- **TreeDialog fixes**: `flattenTree` no longer copies nodes (was mutating copies, subdirs never appeared). Arrow key handler properly isolates from panel handler (`if (treeDlg) return`).
- **ConnectionResetError suppression**: Replaced fragile `new_event_loop` exception-handler monkey-patch with `logging.getLogger("asyncio").setLevel(logging.CRITICAL)` — eliminates traceback noise from `_ProactorBasePipeTransport._call_connection_lost` (Python 3.9 bug: `shutdown()` on reset socket raises uncaught `ConnectionResetError` in `finally` block).
- **`.` and `..` entries**: Added `.` (current dir → drive root) and `..` (parent) to all directory listings. Both marked `_isParent: true`. `.` renders as `[.]` / `ROOT`, `..` as `↑..` / `UP--DIR`. Hidden at drive root (no `parent`).
- **Permission error resilience**: `ListOperation.execute()` wraps `iterdir()` in try/except `(PermissionError, OSError)` — returns empty listing with `parent` so frontend shows `..` to navigate up.
- **Architecture refactoring (API → Service)**:
  - `webnc/services/file_service.py` — `FileService` ABC with 14 abstract methods
  - `webnc/services/windows_service.py` — `WindowsFileService` implementation, all business logic moved from operations (list, view, write, copy, move, rename, mkdir, link, delete, batch-delete, search, file-info, tree, download-path, upload)
  - `webnc/operations/files.py` — trimmed to 4 queued operations (`Copy`, `Move`, `BatchDelete`, `Search`) that delegate to `file_service` singleton
  - `webnc/api/files.py` — sync endpoints call service directly via `Depends(get_file_service)`; async endpoints keep queued operations
  - `webnc/main.py` — global `file_service = WindowsFileService()` alongside `operation_queue` and `config_manager`

### In Progress
- (none)

### Blocked
- (none)

## Key Decisions
- `asyncio` logger set to `CRITICAL` instead of event-loop exception-handler patch — simpler, survives uvicorn's log_config reset, catches all asyncio callback noise
- `.` points to drive root (`/C/`, `/D/`) rather than current directory — gives quick jump-to-root, a frequently requested NC feature
- `_isParent` flag on both `.` and `..` reused existing frontend filtering (select, copy, delete, etc. skip them)
- Service interface returns plain dicts with `success`/`error` fields — no Pydantic models in the interface, stays lightweight for cross-OS implementations
- Service instantiated as global singleton in `main.py` (same pattern as `operation_queue` and `config_manager`) — injected into API endpoints via `Depends(get_file_service)`
- Queued operations delegate to service at runtime (`from webnc.main import file_service`) — avoids circular imports, keeps operation constructors unchanged

## Next Steps
- Phase 2: Productize Core — Linux VFS, Docker, allowed roots, read-only mode
- Phase 3: Plugin system, WebSocket terminal, file versioning

## Critical Context
- `_ProactorBasePipeTransport._call_connection_lost` in Python 3.9 has unguarded `self._sock.shutdown()` in `finally` block — `ConnectionResetError` propagates to event loop callback handler. Setting `asyncio` logger to `CRITICAL` suppresses the traceback.
- TreeDialog's `flattenTree` now pushes node **references** (not copies) to flat array, stores depth as `_depth` on the node. `toggleNode` mutates the original node in `roots`.
- `.` and `..` are added by the frontend (`fetchDir` in `app.js`), not by the backend. Backend only returns `parent` field and `items` list.
- Drive root detection: `data.parent is None` → no `.`/`..` added.
- `FileService.file_info()` returns `{"success": true, "data": {...}}` — the API endpoint unwraps to `result["data"]` for backward compatibility with frontend `InfoDialog`.
- `WindowsFileService` contains all platform-specific code (`ctypes` security lookups, `mklink` fallback, `GetFileAttributesW` perms). Future `LinuxFileService` would use `pwd`/`grp`/`os.stat`.

## Relevant Files
- `client/js/dialogs/TreeDialog.js` — new NDC Tree Dialog component
- `client/js/dialogs/index.js:15` — TreeDialog export
- `client/js/app.js:93,128-132,397,531,667` — treeDlg state, `.`/`..` entries, treeDlg bail-out in key handler, menu item, render
- `client/js/components/Panel.js:6-9,166` — `symName()` handles `.` → `[.]` and `..` → `↑..`; size column shows `ROOT` / `UP--DIR`
- `webnc/main.py:19-21,49` — `ProactorEventLoopPolicy` (simplified), `file_service = WindowsFileService()`
- `webnc/services/__init__.py` — package export
- `webnc/services/file_service.py` — `FileService` ABC (14 abstract methods)
- `webnc/services/windows_service.py` — `WindowsFileService` (all business logic, platform-specific helpers)
- `webnc/api/files.py` — refactored to use `FileService` via `Depends(get_file_service)`
- `webnc/operations/files.py` — trimmed to 4 queued operation classes calling `file_service`
- `webnc/vfs/paths.py` — unchanged, used by service layer

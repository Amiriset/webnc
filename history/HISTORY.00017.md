## Goal
Complete Phase 1 features (NDC Tree Dialog), fix Windows connection-reset crash, add `.`/`..` navigation for error states, refactor into layered architecture (API → Service → VFS → FS), and migrate to Python 3.11.

## Constraints & Preferences
- Windows `ProactorEventLoop` required for `asyncio.create_subprocess_shell`
- `ConnectionResetError` from client disconnects silently swallowed — `asyncio` logger set to `CRITICAL`
- `.` entry navigates to drive root, shows `[.]` / `ROOT`; `..` shows `↑..` / `UP--DIR`
- Service layer (`FileService` ABC) allows future Linux/Mac implementations
- Python 3.11.9 fixed `_call_connection_lost` (`fileno() != -1` check), eliminating the main source of ConnectionResetError tracebacks

## Progress
### Done
- **Python 3.11 migration**: Dependencies reinstalled (`fastapi`, `uvicorn`, `pydantic`, etc.) under `C:\Users\frolo\AppData\Local\Programs\Python\Python311`. `py -3` now runs 3.11.9. `run.bat`/`manage_server.ps1` uses `py` launcher — no changes needed.
- **NDC Tree Dialog** (Phase 1.8): `client/js/dialogs/TreeDialog.js` — full-screen directory tree, lazy-loads via `apiTree`, arrow-key navigation, Enter expand→select, double-click navigates both panels. Menu `Commands → NDC tree` (no longer disabled).
- **TreeDialog fixes**: `flattenTree` no longer copies nodes (was mutating copies, subdirs never appeared). Arrow key handler properly isolates from panel handler (`if (treeDlg) return`).
- **ConnectionResetError suppression**: `logging.getLogger("asyncio").setLevel(logging.CRITICAL)` — eliminates all asyncio callback tracebacks. Python 3.11 further reduces occurrence via `fileno() != -1` guard in `_call_connection_lost`.
- **`.` and `..` entries**: Added `.` (current dir → drive root) and `..` (parent) to all directory listings. Both `_isParent: true`. `.` renders as `[.]` / `ROOT`, `..` as `↑..` / `UP--DIR`. Hidden at drive root (no `parent`).
- **Permission error resilience**: `ListOperation` wraps `iterdir()` in try/except `(PermissionError, OSError)` — returns empty listing with `parent`.
- **Architecture refactoring**:
  - `webnc/services/file_service.py` — `FileService` ABC with 14 abstract methods
  - `webnc/services/windows_service.py` — `WindowsFileService` (all business logic)
  - `webnc/operations/files.py` — trimmed to 4 queued ops delegating to service
  - `webnc/api/files.py` — sync endpoints use `Depends(get_file_service)`
  - `webnc/main.py` — global `file_service = WindowsFileService()`

### In Progress
- (none)

### Blocked
- (none)

## Key Decisions
- `asyncio` logger set to `CRITICAL` instead of event-loop exception-handler patch — simpler, survives uvicorn log_config reset, catches all asyncio callback noise
- `.` points to drive root (`/C/`, `/D/`) rather than current directory — quick jump-to-root
- `_isParent` flag on both `.` and `..` reused existing frontend filtering
- Service interface returns plain dicts with `success`/`error` — no Pydantic in the interface, lightweight for cross-OS
- Service instantiated as global singleton in `main.py` (same as `operation_queue`, `config_manager`)

## Next Steps
- Phase 2: Productize Core — Linux VFS, Docker, allowed roots, read-only mode
- Phase 3: Plugin system, WebSocket terminal, file versioning

## Critical Context
- Python 3.11.9 is now the runtime. `py -3` resolves to 3.11.
- `_ProactorBasePipeTransport._call_connection_lost` in Python 3.9 had unguarded `shutdown()` — 3.11 adds `fileno() != -1` guard, fixing the root cause. `asyncio CRITICAL` logger is the safety net.
- TreeDialog `flattenTree` pushes node references, stores depth as `_depth` on node.
- `.` and `..` added by frontend (`fetchDir`), not backend.
- `FileService.file_info()` returns `{"success": true, "data": {...}}` — API unwraps to `result["data"]`.
- `WindowsFileService` contains all platform-specific code (`ctypes`, `mklink`, `GetFileAttributesW`).

## Relevant Files
- `client/js/dialogs/TreeDialog.js` — NDC Tree Dialog component
- `client/js/dialogs/index.js:15` — TreeDialog export
- `client/js/app.js:93,128-132,397,531,667` — treeDlg state, `.`/`..` entries, key bail-out, menu, render
- `client/js/components/Panel.js:6-9,166` — `symName()` for `.`/`..`; `ROOT` / `UP--DIR`
- `webnc/main.py:19-21,49` — `ProactorEventLoopPolicy`, `file_service = WindowsFileService()`
- `webnc/services/__init__.py` — package export
- `webnc/services/file_service.py` — `FileService` ABC
- `webnc/services/windows_service.py` — `WindowsFileService`
- `webnc/api/files.py` — uses `FileService` via `Depends(get_file_service)`
- `webnc/operations/files.py` — 4 queued ops delegating to service
- `webnc/vfs/paths.py` — unchanged
- `bin/manage_server.ps1:88` — `py webnc_server.py` (picks up 3.11)

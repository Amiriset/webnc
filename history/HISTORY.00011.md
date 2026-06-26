# Summary 00011

## Goal

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
## Goal
Complete terminal workflow (command history, exec subprocess fix) and continue implementing remaining WebNC features.

## Constraints & Preferences
- Windows `ProactorEventLoop` required for `asyncio.create_subprocess_shell` — `SelectorEventLoop` raises `NotImplementedError`
- `ConnectionResetError` from client disconnects must NOT crash the server — swallowed via loop exception handler
- Command history ArrowUp/Down only works when `activeTarget === "terminal"` (panel mode routes arrows to file list)
- History persisted in `localStorage("cmdHistory")` — max 100 entries, survives page reload

## Progress
### Done
- **Subprocess fix** (`webnc/main.py`): Replaced `uvicorn.loops.asyncio.asyncio_loop_factory = lambda ...: SelectorEventLoop` with `WindowsProactorEventLoopPolicy()` + monkey-patched `policy.new_event_loop` that installs a `ConnectionResetError`-swallowing exception handler on every new loop. Subprocess (echo, dir, etc.) now works without `NotImplementedError`.
- **Command history** (`client/js/app.js`): Added `cmdHistoryTexts` state (array of strings, localStorage-backed), `cmdHistoryIdx` state (-1 = new command, 0 = most recent, ...). ArrowUp increments `cmdHistoryIdx` and populates `cmdLine` from history; ArrowDown decrements and clears `cmdLine` at -1. On Enter, command appended to history, saved to localStorage, `cmdHistoryIdx` reset to -1.
- Previous tasks: project structure verification, README/CHANGELOG/SECURITY docs, TLS 1.3, token-to-stderr, terminal overlay layout, `activeTarget` keyboard routing, unified logging, real Windows owner/perms via ctypes, `FileInfo.owner` as `Optional[str]`, `version.txt` reading, login password field, etc.

### In Progress
- **Configurable exec timeout** — adding `exec.timeout_sec` to `config/config.json` and wiring into `exec.py` and `ConfigManager`.

### Blocked
- (none)

## Key Decisions
- `ProactorEventLoop` + exception handler chosen over `SelectorEventLoop` + no subprocess — subprocess functionality is more important than cosmetic crash avoidance
- Loop exception handler logs `ConnectionResetError` at DEBUG level, passes all other exceptions to `default_exception_handler` — prevents crash without hiding real errors
- Command history stored as array of strings (not {cmd, stdout} objects) — smaller localStorage footprint, avoids storing terminal output that can contain sensitive data
- `cmdHistoryIdx = -1` baseline means "blank new command" — ArrowDown from index 0 clears the input to allow fresh typing

## Next Steps
- Symbolic links (`/api/link`)
- Extension-to-action associations
- NDC Tree dialog
- (Command history and exec subprocess — done)

## Critical Context
- Until this fix, **every** `POST /api/exec` returned HTTP 500 with `NotImplementedError` on Windows — `SelectorEventLoop` cannot create subprocesses.
- The `asyncio_loop_factory` patch was the original fix for `ConnectionResetError` — now replaced by the loop exception handler approach which retains subprocess support.
- `config/config.json` currently has no `exec.timeout_sec` — the exec endpoint hardcodes `timeout=30` in `asyncio.wait_for`. The new field will be added under the `"exec"` section.
- `exec.py` uses `asyncio.wait_for(proc.wait(), timeout=30)` — the timeout value is the configurable piece.
- `ConfigManager.get_operation_config("exec", "timeout")` pattern already exists for copy/move/delete/search — exec config will follow the same pattern.
- After config change, the frontend must restart exec polling if the timeout is changed and a command is running.

## Relevant Files
- `webnc/main.py:17-34` — Windows event loop policy + `new_event_loop` monkey-patch with `ConnectionResetError` handler (replaced the old `asyncio_loop_factory` patch)
- `client/js/app.js:79-82` — `loadHistoryTexts()`, `cmdHistoryTexts`, `cmdHistoryIdx` states
- `client/js/app.js:202-218` — `handleCmdEnter()` — pushes command to `cmdHistoryTexts`, saves to localStorage, resets `cmdHistoryIdx`
- `client/js/app.js:599` — input `onKeyDown` — ArrowUp/Down handlers for history navigation
- `config/config.json:70-82` — `"exec"` section (currently `allowed_commands`, `denied_commands`, `editor`); `timeout_sec` to be added
- `webnc/api/exec.py:58` — `asyncio.wait_for(proc.wait(), timeout=30)` — the timeout to make configurable
- `webnc/config_manager.py` — existing `get_operation_config()` method to reuse for exec timeout
- `client/js/dialogs/TimeoutsDialog.js` — timeouts display; exec timeout field to be added
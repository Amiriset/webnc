# Summary 00015

## Goal
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
# Summary 00014

## Goal

- Refine UI/UX — terminal overlay layout, active-target keyboard routing, click-to-focus, secure token handling, unified log format, and release documentation.

## Constraints & Preferences
- Terminal must NOT push panels upward — panels are overlaid with `position: absolute`
- Only one target active at a time: panels OR terminal (or dialog)
- Keyboard goes exclusively to the active target
- Tab cycles: left panel → right panel → terminal → left panel
- Click on panels area → `activeTarget = "panels"`; click on terminal area or command input → `activeTarget = "terminal"`
- Backspace in input must not delete characters when panels are active (input calls `e.preventDefault()` for keys in `keyBindings`)
- Ctrl+O hides panels → auto-switch `activeTarget` to `"terminal"`; shows panels → switch to `"panels"`
- Token must never appear in log files — `print(..., file=sys.stderr)` only
- All logs (uvicorn + webnc_server) must use the same `%(asctime)s | %(levelname)-8s | %(message)s` format
- `log_config` must be passed explicitly to `uvicorn.run()` (default param is captured at class-definition time, not overridable)
- Rebranding section in README, CHANGELOG.md, SECURITY.md for v0.13.0
- `__doc/` and `server.pid` excluded via `.gitignore`; `config/config.json` stays tracked

## Progress
### Done
- Project structurally verified — all backend modules import cleanly, frontend files at correct paths, paren balance = 0
- `README.md` project structure section rewritten to reflect `client/`, `bin/`, `logs/`, `config/` layout
- `bin/manage_server.ps1` — `$WorkingDirectory` set to `$ProjectRoot` (parent of `bin/`); pid/log paths use project root
- `CHANGELOG.md` created for v0.13.0
- `SECURITY.md` created — Supported Versions, Reporting, Security Model, Threat Model, Current Limitations, Remote Exposure Warning
- TLS minimum raised to `ssl.TLSVersion.TLSv1_3` in `webnc/main.py:191`; console message updated
- `console_token.py` — all `logger.info()` replaced with `print(..., file=sys.stderr)`; duplicate line removed; unused `logger` import removed
- Terminal layout changed to template-style overlay — wrapper div `position: relative`, terminal `z-index: 1 height: 100%`, panels `position: absolute inset: 0 z-index: 10` (rendered only when `bothVisible`)
- `activeTarget` state (`"panels"` | `"terminal"`) added — global keyboard handler returns early when `activeTarget === "terminal"`
- Tab key (both tree and normal mode) cycles through left → right → terminal → left
- Ctrl+O handler sets `activeTarget` to `"terminal"` when hiding panels, `"panels"` when showing
- Command input `onKeyDown` calls `e.preventDefault()` for any `keyBindings[e.key]` when panels active (prevents char deletion from Backspace etc.)
- Command input `onClick` sets `activeTarget = "terminal"`; terminal div `onClick` sets `activeTarget = "terminal"` (no `bothVisible` guard)
- Visual indicators — terminal border turns `#00FFFF` when active; command line border same; "Cmd" in status bar turns green
- `uvicorn.run()` now receives explicit `log_config` dict matching our `webnc_server` logger format — uvicorn access, error, and default logs use `%(asctime)s | %(levelname)-8s | %(message)s`

### In Progress
- (none)

### Blocked
- (none)

## Key Decisions
- Tab cycling: left → right → terminal → left (instead of just left ↔ right) — enables one-hand focus switching without mouse
- `activeTarget` (string state) chosen over `document.activeElement` inspection — declarative, no DOM coupling
- Panels overlay via `position: absolute; z-index: 10` prevents terminal from pushing panels upward (matching `template.html`)
- Token printed to `stderr` (not logger) — bypasses RotatingFileHandler entirely
- Custom `log_config` passed to `uvicorn.run()` instead of mutating uvicorn module variable — avoids Python default-param capture gotcha
- `logs/` dir listed in `.gitignore` via generic `*.log` pattern; `config/config.json` tracked (needed for app to run)

## Next Steps
- Symbolic links (`/api/link`)
- Extension-to-action associations
- Command history up/down arrow navigation
- Configurable exec timeout in `config.json`
- NDC Tree dialog

## Critical Context
- `activeTarget` state declared after `keyBindings` in `app.js` — must be in scope of keyboard handler closure
- `keyBindings` includes `"Backspace": "go_up"` — input `onKeyDown` must check `keyBindings[e.key]` to prevent default char deletion when panels active
- Both `tree` Tab handler (hardcoded) and `switch_panel` ACTION map entry now cycle through terminal — must stay in sync
- `uvicorn.config.LOGGING_CONFIG` override is ineffective — default param captured at `import uvicorn` time; must pass `log_config=` dict to `uvicorn.run()`
- `_decode()` in `webnc/api/exec.py` tries utf-8 first, then cp866, cp1251, cp437, latin-1
- `gen_self_signed_cert()` in `webnc/security/tls.py` generates `webnc_server.crt`/`.key`
- `config/config.json` has `keybindings`, `exec`, `editor` sections — must exist before first `ConfigManager()` instantiation

## Relevant Files
- `webnc/security/console_token.py` — token printed to stderr only (no logger)
- `webnc/main.py` — TLS 1.3, custom `log_config` passed to `uvicorn.run()`, Ctrl+O handler sets `activeTarget`
- `webnc/logging_config.py` — `webnc_server` logger, `logs/webnc_server.log`
- `client/js/app.js` — `activeTarget` state, template-style overlay layout, Tab cycling, input `onKeyDown` key-binding guard
- `client/index.html` — paths: `css/nc.css`, `js/react.*.min.js`, `./js/app.js`
- `config/config.json` — `keybindings`, `exec`, `editor` sections
- `CHANGELOG.md` — v0.13.0
- `SECURITY.md` — Security Policy, Threat Model, Remote Exposure Warning
- `README.md` — updated project structure, rebranding section
- `.gitignore` — added `__doc/`, `server.pid`
- `bin/manage_server.ps1` — `$ProjectRoot` working directory
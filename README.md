# WebNC — File Manager

**Local-first, keyboard-driven, two-panel file manager for Windows.**
Inspired by Norton Commander / Midnight Commander. Zero-build web utility: FastAPI backend, single HTML frontend, locally served React runtime, no Node.js dependency. Designed as a remote-first IR/admin console with three-layer security.

> ⚠️ **Security model:** This tool has full filesystem access with no sandbox. All three protection levels (TLS, session auth, provider interface) are enabled by default for localhost. Do not expose to untrusted networks without additional controls.

## Quick Start

```powershell
pip install -r requirements.txt
pip install cryptography   # for RSA-4096 certificate generation

py webnc_server.py         # HTTPS on https://localhost:8000
```

Open browser → accept self-signed cert → paste session token from console output.

### Management scripts

```powershell
.\run.bat              # start with HTTPS (default)
.\run.bat --insecure    # start with HTTP (debug only)
.\run.bat stop          # stop
.\run.bat restart       # restart
.\run.bat status        # check health
.\run.bat monitor       # live health-check loop with auto-restart
```

## Security

Three-layer security model:

| Layer | What | Details |
|-------|------|---------|
| **Transport** | TLS 1.3 | RSA-4096, auto-generated self-signed cert, CRIME/BREACH protection |
| **Session** | Zero-knowledge auth | SHA-256(nonce+timestamp+secret), no passwords stored/transmitted |
| **Provider** | Extensible auth | `AuthProvider` interface for AD/Kerberos/JWT integration |

Token is ephemeral (RAM only, 5-min window), printed once at startup.

> For older systems without TLS 1.3 support, you can downgrade to TLS 1.2 at your own risk by changing `ctx.minimum_version` in `webnc/main.py`.

**Detailed:** [ARCHITECTURE.md](docs/ARCHITECTURE.md) · [COMPLIANCE.md](docs/COMPLIANCE.md)

## Features

| Feature | Key | Description |
|---------|-----|-------------|
| Two-panel layout | Tab | Dual-pane NC-style, per-panel sort/filter/view modes |
| Copy | F5 | To opposite panel (async with retry) |
| Move / Rename | F6 | To opposite panel or rename in place |
| Create directory | F7 | |
| Delete | F8 | With confirmation dialog |
| View | F3 | Read-only text viewer (<64KB) |
| Info / Edit | F4 | Directory info or file editor (Ctrl+S to save) |
| Search | F9 | Glob/regex across drives, results in opposite panel |
| Quit | F10 | With confirmation dialog |
| Fullscreen | F11 | Toggle browser fullscreen |
| Selection | Insert / + / - / * | Toggle, select group, deselect group, invert |
| Drive switch | Alt+F1 / Alt+F2 | Left / right panel drive selector |
| Sync directories | Commands menu | TC-style dual-pane sync with per-file action cycling |
| Compare directories | Commands menu | 4-tab diff view (Different / Only Left / Only Right / Same) |
| NDC Tree | Commands menu | Full-screen directory tree, lazy-load, arrow-key nav |
| Archive browsing | F4 on .zip/.tar | List archive contents (password support for ZIP) |
| System info | Commands menu | OS, CPU, RAM, uptime, drives |
| History | Commands menu | Per-panel navigation history (last 50) |

**Detailed:** [USER_GUIDE.md](docs/USER_GUIDE.md)

## Configuration

Two separate config mechanisms:

| Config | Location | Controls |
|--------|----------|----------|
| **UI preferences** | Browser `localStorage` (`nc_config`) | View mode, sort, hidden files, confirmations, font size |
| **Server settings** | `config/config.json` | Operation timeouts/retries, keybindings, exec rules, editor limits |

Server config is managed via `Commands → Timeouts...` dialog or `PUT /api/config`.

**Detailed:** [CLI-TOOLS.md](docs/CLI-TOOLS.md)

## Project Structure

```
webnc_server.py          # Entry point
webnc/                   # Backend package
├── api/                 # REST endpoints (files, sync, compare, archive, ...)
├── operations/          # Async operation boundary (Copy, Move, BatchDelete, Search)
├── services/            # Business logic layer (FileService ABC + WindowsFileService)
├── models/              # Pydantic request/response models
├── security/            # TLS, auth middleware, token provider
├── vfs/                 # Path sanitization (/C/Users → C:\Users)
├── config_manager.py    # Thread-safe JSON config with atomic writes
└── main.py              # FastAPI app factory
client/                  # Frontend (React, no build step)
├── js/app.js            # Main component
├── js/components/       # Panel.js
├── js/dialogs/          # Sync, Compare, Editor, Search, Archive, ...
└── js/lib/              # api.js, utils.js, config.js
config/config.json       # Operation settings (auto-created)
bin/run.bat              # CMD wrapper
bin/manage_server.ps1    # PowerShell management
history/                 # Development history summaries (HISTORY.00001-00015)
version.txt              # Application version
```

**Detailed:** [REPOSITORY_MAP.md](docs/REPOSITORY_MAP.md) · [CODEBASE_DOCUMENTATION.md](docs/CODEBASE_DOCUMENTATION.md)

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/list` | GET | Directory listing |
| `/api/view` | GET | File content |
| `/api/edit` | POST | Save file |
| `/api/download` | GET | Download file |
| `/api/upload` | POST | Upload file |
| `/api/info` | GET | File/dir metadata |
| `/api/copy`, `/api/move` | POST | Async copy/move |
| `/api/delete`, `/api/batch-delete` | POST | Delete |
| `/api/search` | POST | File search |
| `/api/compare` | GET | Directory diff |
| `/api/sync/plan`, `/api/sync/execute` | GET/POST | Sync |
| `/api/archive/list` | GET | Archive contents |
| `/api/exec` | POST | Execute shell command |
| `/api/link` | POST | Create symlink/junction/hardlink |
| `/api/operation/{id}` | GET | Poll async status |
| `/api/config` | GET/PUT | Server config |
| `/api/health` | GET | Health check (no auth) |
| `/api/sysinfo` | GET | System information |
| `/api/drives` | GET | Drive listing |

**Detailed:** [API_REFERENCE.md](docs/API_REFERENCE.md)

## CLI Arguments

```console
$ py webnc_server.py --help
--host HOST         Bind address (default: 127.0.0.1)
--port PORT         Bind port (default: 8000)
--insecure          Disable SSL/TLS (HTTP, no encryption)
--cert CERT         SSL certificate file
--key KEY           SSL key file
--auth AUTH         Auth provider: console-token (default)
--reload            Enable auto-reload (default: off)
```

**Detailed:** [CLI-TOOLS.md](docs/CLI-TOOLS.md)

## Roadmap

### Implemented
- [x] In-browser file editor (F4) — `POST /api/edit`, EditorDialog with Ctrl+S
- [x] Find File panel mode (`viewMode: "search"`) — F9 populates opposite panel
- [x] Fullscreen mode (EGA Lines) — F11, menu toggle
- [x] Keyboard shortcut config — `keybindings` in `config.json`, action dispatch map
- [x] Command input — `POST /api/exec`, interactive `>` line, terminal output area
- [x] Operation retry/timeout config — per-operation in `config.json`, polling on frontend
- [x] Command history — ArrowUp/Down, localStorage-backed, max 100 entries
- [x] Symbolic links — `POST /api/link`, symlink/junction/hardlink fallback

### Productize Core
- [ ] Linux support via VFS abstraction layer
- [ ] Docker image
- [ ] Allowed roots (path allowlist)
- [ ] Read-only mode
- [ ] Operation progress / cancel (background queue UI)
- [ ] Audit log for file operations

### Usability
- [ ] Drag & drop upload
- [ ] Image / text preview (inline)
- [ ] Clipboard copy / paste
- [ ] Archive extract / create
- [ ] Editor enhancement — find/replace (max_edit_size config already implemented)

### Self-Hosted Product
- [ ] SFTP / FTP provider via VFS
- [ ] Users & RBAC
- [ ] Reverse proxy deployment docs
- [ ] GitHub release
- [ ] Demo video
- [ ] Landing page

### Also Planned
- [ ] Extension-to-action associations
- [ ] Terminal emulation (Ctrl+O) — command input exists, full terminal planned
- [ ] Directory hotlist
- [ ] NDC Tree dialog

## Documentation

| Document | Description |
|----------|-------------|
| [API_REFERENCE.md](docs/API_REFERENCE.md) | All endpoints, request/response formats |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design, data flow, security model |
| [CODEBASE_DOCUMENTATION.md](docs/CODEBASE_DOCUMENTATION.md) | Module organization, architectural decisions |
| [REPOSITORY_MAP.md](docs/REPOSITORY_MAP.md) | Every file and folder with description |
| [CLI-TOOLS.md](docs/CLI-TOOLS.md) | CLI args, management scripts, config format |
| [USER_GUIDE.md](docs/USER_GUIDE.md) | Full user manual |
| [SECURITY.md](docs/SECURITY.md) | Threat model, vulnerability reporting |
| [COMPLIANCE.md](docs/COMPLIANCE.md) | Security audit, data handling, compliance |
| [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Known issues and solutions |
| [CHANGELOG.md](CHANGELOG.md) | Version history and release notes |
| [History.md](History.md) | Detailed development history |
| [history/](history/) | Per-milestone development summaries (00001–00015) |

## License

See [LICENSE](LICENSE).

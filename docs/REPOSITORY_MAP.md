# WebNC Repository Map

This document provides a complete mapping of folders and files in the WebNC repository with brief descriptions of their purpose.

## Root Directory

| File/Folder | Description |
|-------------|-------------|
| `docs/` | Documentation files (API reference, architecture, user guide, etc.) |
| `docs/API_REFERENCE.md` | API endpoint reference with request/response formats |
| `docs/ARCHITECTURE.md` | System architecture, data flow, security model |
| `docs/CODEBASE_DOCUMENTATION.md` | Detailed codebase organization and module docs |
| `docs/REPOSITORY_MAP.md` | This file - folder/file descriptions |
| `docs/CLI-TOOLS.md` | CLI tool documentation (webnc_server.py, run.bat, manage_server.ps1) |
| `docs/USER_GUIDE.md` | End-user manual for the WebNC file manager |
| `docs/SECURITY.md` | Threat model, vulnerability reporting policy |
| `docs/COMPLIANCE.md` | Security compliance, audit, and data handling policies |
| `docs/TROUBLESHOOTING.md` | Known issues, resolved problems, and solutions |
| `webnc/` | Python backend package containing all server-side code |
| `client/` | Frontend static files (HTML, CSS, JavaScript) |
| `bin/` | Management scripts (PowerShell and batch files) |
| `config/` | Configuration files (auto-generated config.json) |
| `logs/` | Log files (rotating log output) |
| `history/` | Development history summaries (HISTORY.00001.md — HISTORY.00015.md) |
| `__doc__/` | Legacy documentation directory (to be migrated) |
| `__pycache__/` | Python compiled bytecode directories |
| `webnc_server.py` | Main entry point for the application |
| `run.bat` | CMD wrapper script for starting/stopping the server |
| `manage_server.ps1` | PowerShell script for server management |
| `requirements.txt` | Python package dependencies |
| `version.txt` | Application version string (read by `webnc/version.py`) |
| `README.md` | Project overview and quick start guide |
| `CHANGELOG.md` | Version history and release notes |
| `History.md` | Detailed development changelog |
| `LICENSE` | Software license information |
| `.gitignore` | Git exclusion rules |

## Backend Package (webnc/)

| File/Folder | Description |
|-------------|-------------|
| `webnc/__init__.py` | Package initialization file |
| `webnc/__main__.py` | Allows package execution via `python -m webnc` |
| `webnc/__pycache__/` | Compiled bytecode for package root |
| `webnc/config.py` | Configuration constants and defaults |
| `webnc/config_manager.py` | Thread-safe JSON configuration management |
| `webnc/logging_config.py` | Logging setup with rotating file handler |
| `webnc/main.py` | FastAPI application factory and setup |
| `webnc/version.py` | Version reader (reads `version.txt` from project root) |
| `webnc/api/` | RESTful API endpoint implementations |
| `webnc/operations/` | Background operation classes and queue management |
| `webnc/models/` | Pydantic data models for request/validation |
| `webnc/security/` | Authentication, authorization, and TLS components |
| `webnc/services/` | Business logic layer (planned for expansion) |
| `webnc/vfs/` | Virtual file system layer for path handling |

### API Module (webnc/api/)

| File/Folder | Description |
|-------------|-------------|
| `webnc/api/__init__.py` | Package initialization |
| `webnc/api/__pycache__/` | Compiled bytecode |
| `webnc/api/archive.py` | Archive listing endpoint (/api/archive/list) |
| `webnc/api/compare.py` | Directory comparison endpoint (/api/compare) |
| `webnc/api/config_api.py` | Configuration endpoints (/api/config) |
| `webnc/api/drives.py` | Drive listing endpoint (/api/drives) |
| `webnc/api/exec.py` | Command execution endpoint (/api/exec) |
| `webnc/api/files.py` | File operations endpoints (list, view, copy, move, etc.) |
| `webnc/api/operations.py` | Operation status polling endpoint (/api/operation/{id}) |
| `webnc/api/static.py` | Frontend static file serving |
| `webnc/api/sync.py` | Directory synchronization endpoints (/api/sync/plan, /api/sync/execute) |
| `webnc/api/system.py` | System information endpoints (/api/sysinfo, /api/health) |

### Operations Module (webnc/operations/)

| File/Folder | Description |
|-------------|-------------|
| `webnc/operations/__init__.py` | Package initialization |
| `webnc/operations/__pycache__/` | Compiled bytecode |
| `webnc/operations/base.py` | AbstractOperation base class with retry/timeout logic |
| `webnc/operations/compare.py` | CompareOperation implementation |
| `webnc/operations/files.py` | File operation implementations (Copy, Move, Delete, Link, Search, etc.) |
| `webnc/operations/queue.py` | OperationQueue — async operation boundary for decoupling FS ops from HTTP |
| `webnc/operations/syncop.py` | SyncPlanOperation and SyncExecuteOperation implementations |
| `webnc/operations/system.py` | System operation classes (if any) |
| `webnc/operations/archive.py` | ArchiveListOperation implementation |

### Models Module (webnc/models/)

| File/Folder | Description |
|-------------|-------------|
| `webnc/models/__init__.py` | Package initialization |
| `webnc/models/__pycache__/` | Compiled bytecode |
| `webnc/models/auth.py` | Authentication-related Pydantic models |
| `webnc/models/compare.py` | Directory comparison Pydantic models |
| `webnc/models/files.py` | File operation Pydantic models |
| `webnc/models/sync.py` | Synchronization Pydantic models |
| `webnc/models/state.py` | Application state Pydantic models |

### Security Module (webnc/security/)

| File/Folder | Description |
|-------------|-------------|
| `webnc/security/__init__.py` | Package initialization |
| `webnc/security/__pycache__/` | Compiled bytecode |
| `webnc/security/auth_provider.py` | AuthProvider interface definition |
| `webnc/security/console_token.py` | ConsoleTokenProvider implementation (default auth) |
| `webnc/security/middleware.py` | SessionAuthMiddleware for request authentication |
| `webnc/security/nc_crypto.py` | Cryptographic utilities (hashing, random generation) |
| `webnc/security/tls.py` | TLS certificate generation and SSL context creation |
| `webnc/security/_state.py` | Internal state management for auth provider |

### Virtual File System Module (webnc/vfs/)

| File/Folder | Description |
|-------------|-------------|
| `webnc/vfs/__init__.py` | Package initialization |
| `webnc/vfs/__pycache__/` | Compiled bytecode |
| `webnc/vfs/paths.py` | Path sanitization and conversion utilities |

### Services Module (webnc/services/)

| File/Folder | Description |
|-------------|-------------|
| `webnc/services/__init__.py` | Package initialization |
| `webnc/services/__pycache__/` | Compiled bytecode |
| *(Currently empty - planned for future business logic)* |

## Frontend (client/)

| File/Folder | Description |
|-------------|-------------|
| `client/index.html` | Entry point - loads React UMD bundles and initializes app |
| `client/css/` | Stylesheets for the application |
| `client/js/` | JavaScript modules for the frontend application |
| `client/css/nc.css` | Norton Commander theme stylesheet with semantic classes |
| `client/js/app.js` | Main WebNC React component |
| `client/js/react.production.min.js` | React 18 UMD bundle |
| `client/js/react-dom.production.min.js` | ReactDOM 18 UMD bundle |
| `client/js/components/` | Reusable UI components |
| `client/js/dialogs/` | Modal dialog components |
| `client/js/lib/` | Library utilities and helpers |

### Frontend Components (client/js/components/)

| File/Folder | Description |
|-------------|-------------|
| `client/js/components/Panel.js` | File panel component with all view modes (Brief, Full, Quick, Info, Tree, Search) |

### Frontend Dialogs (client/js/dialogs/)

| File/Folder | Description |
|-------------|-------------|
| `client/js/dialogs/index.js` | Barrel export file re-exporting all dialogs |
| `client/js/dialogs/ArchiveDialog.js` | Archive viewing dialog |
| `client/js/dialogs/CompareDialog.js` | Directory comparison dialog |
| `client/js/dialogs/ConfigDialog.js` | UI preferences configuration dialog |
| `client/js/dialogs/DriveDialog.js` | Drive selection dialog |
| `client/js/dialogs/EditorDialog.js` | In-browser file editor dialog |
| `client/js/dialogs/HelpDialog.js` | Keyboard reference dialog |
| `client/js/dialogs/HistoryDialog.js` | Navigation history dialog |
| `client/js/dialogs/LoginDialog.js` | Session token entry dialog |
| `client/js/dialogs/SimpleDialogs.js` | Reusable simple dialogs (FileViewer, Confirm, Input) |
| `client/js/dialogs/SysInfoDialog.js` | System information dialog |
| `client/js/dialogs/TimeoutsDialog.js` | Operation timeout/retry configuration dialog |
| `client/js/dialogs/SyncDialog.js` | Directory synchronization dialog (Total Commander style) |

### Frontend Library (client/js/lib/)

| File/Folder | Description |
|-------------|-------------|
| `client/js/lib/api.js` | API client functions + operation polling logic |
| `client/js/lib/config.js` | Client-side configuration management (localStorage) |
| `client/js/lib/styles.js` | Legacy style object references (to be deprecated) |
| `client/js/lib/utils.js` | Utility functions (formatting, colors, path helpers) |

## Management Scripts (bin/)

| File/Folder | Description |
|-------------|-------------|
| `bin/manage_server.ps1` | PowerShell script for server start/stop/restart/status/monitor |
| `bin/run.bat` | CMD wrapper script for manage_server.ps1 |

## Configuration (config/)

| File/Folder | Description |
|-------------|-------------|
| `config/config.json` | Auto-generated operation timeout/retry settings |

## Logs (logs/)

| File/Folder | Description |
|-------------|-------------|
| `logs/webnc_server.log` | Rotating log file (5 MB × 3 backups) |

## Development History (history/)

| File/Folder | Description |
|-------------|-------------|
| `history/HISTORY.00001.md` | Initial backend + frontend prototype |
| `history/HISTORY.00002.md` | Paren balance fix, panel table rewrite, spacing |
| `history/HISTORY.00003.md` | Sort, brief view, menu system, search |
| `history/HISTORY.00004.md` | Info/tree view, filter, sysinfo, compare |
| `history/HISTORY.00005.md` | Per-panel On/Off, config dialog, help, archive |
| `history/HISTORY.00006.md` | SSL support, manage_server.ps1, run.bat |
| `history/HISTORY.00007.md` | TLS 1.3, auth provider, directory sync |
| `history/HISTORY.00008.md` | SyncDialog TC-style redesign |
| `history/HISTORY.00009.md` | ESM modular frontend, static.py rewrite |
| `history/HISTORY.00010.md` | FastAPI package structure, event loop fix |
| `history/HISTORY.00011.md` | Operation retry/timeout config, TimeoutsDialog |
| `history/HISTORY.00012.md` | CSS refactoring, editor, find file panel |
| `history/HISTORY.00013.md` | Fullscreen, keyboard config, command exec |
| `history/HISTORY.00014.md` | Terminal overlay, activeTarget, token stderr |
| `history/HISTORY.00015.md` | Project restructuring, rebranding to WebNC |

## Legacy Documentation (__doc__/)

| File/Folder | Description |
|-------------|-------------|
| `__doc__/` | Legacy documentation directory containing older docs to be migrated to docs/ |

## File Extensions Reference

| Extension | Purpose |
|-----------|---------|
| `.py` | Python source code |
| `.js` | JavaScript ES modules |
| `.html` | HyperText Markup Language files |
| `.css` | Cascading Style Sheets |
| `.md` | Markdown documentation files |
| `.bat` | Windows batch files |
| `.ps1` | PowerShell scripts |
| `.json` | JavaScript Object Notation files |
| `.txt` | Plain text files |
| `.log` | Log files |
| `.crt` | SSL certificate files |
| `.key` | SSL key files |
| `.token` | Session token files (transient) |
| `.pyc` | Python compiled bytecode |

## Key Architectural Files

### Entry Points
- `webnc_server.py` - Main application entry point
- `webnc/__main__.py` - Allows `python -m webnc` execution
- `client/index.html` - Frontend entry point

### Core Backend Components
- `webnc/main.py` - FastAPI application factory
- `webnc/config_manager.py` - Thread-safe configuration management
- `webnc/logging_config.py` - Logging infrastructure
- `webnc/security/middleware.py` - Authentication middleware
- `webnc/security/console_token.py` - Default authentication provider
- `webnc/vfs/paths.py` - Path sanitization utilities
- `webnc/operations/base.py` - Abstract operation base class
- `webnc/operations/queue.py` - Operation queue and thread pool

### Core Frontend Components
- `client/js/app.js` - Main React application component
- `client/js/lib/api.js` - Backend communication layer
- `client/js/lib/utils.js` - Formatting and utility functions
- `client/js/lib/config.js` - Client-side configuration management
- `client/css/nc.css` - Theme stylesheet
- `client/js/components/Panel.js` - Reusable file panel component
- `client/js/dialogs/SyncDialog.js` - Synchronization dialog
- `client/js/dialogs/EditorDialog.js` - File editor dialog

### Management and Deployment
- `bin/manage_server.ps1` - PowerShell server management
- `bin/run.bat` - CMD wrapper for management scripts
- `requirements.txt` - Python dependencies
- `config/config.json` - Operation timeout/retry configuration

This map provides a comprehensive overview of the WebNC repository structure. Each file and folder is organized by concern, following a modular architecture that separates API concerns from operation logic, security from business logic, and frontend from backend concerns.
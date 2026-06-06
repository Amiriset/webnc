# WebNC Codebase Documentation

## Overview
This document provides detailed information about the WebNC codebase organization, architectural solutions, and module organization for both server and client components.

## Repository Structure
```
WebNC/
├── docs/                     # Documentation files
├── webnc/                    # Python backend package
│   ├── api/                  # API endpoint implementations
│   ├── operations/           # Background operation classes
│   ├── models/               # Pydantic data models
│   ├── security/             # Authentication and security components
│   ├── services/             # Business logic layer
│   ├── vfs/                  # Virtual file system layer
│   ├── config_manager.py     # Configuration management
│   ├── logging_config.py     # Logging setup
│   ├── main.py               # FastAPI application factory
│   └── config.py             # Configuration constants
├── client/                   # Frontend static files
│   ├── css/                  # Stylesheets
│   └── js/                   # JavaScript modules
├── bin/                      # Management scripts
├── config/                   # Configuration files
├── logs/                     # Log files
├── webnc_server.py           # Entry point
├── run.bat                   # CMD wrapper
├── manage_server.ps1         # PowerShell management script
├── requirements.txt          # Python dependencies
├── README.md                 # Project overview
├── History.md                # Development history
└── LICENSE                   # License file
```

## Backend (webnc/) Documentation

### Core Application Structure

#### main.py
The main application entry point that:
- Creates the FastAPI application instance
- Sets up middleware (authentication, CORS, etc.)
- Mounts all API routers
- Initializes the configuration manager
- Configures exception handlers
- Sets up startup/shutdown events
- Configures Windows ProactorEventLoop for subprocess support
- Installs ConnectionResetError exception handler on event loop
- Passes custom `log_config` to `uvicorn.run()` for consistent logging

Key components:
```python
def create_app() -> FastAPI:
    app = FastAPI(title="WebNC", version="1.0.0")
    
    # Middleware setup
    app.add_middleware(SessionAuthMiddleware)
    
    # Router mounting
    app.include_router(files_router, prefix="/api")
    app.include_router(sync_router, prefix="/api")
    # ... other routers
    
    # Exception handlers
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request, exc):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
    
    return app
```

#### config_manager.py
Thread-safe configuration management with:
- JSON file storage with atomic writes (.tmp + replace)
- Default values for all operation types
- Runtime configuration updates via API
- Lock-based thread safety
- Automatic creation of config.json on first use

Key methods:
- `get(operation_name)`: Get configuration for an operation
- `set(operation_name, config)`: Set configuration for an operation
- `save()`: Atomically save configuration to disk
- `_merge_defaults()`: Merge user config with defaults

#### logging_config.py
Logging configuration featuring:
- RotatingFileHandler (5 MB × 3 backups)
- Standard error output
- Consistent log format: `%(asctime)s | %(levelname)-8s | %(message)s`
- Handler duplication prevention for reload safety
- UTF-8 encoding for international characters

### API Layer (webnc/api/)

#### files.py
Handles filesystem operations:
- `/api/list`: Directory listing with sorting/filtering
- `/api/view`: File content retrieval (text <64KB, or <max_edit_size for editing)
- `/api/edit`: Save file content (synchronous, text files only)
- `/api/download`: Download file as binary
- `/api/upload`: Upload file via multipart/form-data (max 100MB)
- `/api/info`: File/directory metadata including ownership
- `/api/disk`: Disk usage information
- `/api/drives`: Available drives with labels
- `/api/tree`: Lazy-loaded directory tree
- `/api/search`: File search by glob/regex (async)
- `/api/copy`: Copy file/dir (async with retry)
- `/api/move`: Move file/dir (async with retry)
- `/api/rename`: Rename file/dir (synchronous)
- `/api/mkdir`: Create directory (synchronous)
- `/api/delete`: Delete file/dir (synchronous)
- `/api/batch-delete`: Delete multiple items (async with retry)

Sync vs Async pattern:
- Synchronous endpoints use `queue.run_sync(op, timeout=10.0)` and return `OperationResult` directly
- Asynchronous endpoints use `queue.add_operation(op)` and return `{operation_id, status: "QUEUED", poll: config}`
- Frontend polls `GET /api/operation/{id}` for async operation status

#### compare.py
Directory comparison functionality:
- `/api/compare`: Async directory comparison
- Compares by name, size, date (configurable)
- Returns categorized differences (only_left, only_right, different, same)
- Uses `shutil.disk_usage()` and `os.scandir()` wrapped in threads

#### sync.py
Directory synchronization:
- `/api/sync/plan`: Generate sync plan (async)
- `/api/sync/execute`: Execute sync actions (async)
- Supports options: subdirs, by_content, ignore_date, asymmetric, filter
- Returns suggested actions for auto-marking in UI

#### archive.py
Archive handling:
- `/api/archive/list`: List ZIP/TAR/etc. contents (async)
- Supports password-protected ZIP archives
- Returns normalized file listing with size/packed/modified dates
- Uses `zipfile` and `tarfile` modules in thread pool

#### system.py
System information endpoints:
- `/api/sysinfo`: OS, hostname, CPU, RAM, uptime, drives
- `/api/health`: Health check (no auth required) — returns `{status, state, version}`
- Uses `platform`, `psutil`, and Win32 APIs where applicable

#### exec.py
Command execution endpoint:
- `/api/exec`: Execute shell command on server (synchronous, 30s timeout)
- `_decode()`: Fallback chain for stdout/stderr: UTF-8 → CP866 (OEM) → CP1251 (ANSI) → CP437 → Latin-1
- Command allow/deny checks via `config.json` → `exec.allowed_commands` / `exec.denied_commands`
- Uses `asyncio.create_subprocess_shell()` with 30s timeout
- Default denied commands: `format`, `diskpart`, `shutdown`, `reg.exe`

#### drives.py
Drive information:
- `/api/drives`: Lists available drives with labels
- Uses `GetVolumeInformationW` via ctypes for volume labels
- Filters to only available/ready drives
- Exempt from authentication for usability

#### operations.py
Operation status polling:
- `/api/operation/{id}`: Get operation status
- Returns detailed progress information
- Supports cancellation (planned)
- Tracks operation results and errors

#### static.py
Frontend static file serving:
- Serves React bundles, CSS, and JavaScript modules
- Sets correct MIME types for ES modules (`text/javascript`)
- Handles client-side routing fallback to index.html
- Implements caching headers for performance

### Operations Layer (webnc/operations/)

#### base.py
Abstract base class for all operations:
- `AbstractOperation`: Core operation functionality
- Thread-safe execution with retry logic
- Configurable timeouts and poll intervals
- Smart retry classification (`should_retry()`)
- Progress tracking and result handling
- Integration with ConfigManager
- Key methods:
  - `run()`: Main execution template method
  - `should_retry()`: Determines if error is retriable
  - `get_poll_config()`: Returns timeout/interval for frontend
  - `op_config_key`: Identifies operation type in config

#### files.py
File operation implementations:
- `ListOperation`: Directory listing with sorting/filtering
- `ViewOperation`: File content reading (text <64KB)
- `WriteOperation`: File creation/overwrite (for editor)
- `DownloadOperation`: File download preparation
- `UploadOperation`: File upload with size validation
- `CopyOperation`: shutil.copytree/shutil.copy2 with metadata preservation
- `MoveOperation`: shutil.move with cross-device handling
- `RenameOperation`: Path.rename with validation
- `MakeDirectoryOperation`: Path.mkdir with parents
- `LinkOperation`: os.symlink with mklink /J (junction) / /H (hardlink) fallback
- `DeleteOperation`: shutil.rmtree or Path.unlink
- `BatchDeleteOperation`: Multiple delete with individual error handling
- `SearchOperation`: os.walk with glob/regex pattern matching
- `FileInfoOperation`: File/directory metadata with Windows owner/permissions
- `TreeOperation`: Lazy directory tree (immediate subdirs)
- Each implements `_is_non_retriable()` for specific error types

#### compare.py
- `CompareOperation`: Directory comparison logic
- Walks both directory trees simultaneously
- Compares file name, size, modification time
- Returns structured difference report
- Supports content-based comparison (slower but accurate)

#### syncop.py
- `SyncPlanOperation`: Generates synchronization plan
- Walks both directory trees
- Determines required actions based on options
- Marks suggested actions for auto-selection
- `SyncExecuteOperation`: Executes sync actions
- Processes action list: copy/delete operations
- Handles errors per action, continues on failure

#### archive.py
- `ArchiveListOperation`: Lists archive contents
- Supports ZIP (with password), TAR, GZ, BZ2, XZ
- Uses appropriate libraries in thread pool
- Handles password prompts via 401 responses
- Returns normalized file information

#### queue.py
- `OperationQueue`: Thread pool operation manager
- Configurable worker count (defaults to CPU count)
- Thread-safe queue operations
- Operation lifecycle management
- Graceful shutdown handling
- Progress tracking and statistics

### Security Layer (webnc/security/)

#### auth_provider.py
- `AuthProvider`: Abstract base class for authentication
- Defines `authenticate()` and `authorize()` interfaces
- `UserInfo`: Dataclass for user information (username, roles)
- Designed for extensibility to AD/Kerberos/JWT/LDAP

#### console_token.py
- `ConsoleTokenProvider`: Default authentication provider
- Zero-knowledge SHA-256 handshake
- Ephemeral token generation (`secrets.token_hex(32)`)
- Nonce-based replay protection
- 5-minute timestamp window
- Constant-time comparison to prevent timing attacks
- Token stored only in server RAM and client sessionStorage

#### middleware.py
- `SessionAuthMiddleware`: Authentication middleware
- Validates `X-NC-Nonce`, `X-NC-Timestamp`, `X-NC-Signature` headers
- Exempts `/api/health`, `/api/drives`, `/api/disk` from auth
- Sets `request.state.user_info` for downstream use
- Handles authentication failures (401 response)
- Integrates with AuthProvider interface

#### tls.py
- TLS certificate generation and context creation
- `_gen_self_signed_cert()`: RSA-4096 certificate via cryptography
- `_create_ssl_context()`: TLS 1.3 configuration
- Security settings: `OP_NO_COMPRESSION`, cipher server preference
- SAN includes: localhost, 127.0.0.1, ::1
- Auto-renewal every 10 years or on certificate deletion

#### nc_crypto.py
- Cryptographic utilities for authentication
- SHA-256 hashing with salt support
- Secure random token generation
- Password hashing utilities (for future use)
- Constant-time comparison functions

### Virtual File System (webnc/vfs/)

#### paths.py
Path sanitization and conversion utilities:
- `safe_path()`: Converts URL paths to Windows absolute paths
  - `/C/Users/foo` → `C:\Users\foo`
  - Validates against path traversal attempts
  - Works with any drive letter (`/D/`, `/E/`, etc.)
- `relative_path()`: Converts Windows paths to URL format
- `is_safe_path()`: Path safety validation
- UNC path handling (planned)
- Symbolic link resolution (planned)

### Models Layer (webnc/models/)

Pydantic models for request/response validation:
- `files.py`: File operation models (CopyRequest, EditRequest, etc.)
- `sync.py`: Synchronization models (SyncRequest, SyncAction, etc.)
- `compare.py`: Comparison models (CompareRequest, CompareResult, etc.)
- `auth.py`: Authentication models (TokenInfo, UserInfo, etc.)
- `state.py`: Application state models
- Automatic validation, serialization, and documentation
- Used throughout API layer for input/output validation

### Services Layer (webnc/services/)
Currently minimal, planned for future business logic:
- Intended home for complex operations
- Future location for VFS providers (SFTP/FTP, cloud storage)
- Planned RBAC and permission services
- Will house business rules separate from API concerns

### Configuration Layer (config/)
- `config.json`: Auto-generated operation timeout/retry settings, keybindings, exec rules, editor limits
- Created on first ConfigManager instantiation
- Contains defaults for all 8 operation types, keybindings, exec command rules, editor size limit
- Editable via `/api/config` endpoint
- Thread-safe updates with atomic file writes

#### Config Structure
```json
{
  "operations": {
    "copy": { "max_retries": 3, "timeout": 600, "interval": 500 },
    "move": { "max_retries": 3, "timeout": 600, "interval": 500 },
    "batch_delete": { "max_retries": 2, "timeout": 120, "interval": 300 },
    "search": { "max_retries": 2, "timeout": 120, "interval": 300 },
    "compare": { "max_retries": 2, "timeout": 120, "interval": 300 },
    "sync_plan": { "max_retries": 2, "timeout": 120, "interval": 300 },
    "sync_execute": { "max_retries": 2, "timeout": 300, "interval": 500 },
    "archive_list": { "max_retries": 1, "timeout": 30, "interval": 300 }
  },
  "keybindings": {
    "F1": "help", "F3": "view", "F5": "copy", "F6": "move",
    "F7": "mkdir", "F8": "delete", "F9": "search", "F10": "quit"
  },
  "exec": {
    "allowed_commands": [],
    "denied_commands": ["format", "diskpart", "shutdown", "reg.exe"]
  },
  "editor": {
    "max_edit_size": 1048576
  }
}
```

## Frontend (client/) Documentation

### Entry Point (client/index.html)
Minimal HTML entry point:
- Loads React UMD bundles (react.production.min.js + react-dom.production.min.js)
- Links to CSS stylesheet (`css/nc.css`)
- Initializes ES module application via `<script type="module">`
- Serves as mounting point for React application
- No build process required - pure browser execution

### Styles (client/css/nc.css)
Comprehensive Norton Commander theme:
- Semantic CSS classes for consistent UI:
  - Layout: `.panel`, `.panel-border-active`, `.panel-header-active`
  - File listing: `.filename`, `.directory`, `.filesize`, `.datetime`
  - Interactive: `.nc-btn`, `.nc-input`, `.nc-num`, `.nc-table`
  - States: `.selected`, `.overlay`, `.dialog`, `.title-bar`
  - Colors: `.text-yellow`, `.text-cyan`, `.text-red`
  - Utilities: `.flex`, `.flex-1`, `.gap-*`, `.fs-*`, `.mono`
- Responsive design considerations
- Scrollbar styling for consistent appearance
- Focus outlines for keyboard navigation
- Yellow selection background (`#554400`) for visibility

### Application (client/js/app.js)
Main WebNC React component:
- State management using React hooks (`useState`, `useEffect`)
- Panel state: active panel, paths, items, view modes, sort settings
- Dialog state: open/closed states for all dialog types
- Keyboard handling: global key dispatcher with modal awareness
- Menu system: dropdown menus with hover activation
- Action handlers: F-key mappings (F1-Help, F3-View, etc.)
- API integration: uses `api.js` functions for all backend communication
- Operation polling: manages operation status checks
- Configuration persistence: reads/writes UI preferences to localStorage
- Fullscreen handling: F11 toggle with proper exit handling

### Components (client/js/components/)

#### Panel.js
Reusable file panel component with multiple view modes:
- **View Modes**:
  - Brief: Multi-column layout (`column-width: 120px`)
  - Full: Table view with Name/Extension/Time/Size columns
  - Quick: Shows preview of opposite panel selection
  - Info: Shows directory summary + disk info (opposite panel)
  - Tree: Expandable directory tree with lazy loading
  - Search: Search results view with Name/Path/Size/Date columns
- Features:
  - Keyboard navigation (↑↓, Home/End, PgUp/PgDn, Enter)
  - Per-panel sorting (click column headers)
  - Filter persistence across navigation
  - Selection tracking (Insert, +, -, * keys)
  - Drive switching (Alt+F1/F2)
  - View mode switching via menu
  - Lazy loading for large directories
  - Error and loading states
  - Scroll position preservation

### Dialogs (client/js/dialogs/)
All dialogs as independent ES modules following consistent patterns:

#### Shared Dialog Features
- Consistent styling via CSS classes
- Keyboard trapping (Tab cycles within dialog)
- Escape key closes dialog
- Enter key activates primary action
- Focus management (first input focused on open)
- Responsive sizing and positioning
- Semi-transparent overlay backdrop
- Title bar with close button
- Scrollable content areas when needed

#### Specific Dialogs

##### SyncDialog.js
Total Commander-style directory synchronization:
- Two-phase layout: Setup → Results
- Setup tab: paths, filter, options (subdirs, by_content, etc.)
- Compare button: initiates synchronization plan
- Results tab: dual-pane file list with action cycling
- Show-filter toggles: → = ≠ ← (independent toggles)
- Per-row action cycling: click to cycle through available actions
- Info bar: counts (Total, Same, Diff, L-only, R-only)
- Bottom buttons: Re-compare, Mark All, Synchronize, Close
- Row highlighting: yellow background for selected actions
- Auto-marking: suggests actions based on options
- Proper state cleanup to prevent "trapped user" bugs

##### CompareDialog.js
Directory comparison visualization:
- Four-tab interface: Different / Only Left / Only Right / Same
- Click any row to navigate to that location
- Color-coded differences for easy identification
- File details: name, size, date, status indicators
- Navigation preserving opposite panel position
- Proper handling of empty result sets

##### EditorDialog.js
In-browser file editing:
- `<textarea>` for file content editing
- Ctrl+S save shortcut indicator
- Dirty tracking (unsaved changes warning)
- Save/Cancel buttons with proper validation
- Size limit enforcement (<64KB for performance)
- Monospace font via CSS `.mono` class
- UTF-8 encoding handling
- Error handling for save failures

##### SearchDialog.js
File search interface:
- Pattern input (glob or regex)
- Results list with navigation
- Enter to open selected result in opposite panel
- Esc to close dialog
- Persistent search mode indicator in UI
- Integration with Panel search mode
- Proper clearing of search state on navigation

##### ArchiveDialog.js
Archive viewing interface:
- Table listing: Name, Size, Packed, Modified dates
- Navigation: ↑↓, Enter to open parent directory
- Password handling: retry dialog on 401 response
- Visual indicator for encrypted archives (🔒 lock icon)
- Proper handling of different archive types
- Error handling for corrupt/unreadable archives

##### ConfigDialog.js
UI preferences configuration:
- Default view mode selection
- Default sort field and direction
- Show hidden files toggle
- Confirm delete/overwrite prompts
- Font size adjustment (px-based)
- Preview of changes in real-time
- Save/Reset to defaults buttons
- Storage in localStorage under `nc_config` key

##### TimeoutsDialog.js
Operation timeout/retry configuration:
- Table layout: Operation | Retries | Timeout(s) | Interval(ms)
- Editable fields with validation
- Presets and reset to defaults
- Save → PUT /api/config endpoint
- Real-time validation feedback
- Separate from UI config for concern separation

##### DriveDialog.js
Drive selection interface:
- Lists drives with labels and usage information
- Arrow key navigation
- Letter-key quick selection
- Enter to confirm selection
- Escape to cancel
- Refresh capability
- Tooltips showing detailed drive information

##### InfoDialog.js
File/directory information display:
- Detailed metadata presentation
- Owner information (DOMAIN\Username format)
- Permission details (rwxr-xr-x style)
- Timestamps (created, modified, accessed)
- Size formatting (bytes → KB/MB/GB)
- Disk usage for containing drive
- Different layout for files vs directories
- Refresh capability for updated information

##### HistoryDialog.js
Navigation history management:
- Per-panel history tracking (last 50 unique paths)
- ↑↓ navigation with Enter to navigate
- Clear history button
- Visual indication of current position
- Proper handling of duplicated entries
- Persistent across session (until cleared)

##### HelpDialog.js
Keyboard reference:
- Comprehensive key binding list
- Organized by category (Navigation, Function Keys, etc.)
- Search/filter functionality (planned)
- Print-friendly layout
- Dismissal via Esc/Enter/F1
- Updated dynamically from configuration
- Visual grouping of related keys

##### SysInfoDialog.js
System information display:
- Operating system details
- Hostname and domain information
- CPU specifications and usage
- Memory statistics (total/used/free)
- Uptime formatting
- Drive table with labels and usage
- Refresh capability
- Copy-to-clipboard functionality (planned)

##### LoginDialog.js
Session authentication:
- Token entry via prompt() or URL hash
- Visual guidance for token acquisition
- Error handling for invalid/expired tokens
- Automatic focus on input field
- Enter to submit, Escape to cancel
- Clear instructions for token retrieval
- Security-conscious design (no token storage)

##### SimpleDialogs.js
Reusable simple dialog components:
- `FileViewer`: Read-only file content display
- `Confirm`: Yes/no cancellation dialog
- `Input`: Single-line text input with validation
- Consistent styling with other dialogs
- Reusable across different contexts
- Proper return value handling

### Library (client/js/lib/)

#### api.js
Backend communication layer:
- Low-level `api()` function: handles auth headers, error handling
- Typed endpoint functions: `apiList()`, `apiView()`, `apiCopy()`, etc.
- `pollOperation()`: Generic operation polling with timeout
- Configuration functions: `apiGetConfig()`, `apiSetConfig()`
- URL building with proper encoding
- Error normalization and transformation
- Request timing and logging (development)
- Retry handling for transient network errors

#### utils.js
Utility functions for frontend:
- `fmtSize()`: File size formatting (bytes → KB/MB/GB/TB)
- `fmtDate()`: Date/time formatting with localization
- `fileColor()`: Color coding by file type (extensions)
- `fnmatch()`: Filename pattern matching (simplified)
- Path manipulation helpers
- String formatting and truncation
- DOM manipulation helpers
- Event utility functions

#### config.js
Client-side configuration management:
- `loadConfig()`: Reads UI preferences from localStorage
- `saveConfig()`: Writes UI preferences to localStorage
- Default values for all UI settings
- Validation and sanitization of loaded values
- Change notification system (planned)
- Migration handling for config format changes
- Integration with `localStorage` key `nc_config`

#### styles.js
Legacy style object references:
- Kept for backward compatibility
- Referenced by some older components
- Planned for removal in favor of CSS classes
- Contains color and dimension constants
- Will be deprecated as CSS-only approach matures

## Architectural Solutions

### 1. Three-Layer Security Model
**Problem**: Need secure access without compromising usability or requiring complex infrastructure
**Solution**:
- Layer 1 (Transport): TLS 1.3 with auto-generated certificates
- Layer 2 (Session): Zero-knowledge SHA-256 handshake with nonce/timestamp
- Layer 3 (Provider): Extensible AuthProvider interface for future AD/JWT
**Benefits**: Strong security, no password storage, replay protection, extensibility

### 2. Async Operation Pattern
**Problem**: Long-running filesystem operations blocking the event loop
**Solution**:
- All blocking calls wrapped in `asyncio.to_thread()`
- Operation queue with thread pool
- Frontend polling via operation IDs
- Configurable timeouts and retry logic per operation type
**Benefits**: Non-blocking API, responsive UI, graceful error handling

### 3. Modular Frontend Architecture
**Problem**: Monolithic HTML/JS difficult to maintain and extend
**Solution**:
- ES modules with explicit imports/exports
- Component-based architecture (Panels, Dialogs, Library)
- Consistent styling via CSS classes
- State lifting to application level where appropriate
- Reusable dialog patterns with shared base functionality
**Benefits**: Maintainability, testability, extensibility, clear separation of concerns

### 4. Configuration Separation
**Problem**: UI preferences mixed with operational settings
**Solution**:
- UI preferences: stored in localStorage (`nc_config` key)
- Operational settings: stored in config.json via API
- Separate dialogs: ConfigDialog (UI) vs TimeoutsDialog (operations)
- Runtime updates without restart for operational settings
**Benefits**: Clear concern separation, appropriate persistence mechanisms, live updates

### 5. Safe Path Handling
**Problem**: Path traversal vulnerabilities and cross-platform inconsistencies
**Solution**:
- Virtual File System layer with `safe_path()` function
- URL format (`/C/Users/...`) consistently used in API
- Conversion to Windows paths only at filesystem boundary
- Validation against directory traversal attempts
- Drive letter agnostic (works with any drive)
**Benefits**: Security, consistency, foundation for cross-platform support

### 6. Smart Retry Logic
**Problem**: Blind retry of all operations causing more harm than good
**Solution**:
- Classification of errors as retriable/non-retriable
- Non-retriable: PermissionError, FileNotFoundError, etc.
- Retriable: transient OSError, network issues
- Operation-specific overrides (e.g., ArchiveListOperation skips zip errors)
- Configurable retry limits per operation type
**Benets**: Efficient error handling, prevents endless retry loops, appropriate fault tolerance

### 7. Consistent UI Patterns
**Problem**: Inconsistent dialog behavior and appearance
**Solution**:
- Shared CSS classes for all dialog components
- Standardized keyboard handling (Tab, Enter, Escape)
- Consistent focus management
- Uniform layout patterns (title bar, content, footer)
- Shared utility functions for common operations
- Visual feedback for states (loading, error, success)
**Benefits**: Professional appearance, reduced cognitive friction, accessibility

### 8. Extensible Authentication
**Problem**: Need to support multiple authentication mechanisms
**Solution**:
- Abstract AuthProvider interface with clear contract
- Default ConsoleTokenProvider implementation
- Planned AD/Kerberos and JWT providers
- Middleware agnostic to specific provider implementation
- Easy registration via CLI argument
**Benefits**: Future-proof design, clear integration path, separation of concerns

### 9. Operation Progress Tracking
**Problem**: Users need feedback on long-running operations
**Solution**:
- Operation IDs returned immediately
- Polling endpoint for status updates
- Progress percentages and staged reporting
- Detailed result information on completion
- Error details and troubleshooting information
- Frontend UI components for displaying progress
**Benefits**: Transparency, user confidence, ability to cancel/monitor

### 10. Atomic Configuration Updates
**Problem**: Race conditions and corruption during config writes
**Solution**:
- Write to temporary file (.tmp)
- Validate written content
- Atomic rename/replace operation
- Thread-safe locking during write process
- Read-through cache with invalidation
- Automatic recovery from corrupted state
**Benefits**: Data integrity, crash safety, concurrent access safety

## Data Flow Patterns

### 1. Request-Response Cycle
```
Client Action → API.js function → HTTP request with auth headers
        ↓
FastAPI Route → Middleware validation → AuthProvider check
        ↓
Endpoint handler → Pydantic validation → Operation factory
        ↓
OperationQueue → Thread pool execution → VFS path conversion
        ↓
Filesystem operation → Result → Return up the chain
        ↓
HTTP response → Client processing → UI update
```

### 2. Authentication Handshake
```
Frontend startup → Check URL hash/prompt() for token
        ↓
Token storage in sessionStorage → API requests add auth headers
        ↓
Middleware validates: nonce freshness, timestamp window, signature
        ↓
AuthProvider verifies: SHA-256(nonce + timestamp + secret) == signature
        ↓
Replay protection: nonce not in USED_NONCES set
        ↓
Request proceeds OR 401 → clear session → show login dialog
```

### 3. Async Operation Lifecycle
```
User action (e.g., F5 Copy) → apiCopy() → POST /api/copy
        ↓
Endpoint creates CopyOperation → queues in OperationQueue
        ↓
Returns: {operation_id, status: "QUEUED", poll: {timeout, interval}}
        ↓
Frontend starts polling GET /api/operation/{id} every interval ms
        ↓
OperationQueue assigns to worker thread → executes run() method
        ↓
Should retry? → Check error type against _is_non_retriable()
        ↓
Filesystem operation → Success/failure with metadata
        ↓
Operation updates status → Frontend poll reflects change
        �
        Final state: COMPLETED/FAILED/CANCELLED → UI shows result
```

### 4. Configuration Update Flow
```
User changes setting in TimeoutsDialog → Validation → Save button
        ↓
apiSetConfig() → PUT /api/config with partial config
        ↓
Endpoint validates → ConfigManager.update() → saves to config.json
        ↓
Atomic write: .tmp file → validation → rename to config.json
        ↓
Subsequent operations use new config → no restart required
        ↓
UI preferences unaffected → stored separately in localStorage
```

### 5. UI State Synchronization
```
User action (e.g., change view mode) → React setState()
        ↓
useEffect with dependency → persist to localStorage
        ↓
Component re-renders with new state → immediate visual feedback
        ↓
On next startup → loadConfig() → initializes state from storage
        ↓
Cross-tab communication planned via storage events
```

## Module Dependencies

### Backend Dependencies
```
webnc/
├── main.py ← config_manager.py, logging_config.py, all api/* routers
├── api/
│   ├── files.py ← operations/files.py, config_manager.py, models/files.py
│   ├── compare.py ← operations/compare.py, config_manager.py, models/compare.py
│   ├── sync.py ← operations/syncop.py, config_manager.py, models/sync.py
│   ├── archive.py ← operations/archive.py, config_manager.py, models/files.py
│   ├── config_api.py ← config_manager.py
│   ├── exec.py ← operations/files.py (future)
│   ├── system.py ← (standalone, uses psutil/platform)
│   ├── drives.py ← (standalone, uses ctypes)
│   └── operations.py ← operations/base.py, operations/operations.py, config_manager.py
├── operations/
│   ├── base.py ← config_manager.py
│   ├── files.py ← config_manager.py
│   ├── compare.py ← config_manager.py
│   ├── syncop.py ← config_manager.py
│   └── archive.py ← config_manager.py
├── security/
│   ├── middleware.py ← auth_provider.py, console_token.py
│   ├── console_token.py ← nc_crypto.py
│   ├── auth_provider.py ← (interface)
│   ├── tls.py ← (standalone, uses cryptography)
│   └── nc_crypto.py ← (standalone)
├── vfs/
│   └── paths.py ← (standalone)
├── models/ ← (Pydantic, standalone)
├── services/ ← (planned)
├── config_manager.py ← (standalone)
├── logging_config.py ← (standalone)
└── config.py ← (constants)
```

### Frontend Dependencies
```
client/
├── index.html ← css/nc.css, js/app.js, React UMD bundles
├── css/
│   └── nc.css ← (standalone)
├── js/
│   ├── app.js ← lib/api.js, lib/utils.js, lib/config.js, components/*, dialogs/*
│   ├── components/
│   │   └── Panel.js ← lib/api.js, lib/utils.js
│   ├── dialogs/
│   │   ├── *.js ← lib/api.js, lib/utils.js, lib/config.js (where applicable)
│   └── lib/
│       ├── api.js ← (standalone, uses fetch API)
│       ├── utils.js ← (standalone)
│       └── config.js ← (standalone, uses localStorage)
```

## Extension Guidelines

### Adding New Backend Operations
1. Create new class in `webnc/operations/` inheriting from `BaseOperation`
2. Implement `run()` method with core logic
3. Override `should_retry()` if needed for specific error handling
4. Set `op_config_key` class attribute for configuration lookup
5. Add Pydantic model in `webnc/models/` if needed for request/response
6. Create API endpoint in appropriate `webnc/api/*` file
7. Register router in `main.py`
8. Add defaults to `ConfigManager.OPERATION_DEFAULTS`
9. Create corresponding frontend API function in `client/js/lib/api.js`
10. Add UI component/dialog as needed in `client/js/dialogs/`

### Adding New Frontend Components
1. Create new ES module in `client/js/dialogs/` or `client/js/components/`
2. Follow existing patterns for styling, keyboard handling, focus management
3. Use `api.js` functions for backend communication
4. Connect to state in `app.js` via props or context (planned)
5. Add menu item if applicable in `app.js` menu handlers
6. Add CSS classes to `client/css/nc.css` if needed
7. Export from `client/js/dialogs/index.js` barrel if it's a dialog
8. Add localization strings if needed (planned)
9. Write JSDoc comments for maintainability

### Adding New Authentication Providers
1. Create new class in `webnc/security/` implementing `AuthProvider`
2. Implement `authenticate(request) -> Optional[UserInfo]`
3. Implement `authorize(user: UserInfo, permission: str) -> bool`
4. Add CLI argument handling in `main.py` or `webnc_server.py`
5. Register provider in auth middleware selection logic
6. Update documentation in README and docs/SECURITY.md
7. Add any required dependencies to requirements.txt
8. Consider token storage requirements (RAM vs persistent)
9. Test with various client scenarios (new, expired, invalid tokens)

### Adding New VFS Providers
1. Create new module in `webnc/vfs/` (e.g., `sftp_provider.py`)
2. Implement path conversion functions if needed
3. Extend or replace existing path handling logic
4. Ensure security validations are maintained
5. Update API layer to use new provider where appropriate
6. Test with various path formats and edge cases
7. Consider performance implications and caching strategies
8. Document limitations and requirements

## Code Quality Standards

### Python Backend
- **Type Hints**: Full type annotation using Python 3.9+ syntax
- **Docstrings**: Google-style docstrings for all public functions/classes
- **Line Length**: Maximum 100 characters (flexible for docstrings)
- **Imports**: Standard library → third-party → local applications
- **Naming**: snake_case for variables/functions, PascalCase for classes
- **Constants**: UPPER_SNAKE_CASE in `config.py` or module level
- **Error Handling**: Specific exception catching, never bare `except:`
- **Logging**: Appropriate log levels (DEBUG, INFO, WARNING, ERROR)
- **Security**: Security considerations in docstrings for sensitive functions
- **Testing**: Unit tests planned for all public interfaces

### JavaScript Frontend
- **ES Modules**: Standard import/export syntax
- **Naming**: camelCase for variables/functions, PascalCase for components
- **Constants**: UPPER_SNAKE_CASE at module level
- **JSx Alternative**: Using `const h = React.createElement` for consistency
- **React Hooks**: Proper use of useState, useEffect, useContext
- **Event Handling**: Synthetic events, prevention of defaults where needed
- **State Management**: Lifting state up when shared between components
- **Performance**: Keys on lists, memoization where beneficial
- **Accessibility**: ARIA labels, focus management, keyboard navigation
- **Browser Compatibility**: Targeting modern browsers (ES2020+)
- **Code Formatting**: Consistent formatting via prettier (planned)
- **Linting**: ESLint with React rules (planned)

### Documentation Standards
- **Markdown**: GitHub-flavored markdown
- **Code Fences**: Syntax highlighting for language-specific blocks
- **Links**: Relative links for internal resources, absolute for external
- **Images**: Planned for architectural diagrams
- **Versioning**: Documentation updated with each release
- **Examples**: Concrete examples for API endpoints and usage patterns
- **Tutorials**: Step-by-step guides planned for common tasks
- **Reference**: Complete API reference maintained in API_REFERENCE.md

## Build and Deployment

### Development Setup
```bash
# Clone repository
git clone <repository-url>
cd WebNC

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install cryptography  # for certificate generation

# Run in development mode
py webnc_server.py --reload
# or
.\run.bat
```

### Production Deployment
```bash
# Standard production run
.\run.bat  # HTTPS enabled by default

# For HTTP only (debugging)
.\run.bat --insecure

# With custom certificate
py webnc_server.py --cert mycert.key --key mykey.key

# Specify host/port
py webnc_server.py --host 0.0.0.0 --port 8080

# Enable auto-reload development mode
py webnc_server.py --reload
```

### Environment Variables
Currently no environment variables used. Configuration via:
- Command line arguments (`webnc_server.py --help`)
- Runtime API (`/api/config` endpoint)
- Frontend localStorage (`nc_config` key)
- File-based config (`config/config.json`)

### Process Management
- Uses `manage_server.ps1` for start/stop/restart/status/monitor
- CMD wrapper available via `run.bat`
- Health checking with auto-restart on failure
- PID file tracking for process management
- Log rotation prevents unbounded disk growth
- Graceful shutdown handling for in-flight operations

### Reverse Proxy Configuration
When deployed behind a reverse proxy (NGINX, Apache, etc.):
```nginx
# Example NGINX configuration
server {
    listen 443 ssl;
    server_name webnc.example.com;
    
    # SSL settings
    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;
    ssl_protocols TLSv1.3;
    ssl_prefer_server_ciphers on;
    
    # Proxy settings
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (if added in future)
        # proxy_set_header Upgrade $http_upgrade;
        # proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

## Migration Guides

### From Web Norton Commander to WebNC
1. **Name Changes**: All references updated from "Web Norton Commander" to "WebNC"
2. **Configuration**: New `config.json` structure, old formats not supported
3. **API Endpoints**: Enhanced with additional fields and better validation
4. **Security Model**: Added three-layer security with stronger defaults
5. **UI Improvements**: Redesigned dialogs, better consistency, accessibility
6. **Operation System**: Replaced synchronous queuing with thread pool + polling
7. **Frontend Architecture**: Modular ES modules replacing monolithic HTML/JS
8. **Logging**: Enhanced structured logging with rotation

### Version-Specific Migrations
Specific migration paths will be documented in `History.md` and release notes as the project evolves.

## Troubleshooting Common Issues

### Development Issues
- **Missing dependencies**: Ensure `cryptography` installed for certificate generation
- **Port already in use**: Check for existing processes on port 8000
- **Certificate errors**: Delete `nc_server.crt` and `nc_server.key` to regenerate
- **Authentication failures**: Clear browser storage or use new token from console
- **Frontend not updating**: Hard refresh (Ctrl+F5) to bypass caching
- **Syntax errors**: Check browser console for ES module loading issues

### Production Issues
- **Server hangs**: Check for blocking filesystem calls not wrapped in threads
- **Memory growth**: Monitor operation queue size and log rotation
- **Certificate expiration**: Automatic every 10 years or manual deletion triggers renewal
- **Performance degradation**: Check thread pool utilization and disk I/O
- **Authentication lockout**: Server restart generates new token; old tokens become invalid
- **Network timeouts**: Adjust proxy timeouts if behind reverse proxy
- **Disk space full**: Monitor log rotation and configured retention policy

### Known Limitations
- **Windows-only**: Current implementation relies on Win32 APIs
- **Single-user focus**: Designed for admin use, not multi-user collaboration
- **No offline mode**: Requires persistent backend connection
- **Limited media preview**: Only text files <64KB viewable inline
- **Clipboard integration**: Planned but not yet implemented
- **Drag-and-drop**: Planned for future implementation
- **Terminal emulation**: Ctrl+O terminal planned but not implemented

## Future Directions

### Planned Architectural Improvements
1. **Complete VFS Abstraction**: SFTP/FTP, cloud storage, network providers
2. **WebSocket Implementation**: Real-time updates instead of polling
3. **Plugin System**: Dynamic loading of extensions and providers
4. **Event-Driven Architecture**: Better decoupling of components
5. **Microservice Options**: Potential for service decomposition
6. **Enhanced Caching**: Intelligent result caching for performance

### Feature Roadmap Highlights
1. **Role-Based Access Control**: Per-user/per-module permissions
2. **Audit Logging**: Comprehensive file operation tracking
3. **Background Operations**: Progress bars and cancel functionality
4. **Media Previews**: Image, video, and text file previews
5. **Clipboard Integration**: Copy/paste between WebNC and system
6. **Terminal Emulation**: Full terminal access via Ctrl+O
7. **Drag-and-Drop**: File upload via drag-and-drop interface
8. **Extended Archive Support**: Creation and extraction, not just listing
9. **Search Enhancements**: Saved searches, search-as-you-type
10. **Configuration Profiles**: Export/import of UI and operation settings

This documentation provides a comprehensive overview of the WebNC codebase structure, architectural decisions, and extension guidelines. For the most current information, please refer to the `History.md` file which contains detailed development progress.
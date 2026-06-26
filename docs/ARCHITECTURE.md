# WebNC Architecture

## Overview
WebNC is a local-first, keyboard-driven, two-panel file manager for Windows with a FastAPI backend and React frontend. It follows a modular architecture designed for extensibility, security, and performance.

## High-Level Architecture

```
┌─────────────────┐    HTTP/HTTPS    ┌──────────────────┐
│   Frontend      │ ◀──────────────▶ │   Backend (FastAPI)  │
│   (React)       │                  │                    │
└─────────────────┘                  └─────────┬──────────┘
                                                │
                                                ▼
                                    ┌────────────────────┐
                                    │   VFS Layer          │
                                    │ (Virtual File System)│
                                    └─────────┬──────────┘
                                              │
                                              ▼
                                    ┌────────────────────┐
                                    │   Operation Queue    │
                                    │ (Thread Pool + Async)│
                                    └─────────┬──────────┘
                                              │
                                              ▼
                                    ┌────────────────────┐
                                    │   Filesystem Access  │
                                    │   (Windows API)      │
                                    └────────────────────┘
```

## Core Modules

### Backend (`webnc/` package)

#### 1. Application Entry (`main.py`)
- FastAPI application factory
- Middleware registration (authentication, logging)
- Router mounting for all API endpoints
- Configuration manager initialization
- SSL/TLS context setup
- Custom `log_config` passed to `uvicorn.run()` for consistent logging format

#### 2. API Layer (`webnc/api/`)
- RESTful endpoint implementations
- Request validation using Pydantic models
- Response formatting
- Error handling
- Modules:
  - `files.py`: File operations (copy, move, delete, etc.)
  - `compare.py`: Directory comparison
  - `sync.py`: Directory synchronization
  - `archive.py`: Archive listing
  - `config_api.py`: Configuration endpoints
  - `exec.py`: Command execution
  - `system.py`: System information
  - `drives.py`: Drive listing
  - `operations.py`: Operation status polling
  - `static.py`: Frontend static file serving

#### 3. Operations Layer (`webnc/operations/`)
- Abstract base class for all operations
- Thread-safe execution with retry logic
- Specific operation implementations:
  - `base.py`: AbstractOperation with retry/timeout logic
  - `files.py`: File operation classes (Copy, Move, Delete, etc.)
  - `compare.py`: CompareOperation
  - `syncop.py`: SyncPlanOperation, SyncExecuteOperation
  - `archive.py`: ArchiveListOperation
  - `queue.py`: OperationQueue managing thread pool
  - `system.py`: System operation classes

#### 4. Security Layer (`webnc/security/`)
- Authentication providers and middleware
- TLS/SSL certificate generation
- Request signing and verification
- Token printed to stderr only (not logger) to prevent token leakage to log files
- Modules:
  - `auth_provider.py`: AuthProvider interface definition
  - `console_token.py`: ConsoleTokenProvider (default)
  - `middleware.py`: SessionAuthMiddleware
  - `tls.py`: TLS certificate generation and context creation
  - `nc_crypto.py`: Cryptographic utilities
  - `_state.py`: Auth provider state management

#### 5. Virtual File System (`webnc/vfs/`)
- Path sanitization and conversion
- Safe path resolution to prevent directory traversal
- Modules:
  - `paths.py`: safe_path and relative_path conversion functions

#### 6. Configuration (`webnc/config_manager.py`)
- Thread-safe JSON configuration management
- Atomic file writes using temporary files
- Default values for operation timeouts and retries
- Runtime configuration updates via API

#### 7. Logging (`webnc/logging_config.py`)
- Rotating file handler (5MB × 3 backups)
- Standard error output
- Structured log format: `%(asctime)s | %(levelname)-8s | %(message)s`

#### 8. Models (`webnc/models/`)
- Pydantic models for request/response validation
- Shared data structures
- Modules:
  - `files.py`: File operation models
  - `sync.py`: Synchronization models
  - `compare.py`: Comparison models
  - `auth.py`: Authentication models
  - `state.py`: Application state models

#### 4. Services (`webnc/services/`)
- Business logic layer with platform abstraction
- `FileService` ABC: 14 abstract methods for all filesystem operations
- `WindowsFileService`: Windows-specific implementation (ctypes, mklink, permissions)
- Future: `LinuxFileService` for cross-platform support
- Global singleton in `main.py`, injected into API via `Depends(get_file_service)`

### Frontend (`client/` directory)

#### 1. Entry Point (`index.html`)
- Loads React UMD bundles
- Initializes ES module application
- Links to stylesheet

#### 2. Styles (`css/nc.css`)
- Norton Commander theme styling
- Semantic CSS classes for consistent UI
- Responsive layout definitions

#### 3. Application (`js/app.js`)
- Main NortonCommander React component
- State management for panels, dialogs, and UI
- Event handlers for keyboard shortcuts
- Menu system integration
- Dialog orchestration
- Terminal/command input area (scrollable output, cmdHistory)
- `activeTarget` state (`"panels"` | `"terminal"`) — keyboard goes exclusively to the active target
- Tab cycles: left panel → right panel → terminal → left panel
- Ctrl+O hides panels → auto-switches to terminal; shows panels → switches back
- Fullscreen toggle via `document.documentElement.requestFullscreen()` (F11)
- Configurable keyboard shortcuts via ACTION dispatch map (reads `keybindings` from config)

#### 4. Components (`js/components/`)
- `Panel.js`: File panel with all view modes (Brief, Full, Quick, Info, Tree, Search)

#### 5. Dialogs (`js/dialogs/`)
- All modal dialogs as separate ES modules:
  - `SyncDialog.js`: Directory synchronization (Total Commander style)
  - `CompareDialog.js`: Directory comparison
  - `EditorDialog.js`: In-browser file editor
  - `SearchDialog.js`: File search
  - `TreeDialog.js`: Full-screen NDC directory tree (lazy-load, arrow-key nav, Enter expand→select)
  - `ArchiveDialog.js`: Archive viewing
  - `ConfigDialog.js`: UI preferences
  - `TimeoutsDialog.js`: Operation timeout/retry configuration
  - `DriveDialog.js`: Drive selection
  - `InfoDialog.js`: File/directory information
  - `HistoryDialog.js`: Navigation history
  - `HelpDialog.js`: Keyboard shortcut reference
  - `SysInfoDialog.js`: System information
  - `LoginDialog.js`: Session token entry
  - `SimpleDialogs.js`: File viewer, confirm, input dialogs

#### 6. Library (`js/lib/`)
- `api.js`: API client functions + operation polling
- `utils.js`: Formatting utilities (file sizes, dates, colors)
- `config.js`: LocalStorage configuration management
- `styles.js`: Legacy style object references

## Data Flow

### 1. Request Processing Flow
```
Frontend Request
        ↓
[API Client] → Adds auth headers (nonce, timestamp, signature)
        ↓
HTTP/HTTPS Request to Backend
        ↓
[FastAPI] → Route matching
        ↓
[SessionAuthMiddleware] → Validates auth headers
        ↓
[AuthProvider] → Authenticates request (ConsoleTokenProvider default)
        ↓
[API Endpoint] → Validates request (Pydantic models)
        ↓
[Operation Factory] → Creates operation instance
        ↓
[OperationQueue] → For async: queues in thread pool
                   → For sync: runs directly via run_sync()
        ↓
[Thread Pool] → Executes operation (wrapped in asyncio.to_thread)
        ↓
[VFS Layer] → Safe path conversion (/C/Users → C:\Users)
        ↓
[Filesystem Access] → Windows API calls via ctypes/std lib
        ↓
[Result] → Returned through same chain in reverse
```

### 2. Authentication Flow
```
Frontend
        ↓
[LoginDialog] → Gets token from URL or prompt()
        ↓
[API Request] → Adds X-NC-Nonce, X-NC-Timestamp, X-NC-Signature
        ↓
[SessionAuthMiddleware] → Extracts and validates headers
        ↓
[ConsoleTokenProvider] → Verifies SHA-256(nonce + timestamp + secret)
        ↓
[Replay Protection] → Checks nonce against USED_NONCES set
        ↓
[Timestamp Window] → Verifies |now - ts| < 300 seconds
        ↓
[Request Processing] → Continues if all checks pass
        ↓
[Invalid Request] → Returns 401, triggers logout() and login prompt
```

### 3. Operation Execution Flow
```
Frontend Action (e.g., F5 Copy)
        ↓
[API Client] → Calls apiCopy(source, destination)
        ↓
[POST /api/copy] → Validates request
        ↓
[CopyOperation] → Created with parameters
        ↓
[OperationQueue.add_operation()] → Queues operation
        ↓
[Returns] → {operation_id, status: "QUEUED", poll: {timeout, interval}}
        ↓
[Frontend] → Starts polling GET /api/operation/{id}
        ↓
[OperationQueue] → Processes operation from queue
        ↓
[Thread Pool] → Executes CopyOperation.run()
        ↓
[FileService] → Delegates to WindowsFileService.copy()
        ↓
[Filesystem Access] → Performs copy via shutil.copy2()
        ↓
[Result] → Success/Failure with metadata
        ↓
[Polling Response] → Updated status and progress
        ↓
[Frontend UI] → Updates operation status display
```

### 4. `.` and `..` Navigation
- Frontend adds `.` and `..` entries to directory listings (not backend)
- `.` renders as `[.]` / `ROOT`, navigates to drive root
- `..` renders as `↑..` / `UP--DIR`, navigates to parent directory
- Both marked `_isParent: true` to skip selection/copy/delete operations
- Hidden at drive root (no `parent` field in response)

## Key Architectural Decisions

### 1. Three-Layer Security
- **Transport Layer**: TLS 1.3 with RSA-4096 certificates (hardened SSL context)
- **Session Layer**: Zero-knowledge SHA-256 handshake with nonce/timestamp
- **Provider Layer**: Extensible AuthProvider interface for AD/Kerberos/JWT

### 2. Threading Model
- All blocking filesystem operations wrapped in `asyncio.to_thread()`
- Prevents event loop blocking and server hangs
- Configurable thread pool size in OperationQueue
- Smart retry logic distinguishes retriable vs non-retriable errors

### 2.1 Windows Event Loop
- `WindowsProactorEventLoopPolicy` required for `asyncio.create_subprocess_shell` (exec endpoint)
- `SelectorEventLoop` raises `NotImplementedError` on Windows for subprocess creation
- Monkey-patched `new_event_loop` installs `ConnectionResetError` exception handler to prevent crashes on client disconnect

### 3. Modular Design
- Clear separation of concerns: API → Operations → VFS → FS
- Dependency injection for configuration and logging
- Pluggable authentication providers
- Extensible VFS layer for future network/storage providers

### 4. Configuration Management
- Runtime configuration via API (`/config` endpoints)
- Thread-safe JSON file storage with atomic writes
- Separate UI preferences (localStorage) and operation settings (config.json)
- Defaults with live updating capability

### 5. Frontend-Backend Communication
- RESTful JSON API with standard HTTP methods
- Operation ID pattern for async tasks
- Polling-based status updates (no WebSockets for simplicity)
- Consistent error formatting
- CORS enabled with `allow_origins=["*"]` (same-origin in production via FastAPI static serving)

### 6. Windows Integration
- Native path handling (`/C/Users/...` ↔ `C:\Users\...`)
- Win32 API calls for file ownership and drive information
- ctypes usage for low-level Windows interactions
- Proper error handling for Windows-specific issues

## Performance Considerations

### 1. Blocking Operations
- All filesystem calls moved to thread pool
- Non-blocking API endpoints maintain responsiveness
- Configurable timeouts prevent hanging operations

### 2. Caching
- No built-in caching (designed for real-time filesystem access)
- Frontend maintains view state to reduce redundant requests
- Operation results cached temporarily for polling

### 3. Memory Management
- Rotating logs prevent unbounded disk growth
- Ephemeral authentication tokens minimize memory footprint
- Operation queue prevents unbounded memory growth
- Frontend uses React's efficient reconciliation

### 4. Network Efficiency
- Minimal payload sizes
- Compression enabled via uvicorn
- Efficient JSON serialization
- Batched operations where applicable

## Security Considerations

### 1. Authentication
- Ephemeral tokens prevent replay attacks
- Nonce + timestamp + SHA-256 prevents man-in-the-middle
- Constant-time comparison prevents timing attacks
- Short token lifetime (5 minutes) limits exposure

### 2. Authorization
- AuthProvider interface enables future RBAC
- Module registry allows feature flags per user/role
- Currently all authenticated users have full access
- `/api/health`, `/api/drives`, `/api/disk` exempted for usability

### 3. Filesystem Access
- No sandbox - designed for trusted admin use
- Path validation prevents directory traversal
- Permission errors logged but don't fail operations
- Owner information retrieved via Win32 API only when needed

### 4. Transport Security
- TLS 1.3 only (no fallback to weaker versions)
- CRIME/BREACH protection via OP_NO_COMPRESSION
- Server-preferred cipher ordering
- Certificate auto-generation with proper SAN
- For older systems that do not support TLS 1.3, you can downgrade to TLS 1.2 at your own risk by changing `ctx.minimum_version` in `webnc/main.py`

### 5. Audit and Compliance
- Comprehensive logging of all API calls
- Warning logs for swallowed exceptions
- No sensitive data stored in logs
- Planned audit log feature for file operations

## Extensibility Points

### 1. Authentication Providers
- Implement `AuthProvider` interface
- Register via `--auth` CLI argument
- Examples planned: AD/Kerberos, JWT, LDAP

### 2. Virtual File System
- Extend `webnc/vfs/` with new providers
- Implement SFTP/FTP, cloud storage, etc.
- Maintain same path interface (`/C/Users/...`)

### 3. Operations
- Subclass `AbstractOperation` for new operation types
- Register in `webnc/operations/` directory
- Automatically available via API
- Built-in: Copy, Move, Rename, Mkdir, Link, Delete, BatchDelete, Search, List, View, Write, Download, Upload, FileInfo, Tree

### 4. Frontend Components
- Add new dialogs in `js/dialogs/`
- Add new view modes in `Panel.js`
- Extend menu system in `app.js`
- Reuse existing API client patterns

### 5. Configuration
- Add new operation types to `ConfigManager.OPERATION_DEFAULTS`
- Extend `config.json` schema
- Frontend dialogs automatically adapt to new operations

## Deployment Architecture

### Development Mode
```
$ py webnc_server.py --reload
```
- Auto-reload enabled
- Debug logging
- HTTP or HTTPS based on flags

### Production Mode
```
$ .\run.bat
```
- HTTPS enabled by default
- Self-signed certificate auto-generated
- Health check monitoring with auto-restart
- Log rotation active

### Containerized (Planned)
```
# Future Docker support
FROM python:3.9-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 8000
CMD ["py", "webnc_server.py", "--host", "0.0.0.0"]
```

### Reverse Proxy (Future)
```
# Example Nginx configuration
server {
    listen 443 ssl;
    server_name webnc.example.com;
    
    ssl_certificate /path/to/cert.crt;
    ssl_certificate_key /path/to/key.key;
    ssl_protocols TLSv1.3;
    ssl_prefer_server_ciphers on;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Monitoring and Observability

### 1. Logging
- Structured logs with timestamps and levels
- Rotating file handlers prevent disk exhaustion
- All API calls logged at INFO level
- Errors and warnings captured with stack traces

### 2. Health Checks
- `/api/health` endpoint for liveness probing
- Database connectivity (when added)
- Disk space checks
- Thread pool status

### 3. Metrics (Planned)
- Operation success/failure rates
- Average operation durations
- Active operation counts
- Memory and CPU usage

### 4. Alerting (Planned)
- Failed operation thresholds
- Health check failures
- Authentication failure rates
- Disk space warnings

## Limitations and Constraints

### 1. Platform Specific
- Currently Windows-only due to Win32 API usage
- Path handling assumes Windows drive letters
- Future VFS abstraction layer planned for cross-platform

### 2. Authentication Scope
- Current implementation provides all-or-nothing access
- Planned RBAC for fine-grained permissions
- No built-in user management (designed for single admin use)

### 3. Real-time Updates
- Polling-based rather than push-based
- Configurable polling intervals balance responsiveness vs load
- No WebSocket implementation to simplify deployment

### 4. Offline Capabilities
- Requires persistent backend connection
- No offline mode or conflict resolution planned
- Designed for always-connected admin use cases

### 5. Scale
- Designed for single-user or small team use
- Not optimized for thousands of concurrent users
- Thread pool limits concurrent operations
- Memory usage scales with open files and operation history

## Future Improvements

### 1. Architectural
- Complete VFS abstraction layer for cross-platform support
- Plugin system for extensibility
- Event-driven architecture with WebSockets
- Microservice decomposition options

### 2. Features
- Role-Based Access Control (RBAC)
- Audit logging for all file operations
- Background operations with progress/cancel UI
- Drag-and-drop file upload
- Media previews (images, text, video)
- Clipboard integration
- Terminal emulation (Ctrl+O)

### 3. Performance
- Adaptive thread pool sizing
- Operation result caching
- Frontend virtual scrolling for large directories
- WebSocket implementation for real-time updates

### 4. Security
- Integration with enterprise identity providers
- Detailed audit logs with tamper evidence
- Session persistence options
- Detailed permission models

### 5. DevOps
- Official Docker images
- Kubernetes deployment manifests
- Comprehensive monitoring dashboards
- Automated backup and restore utilities
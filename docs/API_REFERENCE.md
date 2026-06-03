# WebNC API Reference

## Overview
WebNC provides a RESTful API for file management operations. All API endpoints are prefixed with `/api/` and return JSON responses unless otherwise specified.

## Authentication
WebNC uses a three-layer security model:
1. TLS 1.3 transport encryption
2. Zero-knowledge session authentication (SHA-256 handshake)
3. Extensible AuthProvider interface

Authentication tokens are ephemeral and regenerated on each server startup. All API requests (except `/api/health`, `/api/drives`, and `/api/disk`) require authentication via:
- `X-NC-Nonce`: Random nonce value
- `X-NC-Timestamp`: Current timestamp
- `X-NC-Signature`: SHA-256 hash of nonce + timestamp + secret token

## Filesystem Endpoints

### GET /api/list
Retrieve directory listing with sorting, filtering, and visibility options.

**Query Parameters:**
- `path` (string, required): Directory path in URL format (e.g., `/C/Users/`)
- `sort_by` (string, optional): Sort field (`name`, `extension`, `modified`, `size`, `unsorted`). Default: `name`
- `sort_dir` (string, optional): Sort direction (`asc`, `desc`). Default: `asc`
- `filter` (string, optional): FNMatch pattern for filtering (e.g., `*.txt`)
- `show_hidden` (boolean, optional): Whether to show hidden files. Default: false

**Response:**
```json
{
  "path": "/C/Users/",
  "items": [
    {
      "name": "example.txt",
      "path": "/C/Users/example.txt",
      "type": "file",
      "size": 1024,
      "modified": "2026-05-30 14:30:00",
      "hidden": false
    }
  ],
  "total": 1
}
```

**Error Responses:**
- 400: Invalid path or parameters
- 401: Authentication required
- 403: Access denied
- 404: Path not found
- 500: Internal server error

### GET /api/view
Retrieve file content (text files under 64KB, or under `max_edit_size` for editing).

**Query Parameters:**
- `path` (string, required): File path in URL format
- `encoding` (string, optional): Text encoding. Default: `utf-8`
- `for_edit` (boolean, optional): If true, check `max_edit_size` limit. Default: false

**Response:**
```json
{
  "path": "/C/Users/example.txt",
  "content": "Hello, World!",
  "size": 13,
  "is_binary": false
}
```

**Error Responses:**
- 400: Invalid path or file too large
- 401: Authentication required
- 403: Access denied
- 404: File not found
- 413: File too large (when `for_edit=true` and exceeds `max_edit_size`)
- 415: Unsupported media type (binary file)
- 500: Internal server error

### GET /api/info
Get file or directory details including owner information and disk usage.

**Query Parameters:**
- `path` (string, required): Path in URL format

**Response:**
```json
{
  "path": "/C/Users/example.txt",
  "name": "example.txt",
  "type": "file",
  "size": 1024,
  "created": "2026-05-30 10:00:00",
  "modified": "2026-05-30 14:30:00",
  "owner": "DOMAIN\\Username",
  "permissions": "rwxr-xr-x",
  "disk": {
    "total": 100000000000,
    "free": 50000000000,
    "used": 50000000000,
    "percent_used": 50
  }
}
```

**Error Responses:**
- 400: Invalid path
- 401: Authentication required
- 403: Access denied
- 404: Path not found
- 500: Internal server error

### GET /api/disk
Get disk usage for a path.

**Query Parameters:**
- `path` (string, required): Path in URL format

**Response:**
```json
{
  "path": "/C/",
  "total": 100000000000,
  "free": 50000000000,
  "used": 50000000000,
  "percent_used": 50
}
```

**Error Responses:**
- 400: Invalid path
- 401: Authentication required
- 403: Access denied
- 404: Path not found
- 500: Internal server error

### GET /api/drives
List available drives with labels and usage information.

**Response:**
```json
{
  "drives": [
    {
      "letter": "C",
      "label": "Windows",
      "filesystem": "NTFS",
      "total": 100000000000,
      "free": 50000000000,
      "used": 50000000000,
      "percent_used": 50
    }
  ]
}
```

**Error Responses:**
- 401: Authentication required
- 500: Internal server error

### GET /api/tree
Get directory tree structure (lazy-loaded).

**Query Parameters:**
- `path` (string, required): Directory path in URL format

**Response:**
```json
{
  "path": "/C/Users/",
  "tree": [
    {
      "name": "Documents",
      "path": "/C/Users/Documents/",
      "type": "directory",
      "children": [
        {
          "name": "report.docx",
          "path": "/C/Users/Documents/report.docx",
          "type": "file"
        }
      ]
    }
  ]
}
```

**Error Responses:**
- 400: Invalid path
- 401: Authentication required
- 403: Access denied
- 404: Path not found
- 500: Internal server error

### POST /api/search
Search for files using glob or regex patterns (async operation).

**Request Body:**
```json
{
  "path": "/C/",
  "pattern": "*.txt",
  "max_results": 200
}
```

**Response:**
```json
{
  "operation_id": "op_1234567890abcdef",
  "status": "QUEUED",
  "poll": {
    "timeout": 120,
    "interval": 300
  }
}
```

**Error Responses:**
- 400: Invalid parameters
- 401: Authentication required
- 403: Access denied
- 500: Internal server error

### POST /api/edit
Save file content (synchronous operation, text files only).

**Request Body:**
```json
{
  "path": "/C/Users/example.txt",
  "content": "Hello, World!"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Saved /C/Users/example.txt",
  "path": "/C/Users/example.txt"
}
```

**Error Responses:**
- 400: Invalid path
- 401: Authentication required
- 403: Access denied
- 413: File too large (exceeds `max_edit_size` from config)
- 500: Internal server error

### GET /api/download
Download a file (returns binary content).

**Query Parameters:**
- `path` (string, required): File path in URL format

**Response:** Binary file content with `Content-Disposition: attachment` header.

**Error Responses:**
- 400: Invalid path
- 401: Authentication required
- 403: Access denied
- 404: File not found
- 500: Internal server error

### POST /api/upload
Upload a file to a destination directory (multipart/form-data).

**Request:**
- `dest_dir` (query, optional): Destination directory path (default: `/`)
- `file` (form data, required): File to upload (max 100 MB)

**Response:**
```json
{
  "success": true,
  "message": "Uploaded example.txt",
  "path": "/C/Users/example.txt"
}
```

**Error Responses:**
- 400: Invalid destination
- 401: Authentication required
- 403: Access denied
- 413: File too large (exceeds 100 MB limit)
- 500: Internal server error

### POST /api/exec
Execute a shell command on the server (synchronous, 30s timeout).

**Request Body:**
```json
{
  "command": "dir C:\\Users",
  "cwd": "/C/Users"
}
```

**Response:**
```json
{
  "stdout": " Volume in drive C has no label.\n Directory of C:\\Users\n...",
  "stderr": "",
  "returncode": 0
}
```

**Notes:**
- stdout/stderr decoded with fallback chain: UTF-8 → CP866 (OEM) → CP1251 (ANSI) → CP437 → Latin-1
- Commands checked against `exec.allowed_commands` (whitelist) and `exec.denied_commands` (blacklist) in config
- Default denied: `format`, `diskpart`, `shutdown`, `reg.exe`

**Error Responses:**
- 400: Empty command or command not found
- 403: Command is denied (see `exec.denied_commands` in config)
- 408: Command timed out (30s limit)
- 500: Internal server error

### POST /api/copy
Copy file or directory (async operation).

**Request Body:**
```json
{
  "src": "/C/Users/example.txt",
  "dest": "/D/Backup/"
}
```

**Response:**
```json
{
  "operation_id": "op_1234567890abcdef",
  "status": "QUEUED",
  "poll": {
    "timeout": 600,
    "interval": 500
  }
}
```

**Error Responses:**
- 400: Invalid source or destination
- 401: Authentication required
- 403: Access denied
- 409: Conflict (destination exists)
- 500: Internal server error

### POST /api/move
Move file or directory (async operation).

**Request Body:**
```json
{
  "src": "/C/Users/example.txt",
  "dest": "/D/Backup/"
}
```

**Response:**
```json
{
  "operation_id": "op_1234567890abcdef",
  "status": "QUEUED",
  "poll": {
    "timeout": 600,
    "interval": 500
  }
}
```

**Error Responses:**
- 400: Invalid source or destination
- 401: Authentication required
- 403: Access denied
- 409: Conflict (destination exists)
- 500: Internal server error

### POST /api/rename
Rename file or directory (synchronous operation).

**Request Body:**
```json
{
  "path": "/C/Users/example.txt",
  "new_name": "renamed.txt"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Renamed → renamed.txt",
  "path": "/C/Users/renamed.txt"
}
```

**Error Responses:**
- 400: Invalid source or destination
- 401: Authentication required
- 403: Access denied
- 409: Conflict (destination exists)
- 500: Internal server error

### POST /api/mkdir
Create directory (synchronous operation).

**Request Body:**
```json
{
  "path": "/C/Users/NewFolder/"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Created /C/Users/NewFolder/",
  "path": "/C/Users/NewFolder/"
}
```

**Error Responses:**
- 400: Invalid path
- 401: Authentication required
- 403: Access denied
- 409: Conflict (directory exists)
- 500: Internal server error

### POST /api/delete
Delete file or directory (synchronous operation).

**Request Body:**
```json
{
  "path": "/C/Users/example.txt",
  "recursive": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Deleted /C/Users/example.txt"
}
```

**Error Responses:**
- 400: Invalid path
- 401: Authentication required
- 403: Access denied
- 404: Path not found
- 500: Internal server error

### POST /api/batch-delete
Delete multiple files or directories (async operation).

**Request Body:**
```json
{
  "paths": [
    "/C/Users/file1.txt",
    "/C/Users/file2.txt"
  ],
  "recursive": false
}
```

**Response:**
```json
{
  "operation_id": "op_1234567890abcdef",
  "status": "QUEUED",
  "poll": {
    "timeout": 120,
    "interval": 300
  }
}
```

**Error Responses:**
- 400: Invalid paths
- 401: Authentication required
- 403: Access denied
- 404: One or more paths not found
- 500: Internal server error

### GET /api/compare
Compare two directories (async operation).

**Query Parameters:**
- `left` (string, required): Left directory path in URL format
- `right` (string, required): Right directory path in URL format

**Response:**
```json
{
  "operation_id": "op_1234567890abcdef",
  "status": "QUEUED",
  "message": "Compare operation queued"
}
```

**Error Responses:**
- 400: Invalid paths
- 401: Authentication required
- 403: Access denied
- 404: One or more paths not found
- 500: Internal server error

### GET /api/sync/plan
Generate synchronization plan (async operation).

**Query Parameters:**
- `left` (string, required): Left directory path in URL format
- `right` (string, required): Right directory path in URL format
- `subdirs` (boolean, optional): Include subdirectories. Default: true
- `by_content` (boolean, optional): Compare by content. Default: false
- `ignore_date` (boolean, optional): Ignore modification dates. Default: false
- `asymmetric` (boolean, optional): Allow asymmetric operations. Default: false
- `filter` (string, optional): FNMatch pattern for filtering

**Response:**
```json
{
  "operation_id": "op_1234567890abcdef",
  "status": "QUEUED",
  "message": "Sync plan operation queued"
}
```

**Error Responses:**
- 400: Invalid parameters
- 401: Authentication required
- 403: Access denied
- 404: One or more paths not found
- 500: Internal server error

### POST /api/sync/execute
Execute synchronization actions (async operation).

**Request Body:**
```json
{
  "left": "/C/Users/",
  "right": "/D/Backup/",
  "actions": [
    {
      "name": "Documents/",
      "action": "copy_left_to_right"
    }
  ]
}
```

**Response:**
```json
{
  "operation_id": "op_1234567890abcdef",
  "status": "QUEUED",
  "message": "Sync execute operation queued"
}
```

**Error Responses:**
- 400: Invalid parameters
- 401: Authentication required
- 403: Access denied
- 404: One or more paths not found
- 500: Internal server error

### GET /api/archive/list
List contents of archive files (ZIP, TAR, etc.) (async operation).

**Query Parameters:**
- `path` (string, required): Archive file path in URL format
- `password` (string, optional): Password for encrypted archives

**Response:**
```json
{
  "operation_id": "op_1234567890abcdef",
  "status": "QUEUED",
  "message": "Archive list operation queued"
}
```

**Error Responses:**
- 400: Invalid path
- 401: Authentication required
- 403: Access denied
- 404: Archive not found
- 401: Password required or incorrect (for encrypted archives)
- 500: Internal server error

## Operations Endpoints

### GET /api/operation/{id}
Poll operation status.

**Path Parameters:**
- `id` (string, required): Operation ID

**Response:**
```json
{
  "operation_id": "op_1234567890abcdef",
  "status": "COMPLETED",
  "progress": 100,
  "result": {
    "copied": 1,
    "skipped": 0,
    "errors": 0
  },
  "message": "Operation completed successfully"
}
```

**Status Values:**
- `QUEUED`: Operation is waiting to be processed
- `RUNNING`: Operation is currently executing
- `COMPLETED`: Operation completed successfully
- `FAILED`: Operation failed
- `CANCELLED`: Operation was cancelled

**Error Responses:**
- 400: Invalid operation ID
- 401: Authentication required
- 404: Operation not found
- 500: Internal server error

### GET /api/config
Get full configuration (operations, keybindings, exec, editor).

**Response:**
```json
{
  "operations": {
    "copy": {
      "max_retries": 3,
      "timeout": 600,
      "interval": 500
    },
    "move": {
      "max_retries": 3,
      "timeout": 600,
      "interval": 500
    },
    "batch_delete": {
      "max_retries": 2,
      "timeout": 120,
      "interval": 300
    },
    "search": {
      "max_retries": 2,
      "timeout": 120,
      "interval": 300
    },
    "compare": {
      "max_retries": 2,
      "timeout": 120,
      "interval": 300
    },
    "sync_plan": {
      "max_retries": 2,
      "timeout": 120,
      "interval": 300
    },
    "sync_execute": {
      "max_retries": 2,
      "timeout": 300,
      "interval": 500
    },
    "archive_list": {
      "max_retries": 1,
      "timeout": 30,
      "interval": 300
    }
  },
  "keybindings": {
    "F1": "help",
    "F3": "view",
    "F5": "copy",
    "F6": "move",
    "F7": "mkdir",
    "F8": "delete",
    "F9": "search",
    "F10": "quit",
    "F11": "fullscreen",
    "Enter": "navigate",
    "Tab": "switch_panel",
    "Insert": "select"
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

### PUT /api/config
Save full configuration (partial updates supported).

**Request Body:**
```json
{
  "operations": {
    "copy": {
      "max_retries": 5,
      "timeout": 900,
      "interval": 1000
    }
  }
}
```

**Response:**
```json
{
  "message": "Configuration saved successfully"
}
```

**Error Responses:**
- 400: Invalid configuration
- 401: Authentication required
- 500: Internal server error

## System & Auth Endpoints

### GET /api/health
Health check endpoint (no authentication required).

**Response:**
```json
{
  "status": "running",
  "state": "running",
  "version": "0.13.0.00015"
}
```

### GET /api/sysinfo
Get system information.

**Response:**
```json
{
  "os": "Windows 10",
  "hostname": "DESKTOP-ABC123",
  "cpu": {
    "cores": 8,
    "usage": 45
  },
  "ram": {
    "total": 16000000000,
    "used": 8000000000,
    "free": 8000000000,
    "percent_used": 50
  },
  "uptime": 3600,
  "drives": [
    {
      "letter": "C",
      "label": "Windows",
      "filesystem": "NTFS",
      "total": 100000000000,
      "free": 50000000000,
      "used": 50000000000,
      "percent_used": 50
    }
  ]
}
```

**Error Responses:**
- 401: Authentication required
- 500: Internal server error

## WebSocket Endpoints
WebNC does not currently implement WebSocket endpoints.

## Rate Limiting
WebNC does not implement rate limiting as it is designed for local/private network use.

## Versioning
The API follows semantic versioning. The current version is 1.0.0.

## CORS
CORS is enabled with `allow_origins=["*"]` for development convenience. In production, restrict origins as needed.

## Error Format
All error responses follow this format:
```json
{
  "detail": "Error description"
}
```

## Changelog
See `History.md` for detailed development history.
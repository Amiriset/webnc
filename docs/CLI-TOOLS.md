# WebNC CLI Tools Documentation

This document describes the command-line interface tools and utilities provided with WebNC for server management, configuration, and operation.

## Overview

WebNC provides several CLI tools for managing the server instance:
- `webnc_server.py`: Main server entry point with direct argument handling
- `manage_server.ps1`: PowerShell script for comprehensive server management
- `run.bat`: CMD wrapper script for easy server control

All tools are designed to work with the Python launcher (`py`) as specified in project constraints.

## webnc_server.py

The main entry point for the WebNC backend server. This is a thin shim that delegates to the `webnc.main` module.

### Usage
```powershell
py webnc_server.py [options]
```

### Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--host HOST` | Bind address for the server | `127.0.0.1` |
| `--port PORT` | TCP port for the server | `8000` |
| `--insecure` | Disable SSL/TLS (run as HTTP only) | `False` (HTTPS enabled by default) |
| `--cert CERT` | Path to SSL certificate file | Auto-generated |
| `--key KEY` | Path to SSL key file | Auto-generated |
| `--auth AUTH` | Authentication provider: `console-token` (default) | `console-token` |
| `--reload` | Enable auto-reload when code changes (development mode) | `False` |

### Examples

**Start server with default settings (HTTPS on localhost:8000):**
```powershell
py webnc_server.py
```

**Start server on all interfaces (use with caution):**
```powershell
py webnc_server.py --host 0.0.0.0 --port 8000
```
> ⚠️ Warning: Binding to `0.0.0.0` without `--insecure` shows a security warning as it exposes the self-signed certificate to all network interfaces.

**Start server in HTTP mode (for debugging only):**
```powershell
py webnc_server.py --insecure
```

**Start server with custom certificate:**
```powershell
py webnc_server.py --cert /path/to/certificate.crt --key /path/to/private.key
```

**Enable auto-reload for development:**
```powershell
py webnc_server.py --reload
```

**Combine options:**
```powershell
py webnc_server.py --host 127.0.0.1 --port 8080 --reload --insecure
```

### Environment
- Requires Python 3.9+ accessible via `py` launcher
- Dependencies listed in `requirements.txt`
- Auto-generates self-signed RSA-4096 certificate on first run (if `--insecure` not specified)
- Certificate stored as `nc_server.crt` and `nc_server.key` in project root

## manage_server.ps1

A comprehensive PowerShell script for managing the WebNC server lifecycle, including start, stop, restart, status checking, and health monitoring.

### Location
`bin\manage_server.ps1`

### Usage
```powershell
& bin\manage_server.ps1 <command> [options]
```

### Commands

| Command | Description |
|---------|-------------|
| `start` | Start the server instance |
| `stop` | Stop the running server instance |
| `restart` | Stop then start the server instance |
| `status` | Check if server is running and healthy |
| `monitor` | Start health check monitoring with auto-restart |

### Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `-Command` | Management command to execute | `status` |
| `-Port` | TCP port for the server | `8000` |
| `-HostAddr` | Bind address for the server | `127.0.0.1` |
| `-Insecure` | Run server in HTTP mode (no encryption) | `$false` |
| `-HealthInterval` | Health check interval in seconds (monitor mode only) | `15` |

### Examples

**Start server with default settings:**
```powershell
& bin\manage_server.ps1 start
```

**Start server on port 8080:**
```powershell
& bin\manage_server.ps1 start -Port 8080
```

**Start server in HTTP mode:**
```powershell
& bin\manage_server.ps1 start -Insecure
```

**Check server status:**
```powershell
& bin\manage_server.ps1 status
```

**Stop running server:**
```powershell
& bin\manage_server.ps1 stop
```

**Restart server:**
```powershell
& bin\manage_server.ps1 restart
```

**Start health monitoring (checks every 15s, auto-restarts on failure):**
```powershell
& bin\manage_server.ps1 monitor
```

**Start health monitoring with custom interval:**
```powershell
& bin\manage_server.ps1 monitor -HealthInterval 30
```

### Features

#### Process Management
- Tracks server process via PID file (`server.pid` in project root)
- Prevents multiple instances from running on same port
- Graceful shutdown handling
- Force-kill fallback for unresponsive processes

#### Health Monitoring (monitor mode)
- Periodic health checks via `/api/health` endpoint
- Automatic restart on failure or unresponsiveness
- Special handling for PowerShell 5.1 limitations (no `-SkipCertificateCheck`)
- Uses `ServicePointManager.ServerCertificateValidationCallback` for self-signed cert bypass
- Timestamped logging to `logs\server.log`

#### Logging
- Detailed console output with color coding
- File logging to `logs\server.log` with timestamps
- Start/stop events logged automatically
- Health check results logged during monitoring

#### Certificate Handling
- Works with auto-generated self-signed certificates
- Handles certificate generation delays during startup
- Compatible with PowerShell 5.1 and newer versions

#### Security Considerations
- Defaults to HTTPS with localhost binding for security
- Explicit `-Insecure` flag required for HTTP mode
- Clear warnings when binding to `0.0.0.0`
- Certificate validation bypass only for health checks in PowerShell

## run.bat

A simple CMD (batch file) wrapper for `manage_server.ps1` providing easy server control from Command Prompt.

### Location
`bin\run.bat`

### Usage
```cmd
bin\run.bat <command> [options]
```

### Commands

| Command | Description |
|---------|-------------|
| `start` | Start the server (HTTPS by default) |
| `stop` | Stop the server |
| `restart` | Restart the server |
| `status` | Check server status |
| `monitor` | Start health monitoring |

### Options

| Option | Description |
|--------|-------------|
| `--insecure` | Run server in HTTP mode |
| `--ssl` | Alias for default HTTPS behavior (redundant but supported) |

### Examples

**Start server (HTTPS on localhost:8000):**
```cmd
bin\run.bat start
```

**Start server in HTTP mode:**
```cmd
bin\run.bat start --insecure
```

**Check server status:**
```cmd
bin\run.bat status
```

**Stop server:**
```cmd
bin\run.bat stop
```

**Restart server:**
```cmd
bin\run.bat restart
```

**Start health monitoring:**
```cmd
bin\run.bat monitor
```

### Implementation Details
- Simple wrapper that calls `powershell -ExecutionPolicy Bypass -File bin\manage_server.ps1 %*`
- Passes all arguments through to the PowerShell script
- Bypasses execution policy for ease of use
- Maintains compatibility with existing batch file workflows

## Configuration Format

WebNC uses a unified JSON configuration file with four sections:

### 1. Server Configuration (`config/config.json`)
Managed via `/api/config` endpoint, controls operation timeouts, retry settings, keybindings, exec rules, and editor limits.

#### File Location
`config/config.json` (auto-generated in project root)

#### Structure
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
    "F2": "menu_left",
    "F3": "view",
    "F4": "edit",
    "F5": "copy",
    "F6": "move",
    "F7": "mkdir",
    "F8": "delete",
    "F9": "search",
    "F10": "quit",
    "F11": "fullscreen",
    "Enter": "navigate",
    "Tab": "switch_panel",
    "Insert": "select",
    "+": "select_group",
    "-": "deselect_group",
    "*": "invert_selection",
    "Backspace": "go_up",
    "ArrowUp": "up",
    "ArrowDown": "down",
    "Home": "home",
    "End": "end",
    "PageUp": "page_up",
    "PageDown": "page_down"
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

#### Field Descriptions — Operations
- `max_retries`: Number of retry attempts for transient errors (0-10)
- `timeout`: Maximum operation duration in seconds before cancellation
- `interval`: Polling interval in milliseconds for frontend status updates

#### Field Descriptions — Keybindings
- Maps keyboard keys to action names
- Used by the frontend to dispatch keyboard events
- Can be customized via config.json

#### Field Descriptions — Exec
- `allowed_commands`: Whitelist of allowed command prefixes (empty = all allowed except denied)
- `denied_commands`: Blacklist of denied command prefixes (always blocked)

#### Field Descriptions — Editor
- `max_edit_size`: Maximum file size in bytes for the editor (default: 1 MB = 1048576)

#### Non-Retriable Errors
These errors never trigger retries regardless of `max_retries` setting:
- `PermissionError`
- `FileNotFoundError`
- `FileExistsError`
- `NotADirectoryError`
- `IsADirectoryError`
- `BlockingIOError`
- `InterruptedError`

Additionally, `ArchiveListOperation` skips retry on:
- `BadZipFile`
- `ReadError`
- `PasswordRequiredException`
- `ExtractError`

### 2. User Interface Configuration (localStorage)
Stored in browser's `localStorage` under key `nc_config`, manages UI preferences.

#### Structure
```json
{
  "view_mode": "full",
  "sort_by": "name",
  "sort_dir": "asc",
  "show_hidden": false,
  "confirm_delete": true,
  "confirm_overwrite": true,
  "font_size": 14
}
```

#### Field Descriptions
- `view_mode`: Default panel view (`brief`, `full`, `quick`, `info`, `tree`)
- `sort_by`: Default sort field (`name`, `extension`, `time`, `size`, `unsorted`)
- `sort_dir`: Default sort direction (`asc`, `desc`)
- `show_hidden`: Whether to show hidden files by default
- `confirm_delete`: Show confirmation dialog for delete operations
- `confirm_overwrite`: Show confirmation dialog for overwrite operations
- `font_size`: Base font size in pixels

#### Management
- Modified via `Options → Configuration...` dialog
- Automatically saved to localStorage on change
- Loaded at application startup
- Shared across browser tabs/pages for same origin

## Integration Examples

### Development Workflow
```powershell
# 1. Start server with auto-reload for development
py webnc_server.py --reload

# 2. In another terminal, run frontend build/watch commands (if applicable)
# WebNC uses served static files, so no build step needed for basic development

# 3. Test changes - server auto-reloads when Python files change
# Frontend changes require manual refresh (Ctrl+F5) to bypass caching
```

### Production Deployment
```powershell
# 1. Start server with default secure settings
& bin\manage_server.ps1 start

# 2. Or use the batch file equivalent
bin\run.bat start

# 3. Verify status
bin\run.bat status
# Should show: Server: RUNNING (PID xxxx, port 8000, healthy)

# 4. For production monitoring
bin\run.bat monitor
# Will auto-restart server on failure
```

### Debugging Scenarios

**Server fails to start:**
```powershell
# Check if port is already in use
netstat -ano | findstr :8000

# Kill existing process if needed
taskkill /F /PID <pid>

# Try starting with more verbose output
py webnc_server.py --host 127.0.0.1 --port 8000
```

**Authentication issues:**
```powershell
# 1. Check server console for token output
# 2. Ensure browser accepts self-signed certificate
# 3. Clear site data or use private browsing to clear bad state
# 4. Restart server to get new token if needed
```

**Performance problems:**
```powershell
# 1. Check logs for warnings/errors
# 2. Verify no blocking operations outside thread pool
# 3. Check thread pool utilization
# 4. Adjust timeout/retry values via PUT /api/config if needed
```

## Best Practices

### Security
1. **Always use HTTPS in production** - Never expose `--insecure` to untrusted networks
2. **Bind to localhost only** for local use (`--host 127.0.0.1`)
3. **Use strong certificates** for deployment - replace auto-generated cert with CA-signed
4. **Keep dependencies updated** - Regularly check `requirements.txt` for updates
5. **Monitor logs** - Check `logs\nc_server.log` for security warnings

### Performance
1. **Adjust timeouts appropriately** - Longer for large file operations, shorter for quick tasks
2. **Monitor thread pool** - Ensure adequate workers for concurrent operations
3. **Use reasonable retry values** - 3-5 retries is usually sufficient
4. **Consider hardware** - SSD storage significantly improves filesystem operation performance

### Maintenance
1. **Backup configuration** - `config.json` and localStorage settings
2. **Rotate logs** - Log rotation is automatic (5MB × 3 backups)
3. **Update regularly** - Pull latest changes and test in staging first
4. **Document customizations** - Track any changes to default behavior

## Troubleshooting

### Common Issues and Solutions

**Issue**: "Address already in use" error when starting server
**Solution**: 
```powershell
# Find process using port 8000
netstat -ano | findstr :8000
# Kill the process
taskkill /F /PID <pid>
# Retry start command
```

**Issue**: Browser shows certificate warning
**Solution**: 
- This is expected for auto-generated self-signed certificates
- Click "Advanced" → "Proceed to localhost (unsafe)" in Chrome/Firefox
- For production, replace with certificate from trusted CA
- To regenerate dev certificate: delete `nc_server.crt` and `nc_server.key`, then restart

**Issue**: Authentication fails after server restart
**Solution**: 
- Tokens are ephemeral and regenerated on each server start
- Copy new token from server console output
- Or clear browser storage and accept new token prompt
- This is normal security behavior

**Issue**: Server hangs or becomes unresponsive
**Solution**: 
- Check for long-running operations blocking event loop
- Verify all filesystem calls are wrapped in `asyncio.to_thread()`
- Check `logs\nc_server.log` for error messages
- Use `bin\run.bat monitor` for automatic restart on failure
- In extreme cases, manually kill process and restart

**Issue**: Frontend shows blank page
**Solution**: 
1. Open browser dev tools (F12)
2. Check Console tab for JavaScript errors
3. Check Network tab for failed requests (especially to `/api/health`)
4. Verify server is running and accessible
5. Hard refresh with Ctrl+F5 to bypass caching
6. Check for port mismatch (frontend expects localhost:8000)

### Log File Location
- Primary log: `logs\nc_server.log`
- Rotates automatically when reaching 5 MB
- Keeps 3 most recent backup files
- Format: `%(asctime)s | %(levelname)-8s | %(message)s`
- Contains: startup/shutdown events, all API calls, warnings, errors

## Future Enhancements

### Planned CLI Improvements
1. **Configuration import/export** - Backup/restore operation settings
2. **User management commands** - For future RBAC implementation
3. **Certificate management** - Easy replacement/renewal of TLS certs
4. **Database utilities** - For planned metadata storage
5. **Performance profiling** - Built-in profiling tools
6. **Docker integration** - Dockerfile and docker-compose support

### Planned Configuration Enhancements
1. **Runtime configuration validation** - Prevent invalid settings
2. **Configuration profiles** - Named sets of operation settings
3. **Change history** - Track configuration modifications over time
4. **Scheduled operations** - Cron-like scheduling for regular tasks
5. **Resource limits** - Memory, CPU, and disk usage controls

This documentation covers all CLI tools provided with WebNC. For the most current information, please refer to the individual tool's help output (`py webnc_server.py --help`) and the `History.md` file which contains detailed development progress.
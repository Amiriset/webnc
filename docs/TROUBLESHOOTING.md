# WebNC Troubleshooting Guide

This document covers known issues, resolved problems, and solutions for common WebNC deployment and usage scenarios.

## Known Issues

### 1. Self-Signed Certificate Browser Warning
**Symptom**: Browser shows "Your connection is not private" or similar warning on first visit.

**Cause**: WebNC generates a self-signed RSA-4096 certificate on first run. Browsers do not trust self-signed certificates by default.

**Solution**:
- Chrome: Click "Advanced" → "Proceed to localhost (unsafe)"
- Firefox: Click "Advanced" → "Accept the Risk and Continue"
- Edge: Click "Advanced" → "Continue to localhost (unsafe)"
- For production: Replace with a certificate from an internal CA or trusted provider

**To regenerate**: Delete `nc_server.crt` and `nc_server.key` from project root, then restart server.

### 2. Port 8000 Already in Use
**Symptom**: `OSError: [WinError 10048] An attempt was made to access a socket in a way forbidden by its access permissions`

**Cause**: Another process (possibly a previous WebNC instance) is using port 8000.

**Solution**:
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process
taskkill /F /PID <pid>

# Or use a different port
py webnc_server.py --port 8080
```

### 3. Stale Server Process
**Symptom**: `manage_server.ps1` reports server running but it's not responding, or PID file references dead process.

**Cause**: Server crashed or was killed without clean shutdown, leaving stale PID file.

**Solution**:
```powershell
# Check status
& bin\manage_server.ps1 status

# Force stop (kills any matching process)
& bin\manage_server.ps1 stop

# If still stuck, manually delete PID file and kill processes
Remove-Item server.pid -ErrorAction SilentlyContinue
Get-Process -Name "py","python" | Where-Object {
    (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine -match 'webnc_server'
} | Stop-Process -Force

# Then restart
& bin\manage_server.ps1 start
```

### 4. Token Reset After Server Restart
**Symptom**: Browser shows authentication error or login dialog after server restart.

**Cause**: Session tokens are ephemeral and regenerated on each server start. Old tokens are invalidated.

**Solution**:
1. Copy new token from server console output (look for 64-character hex string)
2. Paste token when prompted, or
3. Append `#token=<TOKEN>` to URL: `https://localhost:8000/#token=abc123...`
4. Or clear browser storage for the site and accept new token prompt

### 5. PowerShell Execution Policy Error
**Symptom**: `manage_server.ps1` cannot be loaded because running scripts is disabled on this system.

**Cause**: PowerShell execution policy restricts script execution.

**Solution**:
```powershell
# Option 1: Use run.bat (bypasses execution policy automatically)
bin\run.bat start

# Option 2: Set execution policy for current user
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Option 3: Run with bypass flag
powershell -ExecutionPolicy Bypass -File bin\manage_server.ps1 -Command start
```

## Resolved Problems

### 1. TLS Version Mismatch
**Symptom**: Older clients (Windows 7, legacy browsers) cannot connect — handshake failure.

**Cause**: WebNC requires TLS 1.3 minimum. Some older systems do not support TLS 1.3.

**Solution (at your own risk)**:
If you must support systems without TLS 1.3, you can downgrade to TLS 1.2 by editing `webnc/main.py`:
```python
ctx.minimum_version = ssl.TLSVersion.TLSv1_2
```
This weakens transport security. Only do this in isolated/trusted networks.

**Better alternatives**:
- Update the client system to support TLS 1.3
- Use a reverse proxy that terminates TLS 1.3 and speaks TLS 1.2 to legacy clients

### 2. Event Loop Blocking
**Problem**: Server became unresponsive during large file operations.

**Resolution**: All blocking filesystem operations are now wrapped in `asyncio.to_thread()` via the OperationQueue thread pool. This prevents the event loop from being blocked by long-running I/O operations.

### 3. CORS Issues During Development
**Problem**: Frontend requests were blocked by CORS policy when running on different origins.

**Resolution**: CORS middleware configured with `allow_origins=["*"]` for development. In production, all traffic is served from the same origin (FastAPI serves static files).

### 4. Config File Corruption
**Problem**: Server crash during config write could corrupt `config.json`.

**Resolution**: ConfigManager uses atomic writes:
1. Write to temporary file (`config.json.tmp`)
2. Validate written content
3. Atomic rename/replace operation
4. Thread-safe locking during writes

### 5. Memory Leak from Operation Queue
**Problem**: Completed operations accumulated in memory over time.

**Resolution**: OperationQueue includes automatic cleanup:
- Finished operations older than 300 seconds (`POLL_TTL`) are removed
- Cleanup runs every 60 seconds (`CLEANUP_INTERVAL`)
- Graceful shutdown drains the queue on server exit

### 6. Ctrl+O Not Working in Browser
**Symptom**: Pressing Ctrl+O opens browser's "Open File" dialog instead of toggling panels.

**Cause**: Ctrl+O is a browser-level shortcut in Chrome/Edge that cannot be reliably intercepted by web applications.

**Workaround**: Use the menu items (Left/Right → On/Off, Commands → Panels On/Off) instead. The capture-phase listener is best-effort and may work in some browsers.

### 7. PowerShell 5.1 Certificate Validation
**Symptom**: `manage_server.ps1` health checks fail on PowerShell 5.1 with certificate validation errors.

**Cause**: PowerShell 5.1 does not have `-SkipCertificateCheck` parameter and rejects self-signed certificates by default.

**Resolution**: Script temporarily sets `ServerCertificateValidationCallback` to accept all certificates during health checks, then restores the original callback:
```powershell
[System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }
# ... health check ...
[System.Net.ServicePointManager]::ServerCertificateValidationCallback = $oldCb
```

### 8. Proactor Event Loop Warning Noise
**Problem**: Windows asyncio proactor transport warnings filled logs on client disconnect.

**Resolution**: Warning filter added at startup:
```python
warnings.filterwarnings("ignore", message=".*_ProactorBasePipeTransport.*")
```

### 9. Exec Endpoint NotImplementedError
**Symptom**: `POST /api/exec` returns HTTP 500 with `NotImplementedError: ... SelectorEventLoop cannot subprocess`.

**Cause**: `SelectorEventLoop` (default on Windows) cannot create subprocesses. `asyncio.create_subprocess_shell` requires `ProactorEventLoop`.

**Resolution**: WebNC sets `WindowsProactorEventLoopPolicy` at startup. If you see this error, ensure you're running through `webnc_server.py` (which sets the policy) rather than `uvicorn` directly.

### 10. ConnectionResetError Crashes
**Symptom**: Server crashes when a client disconnects abruptly during a request.

**Cause**: Windows `ProactorEventLoop` raises `ConnectionResetError` when a client disconnects before the response is sent. Unhandled, this crashes the event loop.

**Resolution**: WebNC sets `asyncio` logger to `CRITICAL` to suppress the traceback noise from `_ProactorBasePipeTransport._call_connection_lost` (Python 3.9 bug):
```python
logging.getLogger("asyncio").setLevel(logging.CRITICAL)
```

### 8. File Upload Size Limit
**Problem**: No limit on file uploads could cause memory exhaustion.

**Resolution**: Upload endpoint enforces 100 MB limit:
```python
if len(content) > MAX_UPLOAD_SIZE:  # 100 * 1024 * 1024
    raise HTTPException(status_code=413, detail="File too large")
```

### 9. Symlink Creation Fails
**Symptom**: `POST /api/link` returns error "Cannot create link: enable Developer Mode".

**Cause**: Windows requires Developer Mode enabled for `os.symlink()` to work without elevation.

**Workarounds**:
- Enable Developer Mode: Settings → Update & Security → For developers → Developer Mode
- WebNC automatically falls back to `mklink /J` (junctions) for directories — this works without Developer Mode
- For files, hardlinks (`mklink /H`) work without Developer Mode but require same drive
- Cross-drive hardlinks are not supported by Windows

### 10. Editor Size Limit
**Problem**: Editing very large files could cause browser performance issues.

**Resolution**: Configurable `max_edit_size` (default 1 MB) enforced in `/api/view` endpoint:
```python
if for_edit:
    _check_edit_size(path)  # Raises 413 if too large
```

## Common Deployment Issues

### Development Mode
**Issue**: `--reload` flag doesn't work with SSL
**Solution**: This is a uvicorn limitation. The reloader subprocess loses SSL config. Workaround: restart manually after code changes, or use `--insecure` for development.

**Issue**: Frontend not updating after code changes
**Solution**: Hard refresh with `Ctrl+F5` to bypass browser cache. Backend changes auto-reload with `--reload` flag.

### Production Mode
**Issue**: Server binds to localhost only by default
**Solution**: Use `--host 0.0.0.0` to bind to all interfaces. Warning: ensure firewall rules are in place.

**Issue**: Health monitoring not auto-restarting
**Solution**: Use `bin\run.bat monitor` or `& bin\manage_server.ps1 monitor` for continuous health checking with auto-restart on failure.

### Network Issues
**Issue**: Cannot access from other machines
**Solution**:
1. Ensure server is bound to `0.0.0.0` (not just `127.0.0.1`)
2. Check Windows Firewall allows incoming connections on the port
3. Verify network connectivity with `Test-NetConnection -ComputerName <server> -Port <port>`

**Issue**: Self-signed certificate not accepted by API clients
**Solution**: API clients must disable certificate verification for self-signed certs. Example with `curl`:
```powershell
curl -k https://localhost:8000/api/health
```

## Performance Issues

### Slow Directory Listings
**Cause**: Large directories (>10K files) with full metadata retrieval.
**Solution**:
- Use Brief view mode for faster scanning
- Enable `show_hidden=false` to skip hidden files
- Use filter patterns to reduce result set

### Slow Search Operations
**Cause**: Deep directory trees with many files.
**Solution**:
- Reduce `max_results` in search requests
- Use glob patterns instead of regex when possible
- Search from specific subdirectories rather than drive root

### Operation Timeouts
**Cause**: Large file operations exceeding configured timeout.
**Solution**:
- Increase timeout for specific operation types via `PUT /api/config`
- For very large files, increase `copy.timeout` or `move.timeout`
- Monitor via `GET /api/operation/{id}` for progress

### Thread Pool Exhaustion
**Cause**: Too many concurrent operations.
**Solution**:
- Default thread pool has 4 workers
- Operations queue prevents unbounded concurrency
- Monitor via logs for "Operation queued" messages
- Adjust `max_workers` in `OperationQueue` constructor if needed

## Authentication Issues

### Token Not Working
**Symptom**: 401 Unauthorized on all requests.
**Checklist**:
1. Token matches server console output exactly
2. Token hasn't expired (5-minute timestamp window)
3. Browser accepts self-signed certificate
4. Clock is synchronized (timestamp validation)

### Replay Attack Detection
**Symptom**: First request works, subsequent requests fail with 401.
**Cause**: Nonce reuse detected (replay protection).
**Solution**: Generate new nonce for each request (handled automatically by frontend `api.js`).

### Timestamp Window Expired
**Symptom**: 401 with "timestamp" related error.
**Cause**: Client clock is more than 5 minutes offset from server.
**Solution**: Synchronize system clocks. The timestamp window is 300 seconds.

## Log Analysis

### Log Location
- Primary: `logs/nc_server.log`
- Rotating: 5 MB × 3 backups (max ~15 MB total)

### Log Format
```
2026-05-30 14:30:00,123 | INFO     | GET /api/list path=/C/Users/
```

### Useful Log Patterns
```powershell
# Find all errors
Select-String -Path logs\nc_server.log -Pattern "ERROR"

# Find authentication failures
Select-String -Path logs\nc_server.log -Pattern "401|auth.*fail"

# Find slow operations
Select-String -Path logs\nc_server.log -Pattern "finished.*FAILED"

# Find certificate events
Select-String -Path logs\nc_server.log -Pattern "cert|SSL|TLS"
```

## Getting Help

If your issue is not covered here:
1. Check server logs in `logs/nc_server.log`
2. Check browser console (F12) for frontend errors
3. Review `docs/API_REFERENCE.md` for endpoint details
4. Review `docs/ARCHITECTURE.md` for system design
5. Open an issue with:
   - WebNC version
   - OS and version
   - Browser and version
   - Steps to reproduce
   - Relevant log excerpts
   - Expected vs actual behavior

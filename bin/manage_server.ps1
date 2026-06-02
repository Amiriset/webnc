param(
    [ValidateSet("start","stop","restart","status","monitor")]
    [string]$Command = "status",
    [int]$Port = 8000,
    [string]$HostAddr = "127.0.0.1",
    [switch]$Insecure,
    [int]$HealthInterval = 15
)

$ScriptDir = $PSScriptRoot
$ProjectRoot = Split-Path -Parent $ScriptDir
$PidFile = Join-Path $ProjectRoot "server.pid"

# Bypass cert validation for self-signed cert health checks (warn once)
$script:CertWarningShown = $false
[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {
    param($sender, $certificate, $chain, $sslPolicyErrors)
    if (-not $script:CertWarningShown) {
        Write-Warning "Self-signed certificate detected — skipping validation for health check"
        $script:CertWarningShown = $true
    }
    $true
}
$LogDir = Join-Path $ProjectRoot "logs"
$LogFile = Join-Path $LogDir "server.log"
$Scheme = if ($Insecure) { "http" } else { "https" }
$ServerUrl = "$Scheme`://127.0.0.1:$Port"

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp $Message" | Out-File -FilePath $LogFile -Append -Encoding ASCII
}

function Get-ServerProcess {
    $pids = @()
    if (Test-Path $PidFile) {
        $savedPid = Get-Content $PidFile -Raw -ErrorAction SilentlyContinue
        if ($savedPid -match '\d+') {
            $pids += [int]$Matches[0]
        }
    }
    $proc = $null
    foreach ($spid in $pids) {
        try {
            $proc = Get-Process -Id $spid -ErrorAction Stop
            if ($proc.ProcessName -match '^py$|^python$') { break }
            else { $proc = $null }
        } catch { $proc = $null }
    }
    if (-not $proc) {
        $proc = Get-Process -Name "py","python" -ErrorAction SilentlyContinue | Where-Object {
            try {
                $c = Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)"
                $c.CommandLine -match 'webnc_server'
            } catch { $false }
        } | Select-Object -First 1
    }
    $proc
}

function Get-HealthResponse {
    try {
        $oldCb = [System.Net.ServicePointManager]::ServerCertificateValidationCallback
        $oldProt = [System.Net.ServicePointManager]::SecurityProtocol
        [System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor [System.Net.SecurityProtocolType]::Tls12 -bor [System.Net.SecurityProtocolType]::Tls13
        $iwrParams = @{ Uri = "$ServerUrl/api/health"; UseBasicParsing = $true; TimeoutSec = 5 }
        if ($PSVersionTable.PSVersion.Major -ge 7) { $iwrParams.SkipCertificateCheck = $true }
        $r = Invoke-WebRequest @iwrParams
        return ($r.Content | ConvertFrom-Json)
    } catch { return $null }
    finally {
        [System.Net.ServicePointManager]::ServerCertificateValidationCallback = $oldCb
        [System.Net.ServicePointManager]::SecurityProtocol = $oldProt
    }
}

function Test-Health {
    $resp = Get-HealthResponse
    return ($resp -and $resp.state -eq "running")
}

function Start-Server {
    $existing = Get-ServerProcess
    if ($existing) {
        Write-Host "Server already running (PID $($existing.Id))" -ForegroundColor Yellow
        return
    }
    Write-Host "Starting server on $HostAddr`:$Port ($Scheme)..." -ForegroundColor Green
    $insecureArg = if ($Insecure) { "--insecure" } else { "" }
    $proc = Start-Process -NoNewWindow -FilePath "py" -ArgumentList "webnc_server.py --host $HostAddr --port $Port $insecureArg" -WorkingDirectory $ProjectRoot -PassThru
    $proc.Id | Out-File -FilePath $PidFile -Encoding ASCII
    $maxRetries = 15
    $retryDelay = 2
    $ok = $false
    for ($i = 1; $i -le $maxRetries; $i++) {
        Start-Sleep -Seconds $retryDelay
        $resp = Get-HealthResponse
        if ($resp) {
            switch ($resp.state) {
                "running"          { $ok = $true; break }
                "generating_cert"  { Write-Host "  Generating SSL certificate..." -ForegroundColor Yellow }
                "starting"         { Write-Host "  Booting..." -ForegroundColor Yellow }
                default            { Write-Host "  State: $($resp.state)" -ForegroundColor Yellow }
            }
        }
    }
    if ($ok) {
        Write-Host "Server started successfully" -ForegroundColor Green
        Write-Log "Server started on port $Port (PID $($proc.Id))"
        $global:LASTEXITCODE = 0
    } else {
        Write-Host "Server may have failed to start" -ForegroundColor Red
        Write-Log "Server start command issued but health check failed"
        exit 1
    }
}

function Stop-Server {
    $proc = Get-ServerProcess
    if (-not $proc) {
        Write-Host "Server is not running" -ForegroundColor Yellow
        Remove-Item $PidFile -ErrorAction SilentlyContinue
        return
    }
    Write-Host "Stopping server (PID $($proc.Id))..." -ForegroundColor Cyan
    $proc | Stop-Process -Force
    Start-Sleep -Seconds 1
    Remove-Item $PidFile -ErrorAction SilentlyContinue
    Write-Host "Server stopped" -ForegroundColor Green
    Write-Log "Server stopped"
}

function Get-Status {
    $proc = Get-ServerProcess
    if (-not $proc) {
        Write-Host "Server: STOPPED" -ForegroundColor Red
        return $false
    }
    $resp = Get-HealthResponse
    if ($resp -and $resp.state -eq "running") {
        Write-Host "Server: RUNNING (PID $($proc.Id), port $Port, healthy)" -ForegroundColor Green
    } elseif ($resp) {
        Write-Host "Server: $($resp.state.ToUpper()) (PID $($proc.Id), port $Port)" -ForegroundColor Yellow
    } else {
        Write-Host "Server: RUNNING (PID $($proc.Id)) but NOT RESPONDING" -ForegroundColor Red
    }
    return ($resp -and $resp.state -eq "running")
}

function Start-Monitor {
    Write-Host "=== Health Monitor ===" -ForegroundColor Cyan
    Write-Host "Checking $ServerUrl every ${HealthInterval}s" -ForegroundColor Cyan
    Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
    Write-Log "Monitor started (interval ${HealthInterval}s)"

    while ($true) {
        $now = Get-Date -Format "HH:mm:ss"
        $proc = Get-ServerProcess
        $resp = Get-HealthResponse

        if (-not $proc) {
            Write-Host "$now Server DOWN - restarting..." -ForegroundColor Red
            Write-Log "Monitor: server down, restarting"
            Start-Server
        } elseif (-not $resp -or ($resp.state -ne "running")) {
            $state = if ($resp) { $resp.state } else { "unresponsive" }
            Write-Host "$now Server $state - restarting..." -ForegroundColor Red
            Write-Log "Monitor: server $state, restarting"
            $proc | Stop-Process -Force
            Start-Sleep -Seconds 1
            Remove-Item $PidFile -ErrorAction SilentlyContinue
            Start-Server
        } else {
            Write-Host "$now OK (PID $($proc.Id))" -ForegroundColor DarkGray
        }

        Start-Sleep -Seconds $HealthInterval
    }
}

switch ($Command) {
    "start"   { Start-Server }
    "stop"    { Stop-Server }
    "restart" { Stop-Server; Start-Server }
    "status"  { Get-Status | Out-Null }
    "monitor" { Start-Monitor }
}

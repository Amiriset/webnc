@echo off
rem WebNC — quick launcher
rem Usage:  run                           (start with HTTPS, default)
rem         run --insecure                (start with HTTP, no encryption)
rem         run stop                      (stop server)
rem         run restart                   (restart server)
rem         run restart --insecure        (restart with HTTP)
rem         run status                    (check health)
rem         run monitor                   (health monitor loop)

if "%1"=="" (
    powershell -ExecutionPolicy Bypass -File "%~dp0manage_server.ps1" -Command start
    if not errorlevel 1 (
        echo.
        echo Server started at https://localhost:8000
        echo NOTE: Self-signed cert - accept the risk in the browser
    )
) else if "%1"=="--insecure" (
    powershell -ExecutionPolicy Bypass -File "%~dp0manage_server.ps1" -Command start -Insecure
    if not errorlevel 1 (
        echo.
        echo WARNING: Server started at http://localhost:8000 - no encryption!
    )
) else (
    powershell -ExecutionPolicy Bypass -File "%~dp0manage_server.ps1" -Command %1 %2
    if not errorlevel 1 if "%1"=="start" (
        if "%2"=="--insecure" ( echo Server started ) else ( echo Server started )
    )
)

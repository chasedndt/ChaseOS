@echo off
:: ChaseOS Studio — source launcher
:: Shortcut points here permanently. No rebuild needed after code changes.
:: Double-click or pin to taskbar.

set "VAULT_ROOT=%~dp0..\..\.."
set "PYTHON=%VAULT_ROOT%\.venv\Scripts\python.exe"
set "PYTHONW=%VAULT_ROOT%\.venv\Scripts\pythonw.exe"
set "CHASEOS_STUDIO_STARTUP_LOG=%VAULT_ROOT%\build\studio-shortcut-startup.log"

if not exist "%PYTHON%" (
    echo ERROR: venv not found at %VAULT_ROOT%\.venv
    echo Run: python -m venv .venv ^&^& pip install -e .
    pause
    exit /b 1
)

if exist "%PYTHONW%" (
    start "ChaseOS Studio" "%PYTHONW%" -m runtime.studio.shell.main --vault-root "%VAULT_ROOT%"
    exit /b 0
)

"%PYTHON%" -m runtime.studio.shell.main --vault-root "%VAULT_ROOT%"

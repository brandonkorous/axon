@echo off
REM Start the Axon External Agent Runner
REM
REM Usage: start-ea.bat [codebase_path]
REM   codebase_path  Path to the codebase the EA operates on
REM
REM Environment variables (optional):
REM   AXON_URL       Axon backend URL (default: http://localhost:8000)
REM   AXON_ORG       Organization ID  (default: employment-networks)
REM   AXON_AGENT     Agent ID         (default: enterprise_architect)

setlocal

if "%AXON_URL%"=="" set AXON_URL=http://localhost:8000
if "%AXON_ORG%"=="" set AXON_ORG=employment-networks
if "%AXON_AGENT%"=="" set AXON_AGENT=enterprise_architect

REM Codebase from arg or env
if not "%~1"=="" (
    set CODEBASE=%~1
) else if not "%EA_CODEBASE%"=="" (
    set CODEBASE=%EA_CODEBASE%
) else (
    echo Error: No codebase path provided.
    echo Usage: start-ea.bat [codebase_path]
    echo    or: set EA_CODEBASE=G:\code\splits.network
    exit /b 1
)

echo [EA Runner] Agent:    %AXON_AGENT%
echo [EA Runner] Org:      %AXON_ORG%
echo [EA Runner] Axon:     %AXON_URL%
echo [EA Runner] Codebase: %CODEBASE%
echo.

cd /d %~dp0
python -m runner --axon-url %AXON_URL% --org %AXON_ORG% --agent %AXON_AGENT% --codebase %CODEBASE%

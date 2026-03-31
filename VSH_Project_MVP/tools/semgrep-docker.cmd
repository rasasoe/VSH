@echo off
powershell -ExecutionPolicy Bypass -File "%~dp0docker-tool-wrapper.ps1" -Image "semgrep/semgrep:latest" -CommandPrefix semgrep -ToolArgs %*
exit /b %ERRORLEVEL%

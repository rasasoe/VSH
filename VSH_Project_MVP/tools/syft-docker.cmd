@echo off
powershell -ExecutionPolicy Bypass -File "%~dp0docker-tool-wrapper.ps1" -Image "anchore/syft:latest" -ToolArgs %*
exit /b %ERRORLEVEL%

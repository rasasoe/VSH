#!/usr/bin/env powershell
# VSH Simple Setup & Run Script

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectDir = Join-Path $scriptDir "VSH_Project_MVP"
$venvDir = Join-Path $projectDir "venv"
$desktopDir = Join-Path $projectDir "vsh_desktop"

Write-Host "====== VSH Setup (PowerShell) ======" -ForegroundColor Cyan
Write-Host ""

# 1. Check project
Write-Host "[1/6] Checking project..." -ForegroundColor Yellow
if (-not (Test-Path "$projectDir\requirements.txt")) {
    Write-Host "ERROR: VSH_Project_MVP not found" -ForegroundColor Red
    exit 1
}
Write-Host "OK: Project found" -ForegroundColor Green

# 2. Check Python
Write-Host "[2/6] Checking Python..." -ForegroundColor Yellow
$pyVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python not found" -ForegroundColor Red
    exit 2
}
Write-Host "OK: $pyVersion" -ForegroundColor Green

# 3. Check Node
Write-Host "[3/6] Checking Node.js..." -ForegroundColor Yellow
$nodeVersion = node --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Node.js not found" -ForegroundColor Red
    exit 3
}
Write-Host "OK: $nodeVersion" -ForegroundColor Green

# 4. Setup venv and install Python packages
Write-Host "[4/6] Python setup (pip install)..." -ForegroundColor Yellow

if (-not (Test-Path $venvDir)) {
    Write-Host "  Creating venv..." -ForegroundColor Gray
    python -m venv $venvDir
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: venv creation failed" -ForegroundColor Red
        exit 4
    }
}

$pythonExe = Join-Path $venvDir "Scripts\python.exe"
Write-Host "  Installing requirements..." -ForegroundColor Gray

& $pythonExe -m pip install --upgrade pip -q 2>&1 | Out-Null
& $pythonExe -m pip install -r "$projectDir\requirements.txt" -q 2>&1 | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: pip install failed" -ForegroundColor Red
    exit 5
}
Write-Host "OK: Python packages installed" -ForegroundColor Green

# 5. npm install
Write-Host "[5/6] Node.js setup (npm install)..." -ForegroundColor Yellow

Push-Location $desktopDir
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: vsh_desktop not found" -ForegroundColor Red
    exit 6
}

Write-Host "  Cleaning npm cache..." -ForegroundColor Gray
npm cache clean --force 2>&1 | Out-Null

Write-Host "  Installing npm packages..." -ForegroundColor Gray
npm install --legacy-peer-deps --no-audit --no-fund --loglevel=error 2>&1 | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "  Retrying npm install..." -ForegroundColor Gray
    npm install --legacy-peer-deps --no-audit --no-fund --loglevel=error 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: npm install failed" -ForegroundColor Red
        Pop-Location
        exit 7
    }
}
Write-Host "OK: npm packages installed" -ForegroundColor Green
Pop-Location

# 6. Start services
Write-Host "[6/6] Starting services..." -ForegroundColor Yellow

Push-Location $projectDir

# Start API
Write-Host "  Starting API server..." -ForegroundColor Gray
$apiJob = Start-Job -ScriptBlock {
    param($pythonExe, $projectDir)
    Push-Location $projectDir
    & $pythonExe -m uvicorn vsh_api.main:app --host 127.0.0.1 --port 3000 --log-level warning
} -ArgumentList $pythonExe, $projectDir

# Wait for API
Write-Host "  Waiting for API..." -ForegroundColor Gray
$retry = 0
while ($retry -lt 30) {
    try {
        $health = Invoke-WebRequest -Uri "http://127.0.0.1:3000/health" -TimeoutSec 1 -UseBasicParsing -ErrorAction Stop
        Write-Host "OK: API is running" -ForegroundColor Green
        break
    }
    catch {
        $retry++
        Start-Sleep -Seconds 1
    }
}

if ($retry -ge 30) {
    Write-Host "ERROR: API timeout" -ForegroundColor Red
    Stop-Job $apiJob
    exit 8
}

# Start Vite
Write-Host "  Starting Vite..." -ForegroundColor Gray
Push-Location $desktopDir
$viteJob = Start-Job -ScriptBlock {
    cd $args[0]
    npm run dev 2>&1 | Out-Null
} -ArgumentList $desktopDir
Pop-Location

Start-Sleep -Seconds 5

# Open browser
Write-Host "  Opening browser..." -ForegroundColor Gray
Start-Process "http://localhost:5173"

Write-Host ""
Write-Host "====== SUCCESS ======" -ForegroundColor Cyan
Write-Host "API running: http://127.0.0.1:3000" -ForegroundColor White
Write-Host "Web UI: http://localhost:5173" -ForegroundColor White
Write-Host ""
Write-Host "Demo: VSH_Project_MVP/tests/samples/vuln_project/" -ForegroundColor Gray
Write-Host ""
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow

Pop-Location

# Keep running
try {
    while ($true) {
        Start-Sleep -Seconds 10
    }
}
catch {
    Write-Host "Shutting down..." -ForegroundColor Yellow
    Get-Job | Stop-Job
    exit 0
}

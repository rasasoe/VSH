$ErrorActionPreference = 'Stop'

$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectDir = Join-Path $rootDir 'VSH_Project_MVP'
$desktopDir = Join-Path $projectDir 'vsh_desktop'
$venvDir = Join-Path $projectDir 'venv'
$venvPythonExe = Join-Path $venvDir 'Scripts\python.exe'
$pythonExe = 'python'
$electronExe = Join-Path $desktopDir 'node_modules\electron\dist\electron.exe'
$distIndex = Join-Path $desktopDir 'dist-react\index.html'
$runtimeRoot = Join-Path $HOME '.vsh\runtime_data'
$sqliteDb = Join-Path $runtimeRoot 'vsh.db'
$chromaDir = Join-Path $runtimeRoot 'chroma'
$apiUrl = 'http://127.0.0.1:3000/health'

function Wait-ForApi {
    param([int]$RetryCount = 30)
    for ($i = 0; $i -lt $RetryCount; $i++) {
        try {
            $response = Invoke-RestMethod -Uri $apiUrl -TimeoutSec 2
            if ($response.status -eq 'ok') {
                return $true
            }
        } catch {
            Start-Sleep -Seconds 1
        }
    }
    return $false
}

function Test-PythonModule {
    param(
        [string]$PythonCommand,
        [string]$ModuleName
    )

    $previousErrorAction = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & $PythonCommand -c "import $ModuleName" *> $null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    } finally {
        $ErrorActionPreference = $previousErrorAction
    }
}

function Test-PythonPip {
    param([string]$PythonCommand)

    $previousErrorAction = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & $PythonCommand -m pip --version *> $null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    } finally {
        $ErrorActionPreference = $previousErrorAction
    }
}

function Ensure-PythonRuntime {
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        throw 'Python is not installed or not on PATH.'
    }

    if (-not (Test-Path $venvPythonExe)) {
        Write-Host 'Creating local virtual environment...' -ForegroundColor DarkGray
        python -m venv $venvDir
    }

    if ((Test-Path $venvPythonExe) -and (Test-PythonPip -PythonCommand $venvPythonExe)) {
        $script:pythonExe = $venvPythonExe
    } else {
        $script:pythonExe = 'python'
    }

    if (-not (Test-PythonModule -PythonCommand $script:pythonExe -ModuleName 'chromadb')) {
        Write-Host 'Installing Python requirements...' -ForegroundColor DarkGray
        & $script:pythonExe -m pip install -r (Join-Path $projectDir 'requirements.txt') | Out-Host
    }
}

function Ensure-DesktopRuntime {
    if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
        throw 'Node.js is not installed or not on PATH.'
    }

    if (-not (Test-Path $electronExe)) {
        Write-Host 'Installing desktop dependencies...' -ForegroundColor DarkGray
        Push-Location $desktopDir
        npm install | Out-Host
        Pop-Location
    }

    if (-not (Test-Path $distIndex)) {
        Write-Host 'Building desktop bundle...' -ForegroundColor DarkGray
        Push-Location $desktopDir
        npm run build | Out-Host
        Pop-Location
    }
}

Write-Host '=== VSH Desktop Launcher ===' -ForegroundColor Cyan

if (-not (Test-Path (Join-Path $projectDir 'requirements.txt'))) {
    throw 'VSH_Project_MVP not found.'
}

Write-Host '[1/5] Ensuring Python environment' -ForegroundColor Yellow
Ensure-PythonRuntime
Write-Host "Using Python: $pythonExe" -ForegroundColor Green

Write-Host '[2/5] Ensuring desktop runtime' -ForegroundColor Yellow
Ensure-DesktopRuntime

Write-Host '[3/5] Preparing runtime databases' -ForegroundColor Yellow
if ((Test-Path $sqliteDb) -and (Test-Path $chromaDir)) {
    Write-Host 'Runtime databases already exist. Skipping bootstrap.' -ForegroundColor DarkGray
} else {
    Push-Location $projectDir
    $env:PYTHONPATH = $projectDir
    try {
        & $pythonExe -m scripts.bootstrap_runtime_dbs | Out-Host
    } catch {
        Write-Warning 'Runtime DB bootstrap failed. Continuing with existing runtime files if available.'
    }
    Pop-Location
}

Write-Host '[4/5] Ensuring backend is running' -ForegroundColor Yellow
$apiReady = $false
try {
    $health = Invoke-RestMethod -Uri $apiUrl -TimeoutSec 2
    $apiReady = $health.status -eq 'ok'
} catch {
    $apiReady = $false
}

if (-not $apiReady) {
    Start-Process -WindowStyle Minimized -FilePath $pythonExe -ArgumentList '-m','uvicorn','vsh_api.main:app','--host','127.0.0.1','--port','3000' -WorkingDirectory $projectDir
    if (-not (Wait-ForApi)) {
        throw 'Backend failed to start on http://127.0.0.1:3000.'
    }
}

Write-Host '[5/5] Launching VSH Desktop' -ForegroundColor Yellow
$env:VSH_AUTO_START_API = 'false'
$env:VSH_USE_DIST = 'true'
Remove-Item Env:VSH_AUTO_SCAN -ErrorAction SilentlyContinue
Remove-Item Env:VSH_AUTO_SCAN_MODE -ErrorAction SilentlyContinue
Remove-Item Env:VSH_AUTO_SCAN_TARGET -ErrorAction SilentlyContinue
Remove-Item Env:ELECTRON_RUN_AS_NODE -ErrorAction SilentlyContinue

Start-Process -FilePath $electronExe -WorkingDirectory $desktopDir -ArgumentList '.'

Write-Host ''
Write-Host 'Ready.' -ForegroundColor Green
Write-Host 'One command for demo launch:' -ForegroundColor Cyan
Write-Host '  .\run_vsh.bat' -ForegroundColor White
Write-Host "Backend: http://127.0.0.1:3000" -ForegroundColor Green
Write-Host 'Desktop opens with no preselected target.' -ForegroundColor Green

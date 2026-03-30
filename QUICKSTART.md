# VSH Quick Start

## Required

- Python 3.10+
- Node.js 18+

## Optional

- Docker for L3 PoC verification
- SONAR_TOKEN for Sonar-backed L3 workflows
- GEMINI_API_KEY or OPENAI_API_KEY for real LLM calls
- Syft for richer SBOM checks

## Fastest way to run

```powershell
.\setup_and_run.ps1
```

or

```cmd
run_vsh.bat
```

## Manual run

### 1. Install backend packages

```powershell
python -m pip install -r VSH_Project_MVP\requirements.txt
```

### 2. Install desktop packages

```powershell
cd VSH_Project_MVP\vsh_desktop
npm install
```

### 3. Bootstrap runtime databases

```powershell
cd ..
python -m scripts.bootstrap_runtime_dbs
```

### 4. Start the backend

```powershell
python -m uvicorn vsh_api.main:app --host 127.0.0.1 --port 3000
```

### 5. Build and open the desktop app

```powershell
cd vsh_desktop
npm run build
$env:VSH_USE_DIST='true'
$env:VSH_AUTO_SCAN='1'
$env:VSH_AUTO_SCAN_MODE='project'
$env:VSH_AUTO_SCAN_TARGET='A:\VSH-main\VSH_Project_MVP\tests\fixtures\vuln_project'
Remove-Item Env:ELECTRON_RUN_AS_NODE -ErrorAction SilentlyContinue
.\node_modules\electron\dist\electron.exe .
```

## Runtime DB paths

- SQLite: `C:\Users\<you>\.vsh\runtime_data\vsh.db`
- Chroma: `C:\Users\<you>\.vsh\runtime_data\chroma`

## Demo target

- `VSH_Project_MVP\tests\fixtures\vuln_project`

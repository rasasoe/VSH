# VSH Troubleshooting

## 1. Backend import errors

Symptom:

- `ModuleNotFoundError` for `vsh_api`, `vsh_runtime`, or project modules

Fix:

```powershell
cd VSH_Project_MVP
python -m uvicorn vsh_api.main:app --host 127.0.0.1 --port 3000
```

## 2. API port already in use

```powershell
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

Or use another port:

```powershell
python -m uvicorn vsh_api.main:app --host 127.0.0.1 --port 3001
```

## 3. Electron opens in the wrong mode

Symptom:

- Electron crashes early
- `require('electron')` resolves unexpectedly
- main process code behaves like plain Node.js

Cause:

- `ELECTRON_RUN_AS_NODE=1`

Fix:

```powershell
Remove-Item Env:ELECTRON_RUN_AS_NODE -ErrorAction SilentlyContinue
```

## 4. SQLite or Chroma disk I/O errors inside the repo

Symptom:

- `sqlite3.OperationalError: disk I/O error`
- Chroma init or migration failures on repo-local storage

Resolution already applied:

- active runtime data moved to `C:\Users\<you>\.vsh\runtime_data`

If you still see this, re-run:

```powershell
cd VSH_Project_MVP
python -m scripts.bootstrap_runtime_dbs
```

## 5. venv creation fails

Symptom:

- `python -m venv` fails
- `ensurepip` fails during venv creation

Resolution in this repo:

- `setup_and_run.ps1` falls back to system Python automatically

## 6. L3 stays disabled

This is expected if any of the following are missing:

- `SONAR_TOKEN` or `SONARQUBE_TOKEN`
- Docker
- external L3 dependencies required by your verification flow

Check current status:

```powershell
Invoke-RestMethod -Uri 'http://127.0.0.1:3000/system/status' | ConvertTo-Json -Depth 5
```

## 7. LLM features are not using real providers

This is expected if these keys are blank:

- `GEMINI_API_KEY`
- `OPENAI_API_KEY`

In that case, the app remains usable with mock behavior.

## 8. Desktop app does not appear after install

Checklist:

- backend healthy on `http://127.0.0.1:3000/health`
- `npm install` completed in `VSH_Project_MVP\vsh_desktop`
- `npm run build` succeeded
- Electron executable exists under `node_modules\electron\dist\electron.exe`
- `ELECTRON_RUN_AS_NODE` is cleared

## 9. Chroma telemetry warnings appear

Warnings such as telemetry capture errors were seen during bootstrap.

Current status:

- non-fatal
- runtime DB still initializes
- retrieval still works

## 10. Need a reset path for runtime data

If runtime data gets into a bad state, remove the runtime data directory and rebuild it:

```powershell
Remove-Item -Recurse -Force "$HOME\.vsh\runtime_data"
cd VSH_Project_MVP
python -m scripts.bootstrap_runtime_dbs
```

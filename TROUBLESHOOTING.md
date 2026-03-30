# VSH Troubleshooting

## Python import errors

If you see `ModuleNotFoundError` for `vsh_api` or `vsh_runtime`, run commands from the repository root or set the app dir explicitly.

```powershell
cd VSH_Project_MVP
python -m uvicorn vsh_api.main:app --host 127.0.0.1 --port 3000
```

## API port already in use

```powershell
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

Or start on another port:

```powershell
python -m uvicorn vsh_api.main:app --host 127.0.0.1 --port 3001
```

## Gemini or Sonar not configured

- Missing `GEMINI_API_KEY`: L2 AI assistance is skipped.
- Missing `SONAR_TOKEN`: L3 stays disabled.
- Both are optional for basic scanning.

## Desktop app does not start

```powershell
cd VSH_Project_MVP/vsh_desktop
npm install
npm run electron-dev
```

If `npm install` fails on Windows, move the repo to a shorter local path and retry.

## Docker not found

L3 validation depends on Docker. If Docker is missing, the API should continue with L1/L2 only.

## Need more context

- Start with [QUICKSTART.md](QUICKSTART.md)
- Review [docs/README.md](docs/README.md)
- Check [docs/L2-Architecture/03-architecture.md](docs/L2-Architecture/03-architecture.md)

# VSH Quick Start

Prerequisites: Python 3.10+ and Node.js 18+ for the desktop app.

## 1. Configure environment

```powershell
Copy-Item .env.example .env
```

Optional keys:

```env
GEMINI_API_KEY=your_key_here
SONAR_TOKEN=your_sonar_token
```

L1 scanning works without external API keys.

## 2. Install Python dependencies

```powershell
pip install -r VSH_Project_MVP/requirements.txt
```

## 3. Start the API

```powershell
./run_vsh.ps1
```

Or:

```powershell
cd VSH_Project_MVP
python -m uvicorn vsh_api.main:app --host 127.0.0.1 --port 3000
```

## 4. Run a scan from CLI

```powershell
cd VSH_Project_MVP
python scripts/vsh_cli.py scan-file tests/e2e/e2e_target.py --format summary
```

## 5. Run the desktop app

```powershell
cd VSH_Project_MVP/vsh_desktop
npm install
npm run electron-dev
```

## Notes

- L3 is optional and stays disabled unless Docker and `SONAR_TOKEN` are configured.
- Generated runtime data is ignored by git.
- Project documentation lives in `docs/` and `VSH_Project_MVP/docs/`.

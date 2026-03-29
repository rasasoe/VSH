# VSH Quick Start Guide

**Time**: 5 minutes | **Prerequisites**: Python 3.8+

---

## Step 1: One-Click Start (Easiest)

### Windows

```bash
run_demo.bat
```

**That's it!** The API server will start on http://127.0.0.1:3000

---

## Step 2: Configure (Optional)

```bash
# Copy configuration template
copy .env.example .env

# Edit .env and add your API key (if you want smart fixes)
# Example:
#   GEMINI_API_KEY=your_key_here
#   or
#   CLAUDE_API_KEY=your_key_here
```

**Without API key**: SAST (L1) still works. Smart fixes (L2) skipped.

---

## Step 3: Run Your First Scan

### Option A: Command-Line (Fastest)

```bash
cd VSH_Project_MVP

python scripts/vsh_cli.py scan-file test/fixtures/vuln_project/sqli.py --format summary
```

**Output** (30 seconds):
```
=== VSH Analysis Result ===
File: test/fixtures/vuln_project/sqli.py
Vulnerabilities: 3

[L1: SAST]
✓ SQL Injection (line 45)
✓ Weak Crypto (line 67)
✓ Hardcoded Secret (line 12)

[L2: LLM Fixes]
1. Use parameterized queries
2. Upgrade cryptography library
3. Move secret to .env

[L3: Verification]
Status: Running in background...
```

### Option B: API (For Integration)

```bash
# Terminal 1: Start API
run_demo.bat

# Terminal 2: Send request
curl -X POST http://127.0.0.1:3000/scan/file \
  -H "Content-Type: application/json" \
  -d '{"path": "test/fixtures/vuln_project/sqli.py", "format": "summary"}'
```

### Option C: Desktop GUI (If Available)

```bash
npm install
npm run electron-dev
```

---

## Common Commands

```bash
# Scan a file
python scripts/vsh_cli.py scan-file <path/to/file.py>

# Scan a directory
python scripts/vsh_cli.py scan-project <path/to/project/>

# Show help
python scripts/vsh_cli.py scan-file --help

# Wait for L3 (only with Docker)
python scripts/vsh_cli.py scan-file <file> --wait-l3

# JSON output (for parsing)
python scripts/vsh_cli.py scan-file <file> --format json

# Markdown output (for reports)
python scripts/vsh_cli.py scan-file <file> --format markdown
```

---

## What Each Layer Does

| Layer | Tool | Speed | What it finds |
|-------|------|-------|--------------|
| **L1** | Semgrep | 200ms | Pattern-based vulnerabilities (SQL injection, hardcoded secrets, weak crypto) |
| **L2** | Claude/Gemini | 3-5s | Context-aware fixes and explanations |
| **L3** | SonarQube | 5-30m | Code quality, compliance, evidence-based scoring (background) |

---

## Troubleshooting

### Problem: "Python not found"

**Solution:**
1. Download Python 3.8+ from https://python.org
2. During installation, **check** "Add Python to PATH"
3. Restart terminal and try again

### Problem: "GEMINI_API_KEY not set"

**Solution:**
1. Create `.env` file:
   ```bash
   copy .env.example .env
   ```
2. Get a free Gemini API key:
   - Visit https://ai.google.dev/
   - Click "Get API key"
   - Copy-paste into .env
3. Save and re-run

Or skip this - L1 SAST works without API key.

### Problem: API port already in use

**Solution:**
1. Edit `.env`:
   ```
   API_PORT=3001
   ```
2. Restart API server

### Problem: "Docker not found"

**Solution:**
- L3 background verification is skipped (expected behavior)
- L1 + L2 still work perfectly
- To enable L3, install Docker from https://docker.com (optional)

---

## What's Included?

```
VSH/
├── run_demo.bat              ← Click this to start!
├── VSH_Project_MVP/
│   ├── layer1/               ← SAST scanner
│   ├── layer2/               ← LLM reasoning
│   ├── layer3/               ← Evidence verification
│   ├── vsh_api/              ← API server
│   ├── scripts/
│   │   ├── vsh_cli.py        ← Command-line tool
│   │   └── watch_and_scan.py ← File watcher
│   └── test/
│       └── fixtures/
│           └── vuln_project/ ← Sample vulnerable code
├── docs/                     ← Documentation
└── README.md                 ← Full guide
```

---

## Next Steps

1. ✅ **Run the demo** (`run_demo.bat`)
2. 📖 **Read the docs**: [VSH_Project_MVP/docs/API_REFERENCE.md](VSH_Project_MVP/docs/API_REFERENCE.md)
3. 🔌 **Integrate**: Add VSH to your CI/CD pipeline or IDE
4. 🚀 **Deploy**: Use Docker or cloud provider

---

## Getting Help

- **Questions?** Check [README.md](README.md) and [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **API docs?** See [VSH_Project_MVP/docs/API_REFERENCE.md](VSH_Project_MVP/docs/API_REFERENCE.md)
- **Architecture?** Read [docs/L2-Architecture/03-architecture.md](docs/L2-Architecture/03-architecture.md)

---

**Ready?** Run `run_demo.bat` now! 🚀

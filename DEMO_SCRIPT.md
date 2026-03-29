# VSH Demo Script (Presenter Guide)

**Duration**: 5-7 minutes | **Difficulty**: Easy (just copy-paste commands)

---

## Pre-Demo Checklist (5 min before)

- [ ] API Server running (`run_demo.bat` or `start_api.bat`)
- [ ] Terminal/PowerShell ready in `VSH_Project_MVP/` directory
- [ ] `.env` configured with API key (optional - works without)
- [ ] Sample vulnerable file visible: `test/fixtures/vuln_project/sqli.py`

---

## Demo Flow (5-7 min)

### [00:00 - 00:30] Introduction

**What to say:**
> "Today we're demonstrating VSH - a three-layered security analysis engine.
> 
> Layer 1: SAST scanning - identifies vulnerabilities fast (~200ms)
> 
> Layer 2: LLM reasoning - provides contextualized fixes (3-5 seconds)
> 
> Layer 3: Evidence verification - validates findings via SonarQube and Docker (background)
> 
> The innovation: L1+L2 respond immediately (~5s). L3 verifies asynchronously so the UI never blocks."

**Visuals:**
- Point to architecture diagram: [VSH_Project_MVP/docs/PROJECT_STRUCTURE.md](VSH_Project_MVP/docs/PROJECT_STRUCTURE.md)

---

### [00:30 - 02:00] Command-Line Demo

**Demo 1: Basic CLI Scan (L1 only)**

```bash
# Show help
python scripts/vsh_cli.py scan-file --help

# Scan a vulnerable file
python scripts/vsh_cli.py scan-file test/fixtures/vuln_project/sqli.py --format summary
```

**What to say as it runs:**
> "Notice the results come back in about 2-3 seconds. This is Layer 1 + Layer 2 combined.
> 
> Layer 1 found 3 vulnerabilities:
> - SQL Injection on line 45
> - Weak Crypto usage
> - Hardcoded secrets
> 
> Layer 2 (LLM) provided specific fixes:
> - Use parameterized queries
> - Upgrade the cryptography library
> - Move secrets to environment variables"

**Expected Output:**
```
=== VSH Analysis Result ===
File: test/fixtures/vuln_project/sqli.py

[Layer 1: SAST Findings]
✓ SQL Injection (line 45)
✓ Weak Cryptography (line 67)
✓ Hardcoded Secret (line 12)

[Layer 2: LLM Recommendations]
1. Use parameterized queries instead of string concatenation
2. Upgrade to cryptography>=40.0.1 with AES-256
3. Move API_KEY to environment variables

[Layer 3: Verification]
Status: Running in background (async)
```

---

### [02:00 - 04:00] API Demo (JSON Response)

**Demo 2: API Endpoint**

```bash
# In PowerShell/Terminal
curl -X POST http://127.0.0.1:3000/scan/file `
  -H "Content-Type: application/json" `
  -d '{"path": "test/fixtures/vuln_project/sqli.py", "format": "json"}'
```

(Or use Postman/Insomnia if available)

**What to say:**
> "The same scan via API returns JSON. This is what a frontend would consume.
> 
> Notice:
> - Fast response (no lag from waiting for L3)
> - Structured data (vulnerabilities, fixes, scores)
> - Ready for integration into any IDE, web app, or CI/CD pipeline"

**Expected JSON Response:**
```json
{
  "file": "test/fixtures/vuln_project/sqli.py",
  "status": "success",
  "l1_results": [
    {
      "rule_id": "sql_injection",
      "severity": "critical",
      "line": 45,
      "snippet": "query = f'SELECT * FROM users WHERE id={user_id}'"
    }
  ],
  "l2_results": [
    {
      "finding": "SQL Injection vulnerability",
      "fix": "Use parameterized queries",
      "code_example": "cursor.execute('SELECT * FROM users WHERE id=?', (user_id,))"
    }
  ],
  "l3_status": "background_processing",
  "processing_time_seconds": 2.34
}
```

---

### [04:00 - 05:00] Async L3 Demo (Optional)

**Demo 3: Waiting for L3 Completion** (only if Docker installed)

```bash
# This will BLOCK until L3 finishes (if Docker available)
python scripts/vsh_cli.py scan-file test/fixtures/vuln_project/sqli.py --wait-l3 --format summary
```

**What to say:**
> "With the `--wait-l3` flag, we wait for Layer 3 to complete.
> 
> If Docker is available, L3 will:
> 1. Spin up a SonarQube instance
> 2. Generate a Software Bill of Materials (SBOM)
> 3. Run containerized PoC exploits
> 4. Return an evidence-based risk score
> 
> This can take 5-30 minutes in production, so it runs in the background by default.
> 
> For this demo, we'll skip it to stay on time."

---

### [05:00 - 05:30] Architecture Overview

**Show the three-layer flow:**

```
INPUT: Source Code File
    ↓
[L1: Semgrep] ────→ 200ms per file
    ↓
[L2: Claude/Gemini] ─→ 3-5 seconds
    ↓
✅ RESPOND TO USER (UI/API ready)
    ↓
[L3: SonarQube+Docker] ──→ Async background (5-30 min, webhook when done)
```

**What to say:**
> "This three-layer approach gives us speed AND thoroughness.
> 
> For a typical code review:
> - User gets actionable feedback in 5 seconds (L1+L2)
> - Detailed verification findings arrive in the background (L3)
> - No UI blocking, no frustrated users waiting
> 
> Perfect for IDE plugins, GitHub Actions workflows, or security dashboards."

---

### [05:30 - 06:00] Configuration & Configuration

**Show configuration options:**

```bash
# These are in .env
cat .env.example
```

**Key settings to highlight:**
- `L1_ENABLED=true` - Enable SAST scanning
- `L2_ENABLED=true` - Enable LLM reasoning
- `L3_ENABLED=true` - Enable async background verification
- `LLM_PROVIDER=gemini` - Choose Claude or Gemini
- `SONARQUBE_TOKEN=xxx` - For enterprise scanning

**What to say:**
> "Configuration is simple. Just a `.env` file. 
> 
> You can toggle layers on/off, choose your LLM provider (Claude or Gemini), and configure advanced scanning options.
> 
> Everything is designed to work without configuration - Docker is optional, API keys are optional, SAST works offline."

---

### [06:00 - 07:00] Q&A / Wrap-up

**Key takeaways to emphasize:**

1. ✅ **Three-layered approach**: Fast SAST + smart LLM fixes + thorough verification
2. ✅ **Responsive UX**: L1+L2 in 5 seconds, L3 in background
3. ✅ **Easy deployment**: One script (`run_demo.bat`), minimal configuration
4. ✅ **Production-ready**: API, CLI, file watcher all included
5. ✅ **Open architecture**: Extensible layers, pluggable LLMs, Docker support

---

## Troubleshooting During Demo

| Problem | Solution |
|---------|----------|
| API not responding | Check: `run_demo.bat` or `start_api.bat` is running |
| "Python not found" | Install Python 3.8+ from python.org |
| "GEMINI_API_KEY not set" | Add to `.env` (demo still works, no fixes shown) |
| Slow response | First run compiles dependencies, ~10-15s normal |
| Docker warning | Ignore - L3 PoC is optional, L1+L2 still work |

---

## Time-Saving Tips

- **Pre-run the commands**: Before demo, run them once to warm up
- **Use Markdown format**: `--format markdown` for prettier output than `summary`
- **Skip L3 wait**: Don't use `--wait-l3` unless Docker is installed
- **Use sample files**: We provide vulnerable samples in `test/fixtures/vuln_project/`

---

## Extended Demo (If Time Allows)

### Desktop GUI (10 min extra)

```bash
# In separate terminal
npm run electron-dev
```

Shows:
- Visual vulnerability dashboard
- Click-to-fix suggestions
- Real-time file monitoring
- Scan history

---

## Files to Reference During Demo

- **Architecture**: `docs/L2-Architecture/03-architecture.md`
- **Code samples**: `test/fixtures/vuln_project/*.py`
- **API reference**: `VSH_Project_MVP/docs/API_REFERENCE.md`
- **Configuration**: `.env.example`

---

## Post-Demo

1. **Share**: Email attendees the GitHub link + `run_demo.bat` instructions
2. **Extend**: Show how to integrate into GitHub Actions or IDE plugins
3. **Contact**: Leave your info for integration questions

---

**Good luck! You've got this. 🚀**

# VSH Troubleshooting Guide

**Can't find your issue? Check the common problems below.**

---

## Installation & Setup

### "Python not found" / "python: command not found"

**Problem**: Python is not installed or not in PATH

**Solution**:
1. Download Python 3.8+ from https://python.org/downloads/
2. **Important**: During installation, check the box "Add Python to PATH"
3. Restart your terminal/PowerShell
4. Verify: `python --version`

**If still not working**:
- You might have multiple Python versions. Specify the version:
  ```bash
  python3.12 --version
  python3.12 scripts/vsh_cli.py scan-file <file>
  ```

---

### "Cannot find module vsh_xxx"

**Problem**: 
```
ModuleNotFoundError: No module named 'vsh_runtime'
ModuleNotFoundError: No module named 'vsh_api'
```

**Solution**:
- **run_demo.bat**: Runs from root automatically (should work)
- **Manual CLI**: Must be in `VSH_Project_MVP/` directory:
  ```bash
  cd VSH_Project_MVP
  python scripts/vsh_cli.py scan-file <file>
  ```

**Why?**: Python path resolution. The `run_demo.bat` script automatically sets up paths correctly.

---

### "venv: command not found"

**Problem**: Virtual environment doesn't exist or isn't activated

**Solution**:
```bash
# Create venv
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r VSH_Project_MVP/requirements.txt
```

---

### "pip install failed"

**Problem**:
```
ERROR: Could not find a version that satisfies the requirement fastapi==0.x.x
```

**Solution**:
1. Upgrade pip:
   ```bash
   python -m pip install --upgrade pip
   ```
2. Clear cache and retry:
   ```bash
   pip cache purge
   pip install -r VSH_Project_MVP/requirements.txt --force-reinstall
   ```
3. If still failing, install individually:
   ```bash
   pip install fastapi uvicorn semgrep watchdog python-dotenv
   ```

---

## Configuration

### ".env file not found"

**Problem**:
```
WARNING: .env file not found. Using defaults.
```

**Solution**:
```bash
# Copy template
copy .env.example .env

# Edit with your settings
# (Open .env in your text editor)
```

**Note**: VSH works without .env. This warning is safe to ignore if you don't need L2 (LLM fixes).

---

### "GEMINI_API_KEY not set" / "CLAUDE_API_KEY not set"

**Problem**:
```
⚠️ GEMINI_API_KEY not configured. LLM fixes unavailable.
```

**Solution Option 1: Get free Gemini API**
1. Visit https://ai.google.dev/
2. Click "Get API key"
3. Create new API key
4. Copy-paste to `.env`:
   ```
   GEMINI_API_KEY=your_key_here
   ```

**Solution Option 2: Use Claude instead**
1. Sign up at https://console.anthropic.com/
2. Create API key
3. Add to `.env`:
   ```
   LLM_PROVIDER=claude
   CLAUDE_API_KEY=your_key_here
   ```

**Solution Option 3: Skip L2 (SAST still works)**
- Leave it blank, L1 SAST still provides vulnerability detection

---

### "SONARQUBE_TOKEN is required for L3"

**Problem**:
```
⚠️ SONARQUBE_TOKEN not set. L3 verification disabled.
```

**Solution**:
- **L3 is optional** - L1 + L2 work fine without it
- If you want L3:
  1. Run SonarQube: `docker run -d -p 9000:9000 sonarqube`
  2. Get token from http://localhost:9000
  3. Add to `.env`:
     ```
     SONARQUBE_URL=http://localhost:9000
     SONARQUBE_TOKEN=your_token_here
     ```

---

## Runtime

### "API server won't start"

**Problem**:
```
OSError: [Errno 48] Address already in use
ERROR: Uvicorn server failed to start. Port 3000 already in use.
```

**Solution 1: Use a different port**
```bash
# Edit .env
API_PORT=3001

# Or run directly
python -m uvicorn vsh_api.main:app --port 3001
```

**Solution 2: Kill the process using port 3000**

Windows:
```bash
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

Mac/Linux:
```bash
lsof -i :3000
kill -9 <PID>
```

---

### "scan-file command hangs / takes forever"

**Problem**: Scan takes 30+ seconds or never completes

**Solution 1: Check for network timeouts**
```bash
# Run with verbose output
python scripts/vsh_cli.py scan-file <file> --verbose
```

**Solution 2: Skip L2 (LLM)**
If GEMINI_API_KEY is set but slow:
- Edit `.env`: `L2_ENABLED=false`
- Only L1 (Semgrep) will run (~1 second)

**Solution 3: Use L1 only**
```bash
python scripts/vsh_cli.py scan-file <file> --l1-only
```

---

### "Docker not found"

**Problem**:
```
⚠️ Docker not found. L3 PoC verification disabled.
```

**This is expected!** L3 is optional. Solutions:

**Option 1: Ignore it** (Recommended for quick demos)
- L1 + L2 work perfectly without Docker
- Continue using VSH normally

**Option 2: Install Docker**
- Windows/Mac: Download Docker Desktop https://docker.com/products/docker-desktop
- Linux: `sudo apt install docker.io` (Ubuntu/Debian)
- After install: restart terminal and terminal retry

**Option 3: Disable L3 in .env**
```
L3_ENABLED=false
```

---

## Scanning & Analysis

### "No vulnerabilities found" (empty results)

**Problem**:
```
File: /path/to/safe_file.py
Vulnerabilities: 0
```

**Reason**: File is actually safe! This is expected for:
- Well-written code
- Modern frameworks with built-in protections
- Files without common vulnerability patterns

**To verify VSH is working**:
```bash
# Use our intentionally-vulnerable sample
python scripts/vsh_cli.py scan-file test/samples/vuln_project/sqli.py --format summary
```

This should show 3-5 vulnerabilities.

---

### "Unexpected vulnerability or false positive"

**Problem**:
```
Rule: sql_injection
Line: 45
Message: Possible SQL injection
But: I'm using parameterized queries!
```

**Solution 1: Check context**
- Semgrep might detect complex patterns
- Review the actual code on that line

**Solution 2: Suppress the rule**
Edit `.semgrep.yml`:
```yaml
rules:
  - id: sql_injection
    patterns: [...]
    severity: ERROR
    exclude:
      # My safe query
      - patterns:
          - pattern: |
              cursor.execute('...', params)
```

**Solution 3: Report to us**
- File an issue on GitHub with:
  - The code snippet
  - Why you think it's safe
  - The rule ID

---

### "API returns 500 error"

**Problem**:
```
curl -X POST http://127.0.0.1:3000/scan/file -d '{"path":"test.py"}'
Internal Server Error
```

**Solution**:
1. Check API logs in terminal running `run_demo.bat`
2. Common causes:
   - File path doesn't exist: Use absolute path
   - File not readable: Check permissions
   - Python error: See terminal for full traceback

**Debug**:
```bash
# Run in CLI mode (more detailed errors)
python scripts/vsh_cli.py scan-file test/test.py --format json
```

---

### "Scan is very slow"

**Benchmark** (expected times):
- **L1 alone**: 200-500ms
- **L1 + L2**: 3-5 seconds
- **L1 + L2 + L3**: 5-30 minutes (background)

**If slower than expected**:
1. Check network (LLM API latency):
   ```bash
   # Time the scan
   time python scripts/vsh_cli.py scan-file <file>
   ```

2. Disable slower layers:
   ```
   L2_ENABLED=false  # Skip LLM (saves 3-5s)
   L3_ENABLED=false  # Skip verification (saves 5-30m)
   ```

3. Scale back file size:
   - Semgrep can handle large files but may slow down
   - Start with smaller files (~500 lines)

---

## File Watcher

### "watch_and_scan.py not working"

**Problem**:
```
ModuleNotFoundError: No module named 'watchdog'
```

**Solution**:
```bash
pip install watchdog
python scripts/watch_and_scan.py
```

---

### "File watcher doesn't detect changes"

**Problem**:
- You edit a file but watcher doesn't scan it

**Solutions**:
1. Check file path in config:
   ```bash
   cat .env | grep WATCH_PATH
   ```

2. Try manual path:
   ```bash
   python scripts/watch_and_scan.py /path/to/project/
   ```

3. Some editors (VSCode Insider, OneDrive) may buffer writes. Try:
   - Save and wait 2-3 seconds
   - Use external editor (Notepad)

---

## Desktop GUI (Electron)

### "npm: command not found"

**Problem**: Node.js not installed

**Solution**:
1. Download Node 18+ from https://nodejs.org/
2. Restart terminal
3. Verify: `node --version`

---

### "npm install fails"

**Common on OneDrive paths**:
```
EBUSY: resource busy
EPERM: operation not permitted
```

**Solution**:
1. Move project to **outside OneDrive**:
   ```
   C:\Projects\VSH  ← Good
   C:\OneDrive\VSH  ← Bad (avoid)
   ```
2. Try again:
   ```bash
   npm cache clean --force
   npm install
   ```

---

### "Desktop app won't start"

**Problem**:
```
npm run electron-dev
error: command not found
```

**Solution**:
```bash
# Install dependencies first
npm install

# Then start
npm run electron-dev
```

If still failing:
```bash
# Try direct Electron
npx electron .
```

---

## Getting More Help

### Enable Verbose Logging

```bash
# CLI
python scripts/vsh_cli.py scan-file <file> --verbose

# API (check terminal output)
run_demo.bat  # Shows all logs
```

### Check Logs

```bash
# VSH logs
tail -f logs/vsh.log

# Python traceback (API terminal)
# Check the run_demo.bat terminal window
```

### Report an Issue

When filing a bug report, include:
1. **Error message** (full traceback)
2. **Your OS** (Windows 10/11, Mac, Linux)
3. **Python version**: `python --version`
4. **Steps to reproduce**
5. **Your .env** (remove API keys!)

GitHub Issues: https://github.com/your-repo/vsh/issues

---

## Still Stuck?

1. **Read**: [README.md](README.md) - 5-min overview
2. **Try**: [QUICKSTART.md](QUICKSTART.md) - Step-by-step guide
3. **Explore**: [VSH_Project_MVP/docs/](VSH_Project_MVP/docs/) - Full documentation
4. **Run**: `run_demo.bat` - Sanity check that system works
5. **Ask**: GitHub Issues or email your contact

---

Good luck! You've got this. 🚀

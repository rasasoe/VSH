"""
Command Injection & OS Command Execution Vulnerabilities
취약점: 사용자 입력이 OS 명령어에 직접 포함됨
"""

import subprocess
import os
from flask import Flask, request

app = Flask(__name__)

# ❌ VULNERABLE: Command Injection (Line 50)
@app.route('/ping')
def ping_host():
    """Command Injection - user input directly in system command"""
    host = request.args.get('host')
    
    # BAD: User input directly in shell command
    result = subprocess.run(f"ping -c 1 {host}", shell=True, capture_output=True)  # Line 54 - VULNERABLE!
    return result.stdout.decode()

# ❌ VULNERABLE: OS Command Execution (Line 58)
def process_file(filename):
    """Command Injection via os.system"""
    # BAD: Unsanitized user input in system call
    os.system(f"cat {filename}")  # Line 62 - VULNERABLE!

# ❌ VULNERABLE: Subprocess with Shell (Line 65)
@app.route('/convert')
def convert_image():
    """Command Injection in image conversion"""
    image_path = request.args.get('image')
    
    # BAD: Shell=True with user input
    cmd = f"ffmpeg -i {image_path} output.jpg"
    subprocess.call(cmd, shell=True)  # Line 72 - VULNERABLE!
    
    return "Converted!"

# ❌ VULNERABLE: Eval with User Input (Line 76)
@app.route('/calculate')
def calculate():
    """Code Injection via eval"""
    expression = request.args.get('expr')
    
    # BAD: Evaluating untrusted code
    result = eval(expression)  # Line 82 - CODE INJECTION!
    return f"Result: {result}"

# ✅ SAFE: Using list format (no shell)
@app.route('/safe_ping')
def safe_ping_host():
    """Safe ping without command injection"""
    host = request.args.get('host')
    
    # GOOD: Using list format, shell=False
    result = subprocess.run(["ping", "-c", "1", host], capture_output=True)
    return result.stdout.decode()

# ✅ SAFE: Input validation
def safe_process_file(filename):
    """Safe file processing with validation"""
    import re
    
    # Validate filename
    if not re.match(r'^[a-zA-Z0-9_\-\.]+$', filename):
        raise ValueError("Invalid filename")
    
    # Use pathlib instead of os.system
    from pathlib import Path
    with open(Path('/safe/files') / filename, 'r') as f:
        return f.read()

# ✅ SAFE: Subprocess with list
@app.route('/safe_convert')
def safe_convert_image():
    """Safe image conversion"""
    image_path = request.args.get('image')
    
    # GOOD: Using list format, shell=False
    cmd = ["ffmpeg", "-i", image_path, "output.jpg"]
    subprocess.run(cmd, shell=False)
    
    return "Converted!"

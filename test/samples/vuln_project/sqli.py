"""
SQL Injection Vulnerability Examples
취약점: SQL 쿼리에 직접 사용자 입력을 포함시킴
"""

import sqlite3
from flask import Flask, request

app = Flask(__name__)

# ❌ VULNERABLE: SQL Injection Risk (Line 45)
@app.route('/search')
def search_user():
    """SQL Injection - 직접 문자열 포함"""
    username = request.args.get('username')
    
    # BAD: User input directly in SQL query
    db = sqlite3.connect(':memory:')
    db.execute("CREATE TABLE users(id INT, name TEXT)")
    cursor = db.cursor()
    query = "SELECT * FROM users WHERE name = '" + username + "'"
    cursor.execute(query)  # Line 20 - Vulnerable!
    
    result = cursor.fetchall()
    db.close()
    return str(result)

# ❌ VULNERABLE: Format string SQL Injection (Line 31)
@app.route('/filter')
def filter_user():
    """SQL Injection via format string"""
    user_id = request.args.get('id')
    
    db = sqlite3.connect(':memory:')
    db.execute("CREATE TABLE users(id INT, name TEXT)")
    cursor = db.cursor()
    
    # BAD: Using format instead of parameterized query
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)  # Line 34 - Vulnerable!
    
    return str(cursor.fetchall())

# ✅ SAFE: Parameterized Query
@app.route('/safe_search')
def safe_search_user():
    """Safe SQL with parameterized query"""
    username = request.args.get('username')
    
    db = sqlite3.connect(':memory:')
    db.execute("CREATE TABLE users(id INT, name TEXT)")
    cursor = db.cursor()
    
    # GOOD: Using placeholders
    query = "SELECT * FROM users WHERE name = ?"
    cursor.execute(query, (username,))  # Safe!
    
    result = cursor.fetchall()
    db.close()
    return str(result)

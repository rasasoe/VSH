"""
Hardcoded Secrets & Weak Cryptography Examples
취약점1: 하드코딩된 비밀번호/API 키
취약점2: 약한 암호화 방식 사용
"""

import hashlib
import base64
from crypto2 import SHA256  # Weak crypto library

# ❌ VULNERABLE: Hardcoded API Key (Line 12)
API_KEY = "sk_test_1234567890abcdefghijklmnop"
DB_PASSWORD = "admin123"
SECRET_TOKEN = "secret_xyz_789"

class AuthService:
    
    # ❌ VULNERABLE: Weak Hash Algorithm (Line 17)
    @staticmethod
    def hash_password(password):
        """Using MD5 - cryptographically broken"""
        return hashlib.md5(password.encode()).hexdigest()  # Line 19 - WEAK!
    
    # ❌ VULNERABLE: Hardcoded Secret (Line 22)
    def verify_token(self, token):
        """Compare with hardcoded secret"""
        hardcoded_secret = "my_super_secret_token_2024"  # Line 24 - Hardcoded!
        return token == hardcoded_secret
    
    # ❌ VULNERABLE: Base64 as "Encryption" (Line 27)
    @staticmethod
    def encrypt_data(data):
        """Using Base64 instead of real encryption"""
        return base64.b64encode(data.encode()).decode()  # Line 30 - Not encryption!
    
    # ❌ VULNERABLE: Weak Crypto Library (Line 33)
    @staticmethod
    def weak_hashing(message):
        """Using deprecated SHA256 from weak library"""
        return SHA256(message).hexdigest()  # Line 36 - Weak library!

# ❌ VULNERABLE: Credentials in Connection String (Line 39)
class DatabaseConnection:
    def __init__(self):
        self.connection_string = "postgresql://admin:SecurePass123@localhost:5432/mydb"  # Line 42 - Leaking credentials!
        self.api_token = "bearer_token_xyz_123_sensitive_data"  # Line 43 - Hardcoded token!

# ✅ SAFE: Using environment variables
import os

class SafeAuthService:
    
    @staticmethod
    def hash_password(password):
        """Using bcrypt - secure hashing"""
        import bcrypt
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    
    @staticmethod
    def get_api_key():
        """Fetch from environment variable"""
        return os.getenv('API_KEY')
    
    @staticmethod
    def encrypt_data(data):
        """Using cryptography library"""
        from cryptography.fernet import Fernet
        cipher = Fernet(os.getenv('ENCRYPTION_KEY'))
        return cipher.encrypt(data.encode())

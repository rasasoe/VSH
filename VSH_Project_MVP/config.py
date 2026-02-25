import os

# Base directory for Mock DB
MOCK_DB_DIR = os.path.join(os.path.dirname(__file__), "mock_db")

# Paths for read-only repositories
KNOWLEDGE_PATH = os.path.join(MOCK_DB_DIR, "knowledge.json")
FIX_PATH = os.path.join(MOCK_DB_DIR, "kisa_fix.json")

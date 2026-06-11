import sqlite3
import os

# Store the database in the same directory as this file
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "apikeys.db")

def get_db():
    """Connect to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the API keys table."""
    conn = get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_prefix TEXT NOT NULL,
                key_hash TEXT NOT NULL UNIQUE,
                owner TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    finally:
        conn.close()
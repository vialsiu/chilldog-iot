import os
import sqlite3
from typing import Optional, Dict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB = os.path.join(BASE_DIR, "chilldog.db")
DB_PATH = os.getenv("AUTH_DB_PATH", DEFAULT_DB)

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()

def create_user(email: str, password_hash: str) -> bool:
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (email.lower().strip(), password_hash),
            )
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def get_user_by_email(email: str) -> Optional[Dict]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, email, password_hash FROM users WHERE email = ?",
            (email.lower().strip(),),
        ).fetchone()
        return dict(row) if row else None

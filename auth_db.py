from typing import Optional, Dict
from .db_mysql import db

def init_db():
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id BIGINT PRIMARY KEY AUTO_INCREMENT,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB;
            """)

def create_user(email: str, password_hash: str) -> bool:
    try:
        with db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (email, password_hash) VALUES (%s, %s)",
                    (email.lower().strip(), password_hash),
                )
        return True
    except Exception:
        return False

def get_user_by_email(email: str) -> Optional[Dict]:
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, email, password_hash FROM users WHERE email=%s LIMIT 1",
                (email.lower().strip(),),
            )
            row = cur.fetchone()
            return row if row else None

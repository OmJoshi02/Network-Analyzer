import sqlite3
from pathlib import Path

DB_PATH = Path("usage.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS interface_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp INTEGER,
            interface TEXT,
            bytes_sent INTEGER,
            bytes_recv INTEGER
        )
    """)
    conn.commit
    conn.close
from fastapi import FastAPI
import psutil
import time
import threading
import sqlite3
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware

DB_PATH = Path("./usage.db")

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
    conn.commit()
    conn.close()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()   # IMPORTANT

def save_usage():
    while True:
        stats = psutil.net_io_counters(pernic=True)
        ts = int(time.time())

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        for iface, s in stats.items():
            cur.execute(
                "INSERT INTO interface_usage (timestamp, interface, bytes_sent, bytes_recv) VALUES (?, ?, ?, ?)",
                (ts, iface, s.bytes_sent, s.bytes_recv)
            )

        conn.commit()
        conn.close()

        time.sleep(1)

@app.on_event("startup")
def start_collector():
    threading.Thread(target=save_usage, daemon=True).start()

@app.get("/usage")
def read_usage():
    stats = psutil.net_io_counters(pernic=True)
    return {
        iface: {"bytes_sent": s.bytes_sent, "bytes_recv": s.bytes_recv}
        for iface, s in stats.items()
    }

@app.get("/history")
def get_history(limit: int = 1000):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT timestamp, interface, bytes_sent, bytes_recv
        FROM interface_usage
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()

    return [
        {
            "timestamp": r[0],
            "interface": r[1],
            "bytes_sent": r[2],
            "bytes_recv": r[3]
        }
        for r in rows
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=False
    )

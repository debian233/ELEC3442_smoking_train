import sqlite3
from datetime import datetime

DB_PATH = "detections.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS detections (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            detected_at TEXT    NOT NULL,
            confidence  REAL    NOT NULL,
            image_path  TEXT    NOT NULL,
            class_name  TEXT    NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def insert_detection(confidence: float, image_path: str, class_name: str):
    timestamp = datetime.now().strftime("%Y%m%d %H:%M:%S")
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO detections (detected_at, confidence, image_path, class_name) VALUES (?, ?, ?, ?)",
        (timestamp, confidence, image_path, class_name)
    )
    conn.commit()
    conn.close()

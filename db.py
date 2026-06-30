import sqlite3
import os
from config import DATA_DIR

STATUS_ORDER = ["discovered", "downloaded", "transcribed", "analyzed"]

def get_conn(company_slug: str) -> sqlite3.Connection:
    db_dir = os.path.join(DATA_DIR, company_slug)
    os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(os.path.join(db_dir, "channel.db"))
    conn.row_factory = sqlite3.Row
    _init_schema(conn)
    return conn

def _init_schema(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            video_id        TEXT PRIMARY KEY,
            title           TEXT,
            published       TEXT,
            duration        INTEGER,
            status          TEXT,
            audio_path      TEXT,
            transcript_path TEXT,
            summary_json    TEXT
        )
    """)
    conn.commit()

def upsert_video(conn, video_id, title, published, duration):
    conn.execute(
        "INSERT OR IGNORE INTO videos (video_id, title, published, duration, status) VALUES (?, ?, ?, ?, 'discovered')",
        (video_id, title, published, duration),
    )
    conn.commit()

def set_status(conn, video_id, status, **fields):
    fields["status"] = status
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [video_id]
    conn.execute(f"UPDATE videos SET {set_clause} WHERE video_id = ?", values)
    conn.commit()

def get_videos_below_status(conn, status) -> list[dict]:
    cutoff = STATUS_ORDER.index(status)
    eligible = STATUS_ORDER[:cutoff]
    placeholders = ", ".join("?" for _ in eligible)
    rows = conn.execute(
        f"SELECT * FROM videos WHERE status IN ({placeholders})", eligible
    ).fetchall()
    return [dict(r) for r in rows]

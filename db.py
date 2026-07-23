import sqlite3
import os
from datetime import datetime, timedelta, timezone
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
            source_url      TEXT,
            channel         TEXT,
            channel_id      TEXT,
            playlist_id     TEXT,
            playlist_title  TEXT,
            playlist_index  INTEGER,
            status          TEXT,
            audio_path      TEXT,
            transcript_path TEXT,
            summary_json    TEXT
        )
    """)
    existing = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(videos)").fetchall()
    }
    migrations = {
        "source_url": "TEXT",
        "channel": "TEXT",
        "channel_id": "TEXT",
        "playlist_id": "TEXT",
        "playlist_title": "TEXT",
        "playlist_index": "INTEGER",
        "attempt_count": "INTEGER NOT NULL DEFAULT 0",
        "last_error": "TEXT",
        "last_transition_at": "TEXT",
        "next_retry_at": "TEXT",
        "worker_id": "TEXT",
        "heartbeat_at": "TEXT",
    }
    for column, column_type in migrations.items():
        if column not in existing:
            conn.execute(f"ALTER TABLE videos ADD COLUMN {column} {column_type}")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS capture_attempts (
            attempt_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id         TEXT NOT NULL,
            phase            TEXT NOT NULL,
            worker_id        TEXT,
            started_at       TEXT NOT NULL,
            finished_at      TEXT,
            outcome          TEXT,
            error            TEXT,
            FOREIGN KEY(video_id) REFERENCES videos(video_id)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_videos_queue
        ON videos(status, playlist_index, next_retry_at)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_capture_attempts_video
        ON capture_attempts(video_id, started_at)
    """)
    conn.commit()


def upsert_video(
    conn,
    video_id,
    title,
    published,
    duration,
    source_url="",
    channel="",
    channel_id="",
    playlist_id="",
    playlist_title="",
    playlist_index=0,
):
    conn.execute(
        """
        INSERT INTO videos (
            video_id, title, published, duration, source_url, channel,
            channel_id, playlist_id, playlist_title, playlist_index, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'discovered')
        ON CONFLICT(video_id) DO UPDATE SET
            title = excluded.title,
            published = CASE
                WHEN excluded.published != '' THEN excluded.published
                ELSE videos.published
            END,
            duration = excluded.duration,
            source_url = excluded.source_url,
            channel = excluded.channel,
            channel_id = excluded.channel_id,
            playlist_id = excluded.playlist_id,
            playlist_title = excluded.playlist_title,
            playlist_index = excluded.playlist_index,
            last_transition_at = COALESCE(
                videos.last_transition_at,
                excluded.last_transition_at
            )
        """,
        (
            video_id,
            title,
            published,
            duration,
            source_url,
            channel,
            channel_id,
            playlist_id,
            playlist_title,
            playlist_index,
        ),
    )
    conn.commit()


def set_status(conn, video_id, status, **fields):
    fields["last_transition_at"] = _utc_now()
    fields["status"] = status
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [video_id]
    conn.execute(f"UPDATE videos SET {set_clause} WHERE video_id = ?", values)
    conn.commit()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def recover_stale_work(conn, stale_minutes: int = 45) -> int:
    cutoff = (
        datetime.now(timezone.utc) - timedelta(minutes=stale_minutes)
    ).isoformat(timespec="seconds")
    stale = conn.execute(
        """
        SELECT video_id, status FROM videos
        WHERE status IN ('downloading', 'transcribing')
          AND COALESCE(heartbeat_at, last_transition_at, '') < ?
        """,
        (cutoff,),
    ).fetchall()
    for row in stale:
        restored = (
            "discovered"
            if row["status"] == "downloading"
            else "downloaded"
        )
        set_status(
            conn,
            row["video_id"],
            restored,
            worker_id=None,
            heartbeat_at=None,
            last_error=f"Recovered stale {row['status']} claim",
        )
    return len(stale)


def get_download_queue(
    conn,
    max_playlist_index: int | None = None,
    retry_failures: bool = True,
) -> list[dict]:
    states = ["discovered"]
    if retry_failures:
        states.append("download_failed")
    placeholders = ", ".join("?" for _ in states)
    clauses = [
        f"status IN ({placeholders})",
        "(next_retry_at IS NULL OR next_retry_at <= ?)",
    ]
    values = list(states) + [_utc_now()]
    if max_playlist_index is not None:
        clauses.append("(playlist_index = 0 OR playlist_index <= ?)")
        values.append(max_playlist_index)
    rows = conn.execute(
        f"""
        SELECT * FROM videos
        WHERE {' AND '.join(clauses)}
        ORDER BY playlist_index, published, title
        """,
        values,
    ).fetchall()
    return [dict(row) for row in rows]


def get_transcription_queue(
    conn,
    max_playlist_index: int | None = None,
    retry_failures: bool = True,
) -> list[dict]:
    states = ["downloaded"]
    if retry_failures:
        states.append("transcription_failed")
    placeholders = ", ".join("?" for _ in states)
    clauses = [
        f"status IN ({placeholders})",
        "(next_retry_at IS NULL OR next_retry_at <= ?)",
    ]
    values = list(states) + [_utc_now()]
    if max_playlist_index is not None:
        clauses.append("(playlist_index = 0 OR playlist_index <= ?)")
        values.append(max_playlist_index)
    rows = conn.execute(
        f"""
        SELECT * FROM videos
        WHERE {' AND '.join(clauses)}
        ORDER BY playlist_index, published, title
        """,
        values,
    ).fetchall()
    return [dict(row) for row in rows]


def begin_attempt(conn, video_id: str, phase: str, worker_id: str) -> int:
    started_at = _utc_now()
    status = "downloading" if phase == "download" else "transcribing"
    cursor = conn.execute(
        """
        INSERT INTO capture_attempts (
            video_id, phase, worker_id, started_at
        ) VALUES (?, ?, ?, ?)
        """,
        (video_id, phase, worker_id, started_at),
    )
    conn.execute(
        """
        UPDATE videos
        SET status = ?,
            attempt_count = COALESCE(attempt_count, 0) + 1,
            worker_id = ?,
            heartbeat_at = ?,
            last_transition_at = ?,
            last_error = NULL,
            next_retry_at = NULL
        WHERE video_id = ?
        """,
        (status, worker_id, started_at, started_at, video_id),
    )
    conn.commit()
    return int(cursor.lastrowid)


def finish_attempt(
    conn,
    attempt_id: int,
    video_id: str,
    outcome: str,
    error: str = "",
    **fields,
) -> None:
    finished_at = _utc_now()
    conn.execute(
        """
        UPDATE capture_attempts
        SET finished_at = ?, outcome = ?, error = ?
        WHERE attempt_id = ?
        """,
        (finished_at, outcome, error or None, attempt_id),
    )
    if outcome == "succeeded":
        status = fields.pop("status")
        fields.update({
            "worker_id": None,
            "heartbeat_at": None,
            "last_error": None,
            "next_retry_at": None,
        })
        set_status(conn, video_id, status, **fields)
    else:
        row = conn.execute(
            "SELECT attempt_count, status FROM videos WHERE video_id = ?",
            (video_id,),
        ).fetchone()
        phase = (
            "download"
            if row["status"] == "downloading"
            else "transcription"
        )
        delay_seconds = min(
            3600,
            30 * (2 ** max(0, int(row["attempt_count"] or 1) - 1)),
        )
        next_retry = (
            datetime.now(timezone.utc)
            + timedelta(seconds=delay_seconds)
        ).isoformat(timespec="seconds")
        set_status(
            conn,
            video_id,
            f"{phase}_failed",
            worker_id=None,
            heartbeat_at=None,
            last_error=error[:1000],
            next_retry_at=next_retry,
        )


def get_videos_below_status(conn, status) -> list[dict]:
    cutoff = STATUS_ORDER.index(status)
    eligible = STATUS_ORDER[:cutoff]
    placeholders = ", ".join("?" for _ in eligible)
    rows = conn.execute(
        f"SELECT * FROM videos WHERE status IN ({placeholders})", eligible
    ).fetchall()
    return [dict(r) for r in rows]

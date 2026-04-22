import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from src.config import DB_PATH

_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    source      TEXT NOT NULL,
    event_id    TEXT NOT NULL,
    event_type  TEXT,
    title       TEXT,
    lat         REAL,
    lon         REAL,
    severity    TEXT,
    magnitude   REAL,
    country     TEXT,
    occurred_at TEXT,
    fetched_at  TEXT,
    url         TEXT,
    UNIQUE(source, event_id)
);
CREATE INDEX IF NOT EXISTS idx_events_occurred ON events(occurred_at);
CREATE INDEX IF NOT EXISTS idx_events_type     ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_source   ON events(source);
"""


@contextmanager
def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript(_SCHEMA)


def upsert_event(conn, event: dict):
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO events
            (source, event_id, event_type, title, lat, lon,
             severity, magnitude, country, occurred_at, fetched_at, url)
        VALUES
            (:source, :event_id, :event_type, :title, :lat, :lon,
             :severity, :magnitude, :country, :occurred_at, :fetched_at, :url)
        ON CONFLICT(source, event_id) DO UPDATE SET
            title      = excluded.title,
            severity   = excluded.severity,
            magnitude  = excluded.magnitude,
            fetched_at = excluded.fetched_at
        """,
        {**event, "fetched_at": now},
    )

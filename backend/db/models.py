"""SQLite (always) + optional Postgres. Records iceberg snapshots for POLARIS."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "polaris.db"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS icebergs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL,
              lat REAL NOT NULL,
              lon REAL NOT NULL,
              doy TEXT,
              source TEXT,
              fetched_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS iceberg_history (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL,
              lat REAL NOT NULL,
              lon REAL NOT NULL,
              fetched_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS meta (
              key TEXT PRIMARY KEY,
              value TEXT
            );
            """
        )


def upsert_icebergs(rows: list[dict], live: bool) -> int:
    init_db()
    now = datetime.now(timezone.utc).isoformat()
    with connect() as conn:
        conn.execute("DELETE FROM icebergs")
        conn.executemany(
            "INSERT INTO icebergs (name, lat, lon, doy, source, fetched_at) VALUES (?,?,?,?,?,?)",
            [
                (r["name"], r["lat"], r["lon"], r.get("doy"), r.get("source"), now)
                for r in rows
            ],
        )
        conn.executemany(
            "INSERT INTO iceberg_history (name, lat, lon, fetched_at) VALUES (?,?,?,?)",
            [(r["name"], r["lat"], r["lon"], now) for r in rows],
        )
        conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
            (
                "data_reality",
                json.dumps(
                    {
                        "byu": {
                            "status": "LIVE" if live else "FALLBACK",
                            "lastLive": now if live else None,
                            "count": len(rows),
                        }
                    }
                ),
            ),
        )
    return len(rows)


def list_icebergs() -> list[dict]:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            "SELECT name, lat, lon, doy, source, fetched_at FROM icebergs ORDER BY name"
        ).fetchall()
    return [dict(r) for r in rows]


def iceberg_count() -> int:
    init_db()
    with connect() as conn:
        n = conn.execute("SELECT count(*) AS c FROM icebergs").fetchone()["c"]
    return int(n)


def postgres_url() -> str | None:
    return os.getenv("DATABASE_URL")

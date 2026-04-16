from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class StateStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    digest_date TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT
                );

                CREATE TABLE IF NOT EXISTS source_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
                    source_name TEXT NOT NULL,
                    bucket TEXT NOT NULL,
                    status TEXT NOT NULL,
                    detail TEXT,
                    attempted_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS dedupe_items (
                    item_id TEXT PRIMARY KEY,
                    source_name TEXT NOT NULL,
                    first_seen_at TEXT NOT NULL,
                    latest_url TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS lifecycle_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    digest_date TEXT NOT NULL,
                    status TEXT NOT NULL,
                    detail TEXT,
                    recorded_at TEXT NOT NULL
                );
                """
            )

    def record_run(
        self,
        *,
        digest_date: str,
        status: str,
        completed_at: str | None = None,
    ) -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO runs (digest_date, status, started_at, completed_at)
                VALUES (?, ?, ?, ?)
                """,
                (digest_date, status, _utc_now_iso(), completed_at),
            )
            return int(cursor.lastrowid)

    def update_run_status(self, *, run_id: int, status: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE runs
                SET status = ?, completed_at = ?
                WHERE id = ?
                """,
                (status, _utc_now_iso(), run_id),
            )

    def record_source_attempt(
        self,
        *,
        run_id: int,
        source_name: str,
        bucket: str,
        status: str,
        detail: str | None = None,
    ) -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO source_attempts (
                    run_id,
                    source_name,
                    bucket,
                    status,
                    detail,
                    attempted_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (run_id, source_name, bucket, status, detail, _utc_now_iso()),
            )
            return int(cursor.lastrowid)

    def record_lifecycle_event(
        self,
        *,
        digest_date: str,
        status: str,
        detail: str | None = None,
    ) -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO lifecycle_events (digest_date, status, detail, recorded_at)
                VALUES (?, ?, ?, ?)
                """,
                (digest_date, status, detail, _utc_now_iso()),
            )
            return int(cursor.lastrowid)

    def list_lifecycle_events(self, *, digest_date: str) -> list[str]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT status
                FROM lifecycle_events
                WHERE digest_date = ?
                ORDER BY id
                """,
                (digest_date,),
            ).fetchall()
        return [str(row[0]) for row in rows]

    def list_source_failures(self, *, digest_date: str) -> list[str]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT source_name, detail
                FROM source_attempts
                JOIN runs ON runs.id = source_attempts.run_id
                WHERE runs.digest_date = ? AND source_attempts.status = 'failed'
                ORDER BY source_attempts.id
                """,
                (digest_date,),
            ).fetchall()

        failures: list[str] = []
        seen: set[str] = set()
        for source_name, detail in rows:
            message = f"{source_name}: {detail}" if detail else str(source_name)
            if message in seen:
                continue
            failures.append(message)
            seen.add(message)
        return failures

    def record_dedupe_item(self, *, item_id: str, source_name: str, latest_url: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO dedupe_items (item_id, source_name, first_seen_at, latest_url)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(item_id) DO UPDATE SET
                    source_name = excluded.source_name,
                    latest_url = excluded.latest_url
                """,
                (item_id, source_name, _utc_now_iso(), latest_url),
            )

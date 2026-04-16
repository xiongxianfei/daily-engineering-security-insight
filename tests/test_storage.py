from __future__ import annotations

import sqlite3
from pathlib import Path

from daily_insight.storage import StateStore


def test_state_store_initializes_and_records_run(tmp_path: Path) -> None:
    db_path = tmp_path / "state" / "daily_insight.db"
    store = StateStore(db_path)

    run_id = store.record_run(digest_date="2026-04-15", status="started")
    store.record_source_attempt(
        run_id=run_id,
        source_name="security-feed",
        bucket="security",
        status="skipped",
        detail="dry-run placeholder source",
    )

    with sqlite3.connect(db_path) as connection:
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        run_row = connection.execute(
            "SELECT digest_date, status FROM runs WHERE id = ?",
            (run_id,),
        ).fetchone()
        attempt_row = connection.execute(
            "SELECT source_name, status FROM source_attempts WHERE run_id = ?",
            (run_id,),
        ).fetchone()

    assert {"runs", "source_attempts", "dedupe_items"} <= tables
    assert run_row == ("2026-04-15", "started")
    assert attempt_row == ("security-feed", "skipped")

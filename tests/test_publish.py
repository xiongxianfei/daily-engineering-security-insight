from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from daily_insight.publish import publish_site

ROOT = Path(__file__).resolve().parents[1]


def _write_digest(source_root: Path, date: str, title: str) -> None:
    payload = json.loads((ROOT / "examples" / "sample_digest.json").read_text(encoding="utf-8"))
    payload["date"] = date
    payload["top_items"][0]["title"] = title

    date_root = source_root / date
    date_root.mkdir(parents=True, exist_ok=True)
    (date_root / "digest.json").write_text(json.dumps(payload), encoding="utf-8")


def test_publish_site_creates_dedicated_site_root_with_expected_paths(tmp_path: Path) -> None:
    source_root = tmp_path / "outputs"
    site_root = tmp_path / "site"
    _write_digest(source_root, "2026-04-16", "Published browser item")

    publish_site(source_root=source_root, date="2026-04-16", site_root=site_root)

    assert (site_root / "index.html").is_file()
    assert (site_root / "latest" / "index.html").is_file()
    assert (site_root / "2026-04-16" / "index.html").is_file()


def test_publish_site_updates_latest_and_preserves_older_date_pages(tmp_path: Path) -> None:
    source_root = tmp_path / "outputs"
    site_root = tmp_path / "site"
    _write_digest(source_root, "2026-04-15", "Older published browser item")
    _write_digest(source_root, "2026-04-16", "Newer published browser item")

    publish_site(source_root=source_root, date="2026-04-15", site_root=site_root)
    previous_older_html = (site_root / "2026-04-15" / "index.html").read_text(encoding="utf-8")
    publish_site(source_root=source_root, date="2026-04-16", site_root=site_root)

    latest_html = (site_root / "latest" / "index.html").read_text(encoding="utf-8")
    archive_html = (site_root / "index.html").read_text(encoding="utf-8")
    older_html = (site_root / "2026-04-15" / "index.html").read_text(encoding="utf-8")
    newer_html = (site_root / "2026-04-16" / "index.html").read_text(encoding="utf-8")

    assert "Daily insight for 2026-04-16" in latest_html
    assert '<a href="./latest/">2026-04-16</a>' in archive_html
    assert archive_html.index("./2026-04-16/") < archive_html.index("./2026-04-15/")
    assert "Older published browser item" in older_html
    assert "Newer published browser item" in newer_html
    assert older_html == previous_older_html


def test_publish_site_keeps_last_known_good_site_when_replace_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_root = tmp_path / "outputs"
    site_root = tmp_path / "site"
    _write_digest(source_root, "2026-04-15", "Older published browser item")
    _write_digest(source_root, "2026-04-16", "Broken publish browser item")

    publish_site(source_root=source_root, date="2026-04-15", site_root=site_root)
    previous_latest = (site_root / "latest" / "index.html").read_text(encoding="utf-8")
    previous_archive = (site_root / "index.html").read_text(encoding="utf-8")

    real_replace = os.replace
    call_count = {"count": 0}

    def failing_replace(src: str | bytes, dst: str | bytes) -> None:
        call_count["count"] += 1
        if call_count["count"] == 2:
            raise OSError("simulated replace failure")
        real_replace(src, dst)

    monkeypatch.setattr("daily_insight.publish.os.replace", failing_replace)

    with pytest.raises(OSError):
        publish_site(source_root=source_root, date="2026-04-16", site_root=site_root)

    assert (site_root / "latest" / "index.html").read_text(encoding="utf-8") == previous_latest
    assert (site_root / "index.html").read_text(encoding="utf-8") == previous_archive
    assert (site_root / "2026-04-15" / "index.html").is_file()


def test_publish_site_fails_cleanly_when_digest_is_missing(tmp_path: Path) -> None:
    site_root = tmp_path / "site"

    with pytest.raises(FileNotFoundError):
        publish_site(
            source_root=tmp_path / "outputs",
            date="2026-04-16",
            site_root=site_root,
        )

    assert site_root.exists() is False

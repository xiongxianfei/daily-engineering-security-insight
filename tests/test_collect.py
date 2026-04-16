from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from daily_insight.collect import collect_json, collect_rss, collect_sources
from daily_insight.models import SourceConfig
from daily_insight.normalize import normalize_item


def _write_config(path: Path, payload: list[dict[str, object]]) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_collect_dry_run_records_source_attempts(tmp_path: Path) -> None:
    config_path = tmp_path / "sources.json"
    db_path = tmp_path / "state" / "daily_insight.db"
    _write_config(
        config_path,
        [
            {
                "name": "python-insider",
                "transport": "rss",
                "url": "https://example.com/python-insider.xml",
                "bucket": "software-engineering",
                "enabled": True,
                "required_for_daily_run": True,
                "failure_policy": "fail",
            },
            {
                "name": "openai-news",
                "transport": "rss",
                "url": "https://example.com/openai-news.xml",
                "bucket": "security-for-ai",
                "enabled": True,
                "required_for_daily_run": False,
                "failure_policy": "warn",
            },
        ],
    )

    exit_code = collect_sources(
        date="2026-04-15",
        config_path=config_path,
        out_dir=tmp_path / "inputs" / "2026-04-15",
        dry_run=True,
        state_db_path=db_path,
    )

    assert exit_code == 0
    assert not (tmp_path / "inputs" / "2026-04-15" / "items.jsonl").exists()

    with sqlite3.connect(db_path) as connection:
        run_row = connection.execute(
            "SELECT digest_date, status FROM runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
        attempts = connection.execute(
            "SELECT source_name, status FROM source_attempts ORDER BY id"
        ).fetchall()

    assert run_row == ("2026-04-15", "completed")
    assert attempts == [
        ("python-insider", "dry-run"),
        ("openai-news", "dry-run"),
    ]


def test_collect_required_source_failure_returns_nonzero(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "sources.json"
    db_path = tmp_path / "state" / "daily_insight.db"
    out_dir = tmp_path / "inputs" / "2026-04-15"
    _write_config(
        config_path,
        [
            {
                "name": "python-insider",
                "transport": "rss",
                "url": "https://feeds.example.com/python-insider.xml",
                "bucket": "software-engineering",
                "enabled": True,
                "required_for_daily_run": True,
                "failure_policy": "fail",
            }
        ],
    )

    def boom(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise RuntimeError("feed unavailable")

    monkeypatch.setattr("daily_insight.collect.collect_rss", boom)

    exit_code = collect_sources(
        date="2026-04-15",
        config_path=config_path,
        out_dir=out_dir,
        dry_run=False,
        state_db_path=db_path,
    )

    assert exit_code == 1
    assert not (out_dir / "items.jsonl").exists()

    with sqlite3.connect(db_path) as connection:
        run_row = connection.execute(
            "SELECT digest_date, status FROM runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
        attempt_row = connection.execute(
            "SELECT source_name, status, detail FROM source_attempts ORDER BY id DESC LIMIT 1"
        ).fetchone()

    assert run_row == ("2026-04-15", "failed")
    assert attempt_row == ("python-insider", "failed", "feed unavailable")


def test_collect_warn_source_failure_preserves_successful_inputs(
    tmp_path: Path, monkeypatch
) -> None:
    config_path = tmp_path / "sources.json"
    db_path = tmp_path / "state" / "daily_insight.db"
    out_dir = tmp_path / "inputs" / "2026-04-15"
    _write_config(
        config_path,
        [
            {
                "name": "python-insider",
                "transport": "rss",
                "url": "https://feeds.example.com/python-insider.xml",
                "bucket": "software-engineering",
                "enabled": True,
                "required_for_daily_run": True,
                "failure_policy": "fail",
            },
            {
                "name": "google-threat-intelligence",
                "transport": "rss",
                "url": "https://feeds.example.com/threat-intelligence.xml",
                "bucket": "ai-for-security",
                "enabled": True,
                "required_for_daily_run": False,
                "failure_policy": "warn",
            },
        ],
    )

    def fake_collect(source):  # type: ignore[no-untyped-def]
        if source.name == "google-threat-intelligence":
            raise RuntimeError("temporary outage")
        return [
            normalize_item(
                source_name=source.name,
                bucket=source.bucket,
                title="Python 3.12.4 released",
                url="https://example.com/python-3-12-4",
                summary="Bugfix release",
                published_at="2026-04-15T00:00:00Z",
                tags=["release"],
            )
        ]

    monkeypatch.setattr("daily_insight.collect.collect_rss", fake_collect)

    exit_code = collect_sources(
        date="2026-04-15",
        config_path=config_path,
        out_dir=out_dir,
        dry_run=False,
        state_db_path=db_path,
    )

    assert exit_code == 0
    payload = (out_dir / "items.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(payload) == 1

    with sqlite3.connect(db_path) as connection:
        run_row = connection.execute(
            "SELECT digest_date, status FROM runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
        attempts = connection.execute(
            "SELECT source_name, status FROM source_attempts ORDER BY id"
        ).fetchall()
        dedupe_row = connection.execute(
            "SELECT source_name, latest_url FROM dedupe_items ORDER BY item_id LIMIT 1"
        ).fetchone()

    assert run_row == ("2026-04-15", "completed")
    assert attempts == [
        ("python-insider", "collected"),
        ("google-threat-intelligence", "failed"),
    ]
    assert dedupe_row == ("python-insider", "https://example.com/python-3-12-4")


def test_collect_caps_items_per_source(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "sources.json"
    db_path = tmp_path / "state" / "daily_insight.db"
    out_dir = tmp_path / "inputs" / "2026-04-15"
    _write_config(
        config_path,
        [
            {
                "name": "python-insider",
                "transport": "rss",
                "url": "https://feeds.example.com/python-insider.xml",
                "bucket": "software-engineering",
                "enabled": True,
                "required_for_daily_run": True,
                "failure_policy": "fail",
                "max_items_per_source": 1,
            }
        ],
    )

    def fake_collect(source):  # type: ignore[no-untyped-def]
        return [
            normalize_item(
                source_name=source.name,
                bucket=source.bucket,
                title="Python 3.12.4 released",
                url="https://example.com/python-3-12-4",
                summary="Bugfix release",
                published_at="2026-04-15T00:00:00Z",
                tags=["release"],
            ),
            normalize_item(
                source_name=source.name,
                bucket=source.bucket,
                title="Python 3.12.5 released",
                url="https://example.com/python-3-12-5",
                summary="Another bugfix release",
                published_at="2026-04-16T00:00:00Z",
                tags=["release"],
            ),
        ]

    monkeypatch.setattr("daily_insight.collect.collect_rss", fake_collect)

    exit_code = collect_sources(
        date="2026-04-15",
        config_path=config_path,
        out_dir=out_dir,
        dry_run=False,
        state_db_path=db_path,
    )

    assert exit_code == 0
    payload = (out_dir / "items.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(payload) == 1
    assert "Python 3.12.4 released" in payload[0]


def test_collect_filters_rss_items_to_requested_date(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "sources.json"
    db_path = tmp_path / "state" / "daily_insight.db"
    out_dir = tmp_path / "inputs" / "2026-04-15"
    _write_config(
        config_path,
        [
            {
                "name": "python-insider",
                "transport": "rss",
                "url": "https://feeds.example.com/python-insider.xml",
                "bucket": "software-engineering",
                "enabled": True,
                "required_for_daily_run": True,
                "failure_policy": "fail",
                "max_items_per_source": 10,
            }
        ],
    )

    def fake_collect(source):  # type: ignore[no-untyped-def]
        return [
            normalize_item(
                source_name=source.name,
                bucket=source.bucket,
                title="Python 3.12.4 released",
                url="https://example.com/python-3-12-4",
                summary="Bugfix release",
                published_at="Tue, 15 Apr 2026 08:00:00 GMT",
                tags=["release"],
            ),
            normalize_item(
                source_name=source.name,
                bucket=source.bucket,
                title="Python 3.12.3 released",
                url="https://example.com/python-3-12-3",
                summary="Older bugfix release",
                published_at="Mon, 14 Apr 2026 08:00:00 GMT",
                tags=["release"],
            ),
        ]

    monkeypatch.setattr("daily_insight.collect.collect_rss", fake_collect)

    exit_code = collect_sources(
        date="2026-04-15",
        config_path=config_path,
        out_dir=out_dir,
        dry_run=False,
        state_db_path=db_path,
    )

    assert exit_code == 0
    payload = (out_dir / "items.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(payload) == 1
    assert "Python 3.12.4 released" in payload[0]
    assert "Python 3.12.3 released" not in payload[0]


def test_collect_rss_uses_browser_like_user_agent(monkeypatch) -> None:
    source = SourceConfig(
        name="openai-news",
        transport="rss",
        url="https://example.com/openai-news.xml",
        bucket="security-for-ai",
        enabled=True,
        required_for_daily_run=False,
        failure_policy="warn",
    )
    seen: dict[str, str | None] = {}

    class _FakeResponse:
        def __init__(self, payload: bytes) -> None:
            self._payload = payload

        def read(self) -> bytes:
            return self._payload

        def __enter__(self) -> "_FakeResponse":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
            return None

    def fake_urlopen(request, timeout):  # type: ignore[no-untyped-def]
        seen["user_agent"] = request.get_header("User-agent")
        return _FakeResponse(
            b"<rss><channel><item><title>Trusted access</title>"
            b"<link>https://example.com/1</link>"
            b"<description>Security update</description>"
            b"<pubDate>Tue, 15 Apr 2026 08:00:00 GMT</pubDate>"
            b"</item></channel></rss>"
        )

    monkeypatch.setattr("daily_insight.collect.urlopen", fake_urlopen)

    items = collect_rss(source)

    assert len(items) == 1
    assert seen["user_agent"]
    assert "Mozilla" in seen["user_agent"]


def test_collect_json_cisa_kev_uses_date_added_delta(monkeypatch) -> None:
    source = SourceConfig(
        name="cisa-kev-catalog",
        transport="json",
        url="https://example.com/known-exploited-vulnerabilities.json",
        bucket="security",
        enabled=True,
        required_for_daily_run=False,
        failure_policy="warn",
    )

    class _FakeResponse:
        def __init__(self, payload: bytes) -> None:
            self._payload = payload

        def read(self) -> bytes:
            return self._payload

        def __enter__(self) -> "_FakeResponse":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
            return None

    payload = {
        "vulnerabilities": [
            {
                "cveID": "CVE-2026-0001",
                "vendorProject": "ExampleVendor",
                "product": "Gateway",
                "vulnerabilityName": "Remote code execution",
                "dateAdded": "2026-04-15",
                "shortDescription": "Attackers can execute code remotely.",
                "requiredAction": "Patch immediately.",
            },
            {
                "cveID": "CVE-2026-0002",
                "vendorProject": "ExampleVendor",
                "product": "Console",
                "vulnerabilityName": "Privilege escalation",
                "dateAdded": "2026-04-14",
                "shortDescription": "Attackers can escalate privileges.",
                "requiredAction": "Apply the vendor mitigation.",
            },
        ]
    }

    def fake_urlopen(request, timeout):  # type: ignore[no-untyped-def]
        return _FakeResponse(json.dumps(payload).encode("utf-8"))

    monkeypatch.setattr("daily_insight.collect.urlopen", fake_urlopen)

    items = collect_json(source, digest_date="2026-04-15")

    assert len(items) == 1
    assert items[0].title.startswith("CVE-2026-0001")
    assert items[0].published_at == "2026-04-15"
    assert "Patch immediately." in items[0].summary
    assert "kev" in items[0].tags


def test_collect_sources_dispatches_json_transport(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "sources.json"
    db_path = tmp_path / "state" / "daily_insight.db"
    out_dir = tmp_path / "inputs" / "2026-04-15"
    _write_config(
        config_path,
        [
            {
                "name": "cisa-kev-catalog",
                "transport": "json",
                "url": "https://feeds.example.com/known-exploited-vulnerabilities.json",
                "bucket": "security",
                "enabled": True,
                "required_for_daily_run": False,
                "failure_policy": "warn",
            }
        ],
    )

    def fake_collect_json(source, digest_date):  # type: ignore[no-untyped-def]
        assert source.name == "cisa-kev-catalog"
        assert digest_date == "2026-04-15"
        return [
            normalize_item(
                source_name=source.name,
                bucket=source.bucket,
                title="CVE-2026-0001 ExampleVendor Gateway",
                url="https://www.cisa.gov/known-exploited-vulnerabilities-catalog",
                summary="Patch immediately.",
                published_at="2026-04-15",
                tags=["kev", "CVE-2026-0001"],
            )
        ]

    monkeypatch.setattr("daily_insight.collect.collect_json", fake_collect_json)

    exit_code = collect_sources(
        date="2026-04-15",
        config_path=config_path,
        out_dir=out_dir,
        dry_run=False,
        state_db_path=db_path,
    )

    assert exit_code == 0
    payload = (out_dir / "items.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(payload) == 1
    assert "CVE-2026-0001 ExampleVendor Gateway" in payload[0]

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from daily_insight.cli import app

runner = CliRunner()
ROOT = Path(__file__).resolve().parents[1]


def test_cli_help_lists_foundation_commands() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "collect" in result.stdout
    assert "publish-site" in result.stdout
    assert "render" in result.stdout
    assert "render-html" in result.stdout
    assert "run" in result.stdout
    assert "sources" in result.stdout
    assert "source-health" in result.stdout


def test_sources_command_summarizes_reviewed_catalog() -> None:
    result = runner.invoke(app, ["sources"])

    assert result.exit_code == 0
    assert "reviewed source catalog" in result.stdout
    assert "runtime-approved subset" in result.stdout
    assert "runtime-approved: 10" in result.stdout
    assert "reviewed-candidate: 15" in result.stdout
    assert "deferred: 9" in result.stdout
    assert "software-engineering: 12" in result.stdout
    assert "python-insider" in result.stdout
    assert "google-threat-intelligence" in result.stdout


def test_sources_command_filters_by_bucket_and_status() -> None:
    result = runner.invoke(
        app,
        [
            "sources",
            "--bucket",
            "security",
            "--status",
            "runtime-approved",
        ],
    )

    assert result.exit_code == 0
    assert "filtered sources: 4" in result.stdout
    assert "google-online-security-blog" in result.stdout
    assert "cisa-advisories" in result.stdout
    assert "github-security-blog" in result.stdout
    assert "python-insider" not in result.stdout
    assert "cloudflare-security-blog" not in result.stdout


def test_run_command_requires_existing_config(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "run",
            "--date",
            "2026-04-15",
            "--config",
            str(tmp_path / "missing.json"),
        ],
    )

    assert result.exit_code == 1
    assert "missing" in result.stderr


def test_run_command_uses_date_scoped_paths(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "sources.local.json"
    prompt_path = tmp_path / "prompt.md"
    in_dir = tmp_path / "inputs" / "2026-04-15"
    out_dir = tmp_path / "outputs" / "2026-04-15"
    config_path.write_text("[]", encoding="utf-8")
    prompt_path.write_text("Prompt body", encoding="utf-8")

    recorded: dict[str, object] = {}

    def fake_collect_sources(**kwargs):  # type: ignore[no-untyped-def]
        recorded["collect"] = kwargs
        in_dir.mkdir(parents=True, exist_ok=True)
        (in_dir / "source_summary.json").write_text(
            '{"total_items_seen": 0, "source_failures": [], "bucket_counts": '
            '{"software-engineering": 0, "security": 0, "ai-for-security": 0, '
            '"security-for-ai": 0}, "bucket_health": {"software-engineering": "healthy", '
            '"security": "healthy", "ai-for-security": "healthy", '
            '"security-for-ai": "healthy"}, "coverage_notes": []}',
            encoding="utf-8",
        )
        return 0

    def fake_render_digest(input_path, output_path):  # type: ignore[no-untyped-def]
        recorded["render"] = (input_path, output_path)
        return output_path

    def fake_apply_source_summary(input_path, summary_path):  # type: ignore[no-untyped-def]
        recorded["apply_summary"] = (input_path, summary_path)

    def fake_subprocess_run(args, **kwargs):  # type: ignore[no-untyped-def]
        recorded["subprocess"] = (args, kwargs)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "digest.json").write_text(
            '{"date":"2026-04-15","generated_at":"2026-04-15T12:00:00Z",'
            '"overview_markdown":"# Overview","top_items":[],"action_now":[],'
            '"watchlist":[],"source_summary":{"total_items_seen":0,"source_failures":[],'
            '"bucket_counts":{"software-engineering":0,"security":0,"ai-for-security":0,'
            '"security-for-ai":0}}}',
            encoding="utf-8",
        )
        return None

    monkeypatch.setattr("daily_insight.cli.collect_sources", fake_collect_sources)
    monkeypatch.setattr("daily_insight.cli.render_digest", fake_render_digest)
    monkeypatch.setattr(
        "daily_insight.cli.apply_deterministic_source_summary",
        fake_apply_source_summary,
        raising=False,
    )
    monkeypatch.setattr("daily_insight.cli.subprocess.run", fake_subprocess_run)

    result = runner.invoke(
        app,
        [
            "run",
            "--date",
            "2026-04-15",
            "--config",
            str(config_path),
            "--prompt-path",
            str(prompt_path),
            "--in-dir",
            str(in_dir),
            "--out-dir",
            str(out_dir),
        ],
    )

    assert result.exit_code == 0
    assert recorded["collect"] == {
        "date": "2026-04-15",
        "config_path": config_path,
        "out_dir": in_dir,
        "dry_run": False,
        "state_db_path": None,
    }
    subprocess_args, subprocess_kwargs = recorded["subprocess"]  # type: ignore[misc]
    assert subprocess_args[:4] == ["codex", "exec", "-C", str(Path.cwd())]
    assert "--skip-git-repo-check" in subprocess_args
    assert str(out_dir / "digest.json") in subprocess_args
    assert "Digest date: 2026-04-15" in subprocess_args[-1]
    assert f"Frozen input file: {in_dir / 'items.jsonl'}" in subprocess_args[-1]
    assert f"Source summary file: {in_dir / 'source_summary.json'}" in subprocess_args[-1]
    assert subprocess_kwargs["check"] is True
    assert subprocess_kwargs["stdin"] is subprocess.DEVNULL
    assert recorded["apply_summary"] == (
        out_dir / "digest.json",
        in_dir / "source_summary.json",
    )
    assert recorded["render"] == (out_dir / "digest.json", out_dir / "digest.md")


def test_run_command_stops_when_collection_fails(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "sources.local.json"
    prompt_path = tmp_path / "prompt.md"
    config_path.write_text("[]", encoding="utf-8")
    prompt_path.write_text("Prompt body", encoding="utf-8")

    monkeypatch.setattr("daily_insight.cli.collect_sources", lambda **kwargs: 1)
    called = {"subprocess": False}

    def fake_subprocess_run(*args, **kwargs):  # type: ignore[no-untyped-def]
        called["subprocess"] = True
        return None

    monkeypatch.setattr("daily_insight.cli.subprocess.run", fake_subprocess_run)

    result = runner.invoke(
        app,
        [
            "run",
            "--date",
            "2026-04-15",
            "--config",
            str(config_path),
            "--prompt-path",
            str(prompt_path),
        ],
    )

    assert result.exit_code == 1
    assert called["subprocess"] is False


def test_run_command_does_not_update_published_site(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "repo"
    config_path = root / "configs" / "sources.local.json"
    prompt_path = root / "prompts" / "daily_digest_prompt.md"
    in_dir = root / "inputs" / "2026-04-16"
    out_dir = root / "outputs" / "2026-04-16"
    site_latest = root / "site" / "latest" / "index.html"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    site_latest.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text("[]", encoding="utf-8")
    prompt_path.write_text("Prompt body", encoding="utf-8")
    site_latest.write_text("published latest stays unchanged", encoding="utf-8")

    def fake_collect_sources(**kwargs):  # type: ignore[no-untyped-def]
        in_dir.mkdir(parents=True, exist_ok=True)
        (in_dir / "source_summary.json").write_text(
            '{"total_items_seen": 0, "source_failures": [], "bucket_counts": '
            '{"software-engineering": 0, "security": 0, "ai-for-security": 0, '
            '"security-for-ai": 0}, "bucket_health": {"software-engineering": "healthy", '
            '"security": "healthy", "ai-for-security": "healthy", '
            '"security-for-ai": "healthy"}, "coverage_notes": []}',
            encoding="utf-8",
        )
        return 0

    def fake_subprocess_run(args, **kwargs):  # type: ignore[no-untyped-def]
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "digest.json").write_text(
            '{"date":"2026-04-16","generated_at":"2026-04-16T12:00:00Z",'
            '"overview_markdown":"# Overview","top_items":[],"action_now":[],'
            '"watchlist":[],"source_summary":{"total_items_seen":0,"source_failures":[],'
            '"bucket_counts":{"software-engineering":0,"security":0,"ai-for-security":0,'
            '"security-for-ai":0},"bucket_health":{"software-engineering":"healthy",'
            '"security":"healthy","ai-for-security":"healthy","security-for-ai":"healthy"},'
            '"coverage_notes":[]}}',
            encoding="utf-8",
        )
        return None

    monkeypatch.setattr("daily_insight.cli._repo_root", lambda: root)
    monkeypatch.setattr("daily_insight.cli.collect_sources", fake_collect_sources)
    monkeypatch.setattr("daily_insight.cli.subprocess.run", fake_subprocess_run)
    monkeypatch.setattr(
        "daily_insight.cli.apply_deterministic_source_summary",
        lambda *_args, **_kwargs: None,
        raising=False,
    )
    monkeypatch.setattr(
        "daily_insight.cli.render_digest",
        lambda input_path, output_path: output_path,
    )

    result = runner.invoke(app, ["run", "--date", "2026-04-16"])

    assert result.exit_code == 0
    assert site_latest.read_text(encoding="utf-8") == "published latest stays unchanged"


def test_source_health_command_reads_bucket_statuses_from_state(tmp_path: Path) -> None:
    db_path = tmp_path / "state" / "daily_insight.db"
    import sqlite3

    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                digest_date TEXT NOT NULL,
                status TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT
            );
            CREATE TABLE bucket_health (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                bucket TEXT NOT NULL,
                status TEXT NOT NULL,
                item_count INTEGER NOT NULL,
                detail TEXT,
                recorded_at TEXT NOT NULL
            );
            """
        )
        connection.execute(
            (
                "INSERT INTO runs (id, digest_date, status, started_at, completed_at) "
                "VALUES (1, ?, ?, ?, ?)"
            ),
            ("2026-04-15", "completed", "2026-04-15T00:00:00Z", "2026-04-15T00:10:00Z"),
        )
        connection.execute(
            (
                "INSERT INTO bucket_health "
                "(run_id, bucket, status, item_count, detail, recorded_at) "
                "VALUES (?, ?, ?, ?, ?, ?)"
            ),
            (
                1,
                "security-for-ai",
                "degraded-source-failure",
                0,
                "openai-news failed: HTTP 403",
                "2026-04-15T00:10:00Z",
            ),
        )

    result = runner.invoke(
        app,
        [
            "source-health",
            "--date",
            "2026-04-15",
            "--state-db",
            str(db_path),
        ],
    )

    assert result.exit_code == 0
    assert "security-for-ai: degraded-source-failure" in result.stdout
    assert "openai-news failed: HTTP 403" in result.stdout


def test_render_html_command_writes_browser_readable_html(tmp_path: Path) -> None:
    output_path = tmp_path / "digest.html"

    result = runner.invoke(
        app,
        [
            "render-html",
            str(Path.cwd() / "examples" / "sample_digest.json"),
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    assert output_path.is_file()
    rendered = output_path.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in rendered
    assert "<h1>Daily insight for 2026-04-15</h1>" in rendered
    assert "Example AI security item" in rendered


def test_render_html_command_fails_clearly_for_invalid_input(tmp_path: Path) -> None:
    input_path = tmp_path / "bad.json"
    output_path = tmp_path / "digest.html"
    input_path.write_text('{"date": "2026-04-15"}', encoding="utf-8")

    result = runner.invoke(app, ["render-html", str(input_path), str(output_path)])

    assert result.exit_code == 1
    assert "browser HTML render failed" in result.stderr
    assert output_path.exists() is False


def test_publish_site_command_creates_browser_entrypoints(tmp_path: Path) -> None:
    source_root = tmp_path / "outputs"
    site_root = tmp_path / "site"
    payload = json.loads((ROOT / "examples" / "sample_digest.json").read_text(encoding="utf-8"))
    payload["date"] = "2026-04-16"
    date_root = source_root / "2026-04-16"
    date_root.mkdir(parents=True, exist_ok=True)
    (date_root / "digest.json").write_text(json.dumps(payload), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "publish-site",
            "--source-root",
            str(source_root),
            "--date",
            "2026-04-16",
            "--site-root",
            str(site_root),
        ],
    )

    assert result.exit_code == 0
    assert (site_root / "index.html").is_file()
    assert (site_root / "latest" / "index.html").is_file()
    assert (site_root / "2026-04-16" / "index.html").is_file()


def test_publish_site_command_fails_clearly_when_digest_is_missing(tmp_path: Path) -> None:
    site_root = tmp_path / "site"

    result = runner.invoke(
        app,
        [
            "publish-site",
            "--source-root",
            str(tmp_path / "outputs"),
            "--date",
            "2026-04-16",
            "--site-root",
            str(site_root),
        ],
    )

    assert result.exit_code == 1
    assert "site publish failed" in result.stderr
    assert site_root.exists() is False

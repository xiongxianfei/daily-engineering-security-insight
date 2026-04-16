from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from daily_insight.cli import app
from daily_insight.synthesize import (
    EXIT_COLLECTION_FAILED,
    EXIT_SYNTHESIS_TIMEOUT,
    LifecycleCommandError,
    SynthesisOutcome,
)

runner = CliRunner()


def test_cli_help_lists_foundation_commands() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "collect" in result.stdout
    assert "render" in result.stdout
    assert "run" in result.stdout
    assert "synthesize" in result.stdout


def test_run_command_requires_existing_config_when_collection_needed(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "run",
            "--date",
            "2026-04-15",
            "--config",
            str(tmp_path / "missing.json"),
            "--in-dir",
            str(tmp_path / "inputs" / "2026-04-15"),
            "--out-dir",
            str(tmp_path / "outputs" / "2026-04-15"),
        ],
    )

    assert result.exit_code == 11
    assert "missing" in result.stderr


def test_run_command_uses_date_scoped_paths(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "sources.local.json"
    prompt_path = tmp_path / "prompt.md"
    in_dir = tmp_path / "inputs" / "2026-04-15"
    out_dir = tmp_path / "outputs" / "2026-04-15"
    state_db = tmp_path / "state" / "daily_insight.db"
    config_path.write_text("[]", encoding="utf-8")
    prompt_path.write_text("Prompt body", encoding="utf-8")

    recorded: dict[str, object] = {}

    def fake_collect_sources(**kwargs):  # type: ignore[no-untyped-def]
        recorded["collect"] = kwargs
        return 0

    def fake_synthesize_digest(**kwargs):  # type: ignore[no-untyped-def]
        recorded["synthesize"] = kwargs
        return SynthesisOutcome(
            digest_json=out_dir / "digest.json",
            digest_md=out_dir / "digest.md",
        )

    monkeypatch.setattr("daily_insight.cli.collect_sources", fake_collect_sources)
    monkeypatch.setattr("daily_insight.cli.synthesize_digest", fake_synthesize_digest)

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
            "--state-db",
            str(state_db),
            "--timeout-seconds",
            "120",
        ],
    )

    assert result.exit_code == 0
    assert recorded["collect"] == {
        "date": "2026-04-15",
        "config_path": config_path,
        "out_dir": in_dir,
        "dry_run": False,
        "state_db_path": state_db,
    }
    synthesize_kwargs = recorded["synthesize"]  # type: ignore[assignment]
    assert synthesize_kwargs == {
        "root": Path(__file__).resolve().parents[1],
        "date": "2026-04-15",
        "prompt_path": prompt_path,
        "in_dir": in_dir,
        "out_dir": out_dir,
        "state_db_path": state_db,
        "timeout_seconds": 120,
    }


def test_run_command_reuses_existing_input_bundle(tmp_path: Path, monkeypatch) -> None:
    in_dir = tmp_path / "inputs" / "2026-04-15"
    out_dir = tmp_path / "outputs" / "2026-04-15"
    prompt_path = tmp_path / "prompt.md"
    prompt_path.write_text("Prompt body", encoding="utf-8")
    in_dir.mkdir(parents=True)
    (in_dir / "items.jsonl").write_text("[]\n", encoding="utf-8")

    called = {"collect": False}

    def fake_collect_sources(**kwargs):  # type: ignore[no-untyped-def]
        called["collect"] = True
        return 0

    def fake_synthesize_digest(**kwargs):  # type: ignore[no-untyped-def]
        return SynthesisOutcome(
            digest_json=out_dir / "digest.json",
            digest_md=out_dir / "digest.md",
        )

    monkeypatch.setattr("daily_insight.cli.collect_sources", fake_collect_sources)
    monkeypatch.setattr("daily_insight.cli.synthesize_digest", fake_synthesize_digest)

    result = runner.invoke(
        app,
        [
            "run",
            "--date",
            "2026-04-15",
            "--config",
            str(tmp_path / "missing.json"),
            "--prompt-path",
            str(prompt_path),
            "--in-dir",
            str(in_dir),
            "--out-dir",
            str(out_dir),
        ],
    )

    assert result.exit_code == 0
    assert called["collect"] is False
    assert "reusing frozen input bundle" in result.stdout


def test_run_command_stops_when_collection_fails(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "sources.local.json"
    prompt_path = tmp_path / "prompt.md"
    in_dir = tmp_path / "inputs" / "2026-04-15"
    out_dir = tmp_path / "outputs" / "2026-04-15"
    config_path.write_text("[]", encoding="utf-8")
    prompt_path.write_text("Prompt body", encoding="utf-8")

    monkeypatch.setattr("daily_insight.cli.collect_sources", lambda **kwargs: 1)
    called = {"synthesize": False}

    def fake_synthesize_digest(**kwargs):  # type: ignore[no-untyped-def]
        called["synthesize"] = True
        return None

    monkeypatch.setattr("daily_insight.cli.synthesize_digest", fake_synthesize_digest)

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

    assert result.exit_code == EXIT_COLLECTION_FAILED
    assert called["synthesize"] is False


def test_synthesize_command_reports_already_complete(tmp_path: Path, monkeypatch) -> None:
    prompt_path = tmp_path / "prompt.md"
    prompt_path.write_text("Prompt body", encoding="utf-8")

    def fake_synthesize_digest(**kwargs):  # type: ignore[no-untyped-def]
        return SynthesisOutcome(
            digest_json=tmp_path / "outputs" / "2026-04-15" / "digest.json",
            digest_md=tmp_path / "outputs" / "2026-04-15" / "digest.md",
            already_complete=True,
        )

    monkeypatch.setattr("daily_insight.cli.synthesize_digest", fake_synthesize_digest)

    result = runner.invoke(
        app,
        [
            "synthesize",
            "--date",
            "2026-04-15",
            "--prompt-path",
            str(prompt_path),
        ],
    )

    assert result.exit_code == 0
    assert "already complete" in result.stdout


def test_synthesize_command_propagates_lifecycle_errors(tmp_path: Path, monkeypatch) -> None:
    prompt_path = tmp_path / "prompt.md"
    prompt_path.write_text("Prompt body", encoding="utf-8")

    def fake_synthesize_digest(**kwargs):  # type: ignore[no-untyped-def]
        raise LifecycleCommandError(EXIT_SYNTHESIS_TIMEOUT, "synthesis timed out after 60 seconds")

    monkeypatch.setattr("daily_insight.cli.synthesize_digest", fake_synthesize_digest)

    result = runner.invoke(
        app,
        [
            "synthesize",
            "--date",
            "2026-04-15",
            "--prompt-path",
            str(prompt_path),
        ],
    )

    assert result.exit_code == EXIT_SYNTHESIS_TIMEOUT
    assert "synthesis timed out" in result.stderr

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from daily_insight.cli import app

runner = CliRunner()


def test_cli_help_lists_foundation_commands() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "collect" in result.stdout
    assert "render" in result.stdout
    assert "run" in result.stdout


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
        return 0

    def fake_render_digest(input_path, output_path):  # type: ignore[no-untyped-def]
        recorded["render"] = (input_path, output_path)
        return output_path

    def fake_subprocess_run(args, **kwargs):  # type: ignore[no-untyped-def]
        recorded["subprocess"] = (args, kwargs)
        return None

    monkeypatch.setattr("daily_insight.cli.collect_sources", fake_collect_sources)
    monkeypatch.setattr("daily_insight.cli.render_digest", fake_render_digest)
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
    assert "Frozen input file: inputs/2026-04-15/items.jsonl" in subprocess_args[-1]
    assert subprocess_kwargs["check"] is True
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

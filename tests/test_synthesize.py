from __future__ import annotations

import json
from pathlib import Path

import pytest

from daily_insight.storage import StateStore
from daily_insight.synthesize import (
    COLLECTION_DIAGNOSTICS_UNAVAILABLE,
    EXIT_PRECONDITION_FAILED,
    EXIT_RENDER_FAILED,
    EXIT_SYNTHESIS_OUTPUT_INVALID,
    EXIT_SYNTHESIS_TIMEOUT,
    LifecycleCommandError,
    resolve_timeout,
    synthesize_digest,
)


def _sample_digest() -> dict[str, object]:
    root = Path(__file__).resolve().parents[1]
    return json.loads((root / "examples" / "sample_digest.json").read_text(encoding="utf-8"))


def _write_items_jsonl(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    items = [
        {
            "id": "aaaaaaaaaaaaaaaa",
            "source": "python-insider",
            "bucket_hint": "software-engineering",
            "title": "Python release",
            "url": "https://example.com/python",
            "summary": "Release summary",
            "published_at": "2026-04-15T00:00:00Z",
            "collected_at": "2026-04-15T01:00:00Z",
            "tags": [],
        },
        {
            "id": "bbbbbbbbbbbbbbbb",
            "source": "security-feed",
            "bucket_hint": "security",
            "title": "Security advisory",
            "url": "https://example.com/security",
            "summary": "Security summary",
            "published_at": "2026-04-15T02:00:00Z",
            "collected_at": "2026-04-15T03:00:00Z",
            "tags": [],
        },
    ]
    with path.open("w", encoding="utf-8") as handle:
        for item in items:
            handle.write(json.dumps(item) + "\n")


def test_resolve_timeout_uses_default_env_and_cli_override(monkeypatch) -> None:
    monkeypatch.delenv("DAILY_INSIGHT_SYNTHESIS_TIMEOUT_SECONDS", raising=False)
    assert resolve_timeout(None) == 900

    monkeypatch.setenv("DAILY_INSIGHT_SYNTHESIS_TIMEOUT_SECONDS", "120")
    assert resolve_timeout(None) == 120
    assert resolve_timeout(60) == 60


@pytest.mark.parametrize("value", [0, -1])
def test_resolve_timeout_rejects_non_positive_values(value: int) -> None:
    with pytest.raises(LifecycleCommandError) as exc_info:
        resolve_timeout(value)

    assert exc_info.value.exit_code == EXIT_PRECONDITION_FAILED


def test_synthesize_digest_requires_existing_frozen_input(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    prompt_path = tmp_path / "prompt.md"
    prompt_path.write_text("Prompt body", encoding="utf-8")

    with pytest.raises(LifecycleCommandError) as exc_info:
        synthesize_digest(
            root=root,
            date="2026-04-15",
            prompt_path=prompt_path,
            in_dir=tmp_path / "inputs" / "2026-04-15",
            out_dir=tmp_path / "outputs" / "2026-04-15",
            state_db_path=None,
            timeout_seconds=60,
        )

    assert exc_info.value.exit_code == EXIT_PRECONDITION_FAILED
    assert "missing frozen input bundle" in exc_info.value.message


def test_synthesize_digest_is_noop_when_outputs_are_complete(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    out_dir = tmp_path / "outputs" / "2026-04-15"
    out_dir.mkdir(parents=True)
    digest_json = out_dir / "digest.json"
    digest_md = out_dir / "digest.md"
    digest_json.write_text(json.dumps(_sample_digest(), indent=2) + "\n", encoding="utf-8")
    digest_md.write_text("# already complete\n", encoding="utf-8")

    outcome = synthesize_digest(
        root=root,
        date="2026-04-15",
        prompt_path=tmp_path / "missing-prompt.md",
        in_dir=tmp_path / "missing-input",
        out_dir=out_dir,
        state_db_path=None,
        timeout_seconds=60,
    )

    assert outcome.already_complete is True
    assert outcome.digest_json == digest_json
    assert outcome.digest_md == digest_md


def test_synthesize_digest_records_lifecycle_and_normalizes_source_summary(
    tmp_path: Path, monkeypatch
) -> None:
    root = Path(__file__).resolve().parents[1]
    date = "2026-04-15"
    prompt_path = tmp_path / "prompt.md"
    input_path = tmp_path / "inputs" / date / "items.jsonl"
    out_dir = tmp_path / "outputs" / date
    state_db_path = tmp_path / "state" / "daily_insight.db"
    prompt_path.write_text("Prompt body", encoding="utf-8")
    _write_items_jsonl(input_path)

    store = StateStore(state_db_path)
    run_id = store.record_run(digest_date=date, status="completed")
    store.record_source_attempt(
        run_id=run_id,
        source_name="optional-source",
        bucket="security-for-ai",
        status="failed",
        detail="temporary outage",
    )

    def fake_run_codex_exec(**kwargs):  # type: ignore[no-untyped-def]
        Path(kwargs["output_json"]).write_text(
            json.dumps(_sample_digest(), indent=2) + "\n",
            encoding="utf-8",
        )

    monkeypatch.setattr("daily_insight.synthesize._run_codex_exec", fake_run_codex_exec)

    outcome = synthesize_digest(
        root=root,
        date=date,
        prompt_path=prompt_path,
        in_dir=input_path.parent,
        out_dir=out_dir,
        state_db_path=state_db_path,
        timeout_seconds=60,
    )

    payload = json.loads(outcome.digest_json.read_text(encoding="utf-8"))
    assert payload["source_summary"] == {
        "total_items_seen": 2,
        "source_failures": ["optional-source: temporary outage"],
        "bucket_counts": {
            "software-engineering": 1,
            "security": 1,
            "ai-for-security": 0,
            "security-for-ai": 0,
        },
    }
    assert outcome.digest_md.is_file()
    assert store.list_lifecycle_events(digest_date=date) == [
        "synthesis_started",
        "synthesis_completed",
        "render_started",
        "render_completed",
    ]


def test_synthesize_digest_reports_missing_collection_diagnostics(
    tmp_path: Path, monkeypatch
) -> None:
    root = Path(__file__).resolve().parents[1]
    date = "2026-04-15"
    prompt_path = tmp_path / "prompt.md"
    input_path = tmp_path / "inputs" / date / "items.jsonl"
    out_dir = tmp_path / "outputs" / date
    prompt_path.write_text("Prompt body", encoding="utf-8")
    _write_items_jsonl(input_path)

    def fake_run_codex_exec(**kwargs):  # type: ignore[no-untyped-def]
        Path(kwargs["output_json"]).write_text(
            json.dumps(_sample_digest(), indent=2) + "\n",
            encoding="utf-8",
        )

    monkeypatch.setattr("daily_insight.synthesize._run_codex_exec", fake_run_codex_exec)

    outcome = synthesize_digest(
        root=root,
        date=date,
        prompt_path=prompt_path,
        in_dir=input_path.parent,
        out_dir=out_dir,
        state_db_path=None,
        timeout_seconds=60,
    )

    payload = json.loads(outcome.digest_json.read_text(encoding="utf-8"))
    assert payload["source_summary"]["source_failures"] == [COLLECTION_DIAGNOSTICS_UNAVAILABLE]


def test_synthesize_digest_timeout_records_state_and_preserves_final_outputs(
    tmp_path: Path, monkeypatch
) -> None:
    root = Path(__file__).resolve().parents[1]
    date = "2026-04-15"
    prompt_path = tmp_path / "prompt.md"
    input_path = tmp_path / "inputs" / date / "items.jsonl"
    out_dir = tmp_path / "outputs" / date
    state_db_path = tmp_path / "state" / "daily_insight.db"
    prompt_path.write_text("Prompt body", encoding="utf-8")
    _write_items_jsonl(input_path)
    store = StateStore(state_db_path)

    def fake_run_codex_exec(**kwargs):  # type: ignore[no-untyped-def]
        raise LifecycleCommandError(EXIT_SYNTHESIS_TIMEOUT, "synthesis timed out after 60 seconds")

    monkeypatch.setattr("daily_insight.synthesize._run_codex_exec", fake_run_codex_exec)

    with pytest.raises(LifecycleCommandError) as exc_info:
        synthesize_digest(
            root=root,
            date=date,
            prompt_path=prompt_path,
            in_dir=input_path.parent,
            out_dir=out_dir,
            state_db_path=state_db_path,
            timeout_seconds=60,
        )

    assert exc_info.value.exit_code == EXIT_SYNTHESIS_TIMEOUT
    assert not (out_dir / "digest.json").exists()
    assert not (out_dir / "digest.md").exists()
    assert store.list_lifecycle_events(digest_date=date) == [
        "synthesis_started",
        "synthesis_timed_out",
    ]


def test_synthesize_digest_invalid_output_uses_schema_exit_code(
    tmp_path: Path, monkeypatch
) -> None:
    root = Path(__file__).resolve().parents[1]
    date = "2026-04-15"
    prompt_path = tmp_path / "prompt.md"
    input_path = tmp_path / "inputs" / date / "items.jsonl"
    out_dir = tmp_path / "outputs" / date
    state_db_path = tmp_path / "state" / "daily_insight.db"
    prompt_path.write_text("Prompt body", encoding="utf-8")
    _write_items_jsonl(input_path)
    StateStore(state_db_path)

    def fake_run_codex_exec(**kwargs):  # type: ignore[no-untyped-def]
        Path(kwargs["output_json"]).write_text('{"date": "2026-04-15"}\n', encoding="utf-8")

    monkeypatch.setattr("daily_insight.synthesize._run_codex_exec", fake_run_codex_exec)

    with pytest.raises(LifecycleCommandError) as exc_info:
        synthesize_digest(
            root=root,
            date=date,
            prompt_path=prompt_path,
            in_dir=input_path.parent,
            out_dir=out_dir,
            state_db_path=state_db_path,
            timeout_seconds=60,
        )

    assert exc_info.value.exit_code == EXIT_SYNTHESIS_OUTPUT_INVALID
    assert not (out_dir / "digest.json").exists()
    assert not (out_dir / "digest.md").exists()


def test_synthesize_digest_render_failure_is_distinct(tmp_path: Path, monkeypatch) -> None:
    root = Path(__file__).resolve().parents[1]
    date = "2026-04-15"
    prompt_path = tmp_path / "prompt.md"
    input_path = tmp_path / "inputs" / date / "items.jsonl"
    out_dir = tmp_path / "outputs" / date
    state_db_path = tmp_path / "state" / "daily_insight.db"
    prompt_path.write_text("Prompt body", encoding="utf-8")
    _write_items_jsonl(input_path)
    store = StateStore(state_db_path)

    def fake_run_codex_exec(**kwargs):  # type: ignore[no-untyped-def]
        Path(kwargs["output_json"]).write_text(
            json.dumps(_sample_digest(), indent=2) + "\n",
            encoding="utf-8",
        )

    def boom(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise RuntimeError("renderer unavailable")

    monkeypatch.setattr("daily_insight.synthesize._run_codex_exec", fake_run_codex_exec)
    monkeypatch.setattr("daily_insight.synthesize.render_digest", boom)

    with pytest.raises(LifecycleCommandError) as exc_info:
        synthesize_digest(
            root=root,
            date=date,
            prompt_path=prompt_path,
            in_dir=input_path.parent,
            out_dir=out_dir,
            state_db_path=state_db_path,
            timeout_seconds=60,
        )

    assert exc_info.value.exit_code == EXIT_RENDER_FAILED
    assert (out_dir / "digest.json").exists()
    assert not (out_dir / "digest.md").exists()
    assert store.list_lifecycle_events(digest_date=date) == [
        "synthesis_started",
        "synthesis_completed",
        "render_started",
        "render_failed",
    ]

from __future__ import annotations

import json
import os
import signal
import subprocess
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import ValidationError, validate

from daily_insight.render import render_digest
from daily_insight.storage import StateStore

BUCKETS = (
    "software-engineering",
    "security",
    "ai-for-security",
    "security-for-ai",
)
DEFAULT_TIMEOUT_SECONDS = 900
SYNTHESIS_TIMEOUT_ENV = "DAILY_INSIGHT_SYNTHESIS_TIMEOUT_SECONDS"
COLLECTION_DIAGNOSTICS_UNAVAILABLE = "collection diagnostics unavailable"

EXIT_SUCCESS = 0
EXIT_COLLECTION_FAILED = 10
EXIT_PRECONDITION_FAILED = 11
EXIT_SYNTHESIS_TIMEOUT = 20
EXIT_SYNTHESIS_FAILED = 21
EXIT_SYNTHESIS_OUTPUT_INVALID = 22
EXIT_RENDER_FAILED = 30


class LifecycleCommandError(Exception):
    def __init__(self, exit_code: int, message: str) -> None:
        super().__init__(message)
        self.exit_code = exit_code
        self.message = message


@dataclass(frozen=True)
class SynthesisOutcome:
    digest_json: Path
    digest_md: Path
    already_complete: bool = False


def resolve_timeout(timeout_seconds: int | None) -> int:
    resolved = timeout_seconds
    if resolved is None:
        raw_env = os.environ.get(SYNTHESIS_TIMEOUT_ENV)
        if raw_env:
            try:
                resolved = int(raw_env)
            except ValueError as exc:
                raise LifecycleCommandError(
                    EXIT_PRECONDITION_FAILED,
                    f"invalid {SYNTHESIS_TIMEOUT_ENV} value: {raw_env}",
                ) from exc
        else:
            resolved = DEFAULT_TIMEOUT_SECONDS

    if resolved <= 0:
        raise LifecycleCommandError(
            EXIT_PRECONDITION_FAILED,
            "timeout must be a positive number of seconds",
        )
    return resolved


def _load_schema(schema_path: Path) -> dict[str, Any]:
    return json.loads(schema_path.read_text(encoding="utf-8"))


def _load_validated_digest(path: Path, schema_path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise LifecycleCommandError(
            EXIT_SYNTHESIS_OUTPUT_INVALID,
            f"missing structured digest: {path}",
        ) from exc
    except json.JSONDecodeError as exc:
        raise LifecycleCommandError(
            EXIT_SYNTHESIS_OUTPUT_INVALID,
            f"invalid structured digest JSON at {path}: {exc}",
        ) from exc

    try:
        validate(payload, _load_schema(schema_path))
    except ValidationError as exc:
        raise LifecycleCommandError(
            EXIT_SYNTHESIS_OUTPUT_INVALID,
            f"structured digest did not match schema: {exc.message}",
        ) from exc
    return payload


def outputs_are_complete(*, digest_json: Path, digest_md: Path, schema_path: Path) -> bool:
    if not digest_json.is_file() or not digest_md.is_file():
        return False
    try:
        _load_validated_digest(digest_json, schema_path)
    except LifecycleCommandError:
        return False
    return True


def _load_frozen_items(input_path: Path) -> list[dict[str, Any]]:
    try:
        lines = input_path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError as exc:
        raise LifecycleCommandError(
            EXIT_PRECONDITION_FAILED,
            f"missing frozen input bundle: {input_path}",
        ) from exc

    items: list[dict[str, Any]] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            items.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise LifecycleCommandError(
                EXIT_PRECONDITION_FAILED,
                f"invalid frozen input bundle at {input_path}: {exc}",
            ) from exc
    return items


def _source_failures_for_date(*, digest_date: str, state_db_path: Path | None) -> list[str]:
    if state_db_path is None or not state_db_path.exists():
        return [COLLECTION_DIAGNOSTICS_UNAVAILABLE]

    try:
        store = StateStore(state_db_path)
        return store.list_source_failures(digest_date=digest_date)
    except Exception:
        return [COLLECTION_DIAGNOSTICS_UNAVAILABLE]


def _normalized_source_summary(
    *,
    digest_date: str,
    input_path: Path,
    state_db_path: Path | None,
) -> dict[str, Any]:
    items = _load_frozen_items(input_path)
    counts = Counter(str(item.get("bucket_hint", "")) for item in items)
    return {
        "total_items_seen": len(items),
        "source_failures": _source_failures_for_date(
            digest_date=digest_date,
            state_db_path=state_db_path,
        ),
        "bucket_counts": {bucket: int(counts.get(bucket, 0)) for bucket in BUCKETS},
    }


def _promote(path_from: Path, path_to: Path) -> None:
    path_to.parent.mkdir(parents=True, exist_ok=True)
    path_from.replace(path_to)


def _record_lifecycle_event(
    *,
    state_db_path: Path | None,
    digest_date: str,
    status: str,
    detail: str | None = None,
) -> None:
    if state_db_path is None:
        return
    StateStore(state_db_path).record_lifecycle_event(
        digest_date=digest_date,
        status=status,
        detail=detail,
    )


def _terminate_process_group(process: subprocess.Popen[str]) -> None:
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return

    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            return
        process.wait(timeout=5)


def _run_codex_exec(
    *,
    root: Path,
    date: str,
    prompt_path: Path,
    input_path: Path,
    output_json: Path,
    schema_path: Path,
    timeout_seconds: int,
) -> None:
    prompt = prompt_path.read_text(encoding="utf-8")
    try:
        frozen_input_display = str(input_path.relative_to(root))
    except ValueError:
        frozen_input_display = str(input_path)
    process = subprocess.Popen(
        [
            "codex",
            "exec",
            "-C",
            str(root),
            "--skip-git-repo-check",
            "--full-auto",
            "--json",
            "--output-schema",
            str(schema_path),
            "--output-last-message",
            str(output_json),
            (
                f"{prompt}\n\n"
                f"Digest date: {date}\n"
                f"Frozen input file: {frozen_input_display}\n\n"
                "Wait for all requested work before returning. "
                "Produce only the final structured report."
            ),
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )

    try:
        _, stderr_text = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        _terminate_process_group(process)
        raise LifecycleCommandError(
            EXIT_SYNTHESIS_TIMEOUT,
            f"synthesis timed out after {timeout_seconds} seconds",
        ) from exc

    if process.returncode != 0:
        detail = (stderr_text or "").strip()
        message = f"synthesis subprocess failed with exit code {process.returncode}"
        if detail:
            message = f"{message}: {detail}"
        raise LifecycleCommandError(EXIT_SYNTHESIS_FAILED, message)


def synthesize_digest(
    *,
    root: Path,
    date: str,
    prompt_path: Path,
    in_dir: Path,
    out_dir: Path,
    state_db_path: Path | None,
    timeout_seconds: int | None,
) -> SynthesisOutcome:
    schema_path = root / "schemas" / "daily_insight.schema.json"
    input_path = in_dir / "items.jsonl"
    digest_json = out_dir / "digest.json"
    digest_md = out_dir / "digest.md"

    if outputs_are_complete(digest_json=digest_json, digest_md=digest_md, schema_path=schema_path):
        return SynthesisOutcome(digest_json=digest_json, digest_md=digest_md, already_complete=True)

    if not input_path.is_file():
        raise LifecycleCommandError(
            EXIT_PRECONDITION_FAILED,
            f"missing frozen input bundle: {input_path}",
        )
    if not prompt_path.is_file():
        raise LifecycleCommandError(
            EXIT_PRECONDITION_FAILED,
            f"missing prompt file: {prompt_path}",
        )

    resolved_timeout = resolve_timeout(timeout_seconds)
    out_dir.mkdir(parents=True, exist_ok=True)
    temp_json = out_dir / "digest.json.tmp"
    temp_md = out_dir / "digest.md.tmp"

    _record_lifecycle_event(
        state_db_path=state_db_path,
        digest_date=date,
        status="synthesis_started",
    )
    try:
        _run_codex_exec(
            root=root,
            date=date,
            prompt_path=prompt_path,
            input_path=input_path,
            output_json=temp_json,
            schema_path=schema_path,
            timeout_seconds=resolved_timeout,
        )
        payload = _load_validated_digest(temp_json, schema_path)
        payload["source_summary"] = _normalized_source_summary(
            digest_date=date,
            input_path=input_path,
            state_db_path=state_db_path,
        )
        validate(payload, _load_schema(schema_path))
        temp_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    except LifecycleCommandError as exc:
        status = (
            "synthesis_timed_out"
            if exc.exit_code == EXIT_SYNTHESIS_TIMEOUT
            else "synthesis_failed"
        )
        _record_lifecycle_event(
            state_db_path=state_db_path,
            digest_date=date,
            status=status,
            detail=exc.message,
        )
        raise
    except ValidationError as exc:
        _record_lifecycle_event(
            state_db_path=state_db_path,
            digest_date=date,
            status="synthesis_failed",
            detail=exc.message,
        )
        raise LifecycleCommandError(
            EXIT_SYNTHESIS_OUTPUT_INVALID,
            f"structured digest did not match schema: {exc.message}",
        ) from exc

    _promote(temp_json, digest_json)
    _record_lifecycle_event(
        state_db_path=state_db_path,
        digest_date=date,
        status="synthesis_completed",
    )

    _record_lifecycle_event(
        state_db_path=state_db_path,
        digest_date=date,
        status="render_started",
    )
    try:
        render_digest(digest_json, temp_md)
    except Exception as exc:
        _record_lifecycle_event(
            state_db_path=state_db_path,
            digest_date=date,
            status="render_failed",
            detail=str(exc),
        )
        raise LifecycleCommandError(EXIT_RENDER_FAILED, f"render failed: {exc}") from exc

    _promote(temp_md, digest_md)
    _record_lifecycle_event(
        state_db_path=state_db_path,
        digest_date=date,
        status="render_completed",
    )
    return SynthesisOutcome(digest_json=digest_json, digest_md=digest_md, already_complete=False)

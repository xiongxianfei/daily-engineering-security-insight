# Unattended Synthesis Specification

## Goal

Define the operator-visible lifecycle for unattended digest synthesis after deterministic collection has produced a frozen input bundle.

This spec covers timeout, resume, exit-code, and partial-output behavior for:

- `uv run daily-insight run`
- `uv run daily-insight synthesize`

It does not redefine the digest content contract already covered by `specs/daily-digest.md`.

Related plan: `docs/plans/2026-04-16-harden-unattended-daily-synthesis.md`

## Examples

### Example 1: Fresh unattended daily run succeeds

Given no existing `inputs/2026-04-17/items.jsonl`

When the operator runs:

```bash
uv run daily-insight run --date 2026-04-17 --config configs/sources.local.json --state-db state/daily_insight.db
```

Then the system collects sources, synthesizes from the frozen input, renders Markdown, writes:

- `inputs/2026-04-17/items.jsonl`
- `outputs/2026-04-17/digest.json`
- `outputs/2026-04-17/digest.md`

And exits `0`.

### Example 2: Resume from a previously frozen input

Given `inputs/2026-04-17/items.jsonl` already exists and a previous synthesis attempt timed out

When the operator runs:

```bash
uv run daily-insight synthesize --date 2026-04-17 --in-dir inputs/2026-04-17 --out-dir outputs/2026-04-17 --state-db state/daily_insight.db
```

Then the system MUST resume from the existing frozen input bundle, MUST NOT recollect live sources, and exits `0` after writing both final outputs.

### Example 3: Synthesis times out

Given a valid frozen input bundle exists

When the operator runs:

```bash
uv run daily-insight synthesize --date 2026-04-17 --timeout-seconds 60 --state-db state/daily_insight.db
```

And the Codex subprocess does not finish within `60` seconds

Then the command exits `20`, preserves `inputs/2026-04-17/items.jsonl`, records a synthesis-timeout state, and leaves no newly trusted final `digest.json` or `digest.md` in place.

### Example 4: The date is already complete

Given:

- `inputs/2026-04-17/items.jsonl` exists
- `outputs/2026-04-17/digest.json` exists and validates against `schemas/daily_insight.schema.json`
- `outputs/2026-04-17/digest.md` exists

When the operator reruns:

```bash
uv run daily-insight run --date 2026-04-17 --config configs/sources.local.json --state-db state/daily_insight.db
```

Then the command exits `0`, reports that the date is already complete, and does not recollect, re-synthesize, or overwrite the existing outputs.

## Inputs and Outputs

### Inputs

- digest date `YYYY-MM-DD`
- frozen input bundle at `inputs/YYYY-MM-DD/items.jsonl`
- optional source config for `run`
- optional state database at `state/daily_insight.db`
- synthesis timeout configuration

### Outputs

- structured digest at `outputs/YYYY-MM-DD/digest.json`
- rendered digest at `outputs/YYYY-MM-DD/digest.md`
- operator-visible exit code and lifecycle message
- persisted lifecycle state for collection, synthesis, and render stages

## Requirements

### R1. Stage Boundary

The system MUST treat collection, synthesis, and rendering as distinct lifecycle stages.

`run` MUST orchestrate those stages in order:

1. collection, only when no frozen input bundle exists for the date
2. synthesis from the frozen input bundle
3. rendering from the structured digest JSON

`synthesize` MUST operate only from an existing frozen input bundle and MUST NOT recollect live sources.

### R2. Frozen Input Reuse

If `inputs/YYYY-MM-DD/items.jsonl` already exists, `run` MUST reuse that frozen input and MUST NOT recollect live data for the same date.

If `synthesize` is invoked and the frozen input bundle is missing, the command MUST fail with the precondition exit code defined in `R5`.

An empty or sparse frozen input bundle is still a valid input bundle. The system MUST synthesize from it rather than recollecting.

### R3. Timeout Contract

The default unattended synthesis timeout MUST be `900` seconds.

The timeout MUST be overrideable by:

1. a CLI option `--timeout-seconds`
2. an environment variable `DAILY_INSIGHT_SYNTHESIS_TIMEOUT_SECONDS`

The CLI option MUST take precedence over the environment variable.

Non-positive timeout values MUST be rejected as precondition errors.

### R4. Resume Command

The CLI MUST expose a first-class `synthesize` command for resuming or re-attempting synthesis from frozen input.

The `run` command MUST use the same synthesis lifecycle contract as `synthesize`, rather than a separate implicit subprocess path.

### R5. Exit Codes

The lifecycle commands MUST use these exit codes:

- `0`: success, including an already-complete no-op
- `10`: collection failed
- `11`: operator precondition failed
  - examples: missing frozen input for `synthesize`, invalid timeout value, missing required local config or prompt artifact
- `20`: synthesis timed out
- `21`: synthesis subprocess failed before producing a usable digest
- `22`: synthesis completed but the structured digest output was missing or schema-invalid
- `30`: render failed after a valid structured digest was produced

### R6. Persisted Lifecycle States

The persisted lifecycle model MUST distinguish these stage/status names exactly:

- `collection_started`
- `collection_failed`
- `collection_completed`
- `synthesis_started`
- `synthesis_timed_out`
- `synthesis_failed`
- `synthesis_completed`
- `render_started`
- `render_failed`
- `render_completed`

How those names are stored is an implementation detail, but they MUST be inspectable from the persisted state for a date.

### R7. Output Promotion

The system MUST write synthesis and render outputs through temporary paths and only promote them to the final output paths after the stage succeeds.

The final `outputs/YYYY-MM-DD/digest.json` MUST only appear after a schema-valid structured digest exists.

The final `outputs/YYYY-MM-DD/digest.md` MUST only appear after rendering succeeds.

If synthesis or render fails, any temporary files MAY remain for debugging, but the final trusted output paths MUST NOT be newly created or overwritten by partial results.

### R8. Existing Outputs

If both final outputs already exist and `digest.json` validates against `schemas/daily_insight.schema.json`, `run` and `synthesize` MUST exit `0` and report that the date is already complete.

If only one final output exists, or if `digest.json` exists but is not schema-valid, the system MUST treat the date as incomplete and regenerate from the frozen input bundle rather than trusting the partial outputs.

### R9. Source Summary and Empty Buckets

The final digest MUST preserve explicit zero-count buckets in `source_summary.bucket_counts`.

The system MUST NOT silently re-bucket items to make an empty bucket appear populated.

When a state database is available for the date, recovery synthesis MUST surface source collection failures for that date in `source_summary.source_failures`.

When lifecycle state for source failures is unavailable, the digest MUST still preserve zero-count buckets and MUST report that collection diagnostics are unavailable rather than inventing failure details.

### R10. Observability

The CLI MUST emit a concise operator-visible message for each of these cases:

- reusing an existing frozen input bundle
- synthesis timeout
- already-complete no-op
- missing frozen input for `synthesize`

Persisted lifecycle state MUST be updated before the command exits.

### R11. Compatibility and Migration

Any lifecycle-state or SQLite schema change MUST be additive and MUST preserve readability of existing `state/daily_insight.db` records.

Linux operator documentation and `systemd` examples MUST require the service-manager timeout to exceed the application synthesis timeout by at least `60` seconds so the application can record a trusted failure state before the service manager terminates it.

## Edge Cases

- A date with zero items in one or more buckets MUST still produce a digest with explicit zero-count bucket coverage.
- A date with zero items in all buckets MAY still produce a digest if a frozen input bundle exists; the digest MUST make the lack of coverage explicit.
- A missing state database MUST NOT force recollection when a frozen input bundle already exists.
- If `digest.json` exists but `digest.md` does not, the run is incomplete and the system MUST render or regenerate from the frozen input rather than treating the date as complete.

## Non-goals

- changing the digest ranking rubric beyond what is required to preserve empty-bucket and failure visibility
- replacing Codex CLI with another synthesis backend
- recollecting live data automatically as part of synthesis recovery
- specifying the internal Python module layout beyond externally visible commands, state names, and files

## Acceptance Criteria

- Operators can resume synthesis from frozen input with a documented CLI command.
- The lifecycle contract covers success, timeout, subprocess failure, invalid structured output, and render failure with explicit exit codes.
- A completed date is idempotent to rerun and does not overwrite trusted outputs by default.
- Partial or invalid outputs are not trusted as completed results.
- Persisted lifecycle state and digest `source_summary` preserve enough information to distinguish collection, synthesis, and render failures.

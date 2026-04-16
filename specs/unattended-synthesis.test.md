# Unattended Synthesis Test Specification

Map the unattended synthesis lifecycle contract to concrete tests.

Related spec: `specs/unattended-synthesis.md`
Related plan: `docs/plans/2026-04-16-harden-unattended-daily-synthesis.md`

## Requirement Coverage Map

- `R1` stage boundary -> `T1`, `T2`, `T3`
- `R2` frozen input reuse -> `T2`, `T4`
- `R3` timeout contract -> `T5`, `T6`
- `R4` resume command -> `T3`, `T4`
- `R5` exit codes -> `T4`, `T5`, `T6`, `T7`, `T8`, `T9`
- `R6` persisted lifecycle states -> `T5`, `T6`, `T7`, `T8`, `T10`
- `R7` output promotion -> `T7`, `T8`, `T9`
- `R8` existing outputs -> `T2`, `T7`, `T11`
- `R9` source summary and empty buckets -> `T10`, `T12`
- `R10` observability -> `T2`, `T4`, `T5`, `T11`
- `R11` compatibility and migration -> `T13`, `T14`

## Unit and Integration Tests

### T1. `run` performs collection before synthesis on a fresh date

- Type: integration
- Fixture:
  - no `inputs/YYYY-MM-DD/items.jsonl`
  - mocked collection, synthesis, and render boundaries
- Verify:
  - `run` invokes collection first
  - synthesis receives the date-scoped frozen input path
  - render receives the date-scoped structured digest path

### T2. `run` reuses an existing frozen input bundle

- Type: integration
- Fixture:
  - `inputs/YYYY-MM-DD/items.jsonl` already exists
  - mocked collection boundary
- Verify:
  - `run` does not recollect
  - operator-visible output says the frozen input is being reused
  - synthesis and render proceed from the existing date-scoped paths

### T3. `synthesize` consumes existing frozen input without collection

- Type: integration
- Fixture:
  - valid `inputs/YYYY-MM-DD/items.jsonl`
  - mocked Codex subprocess and render path
- Verify:
  - `synthesize` can run independently of `run`
  - no collection function is called

### T4. Missing frozen input fails with the precondition exit code

- Type: integration
- Fixture:
  - absent `inputs/YYYY-MM-DD/items.jsonl`
- Verify:
  - `synthesize` exits with `11`
  - operator-visible output reports the missing frozen input
  - no synthesis subprocess is launched

### T5. Timeout precedence and timeout exit behavior

- Type: integration
- Fixture:
  - valid frozen input
  - mocked Codex subprocess that exceeds timeout
- Verify:
  - default timeout is `900`
  - environment timeout is honored when CLI override is absent
  - CLI `--timeout-seconds` overrides the environment
  - timeout exits with `20`
  - lifecycle state records `synthesis_started` then `synthesis_timed_out`

### T6. Invalid timeout value fails as a precondition error

- Type: unit or integration
- Fixture:
  - `--timeout-seconds 0` and `--timeout-seconds -1`
- Verify:
  - command exits with `11`
  - no subprocess launch occurs

### T7. Existing complete outputs are a successful no-op

- Type: integration
- Fixture:
  - valid frozen input
  - schema-valid `outputs/YYYY-MM-DD/digest.json`
  - existing `outputs/YYYY-MM-DD/digest.md`
- Verify:
  - `run` and `synthesize` exit `0`
  - no collection or synthesis subprocess is launched
  - operator-visible output says the date is already complete

### T8. Partial outputs are treated as incomplete

- Type: integration
- Fixture:
  - valid frozen input
  - only one of `digest.json` or `digest.md` exists
- Verify:
  - the command does not treat the date as complete
  - synthesis and/or render re-run from frozen input
  - final outputs are promoted only after success

### T9. Invalid structured digest fails with the synthesis-output exit code

- Type: integration
- Fixture:
  - valid frozen input
  - mocked Codex subprocess exits successfully but produces no `digest.json` or schema-invalid JSON
- Verify:
  - command exits with `22`
  - final trusted output paths are not newly promoted

### T10. Persisted lifecycle states distinguish stages

- Type: integration
- Fixture:
  - state database written through the normal CLI path
- Verify:
  - collection, synthesis, and render states are inspectable for a date
  - the persisted state uses the names defined in `R6`
  - state updates occur before command exit

### T11. Render failure is distinct from synthesis success

- Type: integration
- Fixture:
  - schema-valid structured digest exists
  - mocked render stage raises an error
- Verify:
  - command exits with `30`
  - lifecycle state records `synthesis_completed`, then `render_started`, then `render_failed`
  - `digest.md` is not promoted as a trusted final file

### T12. Empty buckets and missing collection diagnostics remain explicit

- Type: integration
- Fixture:
  - frozen input bundle with zero items in one or more buckets
  - run once with matching state DB
  - run once without matching state DB
- Verify:
  - `source_summary.bucket_counts` preserves zero-count buckets
  - `source_summary.source_failures` includes persisted source failures when available
  - when state is unavailable, the digest reports collection diagnostics unavailable instead of inventing failures

### T13. Existing state database remains readable after migration

- Type: integration
- Fixture:
  - a pre-change SQLite file produced by the current repository
- Verify:
  - the upgraded code can read existing records
  - new lifecycle states can be added without destroying or rewriting earlier rows

### T14. `systemd` timeout guidance matches the CLI contract

- Type: doc/config review
- Fixture:
  - `docs/codex-machine-setup.md`
  - `ops/systemd/daily-insight.service`
- Verify:
  - operator docs require the service timeout to exceed the CLI timeout by at least `60` seconds
  - service examples do not imply a shorter or conflicting timeout contract

## Dedicated-Machine Validation

### T15. Unattended run completes or fails fast with resumable state

- Type: end-to-end
- Fixture:
  - live `configs/sources.local.json`
  - working Codex auth
- Verify:
  - `uv run daily-insight run --date YYYY-MM-DD --config configs/sources.local.json --state-db state/daily_insight.db`
    either:
    - exits `0` with both final outputs present
    - or exits with the documented nonzero code while preserving `inputs/YYYY-MM-DD/items.jsonl` and a resumable lifecycle state

### T16. Resume from frozen input succeeds on the dedicated machine

- Type: end-to-end
- Fixture:
  - preserved `inputs/YYYY-MM-DD/items.jsonl` from a previous incomplete run
- Verify:
  - `uv run daily-insight synthesize --date YYYY-MM-DD --in-dir inputs/YYYY-MM-DD --out-dir outputs/YYYY-MM-DD --state-db state/daily_insight.db`
    completes without recollecting live sources
  - final outputs are present and schema-valid

## What Not To Test

- ranking quality beyond the digest-content contract already covered by `specs/daily-digest.md`
- source selection changes unrelated to synthesis lifecycle handling
- internal module names or helper function structure, except where lifecycle state names are operator-visible

## Open Gaps

- None in the current contract. If implementation chooses a different status-storage layout, the tests should still validate the externally visible status names and stage distinctions from `R6`.

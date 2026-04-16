# Harden unattended daily synthesis

- Status: complete
- Owner: maintainer
- Start date: 2026-04-16
- Last updated: 2026-04-16
- Related issue or PR: n/a
- Supersedes: none

## Goal

Make the unattended `uv run daily-insight run` path fail fast or recover cleanly when Codex synthesis stalls, while preserving frozen inputs and giving operators a deterministic way to resume from `inputs/YYYY-MM-DD/items.jsonl` without recollecting live sources.

## Why now

The repository is operational enough to collect and render a digest, but it is not yet reliable enough for unattended daily use. On 2026-04-16, `daily-insight run --date 2026-04-16 --config configs/sources.local.json --state-db state/daily_insight.db` completed collection and froze `inputs/2026-04-16/items.jsonl`, yet the nested `codex exec` step remained long-running with no `digest.json` written. The current workaround is manual recovery from the frozen input, which is acceptable as an operator fallback but not as the primary `systemd`-driven workflow.

## Context and orientation

- The repository now runs on Python 3.12 + `uv` with a Typer CLI, Pydantic models, SQLite state, Ruff, pytest, and Linux `systemd`.
- The closed operationalization plan in `docs/plans/2026-04-15-operationalize-daily-insight-repository.md` established collection, rendering, CI, and basic Linux host operations, then captured a later discovery that unattended synthesis and collection must be treated as separate recovery stages.
- `daily_insight/cli.py` currently implements:
  - `collect` -> deterministic source collection into `inputs/YYYY-MM-DD/items.jsonl`
  - `render` -> Markdown rendering from a structured digest JSON
  - `run` -> `collect_sources(...)`, then a direct `subprocess.run(["codex", "exec", ...])`, then render
- `run` now closes stdin explicitly with `stdin=subprocess.DEVNULL`, but that only prevents inherited interactive stdin. It does not yet provide timeout control, retry policy, structured synthesis state, or a first-class resume command from frozen input.
- The current SQLite schema in `daily_insight/storage.py` records run starts/completions and per-source collection attempts, but it does not distinguish collection success from synthesis success in a way operators can inspect later.
- The current CLI tests in `tests/test_cli.py` cover:
  - help surface
  - missing config handling
  - date-scoped path wiring
  - early exit when collection fails
  - unattended stdin closure for `codex exec`
- The current digest spec in `specs/daily-digest.md` defines required outputs and bucket behavior, but it does not yet define the operator-visible contract for synthesis timeout, synthesis failure, or resume-from-frozen-input behavior.
- Because timeout, resume, exit-code, and partial-output behavior are externally observable to operators, this initiative should introduce a dedicated lifecycle spec and test spec instead of overloading the digest-content spec alone.
- The workflow doc now states that `inputs/YYYY-MM-DD/items.jsonl` is the recovery boundary, but there is no explicit CLI command surface that operationalizes that guidance yet.
- Live operator evidence so far:
  - `2026-04-15` completed end-to-end with `digest.json` and `digest.md`
  - `2026-04-16` froze 25 collected items and required manual digest recovery from the frozen input after unattended synthesis remained long-running

## Scope

### In scope

- define the contract for synthesis timeout, failure visibility, and resume behavior after collection has already succeeded
- introduce an explicit unattended synthesis stage that can run against existing frozen input without recollecting sources
- add operator-visible timeout, exit-code, and state-tracking behavior around `codex exec`
- update tests, workflow docs, machine setup docs, and systemd-facing guidance to reflect the new run/recovery behavior
- verify the unattended path and the resume path on the dedicated Linux Codex machine

### Out of scope

- changing the approved source inventory or adding new live sources
- improving ranking or prompt quality beyond what is necessary to harden process control
- replacing Codex CLI with another synthesis backend
- adding delivery adapters such as email, Slack, or ticketing outputs
- broad refactors to collection, normalization, or schema shape unrelated to synthesis lifecycle handling

## Constraints

- Preserve deterministic collection as the first stage and keep `inputs/YYYY-MM-DD/items.jsonl` as the canonical recovery boundary.
- Do not silently recollect live data for a date when frozen input already exists for that date.
- Keep the four digest buckets distinct and preserve empty-bucket visibility through `source_summary`.
- Keep the operator path Linux-first and compatible with the current `systemd` service/timer model.
- The application timeout and `systemd` timeout / kill behavior must be aligned so the CLI can record a trusted failure state before the service manager tears the process tree down.
- Prefer the smallest behavioral surface needed to make unattended runs reliable; do not add parallel ad hoc scripts when the Typer CLI can own the contract.
- Any behavior change must follow `plan -> spec -> test-spec -> implement -> verify -> docs -> review`.
- Report only commands actually run in validation notes.
- Keep repo-local verification independent of live Codex credentials whenever feasible by faking or simulating the Codex subprocess in tests.

## Done when

- a dedicated unattended-synthesis spec and test spec explicitly define timeout, failure, resume, partial-output, and pre-existing-input/output behavior
- the CLI has a documented way to run synthesis from an existing frozen input bundle without recollecting sources
- unattended synthesis has an explicit timeout, override mechanism, and exit-code contract instead of indefinite waiting with no operator-visible state transition
- SQLite state and CLI exit behavior use documented stage/status names that let an operator distinguish:
  - collection failed
  - collection completed and synthesis has not started
  - collection succeeded but synthesis failed or timed out
  - synthesis succeeded but render failed
  - synthesis and render completed successfully
- repo-local tests cover the new synthesis lifecycle and recovery path without relying on live Codex execution
- the Linux operator docs and `systemd` guidance describe the normal unattended path and the manual recovery path from frozen input
- one dedicated-machine validation proves the hardened path can either complete unattended or fail fast with enough information to resume safely

## Milestones

1. Define the synthesis lifecycle contract [complete]
   - Files/components: new `specs/unattended-synthesis.md`, new `specs/unattended-synthesis.test.md`, `docs/workflows.md`, cross-reference updates in `specs/daily-digest.md`
   - Dependencies: none
   - Risk: medium; implementation will drift immediately if timeout and recovery semantics remain implicit
   - Work:
     - specify operator-visible behavior for synthesis success, timeout, nonzero exit, and resume-from-frozen-input
     - define the default timeout, how it is overridden, and whether the override is CLI-only, environment-based, or both
     - define exact CLI exit codes and persisted status names for collection failure, synthesis timeout, synthesis failure, render failure, and full success
     - define whether `run` should fail immediately when frozen input already exists but synthesis is incomplete, or whether it should offer an explicit resume path
     - define behavior when frozen input already exists and outputs also already exist
     - define temp-file and atomic-promotion rules for `digest.json` and `digest.md`
     - define the required observability for empty buckets and source failures when a recovery run is synthesized from a previously collected bundle
   - Validation commands:
     - none; maintainer review of the new spec and test spec is the acceptance step before implementation begins
   - Expected observable result: maintainers can review a precise, self-contained contract for unattended synthesis and recovery before code changes begin.

2. Implement internal synthesis supervision and stage state [complete]
   - Files/components: new internal synthesis module such as `daily_insight/synthesize.py`, `daily_insight/storage.py`, `daily_insight/cli.py`, `tests/test_cli.py`, `tests/test_storage.py`, new lifecycle tests in `tests/`
   - Dependencies: Milestone 1
   - Risk: high; subprocess timeout and process-tree cleanup can create false failures, orphan processes, or misleading state if handled sloppily
   - Work:
     - add explicit timeout handling around the synthesis subprocess using the contract from Milestone 1
     - ensure timed-out or failed Codex runs update SQLite state distinctly from successful collection runs
     - decide and implement whether synthesis attempts belong in a new table or an extended run-state model, including migration safety for existing `state/daily_insight.db`
     - ensure failure leaves frozen input intact and does not publish partial `digest.json` / `digest.md` as trusted outputs
     - ensure timeout or kill handling cleans up the entire Codex process tree rather than leaving orphaned children
   - Validation commands:
     - `uv run pytest -q tests/test_cli.py tests/test_storage.py tests/test_synthesize.py`
     - `uv run ruff check .`
     - `uv run python - <<'PY' ... inspect SQLite stage/status rows after simulated timeout/failure ... PY`
   - Expected observable result: the repository has a supervised synthesis primitive with explicit timeout and stage-level state before any new public recovery surface is exposed.

3. Expose the public synthesis and resume contract in the CLI [complete]
   - Files/components: `daily_insight/cli.py`, internal synthesis module from Milestone 2, `tests/test_cli.py`, possibly `scripts/run_daily.sh`
   - Dependencies: Milestone 2
   - Risk: medium; the run path is operator-facing and tightly coupled to the current daily workflow
   - Work:
     - add a dedicated `synthesize` subcommand or equivalent explicit resume surface that consumes `inputs/YYYY-MM-DD/items.jsonl`
     - refactor `run` to orchestrate `collect -> synthesize -> render` through the same stage boundary instead of a monolithic subprocess call
     - preserve current date-scoped defaults and output locations
     - ensure pre-existing frozen input and pre-existing outputs follow the Milestone 1 contract rather than implicit current behavior
   - Validation commands:
     - `uv run pytest -q tests/test_cli.py tests/test_synthesize.py`
     - `uv run daily-insight --help`
   - Expected observable result: operators have one first-class command for resuming synthesis from frozen input, and `run` becomes a thin composition over the same supervised stage boundaries.

4. Update Linux operator workflow and recovery docs [complete]
   - Files/components: `README.md`, `docs/codex-machine-setup.md`, `docs/workflows.md`, `scripts/run_daily.sh`, `ops/systemd/daily-insight.service`, `ops/systemd/daily-insight.timer`
   - Dependencies: Milestone 3
   - Risk: medium; the code can be correct but still unusable if the operator docs and systemd examples do not reflect the new recovery contract
   - Work:
     - document the normal unattended path, timeout behavior, and recovery path from frozen input
     - align CLI timeout behavior with `systemd` timeout / kill semantics so service-manager behavior does not race persisted synthesis state
     - decide whether `systemd` should call `run` directly, a wrapper with additional timeout environment, or a resumed synthesis path after partial failure
     - keep publication-safe docs aligned with the actual Linux operator flow
   - Validation commands:
     - `systemd-analyze verify ops/systemd/daily-insight.service ops/systemd/daily-insight.timer`
     - `bash scripts/ci.sh`
   - Expected observable result: a Linux operator can tell exactly how to respond when collection succeeded but synthesis did not finish, without rereading old plan notes.

5. Validate unattended and recovery behavior on the dedicated machine [complete]
   - Files/components: live operator config, `inputs/`, `outputs/`, `state/daily_insight.db`, validation notes in this plan
   - Dependencies: Milestone 4, working Codex CLI auth
   - Risk: medium; repo-local tests can simulate failures, but only the dedicated machine can prove the full unattended path against real Codex execution
   - Work:
     - run one date-scoped unattended command with the hardened path
     - if necessary, exercise the resume path from a preserved `inputs/YYYY-MM-DD/items.jsonl`
     - confirm final outputs, CLI exit behavior, and persisted state transitions match the documented contract
   - Validation commands:
     - `uv run daily-insight run --date YYYY-MM-DD --config configs/sources.local.json --state-db state/daily_insight.db`
     - `uv run daily-insight synthesize --date YYYY-MM-DD --in-dir inputs/YYYY-MM-DD --out-dir outputs/YYYY-MM-DD --state-db state/daily_insight.db`
     - `uv run python -m json.tool outputs/YYYY-MM-DD/digest.json > /dev/null`
     - `uv run daily-insight render outputs/YYYY-MM-DD/digest.json outputs/YYYY-MM-DD/digest.md`
     - `uv run python - <<'PY' ... inspect SQLite stage/status rows for the validation run ... PY`
   - Expected observable result: the daily operator path is either reliably unattended or deterministically resumable from frozen input, with validation notes that prove the distinction.

## Progress

- 2026-04-16: created this plan after post-merge operator verification showed that `daily-insight run` could finish collection for `2026-04-16` but still leave the synthesis step long-running without writing `outputs/2026-04-16/digest.json`.
- 2026-04-16: confirmed the repo already documents frozen input as the recovery boundary, but the CLI and state model do not yet operationalize that guidance with an explicit synthesis command or stage-specific failure state.
- 2026-04-16: revised the plan after plan review to require a dedicated unattended-synthesis spec, explicit timeout / exit-code / status decisions, stronger state validation, and internal lifecycle hardening before exposing a new public CLI surface.
- 2026-04-16: completed the Milestone 1 spec slice by adding `specs/unattended-synthesis.md`, `specs/unattended-synthesis.test.md`, and cross-references in the digest/workflow docs.
- 2026-04-16: completed Milestone 2 by adding `daily_insight/synthesize.py`, additive `lifecycle_events` persistence in SQLite, supervised timeout/error handling for `codex exec`, deterministic `source_summary` normalization from frozen inputs, and stage-specific lifecycle records for collection, synthesis, and render.
- 2026-04-16: completed Milestone 3 by refactoring `daily_insight/cli.py` so `run` reuses existing frozen input, no-ops on an already-complete date, maps collection failures to the documented exit code, and exposes a first-class `synthesize` recovery command.
- 2026-04-16: completed Milestone 4 by updating README/operator workflow docs and aligning the sample `systemd` service with `DAILY_INSIGHT_SYNTHESIS_TIMEOUT_SECONDS=900` and `TimeoutStartSec=960`.
- 2026-04-16: completed Milestone 5 on the dedicated machine using temporary validation directories under `/tmp/daily-insight-validation-Y3h2tC/`, where a live `run` for April 16, 2026 completed end-to-end and a follow-up `synthesize` run reused the preserved frozen input without recollecting sources.

## Decision log

- 2026-04-16: create a new plan instead of reopening the closed operationalization plan -> this is a new behavior initiative with its own operator contract and review scope.
- 2026-04-16: treat synthesis hardening as separate from source or prompt quality work -> the current blocker is run reliability, not content selection.
- 2026-04-16: plan around an explicit synthesis stage rather than a monolithic `run`-only path -> recovery from frozen input should be a first-class operator action, not an undocumented manual workaround.
- 2026-04-16: keep Codex CLI as the synthesis backend for this initiative -> the problem to solve is supervision and recovery, not model-provider replacement.
- 2026-04-16: use a dedicated unattended-synthesis spec instead of overloading the digest-content spec -> timeout, resume, and exit-code behavior are operator-visible runtime contracts, not just content-shape rules.
- 2026-04-16: sequence internal supervision/state work before public CLI exposure -> the public `synthesize` command should not ship before timeout and state semantics exist.
- 2026-04-16: define `run` to reuse an existing frozen input bundle instead of recollecting the same date -> this preserves determinism and turns the existing recovery boundary into the default operator behavior.
- 2026-04-16: make a valid existing `digest.json` + `digest.md` pair a successful no-op -> repeated runs for a completed date should be idempotent by default.
- 2026-04-16: set the unattended synthesis default timeout to `900` seconds, with CLI override taking precedence over `DAILY_INSIGHT_SYNTHESIS_TIMEOUT_SECONDS` -> the contract needs one default that operator docs and `systemd` settings can align around.
- 2026-04-16: normalize `source_summary` from frozen input and persisted collection state after synthesis -> empty buckets and collection failures should remain deterministic even if the model omits or rewrites them.
- 2026-04-16: validate the live machine with temporary input/output directories for the same digest date -> this exercises real collection and recovery behavior without overwriting the trusted repository artifacts already stored under `inputs/2026-04-16/` and `outputs/2026-04-16/`.

## Surprises and discoveries

- 2026-04-16: closing stdin explicitly fixed one unattended-run bug, but it did not by itself guarantee timely completion of the nested `codex exec` step.
- 2026-04-16: the current SQLite schema gives good visibility into collection attempts but almost no visibility into synthesis lifecycle, which makes post-failure diagnosis harder than it should be.
- 2026-04-16: the repository already has enough deterministic structure to recover a date manually from frozen input; the missing piece is a first-class command and failure contract, not a new storage model for collected data.
- 2026-04-16: repeated synthesis from the same frozen April 16, 2026 bundle produced another valid digest with different byte-for-byte content and size, so the pipeline is operationally resumable but not content-deterministic at the model-output layer.

## Validation and acceptance

- Milestone 1 is accepted when the dedicated lifecycle spec and test spec explicitly describe timeout, failure, resume, exit-code, state-status, and partial-output behavior.
- Milestone 2 is accepted when repo-local tests prove timeout/failure handling, process cleanup, and stage persistence without relying on live Codex execution.
- Milestone 3 is accepted when the CLI exposes a dedicated synthesis-stage command and `run` composes over it without breaking current date-scoped defaults.
- Milestone 4 is accepted when Linux operator docs and `systemd` guidance describe the new run and recovery behavior unambiguously.
- Milestone 5 is accepted when a dedicated-machine validation shows either a complete unattended run or a documented fast-fail plus successful resume from frozen input, with persisted state matching the contract.

## Validation notes

- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight run --date 2026-04-16 --config configs/sources.local.json --state-db state/daily_insight.db` -> collection completed and froze `inputs/2026-04-16/items.jsonl`, but unattended synthesis remained long-running with no `digest.json` produced during the observed window.
- `PATH=$HOME/.local/bin:$PATH pgrep -af 'daily-insight run --date 2026-04-16|codex exec -C /home/xiongxianfei/data/20260415-daily-engineering-security-insight'` -> confirmed a persistent `uv -> python -> node codex exec -> vendor codex` process tree during the stalled synthesis attempt.
- `readlink /proc/<codex-pid>/fd/0` on the live synthesis process -> showed `/dev/null`, confirming the later long-running behavior was not caused by inherited interactive stdin.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run pytest -q` -> passed after the stdin fix, confirming the repo remained green even though unattended synthesis still needed lifecycle hardening.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run ruff check .` -> passed after the lifecycle implementation and doc updates.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run pytest -q tests/test_cli.py tests/test_storage.py tests/test_synthesize.py` -> passed with the focused lifecycle coverage.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run pytest -q` -> passed across the full suite after the new synthesis supervision path landed.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run python -m json.tool schemas/daily_insight.schema.json > /dev/null` -> passed.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight collect --dry-run --config configs/sources.example.json` -> passed and preserved placeholder-safe dry-run behavior.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight render examples/sample_digest.json /tmp/digest.md` -> passed.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight --help` -> showed the expected `collect`, `render`, `run`, and `synthesize` commands.
- `systemd-analyze verify ops/systemd/daily-insight.service ops/systemd/daily-insight.timer` -> passed with the existing workspace permission warnings on the sample unit files (`executable` / `world-writable`).
- `PATH=$HOME/.local/bin:$PATH UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv bash scripts/ci.sh` -> passed after the lifecycle implementation and doc updates.
- `PATH=$HOME/.local/bin:$PATH codex login status` -> reported `Logged in using ChatGPT` on the dedicated machine before the live validation runs.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run python - <<'PY' ... query pre-validation max ids from state/daily_insight.db ... PY` -> captured the starting high-water marks `runs_max=15`, `attempts_max=60`, and `lifecycle_max=4`.
- `PATH=$HOME/.local/bin:$PATH UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight run --date 2026-04-16 --config configs/sources.local.json --state-db state/daily_insight.db --in-dir /tmp/daily-insight-validation-Y3h2tC/run-input --out-dir /tmp/daily-insight-validation-Y3h2tC/run-output` -> succeeded; collected 25 items, preserved the optional `openai-news` `HTTP Error 403: Forbidden` warning, and wrote `digest.json` plus `digest.md`.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run python -m json.tool /tmp/daily-insight-validation-Y3h2tC/run-output/digest.json > /dev/null` -> passed.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run python - <<'PY' ... query runs/source_attempts/lifecycle_events rows above the pre-validation ids ... PY` -> showed one new completed collection run (`run_id=16`), four new source-attempt rows, and the expected lifecycle sequence `collection_started -> collection_completed -> synthesis_started -> synthesis_completed -> render_started -> render_completed`.
- `PATH=$HOME/.local/bin:$PATH UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight synthesize --date 2026-04-16 --in-dir /tmp/daily-insight-validation-Y3h2tC/run-input --out-dir /tmp/daily-insight-validation-Y3h2tC/resume-output --state-db state/daily_insight.db` -> succeeded from the preserved frozen input without recollecting sources.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run python -m json.tool /tmp/daily-insight-validation-Y3h2tC/resume-output/digest.json > /dev/null` -> passed.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight render /tmp/daily-insight-validation-Y3h2tC/resume-output/digest.json /tmp/daily-insight-validation-Y3h2tC/resume-rerender.md` -> passed.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run python - <<'PY' ... query runs/source_attempts/lifecycle_events rows above the post-run ids ... PY` -> showed no new `runs` or `source_attempts` rows and only the expected resume lifecycle sequence `synthesis_started -> synthesis_completed -> render_started -> render_completed`.

## Idempotence and recovery

- Preserve `inputs/YYYY-MM-DD/items.jsonl` as the handoff boundary between deterministic collection and synthesis recovery.
- Do not overwrite a trusted `digest.json` / `digest.md` pair with a partial or failed synthesis attempt; use temporary files and atomic promotion where needed.
- If synthesis times out, preserve the frozen input, record the failure state, and make the documented next step a resume command rather than recollection.
- If a later implementation adds timeout-based process termination, ensure it cleans up the entire Codex process tree instead of leaving orphaned child processes behind.
- If the implementation changes the SQLite schema or status model, migrate additively, back up `state/daily_insight.db`, and verify existing runs remain readable before relying on the new model operationally.
- If `digest.json` exists but `digest.md` does not, treat the JSON file as potentially valid but the overall run as incomplete until the render step is either completed or the JSON is revalidated against the current schema.
- Keep live-source collection, synthesis, and rendering failures distinguishable in both CLI exit behavior and persisted state.

## Outcomes and retrospective

- Completed on 2026-04-16.
- The CLI now has a first-class `synthesize` recovery command, a `900` second default timeout with CLI/env overrides, additive SQLite lifecycle events, idempotent no-op handling for complete dates, and deterministic `source_summary` normalization from frozen inputs plus persisted collection failures.
- Dedicated-machine validation proved both the live unattended `run` path and the explicit frozen-input `synthesize` recovery path on April 16, 2026 without requiring manual recollection of sources.

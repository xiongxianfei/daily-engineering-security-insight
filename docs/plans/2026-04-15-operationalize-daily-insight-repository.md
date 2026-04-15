# Operationalize daily insight repository

- Status: closed
- Owner: maintainer
- Start date: 2026-04-15
- Last updated: 2026-04-16
- Related issue or PR: n/a
- Supersedes: `docs/plans/2026-04-15-bootstrap-daily-insight.md`

## Goal

Create a Linux-hosted, Codex CLI-oriented repository that uses Python 3.12, `uv`, Typer, Pydantic, SQLite, Ruff, pytest, and a `systemd` timer to deterministically collect daily inputs across four buckets, synthesize a schema-validated digest, render Markdown, and support repeatable daily operation on a dedicated Codex machine.

## Why now

The local scaffold covers much of the repository surface, but it is still organized around ad hoc scripts, `requirements.txt`, and partial local verification. The implementation should not proceed against that implicit scaffold because the intended runtime stack is now explicit: Python 3.12 + `uv` + Typer + Pydantic + SQLite + Ruff + pytest + Linux `systemd`. The plan needs to sequence the migration to that foundation before collector hardening and operations work begin.

## Context and orientation

- The local workspace already contains an initial scaffold: collectors, schema, example digest, renderer, CI workflow, setup docs, and a bootstrap plan.
- The four required buckets are `software-engineering`, `security`, `ai-for-security`, and `security-for-ai`.
- The intended implementation stack is Python 3.12, `uv`, Typer, Pydantic, SQLite, Ruff, pytest, and a Linux `systemd` timer.
- The destination GitHub repository at `https://github.com/xiongxianfei/daily-engineering-security-insight` is empty, but this local workspace is not. Planning should focus on operationalizing and publishing the existing scaffold rather than recreating it from scratch.
- The workspace is not a Git clone right now; `git status --short` fails with `fatal: not a git repository`. Treat this directory as local staging content until it is connected to the GitHub remote.
- The current scaffold does not yet match that stack:
  - packaging is based on `requirements.txt` and `requirements-dev.txt`, not `pyproject.toml` + `uv`
  - the collector entrypoint uses `argparse`, not Typer
  - config and normalized item boundaries are raw dictionaries, not Pydantic models
  - there is no documented SQLite role or schema yet
  - CI is pinned to Python 3.11 today instead of Python 3.12
  - repo-local linting is not yet enforced with Ruff
  - the versioned source config is still only a placeholder example; there is no approved live-source inventory yet
- Historical validation notes show the repo is partially runnable, but those notes came from a non-target environment and should not define the final operator workflow:
  - schema JSON parsed successfully
  - collector dry-run succeeded against the example config
  - renderer succeeded when writing to a known writable staging path
  - `pytest` failed before collection because the active environment did not yet have `jsonschema` installed
  - writing under repo-local `outputs/` previously hit a permissions error in that environment
- The intended architecture is:
  - frozen normalized input under `inputs/YYYY-MM-DD/items.jsonl` remains the source of truth for synthesis
  - Typer provides the operator-facing CLI for collect, render, and daily-run commands
  - Pydantic validates source config, normalized collector items, and internal command inputs
  - SQLite stores local operational state such as run history, source attempts, and dedupe metadata; it does not replace date-scoped JSON artifacts
  - Linux `systemd` units schedule the daily command on the dedicated Codex host; Windows scheduling is not a target for this initiative
  - digest quality should come from a small approved set of primary sources per bucket, not one broad aggregator

## Scope

### In scope

- finalize repository bootstrap for the daily insight workflow
- migrate the scaffold onto the declared Python 3.12 + `uv` + Typer + Pydantic + SQLite + Ruff + pytest foundation
- define and freeze an approved source inventory with rationale and failure policy before wiring live collection into the daily run
- keep specs, test specs, schema, examples, scripts, and docs aligned
- make machine setup and daily operation reproducible on the dedicated Linux Codex host
- prepare the local scaffold to be pushed into the target GitHub repo

### Out of scope

- authenticated enterprise source integrations
- automated delivery to email, Slack, or ticketing systems
- multi-user or hosted product features
- broad prompt experimentation before deterministic collection quality is stable
- Windows scheduling or a non-`systemd` production scheduler

## Constraints

- Prefer deterministic collection before synthesis.
- Keep the four buckets distinct in both input metadata and digest output.
- Use frozen date-scoped inputs under `inputs/YYYY-MM-DD/` before Codex synthesis.
- Target runtime is Linux on a dedicated Codex machine with `systemd`; do not design this plan around Windows parity.
- Project packaging, dependency management, and command execution should use Python 3.12 and `uv`.
- Typer should be the primary operator entrypoint instead of adding more ad hoc shell-only commands.
- Pydantic should own config and normalized-item validation at process boundaries.
- SQLite is for local operational state and auditability, not as the canonical digest payload store.
- Prefer primary official advisories, changelogs, release notes, and machine-readable feeds over broad summary aggregators when both exist.
- Every approved live source should declare its bucket, transport, rationale, expected signal, and failure policy.
- Keep example source config public and placeholder-safe; keep operator-managed live source config separate from versioned examples.
- Keep diffs reviewable and milestone-sized.
- Follow `plan -> spec -> test-spec -> implement -> verify -> docs -> review` for behavior-changing work.
- Do not assume GitHub Actions can run Codex CLI; daily generation runs on a dedicated machine.
- Report only commands actually run in validation notes.

## Done when

- the repository can be bootstrapped from docs on the dedicated Linux Codex machine using Python 3.12 and `uv`
- one documented `uv`-managed CLI path can deterministically collect inputs for a date, produce schema-valid JSON, and render Markdown
- an approved source inventory exists for all four buckets before live-source collection is enabled
- specs, test specs, schema, example data, scripts, and workflow docs all match the implemented behavior
- CI runs on Python 3.12 and covers Ruff plus the repo-local checks that do not require Codex credentials or live private sources
- Linux `systemd` service and timer units are documented, syntactically valid, and aligned with the shipped CLI command
- the workspace contents are ready for maintainer publication to the target GitHub repo with no missing operator, recovery, or plan docs

## Milestones

1. Baseline repository scaffold and contract [complete]
   - Files/components: `AGENTS.md`, `README.md`, `docs/workflows.md`, `docs/codex-machine-setup.md`, `specs/daily-digest.md`, `specs/daily-digest.test.md`, `schemas/daily_insight.schema.json`, `examples/sample_digest.json`, `.github/workflows/ci.yml`
   - Dependencies: none
   - Risk: low
   - Validation commands:
     - `python -m json.tool schemas/daily_insight.schema.json`
     - `python scripts/render_digest.py examples/sample_digest.json <writable-output-path>`
   - Expected observable result: the repo documents the four-bucket contract, sample output validates structurally, and contributors can inspect the intended end-to-end shape without live sources.

2. Establish the Python 3.12 application foundation [complete]
   - Files/components: `pyproject.toml`, `uv.lock`, `.python-version` or equivalent docs, `.github/workflows/ci.yml`, `scripts/ci.sh`, `README.md`, `docs/codex-machine-setup.md`, new CLI/package modules such as `daily_insight/cli.py`, `daily_insight/config.py`, `daily_insight/models.py`, `daily_insight/storage.py`
   - Dependencies: Milestone 1
   - Risk: medium; packaging and entrypoint churn can mask real product issues if the runtime contract stays implicit
   - Work:
     - replace `requirements*.txt`-first workflow with `pyproject.toml` + `uv` while keeping verification commands explicit
     - introduce a Typer CLI as the primary operator interface with stable commands for collect, render, and full daily runs
     - move source config and normalized item validation to Pydantic models instead of raw dictionaries at process boundaries
     - define a minimal SQLite schema and ownership for run history, source attempts, and dedupe metadata
     - upgrade CI to Python 3.12 and add Ruff to repo-local verification
   - Validation commands:
     - `uv sync --dev`
     - `uv run ruff check .`
     - `uv run pytest -q`
     - `uv run daily-insight --help`
   - Expected observable result: a fresh Python 3.12 environment can install the repo with `uv`, run lint/tests, and discover one stable CLI entrypoint for operator commands.

3. Freeze the approved source inventory [complete]
   - Files/components: `docs/source-inventory.md`, `configs/sources.example.json`, `docs/workflows.md`, `README.md`, `daily_insight/config.py`
   - Dependencies: Milestone 2
   - Risk: medium; poor source selection will degrade digest quality more than prompt or rendering tweaks
   - Work:
     - define a small approved set of high-signal sources for each bucket, prioritizing official advisories, changelogs, release notes, and machine-readable feeds
     - record for each approved source: name, bucket, transport, rationale, expected signal, and how failures should surface in `source_summary`
     - separate public placeholder examples from operator-managed live configuration so the repo remains safe to publish
     - decide which sources are required for a complete daily run and which are optional enrichers
   - Validation commands:
     - `uv run python -m json.tool configs/sources.example.json > /dev/null`
     - `uv run daily-insight collect --dry-run --date 2026-04-15 --config configs/sources.example.json`
   - Expected observable result: maintainers have an explicit source inventory to review and approve, and the example config exercises the intended config shape without depending on private or unstable feeds.

4. Harden deterministic collection and repo-local verification [complete]
   - Files/components: `collectors/collect_sources.py`, `collectors/normalize.py`, `configs/sources.example.json`, `tests/`, `daily_insight/config.py`, `daily_insight/models.py`, `daily_insight/storage.py`, `scripts/ci.sh`, `docs/source-inventory.md`
   - Dependencies: Milestone 2, Milestone 3
   - Risk: medium; collection failures, source-shape drift, and local state mistakes can look like digest quality problems if failure paths are not explicit
   - Work:
     - add or expand tests for collector normalization, config validation, failure visibility, and SQLite-backed run bookkeeping
     - preserve `inputs/YYYY-MM-DD/items.jsonl` as the frozen synthesis input while recording operational metadata in SQLite
     - make dry-run behavior deterministic from the example config and expose skipped or failed sources explicitly
     - implement the approved source inventory without allowing one noisy feed to dominate a bucket
     - document and verify writable-path assumptions for `inputs/`, `outputs/`, and the SQLite state directory
   - Validation commands:
     - `uv run python -m json.tool schemas/daily_insight.schema.json > /dev/null`
     - `uv run daily-insight collect --dry-run --date 2026-04-15 --config configs/sources.example.json`
     - `uv run pytest -q`
   - Expected observable result: repo-local verification proves that collection inputs remain deterministic, failures stay visible, and the local state layer does not replace or corrupt frozen date-scoped artifacts.

5. Operationalize Linux daily runs with `systemd` [complete]
   - Files/components: `scripts/run_daily.sh` or a replacement wrapper, `prompts/daily_digest_prompt.md`, `ops/systemd/daily-insight.service`, `ops/systemd/daily-insight.timer`, `docs/codex-machine-setup.md`, `README.md`, `daily_insight/cli.py`, `daily_insight/storage.py`
   - Dependencies: Milestone 4, working Codex CLI auth on the dedicated machine
   - Risk: medium; runtime failures can come from machine auth, Linux path assumptions, timer environment differences, or non-atomic writes around partial runs
   - Work:
     - align the daily-run command and any shell wrapper with the Typer CLI introduced in Milestone 2
     - make Linux-only support explicit in docs and systemd unit examples
     - verify that a date-scoped run writes `outputs/YYYY-MM-DD/digest.json` and `outputs/YYYY-MM-DD/digest.md`
     - capture operator recovery steps for partial runs, missing source configs, SQLite lock issues, and Codex auth failures
     - validate `systemd` unit and timer definitions before relying on them operationally
   - Validation commands:
     - `uv run daily-insight run --date 2026-04-15 --config configs/sources.local.json`
     - `uv run daily-insight render outputs/2026-04-15/digest.json outputs/2026-04-15/digest.md`
     - `systemd-analyze verify ops/systemd/daily-insight.service ops/systemd/daily-insight.timer`
   - Expected observable result: an operator on the dedicated Linux Codex machine can run one documented command for a date and obtain both structured and human-readable digests, with `systemd` units that match the shipped workflow.

6. Prepare publication and maintainer handoff [complete]
   - Files/components: `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `.github/workflows/ci.yml`, `docs/plan.md`, `docs/plans/2026-04-15-operationalize-daily-insight-repository.md`
   - Dependencies: Milestone 5
   - Risk: low
   - Work:
     - confirm repo metadata, contribution docs, CI checks, and operator setup docs match the implemented Linux + `uv` workflow
     - document publication prerequisites for connecting this local workspace to the empty GitHub repo without treating `git push` as a code-verification step
     - close or supersede this plan only if a materially different behavior initiative remains after publication readiness
   - Validation commands:
     - `uv run ruff check .`
     - `uv run pytest -q`
     - `bash scripts/ci.sh`
   - Expected observable result: the workspace is internally consistent, maintainers have a clear publish checklist, and the repository can be connected and pushed without missing docs or hidden operational assumptions.

## Progress

- 2026-04-15: initial scaffold created with collectors, schema, renderer, sample digest, setup docs, and CI workflow.
- 2026-04-15: created a replacement active plan instead of writing a second overlapping bootstrap summary; the old plan remains as the superseded stub.
- 2026-04-15: verified that schema parsing, example collector dry-run, and sample rendering work in part; the local environment still needs dependency bootstrap and output-path permission confirmation.
- 2026-04-16: revised the plan to align the implementation sequence with the declared Python 3.12 + `uv` + Typer + Pydantic + SQLite + Ruff + pytest + Linux `systemd` stack before additional behavior work.
- 2026-04-16: promoted live-source approval into its own milestone so collection hardening and daily-run automation do not proceed against an implicit source list.
- 2026-04-16: implemented the Milestone 2 foundation slice: `pyproject.toml`, `uv.lock`, `.python-version`, the `daily_insight` package, typed config/models, SQLite state store, a Typer CLI, and Python 3.12 + `uv` CI/docs updates.
- 2026-04-16: completed Milestone 3 by freezing the approved source inventory in `docs/source-inventory.md`, adding required-versus-supplemental source metadata to the typed config model, and keeping `configs/sources.example.json` placeholder-safe for deterministic dry-runs.
- 2026-04-16: completed the repo-local Milestone 4 hardening slice by recording collection runs and source attempts in SQLite, honoring `fail` versus `warn` source policies, capping items per source, and keeping the frozen JSONL input as the canonical artifact.
- 2026-04-16: started Milestone 5 by aligning the Typer `run` command, `scripts/run_daily.sh`, and the sample `systemd` unit with the same date-scoped command contract.
- 2026-04-16: completed Milestone 5 with a real Linux-host end-to-end run using an operator-managed `configs/sources.local.json`, producing `outputs/2026-04-15/digest.json` and `outputs/2026-04-15/digest.md`.
- 2026-04-16: completed Milestone 6 by tightening maintainer handoff docs, publication prerequisites, ignored local state, and repository contribution guidance around the implemented Linux + `uv` workflow.

## Surprises and discoveries

- 2026-04-15: the local workspace is not empty even though the destination GitHub repo is empty; plan scope should focus on operationalizing and publishing the existing scaffold.
- 2026-04-15: the workspace currently has no `.git` metadata, so GitHub publication is a later operator step rather than something that can be verified locally today.
- 2026-04-15: `pytest` currently fails because `jsonschema` is not installed in the active Python environment.
- 2026-04-15: rendering to a known writable staging path works, but creating repo-local outputs previously failed in another environment; operator-path assumptions must be revalidated on the Linux target host rather than codified from that earlier result.
- 2026-04-16: the current scaffold reflects earlier implementation defaults more than the declared target stack; the plan must explicitly migrate the runtime foundation instead of treating that work as incidental cleanup.
- 2026-04-16: source choice is a first-order product decision for digest quality, so the plan should treat source approval as a concrete milestone rather than an implied later dependency.
- 2026-04-16: `uv sync --dev` fails on this Codex workspace when the project environment targets repo-local `.venv`; the same sync succeeds when `UV_PROJECT_ENVIRONMENT` points at `/tmp`, so the blocker appears to be a workspace filesystem quirk rather than the package metadata.
- 2026-04-16: the highest-signal security source in the approved inventory is still CISA KEV, but it does not fit the current RSS-only collector cleanly, so it remains an approved manual side channel until Milestone 4 decides whether to add a new transport or keep it operator-reviewed.
- 2026-04-16: `systemd-analyze verify` succeeds for the sample unit and timer, but this workspace mounts those files as executable and world-writable; permission warnings are environmental and could not be cleared with `chmod`.
- 2026-04-16: OpenAI News rejects the current RSS fetch path with `HTTP Error 403: Forbidden`, so it remains an optional `warn` source rather than a required blocker for daily generation.
- 2026-04-16: `codex exec` refuses to run in this non-Git workspace unless `--skip-git-repo-check` is passed through the CLI wrapper.
- 2026-04-16: the structured-output schema needed `top_items[].published_at` in the required field list before `codex exec` would accept it as a valid JSON schema.

## Decision log

- 2026-04-15: replace the thin bootstrap stub with a more detailed active plan file -> avoids duplicating the same initiative while preserving the original stub for historical context.
- 2026-04-15: treat repository bootstrap, machine operability, and GitHub publication as separate milestones -> keeps each PR-sized and reviewable.
- 2026-04-15: keep production source integrations and delivery adapters out of this plan -> the current goal is a dependable single-machine daily digest workflow, not full distribution.
- 2026-04-16: make Linux + `systemd` the only target runtime for this initiative -> the requested stack already chooses that direction, and keeping Windows parity in scope would add ambiguity without improving the operator path.
- 2026-04-16: insert a dedicated foundation milestone before collector hardening -> Typer, Pydantic, SQLite, `uv`, Python 3.12, and Ruff change architecture and verification enough that they should not be hidden inside a generic test-hardening milestone.
- 2026-04-16: treat GitHub publication as maintainer handoff, not as repository validation -> `git push` proves repository connectivity, not correctness.
- 2026-04-16: add an explicit source-inventory milestone before live collection hardening -> source quality and failure policy affect digest usefulness more than later prompt or scheduling work.
- 2026-04-16: keep the repo default `uv` workflow unchanged and use `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv` only for local verification on this machine -> the workaround avoids encoding a workspace-specific filesystem limitation into project docs or code.
- 2026-04-16: keep the versioned example config placeholder-safe even after source approval -> repo-local validation should not depend on live network feeds, while `docs/source-inventory.md` remains the reviewed source of truth for real operator URLs.
- 2026-04-16: cap machine-readable sources with `max_items_per_source` in the typed config -> this prevents one noisy feed from dominating a bucket before synthesis/ranking logic runs.
- 2026-04-16: make `scripts/run_daily.sh` a thin wrapper over `uv run daily-insight run` -> the operator path, tests, and `systemd` unit should exercise one command contract instead of parallel shell and Python flows.
- 2026-04-16: keep OpenAI News as an optional source with `warn` failure policy -> the live operator run proved the current RSS endpoint is not reliable enough to gate daily generation.
- 2026-04-16: keep `state/` out of version control -> SQLite run history is operator-local state, not a review artifact.
- 2026-04-16: treat this plan as complete once the live Linux run, publication handoff docs, and repo-local verification all pass -> no separate follow-on operationalization plan is needed for the current contract.

## Validation and acceptance

- Milestone 1 is accepted when the contract files and sample data describe the same four-bucket digest shape.
- Milestone 2 is accepted when a fresh Python 3.12 environment can install the repo with `uv`, discover the Typer CLI, run Ruff, and pass repo-local pytest checks.
- Milestone 3 is accepted when maintainers have approved a source inventory covering all four buckets, and each approved source has documented rationale, transport, and failure handling.
- Milestone 4 is accepted when deterministic collection, failure visibility, and SQLite-backed local state are covered by repo-local verification without replacing frozen JSON artifacts.
- Milestone 5 is accepted when the dedicated Linux Codex machine can run one documented daily command for a date and produce both `digest.json` and `digest.md`, and the shipped `systemd` units verify cleanly.
- Milestone 6 is accepted when the repo-local docs, CI, and handoff checklist are internally consistent and a maintainer can connect and publish the repository to `https://github.com/xiongxianfei/daily-engineering-security-insight` without missing operational steps.

## Validation notes

- `python -m json.tool schemas\daily_insight.schema.json | Out-Null` -> passed
- `python collectors\collect_sources.py --dry-run --config configs\sources.example.json` -> passed; placeholder example feeds were skipped as intended and dry-run completed
- `python scripts\render_digest.py examples\sample_digest.json C:\Users\xiongxianfei\.codex\memories\plan-verification-digest.md` -> passed
- `python -m pytest -q` -> failed during collection with `ModuleNotFoundError: No module named 'jsonschema'`
- `python scripts\render_digest.py examples\sample_digest.json outputs\plan-verification\digest.md` -> failed with `PermissionError: [WinError 5] Access is denied`
- `~/.local/bin/uv lock` -> passed
- `~/.local/bin/uv sync --dev` -> failed in repo-local `.venv` with `Operation not permitted (os error 1)` while installing the project wheel
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv sync --dev` -> passed
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run python -m pytest -q tests/test_cli.py tests/test_config.py tests/test_storage.py tests/test_schema.py` -> passed
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight --help` -> passed
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run ruff check .` -> passed
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run python -m json.tool schemas/daily_insight.schema.json > /dev/null` -> passed
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight collect --dry-run --config configs/sources.example.json` -> passed
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight render examples/sample_digest.json /tmp/digest.md` -> passed
- `PATH=$HOME/.local/bin:$PATH UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv bash scripts/ci.sh` -> passed
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run python -m pytest -q tests/test_config.py` -> passed
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run python -m json.tool configs/sources.example.json > /dev/null` -> passed
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight collect --dry-run --date 2026-04-15 --config configs/sources.example.json` -> passed
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run python -m pytest -q tests/test_collect.py` -> passed
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run python -m pytest -q tests/test_cli.py` -> passed
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run pytest -q` -> passed
- `systemd-analyze verify ops/systemd/daily-insight.service ops/systemd/daily-insight.timer` -> passed with environment-owned permission warnings about executable/world-writable files
- `PATH=$HOME/.local/bin:$PATH codex --version` -> passed (`codex-cli 0.121.0`)
- `PATH=$HOME/.local/bin:$PATH codex login status` -> passed (`Logged in using ChatGPT`)
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight collect --date 2026-04-15 --config configs/sources.local.json --out-dir inputs/2026-04-15 --state-db state/daily_insight.db` -> passed; collected 25 items, with `openai-news` failing as a visible warning
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight run --date 2026-04-15 --config configs/sources.local.json --state-db state/daily_insight.db` -> passed; produced `outputs/2026-04-15/digest.json` and `outputs/2026-04-15/digest.md`
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run python -m json.tool outputs/2026-04-15/digest.json > /dev/null` -> passed

## Idempotence and recovery

- Keep this file as the durable record of the completed initiative; start a new plan file if later work changes the behavior materially.
- During implementation, keep date-scoped inputs and outputs isolated under `inputs/YYYY-MM-DD/` and `outputs/YYYY-MM-DD/` so failed runs can be retried without mixing dates.
- Keep local operational state under a dedicated SQLite path such as `state/daily_insight.db`; back it up before any schema migration and prefer additive migrations over destructive rewrites.
- Daily-run implementation should write to temporary files and atomically promote them into `inputs/YYYY-MM-DD/` and `outputs/YYYY-MM-DD/` so a failed run does not leave partially trusted artifacts behind.
- If local verification fails after dependency, path, or permissions changes, rerun the minimum checks in this order: `uv sync --dev`, Ruff, schema parse, collector dry-run, renderer, pytest.
- If an approved source becomes unavailable or too noisy, keep its failure visible in `source_summary`, update `docs/source-inventory.md`, and avoid silently swapping in a lower-signal replacement without review.
- If the machine cannot write repo-local outputs, test a known writable staging path first to separate script logic problems from filesystem permissions before changing code.
- If the `systemd` timer misfires or the machine enters a bad operational state, disable it with `systemctl disable --now daily-insight.timer`, resolve the underlying issue, and re-enable only after one manual date-scoped run succeeds.
- If SQLite records become inconsistent with on-disk artifacts, preserve the date-scoped JSON files as the source of truth, inspect the state database separately, and repair or rebuild operational metadata without rewriting the frozen digest inputs.

## Outcomes and retrospective

- Completed on 2026-04-16.
- Final operator command surface is `uv run daily-insight` with `collect`, `render`, and `run` subcommands; `scripts/run_daily.sh` remains a thin Linux wrapper for `systemd`.
- The approved live-source inventory is documented in `docs/source-inventory.md`, while the versioned example config stays placeholder-safe and the live `configs/sources.local.json` stays operator-managed.
- Linux machine-specific gotchas are now explicit: this workspace needs `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv` for local verification, sample `systemd` units verify with environmental permission warnings, and non-Git workspaces require `--skip-git-repo-check` for Codex execution.

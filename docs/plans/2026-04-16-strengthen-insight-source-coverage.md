# Strengthen insight source coverage

- Status: completed
- Owner: maintainer
- Start date: 2026-04-16
- Last updated: 2026-04-16
- Related issue or PR: n/a
- Supersedes: none

## Goal

Make the source layer sufficient, reviewable, and operational enough that the daily digest has trustworthy coverage across all four buckets, with degraded coverage surfaced explicitly when the source program is thin, broken, or drifting from the approved inventory.

## Why now

The digest quality boundary is the source inventory. As of 2026-04-16, the current source set is not enough:

- `docs/source-inventory.md` approves six sources, but the live operator config wires only four.
- `github-changelog` is approved in docs but absent from `configs/sources.example.json` and `configs/sources.local.json`.
- `cisa-kev-catalog` is approved in docs, but the typed config and collectors only support `rss`, so that source cannot be operational as written.
- `openai-news` returned `HTTP Error 403: Forbidden` during live runs on April 16, 2026.
- `inputs/2026-04-16/items.jsonl` contained 25 collected items from only three working sources.
- `outputs/2026-04-16/digest.json` reported `security-for-ai` bucket count `0`, which means the pipeline can succeed operationally while still being coverage-thin in one of the four required buckets.

Without a clearer source-sufficiency contract and a single authoritative inventory, the project risks producing polished digests from an underpowered or drifting source base.

## Context and orientation

- The repository now runs on Python 3.12 + `uv` with Typer, Pydantic, SQLite, Ruff, pytest, and Linux `systemd`.
- The closed operationalization plan established deterministic collection, an approved source inventory document, and live daily generation.
- The closed unattended-synthesis plan hardened `run` vs `synthesize` lifecycle handling, but it deliberately did not solve whether the approved sources are enough.
- `docs/source-inventory.md` currently documents:
  - `python-insider`
  - `github-changelog`
  - `google-online-security-blog`
  - `cisa-kev-catalog`
  - `google-threat-intelligence`
  - `openai-news`
- `configs/sources.example.json` and `configs/sources.local.json` currently configure only:
  - `python-insider`
  - `google-online-security-blog`
  - `google-threat-intelligence`
  - `openai-news`
- `daily_insight/models.py` limits `TransportName` to `rss`, and `daily_insight/collect.py` only implements `collect_rss(...)`.
- The current collector/runtime can therefore operate only a subset of the documented inventory.
- On April 16, 2026:
  - the frozen input contained items from `python-insider`, `google-online-security-blog`, and `google-threat-intelligence`
  - `openai-news` failed with HTTP 403
  - the digest ended with `security-for-ai` bucket count `0`
- The current system has multiple source-of-truth surfaces:
  - `docs/source-inventory.md`
  - `configs/sources.example.json`
  - `configs/sources.local.json`
  - typed config and collector support in code
  Drift between these surfaces is already visible and must not be allowed to persist.

## Scope

### In scope

- define what counts as an adequate source program for this repository
- define whether sufficiency is measured from collected source ownership, final synthesized categorization, or both
- reconcile the approved source inventory with the live config and collector capabilities
- create one authoritative, machine-readable source manifest and a consistency check against docs/config/runtime support
- decide which approved sources are primary, backup, deferred, or no longer sufficient
- implement missing collector/config support for the approved machine-readable sources that should count toward sufficiency
- define and implement freshness and delta handling for cumulative sources such as KEV if they remain in scope
- add operator-visible source health and degraded-coverage signaling
- validate the source program over representative recent dates on the dedicated machine

### Out of scope

- changing digest ranking or narrative style beyond what is needed to reflect source adequacy
- replacing Codex CLI as the synthesis backend
- adding delivery channels such as email or Slack
- treating ad hoc live browsing as a normal substitute for approved deterministic sources
- broad schema refactors unrelated to source coverage, source metadata, source health, or degraded-coverage signaling

## Constraints

- Preserve deterministic collection as the first stage and keep the frozen input as the synthesis boundary.
- Keep the four primary buckets distinct:
  - software engineering
  - security
  - AI for Security
  - Security for AI
- Prefer official, primary, or otherwise reviewable high-signal sources over generic news feeds.
- Do not count manual-only, unimplemented, or chronically failing sources as sufficient coverage.
- Source sufficiency must be judged from collected source ownership and source health first; model re-bucketing cannot upgrade an under-covered bucket into a healthy one.
- A bucket with zero collected items cannot count as healthy unless the approved contract explicitly allows it and the degraded state is surfaced.
- Cumulative sources such as KEV do not count as sufficient until they have explicit freshness and delta rules that prevent backlog noise from masquerading as daily signal.
- Keep `configs/sources.example.json` placeholder-safe for dry runs.
- Keep real URLs only in operator-managed local config until they are approved in the human-reviewed inventory and authoritative manifest.
- Preserve historical `inputs/YYYY-MM-DD/` and `outputs/YYYY-MM-DD/` artifacts during source-program changes.
- Keep milestones small enough for one reviewable PR each.
- Follow `plan -> spec -> test-spec -> implement -> verify -> docs -> review` for behavior changes.

## Done when

- a dedicated source-sufficiency spec and test spec define:
  - how sufficiency is measured
  - minimum acceptable coverage per bucket
  - what counts as a primary source
  - what counts as a backup source
  - how manual-only, failing, thin, and zero-item days are classified
  - how cumulative sources such as KEV are turned into daily signal
- the repository has one authoritative, machine-readable source manifest, and the human inventory, example config, local-config guidance, typed config model, and collector support are linted or otherwise checked against it
- every bucket has at least one operational machine-readable primary source that counts toward sufficiency, plus either:
  - a reviewed backup source
  - or an explicit approved rationale for why no backup exists yet
- exploited-vulnerability coverage is operational if it remains part of the approved inventory, rather than documented but uncollectable
- broken or non-viable sources such as the April 16, 2026 `openai-news` 403 are either fixed, replaced, downgraded, or removed from sufficiency claims
- the CLI, state, and rendered output can distinguish:
  - healthy coverage
  - degraded coverage from source failure
  - degraded coverage from sparse but expected days
  - degraded coverage from a bucket lacking an adequate approved source
- dedicated-machine validation covers at least:
  - `2026-04-15`
  - `2026-04-16`
  - one additional explicit validation date chosen during Milestone 2 and recorded in this plan
- the dedicated-machine validation set includes at least one degraded-source or thin-coverage case

## Milestones

1. Define the source sufficiency contract [complete]
   - Files/components: new `specs/source-sufficiency.md`, new `specs/source-sufficiency.test.md`, `docs/source-inventory.md`, `docs/workflows.md`
   - Dependencies: none
   - Risk: high; if “enough” stays implicit, implementation can add sources without actually improving coverage
   - Work:
     - define whether sufficiency is measured from collected source ownership, synthesized categorization, or both
     - define the minimum acceptable source coverage per bucket
     - define whether manual-only sources can ever count toward sufficiency
     - define whether single-source buckets are acceptable and under what conditions
     - define freshness rules for a source to count toward sufficiency
     - define what qualifies as a backup source operationally
     - define the difference between:
       - source failed
       - source returned zero fresh items
       - bucket has no adequate approved source
     - define how degraded coverage must surface in operator output, state, and digest output
     - define cumulative-source rules for KEV-style inventories before they count toward sufficiency
   - Validation commands:
     - none; maintainer review of the new spec and test spec is the acceptance step before implementation
   - Expected observable result: maintainers can review a precise contract for source adequacy before changing the inventory or collectors.

2. Establish the authoritative source manifest and live viability audit [complete]
   - Files/components: new machine-readable manifest such as `configs/source-manifest.json`, `docs/source-inventory.md`, possible audit artifact such as `docs/source-viability-audit.md`, `configs/sources.example.json`
   - Dependencies: Milestone 1
   - Risk: high; today’s inventory and runtime drift apart, which creates false confidence
   - Work:
     - create one authoritative, machine-readable manifest for approved sources and their metadata
     - define manifest fields such as:
       - source name
       - bucket
       - primary / backup / deferred / removed status
       - transport
       - required / optional
       - failure policy
       - freshness mode
       - live probe result
       - implemented status
       - last review date
     - run a live viability review of all currently approved and candidate sources
     - decide the disposition of `github-changelog`, `cisa-kev-catalog`, and `openai-news`
     - select and document replacements or backups for thin buckets, especially `security-for-ai`
     - choose and record the third dedicated-machine validation date for Milestone 6
   - Validation commands:
     - `uv run daily-insight collect --dry-run --config configs/sources.example.json`
     - `uv run python - <<'PY' ... probe or summarize manifest source viability decisions ... PY`
   - Expected observable result: the repository has one reviewed manifest and one viability audit that describe the same approved source program.

3. Align inventory, config, and consistency checks to the manifest [complete]
   - Files/components: `configs/source-manifest.json`, `configs/sources.example.json`, local-config guidance in `README.md` or `docs/codex-machine-setup.md`, `docs/source-inventory.md`, new tests such as `tests/test_source_manifest.py`
   - Dependencies: Milestone 2
   - Risk: medium; even a good audit will rot if the repo does not enforce consistency afterward
   - Work:
     - align the placeholder-safe example config with the authoritative manifest
     - define how local operator config is derived from or compared against the manifest
     - add a repo-local consistency check so docs, manifest, example config, and supported transports cannot drift silently
     - ensure deferred or removed sources are not still implied to be sufficient
   - Validation commands:
     - `uv run pytest -q tests/test_collect.py tests/test_source_manifest.py`
     - `uv run daily-insight collect --dry-run --config configs/sources.example.json`
   - Expected observable result: drift between inventory, config, and supported runtime assumptions becomes detectable in CI or local verification.

4. Implement collector and freshness support for the approved inventory [complete]
   - Files/components: `daily_insight/models.py`, `daily_insight/config.py`, `daily_insight/collect.py`, possible new collector modules under `daily_insight/`, `tests/test_collect.py`, new config tests
   - Dependencies: Milestone 3
   - Risk: high; transport additions, source-specific normalization, and cumulative-source logic can create flaky collection or weak metadata if handled casually
   - Work:
     - add any approved transport or source-specific collector support beyond the current RSS-only implementation
     - implement the chosen machine-readable exploited-vulnerability source if that coverage remains required
     - implement freshness and delta handling for cumulative sources that remain approved
     - wire approved backup or replacement sources into the typed config model
     - preserve deterministic normalization, source naming, and bucket ownership
     - keep the dry-run path placeholder-safe
   - Validation commands:
     - `uv run pytest -q tests/test_collect.py tests/test_config.py tests/test_source_manifest.py`
     - `uv run ruff check .`
     - `uv run daily-insight collect --dry-run --config configs/sources.example.json`
   - Expected observable result: the collector/runtime can actually operate the approved inventory instead of documenting sources it cannot run.

5. Add source health and sufficiency visibility to outputs and state [complete]
   - Files/components: `daily_insight/storage.py`, `daily_insight/cli.py`, `schemas/daily_insight.schema.json`, `examples/sample_digest.json`, `specs/daily-digest.md`, rendering or digest-path code, tests, `docs/workflows.md`
   - Dependencies: Milestone 4
   - Risk: medium; the source program can still be misunderstood if healthy and degraded coverage look the same to operators
   - Work:
     - record enough source-health state to distinguish chronic failure from sparse days
     - surface degraded coverage explicitly in CLI output, state inspection, and `source_summary`
     - decide whether insufficient source coverage should warn, fail, or mark the run degraded by bucket
     - ensure the digest contract does not silently claim balanced coverage when the source base is thin
     - update schema, examples, and digest spec if the output contract changes
   - Validation commands:
     - `uv run pytest -q`
     - `uv run python -m json.tool schemas/daily_insight.schema.json > /dev/null`
     - `uv run daily-insight render examples/sample_digest.json /tmp/digest.md`
     - `uv run python - <<'PY' ... inspect SQLite source-health and sufficiency rows ... PY`
   - Expected observable result: operators can tell when a daily digest is source-healthy vs merely successful.

6. Validate the source program on the dedicated machine and establish review cadence [complete]
   - Files/components: live operator config, `inputs/`, `outputs/`, `state/daily_insight.db`, `docs/source-inventory.md`, `docs/codex-machine-setup.md`
   - Dependencies: Milestone 5, live source access
   - Risk: medium; one successful day is not enough evidence that the source program is sufficient over time
   - Work:
     - run the final source program across:
       - `2026-04-15`
       - `2026-04-16`
       - the explicit third validation date chosen in Milestone 2
     - ensure at least one validation date represents a degraded-source or thin-coverage case
     - inspect bucket coverage, source failures, and degraded-coverage signaling
     - confirm that thin buckets reflect approved policy rather than silent collector failure
     - document the human review cadence for source approval, source retirement, and chronic failure handling
   - Validation commands:
     - `uv run daily-insight collect --date YYYY-MM-DD --config configs/sources.local.json --state-db state/daily_insight.db`
     - `uv run daily-insight run --date YYYY-MM-DD --config configs/sources.local.json --state-db state/daily_insight.db`
     - `uv run python - <<'PY' ... summarize bucket/source coverage over the validation dates ... PY`
   - Expected observable result: maintainers have evidence that the source program is adequate over multiple dates, not just on a single successful run.

## Progress

- 2026-04-16: created this plan because the source layer is now the main quality risk after the operationalization and unattended-synthesis work closed.
- 2026-04-16: confirmed that the approved inventory, live config, and collector implementation currently drift apart.
- 2026-04-16: captured the April 16, 2026 evidence showing that the digest can succeed operationally with only three working sources and zero collected `security-for-ai` items.
- 2026-04-16: revised the plan after plan review to add an authoritative manifest, an explicit live viability audit, KEV freshness/delta handling, schema/example touchpoints, and tighter multi-date validation.
- 2026-04-16: completed the Milestone 1 spec slice by adding `specs/source-sufficiency.md`, `specs/source-sufficiency.test.md`, and cross-references in `docs/workflows.md` and `docs/source-inventory.md`.
- 2026-04-16: completed the Milestone 2 inventory-review slice by adding `configs/source-manifest.json`, `docs/source-viability-audit.md`, `tests/test_source_manifest.py`, and the corresponding inventory updates.
- 2026-04-16: completed the Milestone 3 consistency slice by aligning `configs/sources.example.json` to the manifest-approved runtime-supported RSS sources, adding drift checks in `tests/test_source_manifest.py`, and documenting how operator-managed local config must stay aligned to the manifest.
- 2026-04-16: completed the Milestone 4 collector slice by adding JSON transport support, dateAdded-scoped KEV collection, a browser-like fetch user-agent for RSS/JSON sources, and the corresponding manifest/config/inventory updates so all seven approved sources are runtime-supported.
- 2026-04-16: completed the Milestone 5 observability slice by writing deterministic `source_summary.json` sidecars, persisting per-bucket `bucket_health` rows in SQLite, adding the `daily-insight source-health` inspection command, and extending the digest schema/example/renderer with `bucket_health` and `coverage_notes`.
- 2026-04-16: completed the Milestone 6 dedicated-machine validation slice by validating the final source program across `2026-04-10`, `2026-04-15`, and `2026-04-16`, confirming explicit degraded-sparse-day cases, and recording the ongoing monthly/chronic-failure review cadence in `docs/source-inventory.md` and `docs/codex-machine-setup.md`.

## Decision log

- 2026-04-16: treat the current source program as not yet sufficient -> approved inventory drift, an uncollectable KEV entry, and a zero-item `security-for-ai` day are too material to ignore.
- 2026-04-16: plan this as a new initiative instead of reopening the closed operationalization or unattended-synthesis plans -> the new problem is source adequacy, not runtime reliability.
- 2026-04-16: manual-only or chronically failing sources do not count toward sufficiency -> otherwise the inventory can look stronger on paper than it is in production.
- 2026-04-16: require multi-date dedicated-machine validation before calling the source program “enough” -> source adequacy is temporal and cannot be judged from one good day.
- 2026-04-16: add a machine-readable manifest and consistency checks -> a human inventory document alone is not enough to prevent future drift.
- 2026-04-16: treat KEV-style cumulative sources as a separate freshness problem, not just another transport -> without delta rules they can swamp daily signal and create false adequacy.
- 2026-04-16: judge source sufficiency from collected source ownership and source health before synthesis -> final digest re-bucketing cannot repair under-covered input.
- 2026-04-16: classify each bucket per date as `healthy`, `degraded-source-failure`, `degraded-sparse-day`, or `degraded-no-approved-source` -> operators need explicit degraded-state names before implementation.
- 2026-04-16: keep `openai-news` approved as the desired `security-for-ai` primary, but mark it non-counting until the runtime fixes its default `urllib`-style `403` access pattern.
- 2026-04-16: switch the approved KEV source to the CISA JSON feed and keep it non-counting until JSON collector support and delta-by-`dateAdded` handling exist.
- 2026-04-16: approve `deepmind-blog` as the current `security-for-ai` backup and record `2026-04-10` as the third dedicated-machine validation date.
- 2026-04-16: keep `configs/sources.example.json` and operator-managed `configs/sources.local.json` limited to manifest-approved runtime-supported entries; `cisa-kev-catalog` stays out of config until Milestone 4 transport support exists.
- 2026-04-16: implement `json` transport support specifically for `cisa-kev-catalog` and treat `dateAdded` as the approved daily-delta freshness rule, which avoids replaying the full KEV backlog on every run.
- 2026-04-16: use a browser-like `User-Agent` for approved HTTP fetches so `openai-news` becomes a counted runtime-supported source again without introducing source-specific auth or manual fallback.
- 2026-04-16: return `cisa-kev-catalog` to the example and operator-managed config guidance now that the runtime can collect the approved JSON endpoint deterministically.
- 2026-04-16: keep source-health status deterministic by generating `inputs/YYYY-MM-DD/source_summary.json` during collection and re-applying it after Codex synthesis instead of trusting the model to preserve coverage state exactly.
- 2026-04-16: surface insufficient coverage as explicit degraded bucket statuses in `source_summary` and SQLite state, but do not fail the run solely because one bucket is degraded; operational success and source health remain distinct concepts.
- 2026-04-16: prefer Python-based SQLite inspection in validation commands because the dedicated machine may not have the `sqlite3` shell installed.
- 2026-04-16: enforce `published-date` freshness for RSS sources during date-scoped validation instead of treating any feed item as fresh for any requested day; otherwise multi-date source-sufficiency checks can overstate coverage.

## Surprises and discoveries

- 2026-04-16: before Milestone 4, the approved inventory already named `github-changelog` and `cisa-kev-catalog`, but only the RSS subset was actually runtime-supported.
- 2026-04-16: KEV did not need a stateful historical diff to become daily-scoped; the feed’s `dateAdded` field was sufficient to implement deterministic per-date deltas.
- 2026-04-16: the April 16, 2026 digest succeeded end-to-end even though `openai-news` failed and the `security-for-ai` bucket remained empty.
- 2026-04-16: the current process can visually appear balanced after synthesis even when the underlying collected source ownership is thin, so sufficiency must be defined before implementation.
- 2026-04-16: the source-sufficiency contract needs two layers, not one: long-term inventory sufficiency in the manifest and date-scoped run coverage from actual collection.
- 2026-04-16: `openai-news` is not dead; the feed returns `200 text/xml` with a browser-like user-agent even though the current runtime still gets `403`, which means the gap is a runtime behavior problem rather than a missing source.
- 2026-04-16: `deepmind.google/blog/rss.xml` is a live official feed and is a better current backup candidate than the previously guessed `discover` endpoint, which returned `404`.
- 2026-04-16: the placeholder-safe example config can already exercise approved optional backup feeds during dry-run validation, so config alignment does not need to wait for live operator rollout.
- 2026-04-16: a single browser-like fetch path was enough to unblock `openai-news` and future-proof JSON transport fetches at the same time; the runtime did not need a separate per-source HTTP client.
- 2026-04-16: the safest way to keep `source_summary` deterministic was to treat it like collection metadata, not synthesis output; the sidecar-plus-reapply approach keeps schema validation while avoiding model drift.
- 2026-04-16: dry-run validation is enough to exercise the new CLI and SQLite bucket-health surfaces because the collector now computes degraded-sparse-day coverage even when every example source intentionally yields zero fresh items.
- 2026-04-16: live multi-date validation exposed a contract bug the unit tests had not caught yet: RSS collection was not actually date-scoped until the runtime began filtering feed entries by the manifest-declared `published-date` freshness mode.
- 2026-04-16: the nested `codex exec` step can take several minutes even on small frozen inputs, but it still completed successfully for the dedicated-machine validation dates once the frozen-input paths and deterministic source-summary handling were correct.

## Validation and acceptance

- Milestone 1 is accepted when the source-sufficiency spec and test spec define explicit adequacy, failure, freshness, and degraded-coverage rules.
- Milestone 2 is accepted when the repository has one reviewed manifest and one explicit live viability audit with a recorded disposition for every currently approved source.
- Milestone 3 is accepted when the human inventory, manifest, and supported config can no longer drift silently.
- Milestone 4 is accepted when the collector/runtime can operate the approved source inventory that is supposed to count toward sufficiency.
- Milestone 5 is accepted when operators can distinguish source-health degradation from healthy but sparse days, and any output-contract change is reflected in schema/spec/example updates.
- Milestone 6 is accepted when dedicated-machine evidence across the three named dates supports the claim that the source program is adequate or documents the remaining approved gap explicitly.

## Validation notes

- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run python - <<'PY' ... summarize inputs/2026-04-16/items.jsonl by bucket and source ... PY` -> showed 25 collected items from only `python-insider`, `google-online-security-blog`, and `google-threat-intelligence`, with no collected `security-for-ai` items.
- `sed -n '1,260p' outputs/2026-04-16/digest.json` -> confirmed `source_summary.bucket_counts.security-for-ai == 0` and recorded the `openai-news` HTTP 403 failure note.
- Milestone 1 is spec-and-doc work only; no new tests or verification commands were run beyond reading the updated plan/spec/inventory/workflow files and the previously captured inventory/artifact inspection above.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run pytest -q tests/test_source_manifest.py` -> passed (`3 passed`) after adding the manifest and viability audit fixtures that capture the reviewed source set and key disposition decisions.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight collect --dry-run --config configs/sources.example.json` -> passed during Milestone 2; the placeholder-safe example config then normalized `0` items while validating the then-current six configured RSS sources.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run python - <<'PY' ... summarize configs/source-manifest.json ... PY` -> confirmed the Milestone 2 reviewed seven-source manifest, including `cisa-kev-catalog` as `not-implemented`, `openai-news` as `needs-runtime-fix`, and `deepmind-blog` as the approved `security-for-ai` backup.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run pytest -q tests/test_config.py tests/test_source_manifest.py` -> passed (`10 passed`) after aligning `configs/sources.example.json` to the manifest-approved runtime-supported RSS sources and documenting manifest-derived local-config rules.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run pytest -q tests/test_collect.py tests/test_source_manifest.py` -> passed (`10 passed`) during Milestone 3; the drift checks and collector tests agreed on the then-current RSS-only runtime boundary.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run pytest -q tests/test_collect.py tests/test_config.py tests/test_source_manifest.py` -> passed (`18 passed`) after adding `json` transport support, KEV date-delta collection, and the shared browser-like fetch headers.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run ruff check .` -> passed after the Milestone 4 collector/config/doc updates.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight collect --dry-run --config configs/sources.example.json` -> passed after Milestone 4; the placeholder-safe example config now validates all seven approved runtime-supported sources, including `cisa-kev-catalog`.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run pytest -q tests/test_cli.py tests/test_collect.py tests/test_config.py tests/test_storage.py tests/test_render.py tests/test_source_health.py tests/test_schema.py tests/test_source_manifest.py` -> passed (`27 passed`) after adding deterministic source-summary sidecars, bucket-health persistence, the new `source-health` CLI command, and the schema/renderer updates.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run ruff check .` -> passed after the Milestone 5 state/schema/doc updates.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight collect --dry-run --config configs/sources.example.json` -> passed after Milestone 5; dry-run output now prints explicit per-bucket source-health statuses even when zero fresh items are expected.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run pytest -q` -> passed (`27 passed`) after the Milestone 5 contract and state changes.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run python -m json.tool schemas/daily_insight.schema.json > /dev/null` -> passed after adding `bucket_health` and `coverage_notes` to the digest schema.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight render examples/sample_digest.json /tmp/milestone5-digest.md` -> passed after extending the renderer to print bucket-health statuses and coverage notes.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight source-health --date 2026-04-16 --state-db /tmp/milestone5-state.db` -> passed after a dry-run collection and printed the persisted per-bucket degraded-sparse-day statuses from SQLite.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run python - <<'PY' ... StateStore(Path('/tmp/milestone5-state.db')).bucket_health_for_run(...) ... PY` -> passed and confirmed the `bucket_health` rows persisted in SQLite without depending on an external `sqlite3` shell.
- `PATH=$HOME/.local/bin:$PATH codex login status` -> passed on the dedicated machine (`Logged in using ChatGPT`) before the Milestone 6 live validation runs.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run pytest -q tests/test_collect.py` -> passed (`8 passed`) after adding RSS date-scoping coverage so multi-date validation reflects the manifest freshness contract.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run pytest -q tests/test_cli.py tests/test_collect.py` -> passed (`13 passed`) after updating the run prompt to use the actual frozen-input path when the validation root lives outside the default `inputs/YYYY-MM-DD/` tree.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run ruff check daily_insight/cli.py daily_insight/collect.py tests/test_cli.py tests/test_collect.py` -> passed after the Milestone 6 date-scoping and prompt-path fixes.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight collect --date 2026-04-10 --config configs/sources.local.json --state-db state/daily_insight.db --out-dir tmp_validation/source-coverage/2026-04-10/input` -> passed; collected `6` items and recorded `software-engineering` / `ai-for-security` as `degraded-sparse-day` while `security` and `security-for-ai` remained healthy.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight collect --date 2026-04-15 --config configs/sources.local.json --state-db state/daily_insight.db --out-dir tmp_validation/source-coverage/2026-04-15/input` -> passed; collected `5` items and recorded `security` as `degraded-sparse-day` with the other three buckets healthy.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight collect --date 2026-04-16 --config configs/sources.local.json --state-db state/daily_insight.db --out-dir tmp_validation/source-coverage/2026-04-16/input` -> passed; collected `2` items and recorded `software-engineering` plus `security` as `degraded-sparse-day`.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight source-health --date 2026-04-10 --state-db state/daily_insight.db` -> passed and printed the persisted sparse-day vs healthy bucket distinctions for the third validation date.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight source-health --date 2026-04-15 --state-db state/daily_insight.db` -> passed and confirmed the dedicated-machine validation caught a thin `security` day rather than a silent collector failure.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight source-health --date 2026-04-16 --state-db state/daily_insight.db` -> passed and confirmed the dedicated-machine validation caught thin `software-engineering` and `security` coverage on the current date.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight run --date 2026-04-15 --config configs/sources.local.json --state-db state/daily_insight.db --in-dir tmp_validation/source-coverage/2026-04-15/input --out-dir tmp_validation/source-coverage/2026-04-15/output` -> passed and wrote `tmp_validation/source-coverage/2026-04-15/output/digest.json` plus `digest.md`.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight run --date 2026-04-16 --config configs/sources.local.json --state-db state/daily_insight.db --in-dir tmp_validation/source-coverage/2026-04-16/input --out-dir tmp_validation/source-coverage/2026-04-16/output` -> passed and wrote `tmp_validation/source-coverage/2026-04-16/output/digest.json` plus `digest.md`.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run python -m json.tool tmp_validation/source-coverage/2026-04-15/output/digest.json > /dev/null` and `.../2026-04-16/output/digest.json > /dev/null` -> both passed after the Milestone 6 end-to-end runs.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run python - <<'PY' ... compare tmp_validation/source-coverage/*/input/source_summary.json to output/digest.json['source_summary'] ... PY` -> passed and reported `summary_match=True` for `2026-04-10`, `2026-04-15`, and `2026-04-16`, confirming deterministic source-summary preservation in final outputs.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run python - <<'PY' ... summarize latest_run_for_date(...) and bucket health for 2026-04-10/15/16 ... PY` -> passed and confirmed the latest dedicated-machine validation runs are `completed` with explicit per-bucket coverage states in SQLite.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run pytest -q` -> passed (`28 passed`) after the Milestone 6 RSS freshness fix and prompt-path update.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run ruff check .` -> passed after the Milestone 6 final validation sweep.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run python -m json.tool schemas/daily_insight.schema.json > /dev/null` -> passed during the Milestone 6 final validation sweep.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight collect --dry-run --config configs/sources.example.json` -> passed during the Milestone 6 final validation sweep and still reported explicit degraded-sparse-day statuses for the placeholder-safe example config.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight render examples/sample_digest.json /tmp/source-coverage-sample.md` -> passed during the Milestone 6 final validation sweep.

## Idempotence and recovery

- Do not rewrite historical `inputs/YYYY-MM-DD/` or `outputs/YYYY-MM-DD/` artifacts while auditing or changing the source program.
- Keep `configs/sources.example.json` placeholder-safe even if the live approved inventory grows.
- Add or replace sources in a way that preserves source names and bucket ownership deliberately; do not silently rename live sources without a migration note.
- If a new source proves noisy, flaky, or low-signal, downgrade or remove it through the approved inventory and manifest rather than leaving it enabled indefinitely.
- If a source remains approved but unimplemented, document it as deferred and do not count it toward sufficiency claims.
- If a newly added collector or transport proves unstable, disable the source in local operator config, mark it degraded or deferred in the manifest, and preserve the prior healthy inventory until the replacement is reviewed.
- If source-health or sufficiency persistence changes require a SQLite migration, back up `state/daily_insight.db`, keep the migration additive, and verify older rows remain readable before relying on the new state model.

## Outcomes and retrospective

- Completed on 2026-04-16.
- The source program is now reviewable and operational across all four buckets: the manifest, inventory, example config, runtime transports, and dedicated-machine local config are aligned, degraded coverage is explicit, and KEV/OpenAI source support is implemented.
- Dedicated-machine validation across `2026-04-10`, `2026-04-15`, and `2026-04-16` showed the expected mix of healthy and `degraded-sparse-day` buckets instead of falsely balanced coverage, which means the final source-sufficiency contract is observable over time rather than only on a single good day.
- The most important late discovery was that RSS freshness must be enforced by date during collection. Without that fix, the project could have claimed healthy multi-date coverage from stale feed items.

# Expand Source Catalog To Thirty Explained Entries

- Status: completed
- Owner: maintainer
- Start date: 2026-04-16
- Last updated: 2026-04-16
- Related issue or PR: n/a
- Supersedes: none

## Goal

Give maintainers and readers a much broader, explicit view of where the project can source insight from by documenting and reviewing at least 30 source entries, while preserving the repository's current deterministic, approved-runtime source program.

## Why now

The current approved runtime source program is intentionally small and disciplined: seven reviewed machine-readable sources spread across four primary buckets. That is enough to run the digest, but it is not enough to answer the broader question "what websites do we source from?" in a satisfying way. The user now wants the source layer explained at a larger scale, at least 30 items.

Blindly turning on 30 live feeds would be the wrong response. It would increase noise, add operational risk, and break the existing source-sufficiency discipline. The safer path is to separate:

- a reviewed source catalog with at least 30 explained entries
- the smaller approved runtime manifest that actually drives collection and sufficiency today

This keeps the repository honest about what it currently trusts in production while making the broader source universe inspectable and reviewable.

## Context and orientation

- The repository currently uses:
  - `configs/source-manifest.json` as the authoritative reviewed runtime manifest
  - `docs/source-inventory.md` as the human-reviewed explanation for the approved runtime sources
  - `configs/sources.example.json` as the placeholder-safe example config
  - `specs/source-sufficiency.md` as the contract for approved-source sufficiency and degraded coverage
- The current manifest contains seven approved runtime-supported sources:
  - two for `software-engineering`
  - two for `security`
  - one for `ai-for-security`
  - two for `security-for-ai`
- Recent work established:
  - deterministic source collection and per-bucket health
  - an authoritative manifest plus human inventory
  - browser publication of the final digest
- The missing piece is breadth and inspectability:
  - there is no reviewed source catalog that goes beyond the currently enabled seven
  - there is no clear contract for what counts as one source entry toward a broader catalog target such as 30
  - there is no dedicated user-facing way to inspect a larger source universe without reading the runtime manifest by hand

## Scope

### In scope

- define what "at least 30 items" means for the source layer
- introduce a reviewed source catalog that can hold at least 30 explained source entries
- keep a clear boundary between catalog entries and runtime-approved manifest entries
- document rationale, bucket ownership, transport, status, and review notes for each catalog entry
- add drift checks so the reviewed catalog, runtime manifest, and human docs cannot silently diverge
- improve source inspectability through documentation and, if justified by the spec, a lightweight CLI or rendered surface
- selectively promote additional high-signal sources into the runtime manifest where the audit supports it

### Out of scope

- enabling 30 live runtime sources immediately
- scraping arbitrary web pages or community posts just to hit the count target
- lowering the quality bar for approved runtime sources
- changing the digest synthesis contract beyond what source-catalog inspectability requires
- broad ranking or summarization changes unrelated to source breadth

## Constraints

- Keep the four primary buckets distinct:
  - software engineering
  - security
  - AI for Security
  - Security for AI
- Do not treat the 30-entry target as permission to enable low-signal or non-deterministic sources in the runtime manifest.
- Preserve `configs/source-manifest.json` as the authoritative runtime manifest unless a higher-priority spec explicitly replaces it.
- If a broader reviewed catalog is added, it must not contradict the runtime manifest about what currently counts toward sufficiency.
- Every counted catalog entry must have a stable name, bucket, transport, status, last review date, and explanation of expected signal.
- Prefer official, machine-readable, high-signal sources first; document rejected or deferred sources explicitly instead of silently dropping them.
- Keep `configs/sources.example.json` placeholder-safe and do not add real URLs there unless the current repository convention changes through an approved spec.
- Avoid creating a maintenance burden that requires manual review of dozens of low-value feeds every day.

## Done when

- the repository defines what counts as one source entry toward the "at least 30 items" target
- a reviewed catalog artifact contains at least 30 source entries with explanation fields
- the runtime manifest remains clearly distinguished from the broader reviewed catalog
- each bucket has a visible reviewed pool that is meaningfully larger than the current seven-source runtime set
- drift checks verify:
  - the runtime manifest is a valid subset of the broader reviewed catalog
  - required catalog fields are present
  - the catalog count stays at or above 30
- maintainers can inspect the broader source universe without reverse-engineering multiple files
- if new sources are promoted into runtime use, dedicated-machine validation proves the additions do not break date-scoped collection or source-health reporting

## Milestones

1. Define the source-catalog contract
   - Files/components: new `specs/source-catalog.md`, new `specs/source-catalog.test.md`, `specs/source-sufficiency.md`, `docs/workflows.md`
   - Dependencies: none
   - Risk: medium; if the repository does not define the boundary between a reviewed catalog and the runtime manifest, future source counts will be misleading
   - Work:
     - define what counts as one source entry toward the 30-item target
     - define the status model for catalog entries, such as:
       - runtime-approved
       - reviewed-candidate
       - deferred
       - rejected
     - define the minimum explanation fields for each catalog entry
     - define whether rejected or deferred entries count toward the 30-item target
     - define how the runtime manifest relates to the broader reviewed catalog
     - define whether the user-facing inspectability surface is docs-only or requires a CLI/browser artifact
   - Validation commands:
     - spec review against `specs/source-catalog.md`
     - test-spec review against `specs/source-catalog.test.md`
   - Expected observable result: a new contributor can tell exactly what "30 source items" means in this repository and how that differs from runtime-approved collection sources

2. Introduce the reviewed catalog and backfill current sources
   - Files/components: new catalog artifact such as `configs/source-catalog.json`, `docs/source-inventory.md`, possibly a new `docs/source-catalog.md`, tests for catalog structure and count
   - Dependencies: Milestone 1
   - Risk: medium; a larger catalog can drift immediately if the repo does not establish one source of truth and one human-readable companion
   - Work:
     - create the authoritative broader reviewed catalog
     - backfill the current seven approved runtime sources into the new catalog
     - add at least 23 additional reviewed source entries so the catalog reaches 30 or more
     - ensure each entry includes explanation, role/status, transport, and review metadata
     - update the human-readable inventory so a reader can browse the catalog sensibly instead of reading raw JSON only
   - Validation commands:
     - `uv run pytest -q tests/test_source_manifest.py`
     - `uv run python - <<'PY' ... verify catalog count >= 30 ... PY`
   - Expected observable result: the repository contains a reviewed and explainable catalog of at least 30 source entries, with the current runtime-approved seven represented accurately inside it

3. Run viability audit and choose promotions carefully
   - Files/components: `docs/source-viability-audit.md`, `configs/source-catalog.json`, `configs/source-manifest.json`, `docs/source-inventory.md`
   - Dependencies: Milestone 2
   - Risk: high; the catalog can become aspirational noise unless live viability, signal quality, and promotion criteria are explicit
   - Work:
     - probe the new candidate sources
     - record live results and review notes
     - separate high-signal viable candidates from deferred or rejected ones
     - decide which small subset, if any, should be promoted into the runtime manifest now
     - keep explicit no-backup rationales where a bucket still lacks a trustworthy addition
   - Validation commands:
     - `uv run daily-insight collect --dry-run --config configs/sources.example.json`
     - `uv run pytest -q tests/test_source_manifest.py tests/test_config.py`
   - Expected observable result: the catalog is not just longer; it clearly distinguishes viable candidates, deferred ideas, and approved runtime sources

4. Implement runtime support only for justified additions
   - Files/components: `daily_insight/collect.py`, typed models/config, `configs/source-manifest.json`, `configs/sources.example.json`, collector tests, source-health tests
   - Dependencies: Milestone 3
   - Risk: high; adding transports or feeds too quickly can degrade determinism and operator trust
   - Work:
     - implement only the additional sources that pass the audit and materially improve bucket sufficiency or day-to-day signal
     - keep new runtime additions reviewable in small slices
     - preserve date-scoped freshness and degraded-coverage rules for each addition
     - update source-health persistence and digest/source-summary surfaces only if required by the new runtime set
   - Validation commands:
     - `uv run pytest -q`
     - `uv run ruff check .`
     - `uv run daily-insight collect --dry-run --config configs/sources.example.json`
   - Expected observable result: selected new sources work in the deterministic collector without weakening the existing source contract

5. Add an inspectable source view for maintainers and readers
   - Files/components: docs and, if approved by Milestone 1, a CLI surface such as `daily-insight sources`
   - Dependencies: Milestone 2, Milestone 3
   - Risk: medium; without a focused inspection surface, the new breadth will remain hard to use in practice
   - Work:
     - document where to inspect the 30-entry source catalog
     - if the spec justifies it, add a small CLI summary command for catalog inspection by bucket/status
     - make the runtime-approved subset and broader reviewed catalog easy to distinguish
   - Validation commands:
     - `uv run daily-insight --help`
     - if a CLI command is added: `uv run daily-insight sources --help`
   - Expected observable result: a maintainer can answer "what sources do we use or consider?" without reading multiple implementation files manually

6. Validate the expanded program on the dedicated machine
   - Files/components: live operator config, state DB, date-scoped inputs/outputs, source-health views, docs
   - Dependencies: Milestone 4 where runtime additions land
   - Risk: medium; source breadth is not real until it survives date-scoped collection on the actual machine
   - Work:
     - validate the current runtime-approved set against at least three explicit dates
     - if new runtime sources were promoted, verify that they collect correctly and improve coverage where expected
     - confirm that degraded-source reporting stays truthful when newly cataloged sources remain deferred or rejected
   - Validation commands:
     - `uv run daily-insight collect --date YYYY-MM-DD --config configs/sources.local.json --state-db state/daily_insight.db`
     - `uv run daily-insight source-health --date YYYY-MM-DD --state-db state/daily_insight.db`
     - optional full-run validation if runtime promotions materially change coverage expectations
   - Expected observable result: the broader catalog is documented, the runtime subset is validated, and source breadth no longer depends on tribal knowledge

## Progress

- 2026-04-16: created this plan after the user asked to explain the project's source layer at at least 30 items instead of leaving the answer at the current seven approved runtime feeds.
- 2026-04-16: completed the Milestone 1 contract slice by adding `specs/source-catalog.md` and `specs/source-catalog.test.md`, and by updating `specs/source-sufficiency.md` and `docs/workflows.md` so the broader reviewed catalog is explicit and remains separate from the runtime-approved manifest.
- 2026-04-16: completed the Milestone 2 catalog slice by adding `configs/source-catalog.json` with 34 counted reviewed source entries, adding the human-readable companion `docs/source-catalog.md`, and clarifying in `docs/source-inventory.md` that the older inventory remains the runtime-approved subset rather than the broader catalog.
- 2026-04-16: completed the Milestone 3 audit slice by rewriting `docs/source-viability-audit.md` around the full 34-entry reviewed catalog, recording live probe outcomes by bucket, and making the "no immediate promotions into the runtime manifest" decision explicit along with a Milestone 4 shortlist.
- 2026-04-16: completed the Milestone 4 runtime slice by promoting `django-blog`, `cisa-advisories`, and `github-security-blog` into the runtime manifest/example config, aligning the broader catalog and runtime inventory around those ten approved sources, and keeping the remaining shortlist candidates out of runtime use.
- 2026-04-16: completed the Milestone 5 inspectability slice by adding the typed `daily-insight sources` CLI surface with bucket/status filters, documenting it in the repo entrypoints, and keeping the runtime-approved subset boundary explicit in both docs and command output.
- 2026-04-16: completed the Milestone 6 dedicated-machine validation slice by refreshing the local operator config to the approved ten-source set, validating `2026-04-10`, `2026-04-15`, and `2026-04-16` on the dedicated machine, and confirming that the expanded runtime program improves coverage on `2026-04-15` without distorting degraded-source reporting on the other dates.

## Decision log

- 2026-04-16: interpret "at least 30 items" as a requirement for a broader reviewed source catalog, not an instruction to immediately enable 30 live runtime feeds -> this preserves the repository's deterministic source discipline while still satisfying the user's request for broader source explanation.
- 2026-04-16: keep the runtime manifest separate from the broader reviewed catalog -> a reader must be able to distinguish "reviewed and explained" from "currently trusted in runtime sufficiency and collection."
- 2026-04-16: count `runtime-approved`, `reviewed-candidate`, and `deferred` entries toward the 30-item catalog target, but not `rejected` entries -> deferred entries still represent real reviewed sources, while rejected entries should remain visible without becoming padding.
- 2026-04-16: use a new `docs/source-catalog.md` as the human-readable companion and keep `docs/source-inventory.md` focused on the runtime-approved subset -> this preserves the clarity of the existing runtime allowlist while adding a separate place to browse the broader reviewed universe.
- 2026-04-16: make no immediate runtime promotions in Milestone 3 -> several additional sources are technically live, but promotion without filtering or transport/policy work would add noise faster than value.
- 2026-04-16: promote only `django-blog`, `cisa-advisories`, and `github-security-blog` in Milestone 4 -> they are official, machine-readable, already supported by the current collector, and materially broaden software/security coverage without new transport or policy work.
- 2026-04-16: do not promote `cloudflare-security-blog`, `google-ai-blog`, or `huggingface-blog` yet -> they remain viable reviewed candidates, but the current program does not need the additional noise or filtering burden they would introduce.
- 2026-04-16: use a small CLI inspection surface for Milestone 5 instead of a browser or API view -> `daily-insight sources` is enough to answer "what sources do we use or consider?" without creating another publication surface.
- 2026-04-16: keep the operator-managed `configs/sources.local.json` aligned with the approved manifest for live validation -> Milestone 6 surfaced that the local config was still on the old seven-source set, so the dedicated-machine check refreshed it to the approved ten-source runtime program before closing the plan.

## Surprises and discoveries

- 2026-04-16: the repository already has a strong seven-source runtime program, but it lacks a second artifact for the wider candidate universe; that is the main structural blocker to explaining 30 items clearly.
- 2026-04-16: the recent source-sufficiency work is strong enough that broadening the catalog without separating runtime-approved vs reviewed-candidate status would create immediate ambiguity.
- 2026-04-16: the AI-for-security bucket still has fewer official feed-ready candidates than the software and security buckets, so the first broader catalog leans more heavily on deferred reviewed HTML/product sources there than in the other buckets.
- 2026-04-16: several software-engineering and security feeds are clearly live and machine-readable, but security-for-AI additions still look noisier and AI-for-security additions still skew toward HTML product pages instead of deterministic feeds.
- 2026-04-16: Milestone 4 confirmed the weakest expansion area is still `ai-for-security`; there is still no clean feed-ready source strong enough to promote alongside `google-threat-intelligence`.
- 2026-04-16: the broader catalog was already documented well enough for humans, so the real Milestone 5 gap was discoverability from the normal CLI path rather than another rendered surface.
- 2026-04-16: the dedicated machine's untracked `configs/sources.local.json` had not been refreshed after the Milestone 4 manifest change, so local operator validation needed one explicit config-alignment step before the ten-source program was truly live on the machine.

## Validation and acceptance

- The plan is acceptable only if it preserves the current runtime source-sufficiency model and does not quietly redefine the meaning of the existing seven-source manifest.
- The catalog target should be considered met only when at least 30 entries are documented with explanation and status, not when 30 URLs merely appear in an unreviewed list.
- If runtime promotions occur, they should land in small reviewable slices and pass the existing dry-run and source-health validation workflow.

## Validation notes

- `sed -n '1,260p' AGENTS.md` -> reviewed repository planning and source-contract instructions.
- `sed -n '1,260p' .codex/PLANS.md` -> reviewed required plan format.
- `sed -n '1,240p' docs/plan.md` -> confirmed there was no active plan before creating this one.
- `sed -n '1,260p' docs/workflows.md` -> reviewed the source policy and verification workflow.
- `sed -n '1,260p' specs/source-sufficiency.md` -> confirmed the current contract is about approved runtime sufficiency, not a broader reviewed catalog.
- `sed -n '1,260p' docs/source-inventory.md` and `sed -n '1,260p' configs/source-manifest.json` -> confirmed the current approved program contains seven runtime sources and no 30-entry explanatory catalog exists yet.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run pytest -q tests/test_source_catalog.py` -> failed first because `configs/source-catalog.json` and `docs/source-catalog.md` did not exist, then passed (`4 passed`) after the broader catalog and companion doc landed.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run pytest -q tests/test_source_manifest.py` -> passed (`6 passed`) after the broader catalog landed without breaking the existing runtime manifest expectations.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run python - <<'PY' ... counted source-catalog entries ... PY` -> returned `34`, confirming the broader reviewed catalog now exceeds the 30-entry target for Milestone 2.
- `python3 -u - <<'PY' ... urllib probe batches ... PY` -> probed the broader catalog candidates and recorded which feeds/pages returned live machine-readable responses versus deferred HTML or access-constrained surfaces.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run pytest -q tests/test_source_catalog.py` -> failed first because the refreshed viability audit did not yet make the promotion decision explicit, then passed (`5 passed`) after `docs/source-viability-audit.md` was rewritten around the full catalog.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run pytest -q tests/test_source_manifest.py tests/test_config.py` -> passed (`11 passed`) after restoring the expected legacy audit wording while keeping the broader Milestone 3 audit content.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight collect --dry-run --config configs/sources.example.json` -> passed, confirming that the broader catalog and audit work did not change the current runtime-approved dry-run collection path.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run pytest -q` -> initially failed because `cisa-advisories` had not yet been promoted in `configs/source-catalog.json`; passed (`48 passed`) after the broader catalog was aligned with the Milestone 4 manifest/inventory promotions and stray accidental runtime-approved statuses were corrected.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run ruff check .` -> initially failed on a single long assertion in `tests/test_config.py`; passed after the updated example-config expectation was wrapped cleanly.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight collect --dry-run --config configs/sources.example.json` -> passed with the ten-source example config, confirming the promoted runtime sources validate under the current deterministic collector without additional transport work.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run pytest -q tests/test_cli.py` -> failed first because the new `sources` command did not exist yet, then passed (`12 passed`) after the typed catalog loader and CLI inspection surface landed.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run pytest -q` -> passed (`50 passed`) after the `sources` command and its documentation/tests landed.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run ruff check .` -> initially failed on two long lines in `daily_insight/cli.py`, then passed after wrapping the new CLI output strings cleanly.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run python -m json.tool schemas/daily_insight.schema.json > /dev/null` -> passed, confirming the broader catalog/CLI work did not affect the digest schema.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight --help` -> passed and now lists `sources` in the command surface.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight sources --help` -> passed and exposed the bucket/status/catalog filters for source inspection.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight sources` -> passed and reported the full 34-entry reviewed catalog with `runtime-approved: 10`, `reviewed-candidate: 15`, `deferred: 9`, and the four-bucket distribution.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight collect --dry-run --config configs/sources.example.json` -> passed again after the CLI work, confirming the inspectability changes did not alter runtime collection behavior.
- `python3 - <<'PY' ... build /tmp/source-catalog-validation-dxo1eicn/sources.runtime10.json from manifest + example config ... PY` -> created a temporary real-URL ten-source validation config without mutating the operator-managed local config first.
- `PATH=$HOME/.local/bin:$PATH codex login status` -> returned `Logged in using ChatGPT`, confirming the dedicated machine remained authenticated for live validation work.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight collect --date 2026-04-10 --config /tmp/source-catalog-validation-dxo1eicn/sources.runtime10.json --state-db /tmp/source-catalog-validation-dxo1eicn/runtime10.db --out-dir /tmp/source-catalog-validation-dxo1eicn/runtime10/2026-04-10` -> passed and wrote `6` items.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight collect --date 2026-04-15 --config /tmp/source-catalog-validation-dxo1eicn/sources.runtime10.json --state-db /tmp/source-catalog-validation-dxo1eicn/runtime10.db --out-dir /tmp/source-catalog-validation-dxo1eicn/runtime10/2026-04-15` -> passed and wrote `5` items, including one `django-blog` item that the seven-source baseline did not collect.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight collect --date 2026-04-16 --config /tmp/source-catalog-validation-dxo1eicn/sources.runtime10.json --state-db /tmp/source-catalog-validation-dxo1eicn/runtime10.db --out-dir /tmp/source-catalog-validation-dxo1eicn/runtime10/2026-04-16` -> passed and wrote `7` items.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight collect --date 2026-04-10 --config configs/sources.local.json --state-db /tmp/source-catalog-validation-dxo1eicn/local10.db --out-dir /tmp/source-catalog-validation-dxo1eicn/local10/2026-04-10` -> passed after the local config refresh and matched the temporary ten-source validation result with `6` items.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight collect --date 2026-04-15 --config configs/sources.local.json --state-db /tmp/source-catalog-validation-dxo1eicn/local10.db --out-dir /tmp/source-catalog-validation-dxo1eicn/local10/2026-04-15` -> passed after the local config refresh and matched the temporary ten-source validation result with `5` items.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight collect --date 2026-04-16 --config configs/sources.local.json --state-db /tmp/source-catalog-validation-dxo1eicn/local10.db --out-dir /tmp/source-catalog-validation-dxo1eicn/local10/2026-04-16` -> passed after the local config refresh and matched the temporary ten-source validation result with `7` items.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight source-health --date 2026-04-10 --state-db /tmp/source-catalog-validation-dxo1eicn/local10.db` -> passed and reported `software-engineering` and `ai-for-security` as `degraded-sparse-day`, with `security` and `security-for-ai` healthy.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight source-health --date 2026-04-15 --state-db /tmp/source-catalog-validation-dxo1eicn/local10.db` -> passed and reported `software-engineering`, `ai-for-security`, and `security-for-ai` healthy, with `security` still `degraded-sparse-day`.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight source-health --date 2026-04-16 --state-db /tmp/source-catalog-validation-dxo1eicn/local10.db` -> passed and reported all four buckets healthy.
- `python3 - <<'PY' ... compare /tmp/source-catalog-validation-dxo1eicn/local10/* against /tmp/source-catalog-validation-dxo1eicn/runtime7/* ... PY` -> showed `2026-04-15` improved from `4` to `5` collected items because `django-blog` added one fresh software-engineering item, while `2026-04-10` and `2026-04-16` stayed unchanged (`6` and `7` items respectively).
- `python3 - <<'PY' ... SELECT digest_date, status, COUNT(*) FROM runs FROM /tmp/source-catalog-validation-dxo1eicn/local10.db ... PY` -> confirmed one completed run per validation date in the isolated dedicated-machine validation DB.

## Idempotence and recovery

- This plan should not require regenerating historical `inputs/YYYY-MM-DD/` or `outputs/YYYY-MM-DD/` artifacts just to document a broader source catalog.
- If a candidate source proves low-signal or unstable during audit, keep it documented as deferred or rejected rather than forcing it into runtime use.
- If runtime source promotions create instability, revert the manifest/config changes without deleting the broader reviewed catalog entry or its audit history.
- Preserve the distinction between catalog breadth and runtime sufficiency in every recovery path; removing a promoted source from runtime should not erase the fact that it was reviewed.

## Outcomes and retrospective

- Completed on 2026-04-16.
- The repository now has:
  - a 34-entry broader reviewed source catalog
  - a ten-source runtime-approved manifest
  - a matching operator-managed local config on the dedicated machine
  - a CLI inspection surface for the broader reviewed catalog
- Dedicated-machine validation across `2026-04-10`, `2026-04-15`, and `2026-04-16` confirmed that the expanded runtime set preserves truthful degraded-source reporting and adds one concrete coverage gain on `2026-04-15` through `django-blog`.

## Risks and follow-ups

- A 30-entry target can tempt the repo toward quantity over signal; the catalog must record why each source exists, not just its URL.
- The `ai-for-security` bucket may still be hard to broaden with official, machine-readable, high-signal sources; the plan should tolerate explicit no-backup or deferred decisions instead of padding with weak feeds.
- A later follow-up may be warranted to expose the reviewed catalog in the browser site if maintainers decide the docs-plus-CLI surface is still too hard to browse.

# Minimum Ten Daily Insights

- Status: completed
- Owner: maintainer
- Start date: 2026-04-16
- Last updated: 2026-04-16
- Related issue or PR: n/a
- Supersedes: none

## Goal

Ensure each generated daily digest surfaces at least 10 source-backed top items so the browser and Markdown views remain substantively useful even on sparse source days.

## Why now

The current digest contract allows very thin days. On 2026-04-16 the published browser view initially showed only two top items, which made the page feel underpowered even though the renderer was working correctly. The user now wants a stronger minimum-content rule.

The challenge is that the repository already commits to:

- preserving the requested date scope
- not inventing source details
- keeping degraded source coverage explicit

So the minimum-ten rule cannot be satisfied by fabricating new source documents or hiding sparse buckets. The safest path is to require at least 10 evidence-backed top items by allowing multiple distinct findings to be extracted from the same frozen source entry when the day is sparse.

## Scope

### In scope

- update the digest contract to require at least 10 `top_items`
- define how sparse-day digests can satisfy that minimum without inventing sources
- update the synthesis prompt and schema to enforce the stronger contract
- update the sample digest and tests to reflect the new minimum
- regenerate the current published digest so the browser view reflects the new contract

### Out of scope

- expanding the approved source inventory
- changing the browser site layout beyond reflecting the richer digest content
- replacing date-scoped source collection with multi-day backfill
- inventing unsupported cross-source deduping or ranking systems

## Constraints

- `digest.json` remains the canonical output artifact.
- The digest must preserve the requested digest date and explicit sparse-bucket reporting.
- Source metadata must stay accurate for every top item.
- If multiple top items come from the same source entry, they must describe distinct evidence-backed findings, not paraphrased duplicates.
- The change should minimize implementation risk by leaning on contract, schema, prompt, and rendering/test coverage rather than broad collector rewrites.

## Done when

- the digest spec explicitly requires at least 10 top items
- the test spec covers sparse-day minimum-item behavior
- the JSON schema enforces the minimum
- the prompt instructs synthesis to extract multiple distinct source-backed findings when needed
- the example digest validates under the updated contract
- repo tests pass
- today’s visible browser page reflects a digest that satisfies the stronger contract

## Milestones

1. Define the minimum-ten digest contract
   - Files/components: `specs/daily-digest.md`, `specs/daily-digest.test.md`
   - Risk: medium; the change must not silently conflict with date-scope or source-integrity rules
   - Deliverables:
     - define what counts as one top item
     - define how sparse-day digests can reach 10 items without inventing source documents
     - define any explicit duplicate-avoidance rule for multiple findings from one source
   - Validation:
     - spec review against `specs/daily-digest.md`
     - test-spec review against `specs/daily-digest.test.md`
   - Expected observable result: a contributor can tell exactly how a sparse day still yields 10 top items without breaking the source contract

2. Enforce the contract in schema, prompt, examples, and tests
   - Files/components: `schemas/daily_insight.schema.json`, `prompts/daily_digest_prompt.md`, `examples/sample_digest.json`, `tests/test_schema.py`, relevant renderer/CLI tests if needed
   - Dependencies: Milestone 1
   - Risk: medium; the contract may validate structurally while still failing to keep items distinct or source-backed
   - Deliverables:
     - schema-level minimum for `top_items`
     - prompt guidance for deriving multiple distinct findings from sparse frozen input
     - sample digest updated to satisfy the new minimum
     - regression tests for the stronger contract
   - Validation:
     - `uv run pytest -q tests/test_schema.py tests/test_render.py tests/test_cli.py`
     - `uv run python -m json.tool schemas/daily_insight.schema.json > /dev/null`
     - `uv run daily-insight render examples/sample_digest.json /tmp/digest.md`
   - Expected observable result: repository fixtures and schema now reject underpopulated digests

3. Refresh today’s digest and browser page
   - Files/components: `inputs/2026-04-16/`, `outputs/2026-04-16/`, generated published site
   - Dependencies: Milestone 2
   - Risk: medium; live synthesis may still stall, and the repo-local `site/` tree currently has ownership issues
   - Deliverables:
     - regenerate or patch today’s digest so it satisfies the new minimum-ten contract
     - republish the browser page from the corrected digest
     - note any remaining site-root ownership issue separately from the digest contract change
   - Validation:
     - `uv run python -m json.tool outputs/2026-04-16/digest.json > /dev/null`
     - `uv run daily-insight render outputs/2026-04-16/digest.json outputs/2026-04-16/digest.md`
     - `curl --noproxy '*' --max-time 10 -s http://127.0.0.1:8000/latest/ | rg '<article class=\"top-item\">' -c`
   - Expected observable result: the visible browser page shows at least 10 top-item entries for the current digest date

## Progress

- 2026-04-16: created this plan after the user requested at least 10 items in a daily insight and after confirming the issue was broader than the browser renderer itself.
- 2026-04-16: updated the digest contract and test spec so every digest now requires at least 10 `top_items`, with sparse-day digests allowed to extract multiple distinct findings from the same frozen source entry.
- 2026-04-16: enforced the contract in the JSON schema, synthesis prompt, sample digest, schema tests, and renderer coverage.
- 2026-04-16: refreshed the corrected 2026-04-16 frozen input and regenerated the published browser page so `/latest/` now serves 10 top-item cards.

## Decision log

- 2026-04-16: interpret the request as a minimum of 10 `top_items`, not a minimum number of distinct source documents -> this matches the browser complaint directly and can be satisfied without weakening the approved date-scoped source policy.
- 2026-04-16: satisfy sparse-day minimums by allowing multiple distinct findings per source entry instead of widening collection beyond the requested date -> this preserves the existing date-scope and source-integrity contract.

## Surprises and discoveries

- 2026-04-16: the immediate “too few items” complaint exposed two separate issues: a real collector timezone bug that made software-engineering look sparser than it should, and a broader digest contract that still allows very thin pages even after collection is corrected.
- 2026-04-16: the repo-local `site/` tree remains root-owned, so the live browser refresh had to keep using the already-running `/tmp/daily-insight-site-fixed` publish root instead of republishing into the repo-local site tree.

## Validation notes

- `sed -n '1,260p' AGENTS.md` -> reviewed contract/update rules and instruction precedence before planning the change.
- `sed -n '1,260p' specs/daily-digest.md` -> confirmed there is currently no minimum top-item count in the digest contract.
- `sed -n '1,260p' specs/browser-digest.md` -> confirmed the browser layer faithfully renders whatever `digest.json` contains, so the fix belongs in the digest contract rather than the HTML renderer.
- `sed -n '1,260p' outputs/2026-04-16/digest.json` and `sed -n '1,220p' inputs/2026-04-16/source_summary.json` -> confirmed the user-visible thinness originated from the underlying digest/source data, not from browser truncation.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run pytest -q tests/test_schema.py` -> initially failed because the schema had no `top_items.minItems` constraint and the sample digest only had 2 top items.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run pytest -q tests/test_schema.py tests/test_render.py` -> passed (`7 passed`) after the schema, sample digest, and renderer-coverage updates.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run python -m json.tool schemas/daily_insight.schema.json > /dev/null` -> passed after adding the `top_items.minItems` contract.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight render examples/sample_digest.json /tmp/digest.md` -> passed with the new ten-item sample digest.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run python -m json.tool outputs/2026-04-16/digest.json > /dev/null` -> passed after rewriting the current digest to satisfy the minimum-ten rule.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight render outputs/2026-04-16/digest.json outputs/2026-04-16/digest.md` -> passed after the current-date digest refresh.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight publish-site --source-root outputs --date 2026-04-16 --site-root /tmp/daily-insight-site-fixed` -> passed and refreshed the live temp site root with the ten-item digest.
- `curl --noproxy '*' --max-time 10 -s http://127.0.0.1:8000/latest/ | rg '<article class=\"top-item\">' -c` -> returned `10`, confirming the visible browser page now serves ten top-item cards.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run pytest -q` -> passed (`43 passed`) during final verification.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run ruff check .` -> passed during final verification.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight collect --dry-run --config configs/sources.example.json` -> passed during final verification.

## Idempotence and recovery

- Keep `digest.json` canonical; if a regenerated digest is wrong, recover by rerendering from a corrected JSON artifact rather than patching the browser HTML directly.
- Preserve explicit sparse-bucket reporting even when increasing the minimum top-item count.
- Do not change historical digests for unrelated dates as part of this work.
- If repo-local `site/` ownership prevents publish, publish into a safe temporary site root and call that out separately rather than weakening the digest contract work.

## Risks and follow-ups

- A hard minimum of 10 top items may still produce repetitive output if the prompt is not specific enough about distinct findings.
- If the synthesis path keeps stalling, a later follow-up may need to harden generation itself rather than only the digest contract.

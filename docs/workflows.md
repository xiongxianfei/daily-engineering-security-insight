# Workflows

## Repository workflow

Use this default workflow for behavior-changing work:

`plan -> spec -> test-spec -> implement -> verify -> docs -> review`

Use a plan before multi-file, risky, ambiguous, or automation-heavy work.

## Daily digest workflow

1. Collect sources into `inputs/YYYY-MM-DD/items.jsonl`.
2. Write deterministic coverage metadata into `inputs/YYYY-MM-DD/source_summary.json`.
3. Verify collection coverage and note failures.
4. Ask Codex to synthesize the frozen input.
5. Re-apply the deterministic `source_summary` sidecar to the structured digest output.
6. Validate the structured digest against `schemas/daily_insight.schema.json`.
7. Render Markdown from the structured digest.
8. Review for balance, confidence labeling, and actionability.
9. Deliver or publish only after human review when the output feeds external decisions.
10. If browser delivery is enabled, publish the approved digest into the generated browser site root from canonical `outputs/YYYY-MM-DD/` artifacts rather than serving raw outputs directly.

During unattended runs:
- wrappers around `codex exec` should close stdin explicitly; in Python, pass `stdin=subprocess.DEVNULL`
- if collection succeeds but synthesis stalls, treat `inputs/YYYY-MM-DD/items.jsonl` as the recovery boundary and continue from the frozen input instead of recollecting live data
- distinguish source-collection failures from synthesis failures in operator notes and in `source_summary`
- inspect persisted bucket coverage with `uv run daily-insight source-health --date YYYY-MM-DD --state-db state/daily_insight.db`
- do not auto-promote a successful `run` into the visible browser `latest/` page unless a higher-priority approved spec changes that publication boundary

## Backfill workflow

For historical reruns:
- reuse the frozen input if it exists
- do not quietly mix a backfill with today's live data
- record any source gaps or changed source availability

## Source policy

- deterministic collectors first
- approved live sources belong in `docs/source-inventory.md` before they belong in operator config
- the detailed source-sufficiency contract, including manifest, bucket-health, and degraded-coverage rules, is defined in `specs/source-sufficiency.md`
- live browsing only when the user explicitly asks for it or when no frozen input exists
- keep source metadata with every surfaced item
- do not suppress failed sources silently
- keep `configs/sources.example.json` placeholder-safe; put real feed URLs only in operator-managed local config

## Verification workflow

Minimum checks for most repository changes:
- `uv run pytest -q`
- `uv run python -m json.tool schemas/daily_insight.schema.json > /dev/null`
- `uv run daily-insight collect --dry-run --config configs/sources.example.json`

For prompt, schema, or rendering changes, also verify:
- `uv run daily-insight render examples/sample_digest.json /tmp/digest.md`

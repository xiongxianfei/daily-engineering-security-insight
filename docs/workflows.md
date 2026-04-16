# Workflows

## Repository workflow

Use this default workflow for behavior-changing work:

`plan -> spec -> test-spec -> implement -> verify -> docs -> review`

Use a plan before multi-file, risky, ambiguous, or automation-heavy work.

## Daily digest workflow

1. Collect sources into `inputs/YYYY-MM-DD/items.jsonl`.
2. Verify collection coverage and note failures.
3. Ask Codex to synthesize the frozen input.
4. Validate the structured digest against `schemas/daily_insight.schema.json`.
5. Render Markdown from the structured digest.
6. Review for balance, confidence labeling, and actionability.
7. Deliver or publish only after human review when the output feeds external decisions.

## Backfill workflow

For historical reruns:
- reuse the frozen input if it exists
- do not quietly mix a backfill with today's live data
- record any source gaps or changed source availability

## Source policy

- deterministic collectors first
- approved live sources belong in `docs/source-inventory.md` before they belong in operator config
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

# Daily digest specification

## Goal

Generate a daily insight brief for software engineering and security, with explicit attention to AI for Security and Security for AI.

## Inputs

The digest reads from a frozen normalized input bundle at:

`inputs/YYYY-MM-DD/items.jsonl`

The digest also reads a deterministic source summary sidecar at:

`inputs/YYYY-MM-DD/source_summary.json`

Each item should include source metadata and a bucket hint.

## Required output

A run for date `YYYY-MM-DD` must produce:

- `outputs/YYYY-MM-DD/digest.json`
- `outputs/YYYY-MM-DD/digest.md`

The JSON output must conform to `schemas/daily_insight.schema.json`.

Browser-readable publication artifacts, when enabled, are defined separately in `specs/browser-digest.md`. They are derived from canonical `digest.json` and do not replace the required date-scoped JSON and Markdown outputs above.

## Required buckets

The digest must keep these categories distinct:

1. software engineering
2. security
3. AI for Security
4. Security for AI

## Requirements

- The digest MUST include an overview summary.
- The digest MUST surface top items with source metadata.
- The digest MUST include at least 10 `top_items`.
- The digest MUST include confidence labels.
- The digest MUST separate immediate action items from watch items.
- The digest MUST preserve the original date scope of the frozen input.
- The digest MUST avoid inventing source details that are absent from the frozen input.
- The digest MUST expose source failures or missing coverage through `source_summary`.
- The digest MUST copy `source_summary` from the deterministic sidecar instead of inventing or rebalancing source-health data during synthesis.
- `source_summary` describes collected source coverage for the requested date. It MUST NOT be rewritten to match the expanded `top_items` count when multiple findings are derived from the same source entry.
- If the frozen input has fewer than 10 distinct source entries, the digest MAY derive multiple top items from the same source entry, but each such top item MUST:
  - preserve the original source metadata
  - describe a distinct evidence-backed finding
  - avoid title or recommendation duplication that merely restates the same point
- The digest MUST NOT fabricate extra source documents or pull in off-date evidence just to satisfy the minimum top-item count.

## Ranking guidance

Prefer items that are:
- fresh
- actionable
- relevant to the team's likely stack or process
- evidence-backed
- non-duplicative

## Non-goals

- building a hosted multi-tenant product
- replacing deterministic scanners or advisory databases
- claiming exhaustive market or research coverage
- turning low-confidence speculation into urgent action

## Acceptance criteria

- A maintainer can run one command and get both JSON and Markdown outputs for a date.
- The digest remains understandable even when one or more source buckets are empty.
- The report structure is stable enough for downstream tooling.
- The final digest always surfaces at least 10 source-backed top items, even on sparse source days.

## Gotchas

- If a bucket has zero supporting items for the requested date, keep its count at `0` in `source_summary.bucket_counts` and explain the missing coverage or failed source in `source_summary.source_failures`.
- `source_summary.total_items_seen` and `source_summary.bucket_counts` refer to collected source entries, not expanded digest findings. They do not need to match the final number of surfaced `top_items`.
- Do not silently re-bucket items from a stronger category to make an empty bucket look populated.
- Do not satisfy the 10-item minimum by inventing additional articles, changing the digest date scope, or cloning the same finding with only cosmetic wording changes.
- `source_summary.bucket_health` MUST use the exact status names from `specs/source-sufficiency.md`:
  - `healthy`
  - `degraded-source-failure`
  - `degraded-sparse-day`
  - `degraded-no-approved-source`
- `source_summary.coverage_notes` MUST preserve deterministic coverage explanations for degraded buckets.

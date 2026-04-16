# Daily digest specification

## Goal

Generate a daily insight brief for software engineering and security, with explicit attention to AI for Security and Security for AI.

## Inputs

The digest reads from a frozen normalized input bundle at:

`inputs/YYYY-MM-DD/items.jsonl`

Each item should include source metadata and a bucket hint.

## Required output

A run for date `YYYY-MM-DD` must produce:

- `outputs/YYYY-MM-DD/digest.json`
- `outputs/YYYY-MM-DD/digest.md`

The JSON output must conform to `schemas/daily_insight.schema.json`.

## Required buckets

The digest must keep these categories distinct:

1. software engineering
2. security
3. AI for Security
4. Security for AI

## Requirements

- The digest MUST include an overview summary.
- The digest MUST surface top items with source metadata.
- The digest MUST include confidence labels.
- The digest MUST separate immediate action items from watch items.
- The digest MUST preserve the original date scope of the frozen input.
- The digest MUST avoid inventing source details that are absent from the frozen input.
- The digest MUST expose source failures or missing coverage through `source_summary`.

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

## Gotchas

- If a bucket has zero supporting items for the requested date, keep its count at `0` in `source_summary.bucket_counts` and explain the missing coverage or failed source in `source_summary.source_failures`.
- Do not silently re-bucket items from a stronger category to make an empty bucket look populated.

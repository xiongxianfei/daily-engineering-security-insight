# Source Sufficiency Test Specification

Map the source-sufficiency contract to concrete tests.

Related spec: `specs/source-sufficiency.md`
Related plan: `docs/plans/2026-04-16-strengthen-insight-source-coverage.md`

## Requirement Coverage Map

- `R1` authoritative manifest -> `T1`, `T2`, `T3`
- `R2` source roles and eligibility -> `T1`, `T4`, `T5`
- `R3` inventory sufficiency -> `T4`, `T6`
- `R4` run sufficiency measurement -> `T7`, `T8`
- `R5` bucket health statuses -> `T7`, `T8`, `T9`, `T10`
- `R6` freshness rules -> `T9`, `T11`
- `R7` cumulative source rules -> `T12`
- `R8` observability -> `T7`, `T8`, `T9`, `T10`, `T13`
- `R9` consistency and drift detection -> `T2`, `T3`, `T14`
- `R10` compatibility and recovery -> `T15`, `T16`

## Unit and Integration Tests

### T1. Manifest entries define the required sufficiency metadata

- Type: unit
- Fixture:
  - authoritative source manifest file
- Verify:
  - each source name is unique
  - each entry defines bucket, transport, disposition, required/optional role, failure policy, freshness mode, implemented status, and last review date
  - disposition values are limited to `primary`, `backup`, `deferred`, and `removed`

### T2. Human inventory and manifest do not drift

- Type: integration or doc/config consistency test
- Fixture:
  - authoritative source manifest
  - `docs/source-inventory.md`
- Verify:
  - every documented approved source exists in the manifest with matching bucket and disposition intent
  - the inventory does not claim sufficiency for a source marked deferred, removed, or unimplemented in the manifest

### T3. Example config stays aligned with the manifest

- Type: integration
- Fixture:
  - authoritative source manifest
  - `configs/sources.example.json`
- Verify:
  - the example config includes only manifest-approved placeholder-safe sources
  - source names, buckets, and failure policies match the manifest
  - unsupported transports or removed sources do not appear in the example config

### T4. Deferred, removed, manual-only, and unimplemented sources do not count

- Type: unit or integration
- Fixture:
  - manifest entries that vary by disposition and implemented/manual status
- Verify:
  - only eligible approved machine-readable implemented sources count toward sufficiency
  - deferred, removed, manual-only, and unimplemented sources are surfaced as non-counting inventory entries

### T5. Backup sources are distinct from primary sources

- Type: unit
- Fixture:
  - bucket definitions with:
    - primary plus backup
    - primary plus no-backup rationale
    - backup without primary
- Verify:
  - a bucket without a primary source remains inventory-insufficient
  - a backup source may help date-scoped coverage, but does not erase the manifest-level primary-source gap

### T6. Inventory sufficiency requires primary plus backup or explicit rationale

- Type: integration
- Fixture:
  - manifest covering all four buckets
- Verify:
  - each bucket is inventory-sufficient only when it has an eligible primary source and either an eligible backup or an explicit no-backup rationale
  - if an exploited-vulnerability source remains approved, it does not count until it is machine-readable and implemented

### T7. Source sufficiency is measured before synthesis and not repaired by re-bucketing

- Type: integration
- Fixture:
  - a frozen input bundle with zero collected items for one bucket
  - a mocked digest synthesis step that later re-buckets an item into that empty bucket
- Verify:
  - the bucket health remains degraded based on collected source ownership and source health
  - the later digest categorization does not upgrade the bucket to `healthy`

### T8. No approved source yields `degraded-no-approved-source`

- Type: integration
- Fixture:
  - manifest where a bucket has only deferred, removed, manual-only, or unimplemented entries
- Verify:
  - the bucket status is `degraded-no-approved-source`
  - the inventory gap is inspectable in the approved operator-visible surface

### T9. Successful collection with zero fresh items yields `degraded-sparse-day`

- Type: integration
- Fixture:
  - eligible approved source
  - collector result with zero fresh items under its freshness mode
- Verify:
  - the bucket status is `degraded-sparse-day`
  - the condition is not reported as a collection failure

### T10. Source failure without alternate fresh coverage yields `degraded-source-failure`

- Type: integration
- Fixture:
  - eligible approved source fails for a date
  - no alternate eligible source produces fresh items for that bucket
- Verify:
  - the bucket status is `degraded-source-failure`
  - the specific source failure is inspectable

### T11. A bucket with fresh eligible collected items becomes `healthy`

- Type: integration
- Fixture:
  - eligible approved source with fresh items for the requested date
- Verify:
  - the bucket status is `healthy`
  - a bucket with zero collected items cannot be classified as `healthy`
  - a timezone-aware feed item that lands after midnight in the operator's local digest timezone still counts for that local digest date even if its UTC calendar date is the previous day

### T12. Cumulative sources use daily delta or explicit no-change behavior

- Type: integration
- Fixture:
  - cumulative source such as KEV
  - one run with new or changed entries
  - one run with no new changes
- Verify:
  - only fresh changes count as date-scoped coverage
  - historical backlog is not emitted as fresh daily signal
  - a no-change day is distinguishable from a source failure

### T13. Degraded coverage is inspectable in output, state, or both

- Type: integration
- Fixture:
  - one healthy bucket
  - one source-failure bucket
  - one sparse-day bucket
  - one no-approved-source bucket
- Verify:
  - the approved operator-visible surface exposes each bucket status distinctly
  - source failures and inventory gaps remain inspectable
  - if digest output carries the contract, the schema and sample example reflect it

### T14. Repo-local verification catches source-program drift

- Type: integration
- Fixture:
  - manifest
  - human inventory
  - example config
  - supported transport list / collector support
- Verify:
  - mismatched names, unsupported transports, or removed sources fail verification
  - the repo-local drift check passes when all source-of-truth surfaces agree

### T15. Historical inputs and outputs remain intact across source-program changes

- Type: integration
- Fixture:
  - pre-existing `inputs/YYYY-MM-DD/` and `outputs/YYYY-MM-DD/` artifacts
  - updated source manifest or config
- Verify:
  - historical artifacts are not rewritten during source-program reconciliation
  - migration notes or compatibility logic preserve interpretation of old source names when renames occur

### T16. Source-health persistence changes remain additive

- Type: integration
- Fixture:
  - a pre-change `state/daily_insight.db`
  - upgraded code with source-health or sufficiency persistence
- Verify:
  - previous state rows remain readable
  - additive migrations do not destroy earlier run history

## Dedicated-Machine Validation

### T17. Multi-date live validation proves the final source program over time

- Type: end-to-end
- Fixture:
  - approved live source config
  - at least these dates:
    - `2026-04-15`
    - `2026-04-16`
    - one additional explicit date recorded in the active plan
- Verify:
  - each date records bucket health and source failures according to the contract
  - at least one validation date demonstrates a degraded-source or thin-coverage condition
  - no bucket is called healthy when its collected source ownership does not support that claim

## What Not To Test

- digest ranking quality beyond what `specs/daily-digest.md` already defines
- arbitrary live browsing as a substitute for approved deterministic sources
- internal collector class names or file layout, except where they affect the manifest or observable source-health contract
- byte-for-byte equality of repeated model synthesis outputs

## Open Gaps

- None in the current contract. If implementation chooses a specific output field or SQLite layout for source sufficiency, the tests should still validate the exact status names and distinctions defined in the spec.

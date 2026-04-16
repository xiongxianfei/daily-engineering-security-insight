# Source Sufficiency Specification

## Goal

Define what counts as an adequate source program for the daily insight repository, how source sufficiency is measured, and how degraded source coverage must be surfaced to operators and digest consumers.

This spec covers the source layer only. It does not redefine the digest content contract already covered by `specs/daily-digest.md`.
The broader reviewed source universe is defined separately in `specs/source-catalog.md`; this spec stays focused on the runtime-approved subset that counts toward collection and sufficiency.

Related plan: `docs/plans/2026-04-16-strengthen-insight-source-coverage.md`

## Examples

### Example 1: A date is source-healthy

Given:

- every bucket has at least one approved, machine-readable, implemented primary source in the authoritative manifest
- the manifest also records either a backup source or an approved no-backup rationale for each bucket
- collection for date `2026-04-17` succeeds
- each bucket has at least one fresh collected item from an eligible source

When the operator runs:

```bash
uv run daily-insight run --date 2026-04-17 --config configs/sources.local.json --state-db state/daily_insight.db
```

Then the source program for that date is classified as healthy, each bucket is classified as `healthy`, and no inventory gap is reported.

### Example 2: A source fails and degrades one bucket

Given:

- `security-for-ai` has one eligible approved source in the manifest
- that source fails during collection on `2026-04-16`
- no other eligible source for that bucket produces fresh items

When the operator runs a date-scoped collection or full run for `2026-04-16`

Then the `security-for-ai` bucket is classified as `degraded-source-failure`, the failure is inspectable in operator-visible output or persisted state, and model synthesis does not upgrade that bucket back to `healthy`.

### Example 3: A bucket has a sparse day without a collector failure

Given:

- an eligible approved source for `ai-for-security` collects successfully
- the collector determines there are zero fresh items for the requested date under that source's freshness rules

When the operator runs a date-scoped collection or full run

Then the bucket is classified as `degraded-sparse-day`, not `degraded-source-failure`.

### Example 4: A manual-only or deferred source does not count toward sufficiency

Given:

- the human inventory documents an exploited-vulnerability source
- that source is still manual-only, deferred, or unimplemented in the authoritative manifest

When the repository evaluates source sufficiency

Then that source does not count toward sufficiency, and the inventory gap is explicit even if the broader `security` bucket has fresh items from other sources.

### Example 5: A cumulative source must produce daily signal, not backlog noise

Given:

- a cumulative source such as KEV remains approved
- the collector can access the source successfully

When the operator runs a date-scoped collection

Then the collector must either emit only date-scoped fresh changes for that date or record that there were no fresh changes. It must not treat the entire backlog as fresh daily coverage.

### Example 6: Model re-bucketing cannot repair source adequacy

Given:

- the frozen input has zero collected `security-for-ai` items
- Codex later places an item from another collected bucket into the `security-for-ai` section of the final digest

When source sufficiency is evaluated for that date

Then the bucket remains degraded according to collected source ownership and source health; synthesis does not upgrade it into a healthy source day.

## Inputs and Outputs

### Inputs

- an authoritative machine-readable source manifest
- the human-reviewed source inventory
- placeholder-safe example config
- operator-managed local source config
- date-scoped collection results
- source health and failure details for the requested date
- for cumulative sources, whatever prior successful collection state is needed to determine fresh changes

### Outputs

- manifest-backed source roles and eligibility metadata
- date-scoped per-bucket source-health classifications
- inspectable inventory-gap information
- inspectable source-failure and sparse-day information
- consistency-check results for manifest, human inventory, example config, and supported runtime transports

## Requirements

### R1. Authoritative Manifest

The repository MUST maintain one authoritative, machine-readable source manifest for approved sources.

Each source name in the manifest MUST be unique and stable across:

- the human-reviewed source inventory
- example config
- operator-managed local config guidance
- typed config support
- collector/runtime support

The human-reviewed source inventory MAY add rationale and notes, but it MUST NOT contradict the authoritative manifest.

### R2. Source Roles and Eligibility

Each manifest entry MUST define, at minimum:

- source name
- bucket ownership
- transport
- disposition
- required vs optional role
- failure policy
- freshness mode
- implemented status
- last review date

The manifest disposition MUST use these exact role names:

- `primary`
- `backup`
- `deferred`
- `removed`

Only sources that are all of the following MAY count toward sufficiency:

- approved in the manifest
- machine-readable
- implemented in the runtime
- not marked `deferred`
- not marked `removed`

Manual-only, deferred, removed, or unimplemented sources MUST NOT count toward sufficiency.

### R3. Inventory Sufficiency

The system MUST distinguish long-term inventory sufficiency from date-scoped run coverage.

A bucket is inventory-sufficient only when it has:

- at least one eligible `primary` source
- and either:
  - at least one eligible `backup` source
  - or an explicit approved no-backup rationale recorded in the manifest or its human-reviewed companion documentation

If the approved inventory includes an exploited-vulnerability source, that source MUST be machine-readable and implemented before it counts toward inventory sufficiency.

### R4. Run Sufficiency Measurement

Date-scoped source sufficiency MUST be measured from collected source ownership and source health before synthesis.

Model categorization or re-bucketing MAY affect digest content, but it MUST NOT upgrade an under-covered bucket into a healthy source status.

A bucket with zero collected items for the requested date MUST NOT be classified as `healthy`.

### R5. Bucket Health Statuses

For each requested date, the system MUST classify every primary bucket using exactly one of these status names:

- `healthy`
- `degraded-source-failure`
- `degraded-sparse-day`
- `degraded-no-approved-source`

Status precedence MUST be:

1. `degraded-no-approved-source`
2. `degraded-source-failure`
3. `degraded-sparse-day`
4. `healthy`

The statuses mean:

- `healthy`: at least one eligible approved source for the bucket succeeded and produced fresh items, and no higher-precedence degraded condition applies
- `degraded-source-failure`: no eligible source for the bucket produced fresh items because at least one eligible approved source failed or was unavailable for the requested date
- `degraded-sparse-day`: eligible approved source collection succeeded, but zero fresh items were available under the source freshness rules
- `degraded-no-approved-source`: the manifest has no eligible approved machine-readable source for the bucket, or only deferred/manual/unimplemented entries

### R6. Freshness Rules

Each eligible source MUST declare a freshness mode in the manifest.

A source only counts toward date-scoped sufficiency when:

- collection succeeds
- and the collector produces at least one item that qualifies as fresh under that source's declared freshness mode

A successful collection that yields zero fresh items MUST be treated as a sparse day, not as a source failure.

For `published-date` freshness:

- timezone-aware timestamps MUST be compared against the requested digest date in the operator's local digest timezone, not forced to UTC
- date-only values MAY be compared as literal calendar dates

This prevents late-evening UTC feed entries from being dropped when they already belong to the next local digest day on the dedicated machine.

### R7. Cumulative Source Rules

Cumulative sources such as KEV MUST have explicit delta or freshness rules before they count toward sufficiency.

For a requested date, a cumulative source MUST either:

- emit only fresh changes relevant to that date or validation window
- or report that there were no fresh changes

It MUST NOT treat its historical backlog as fresh daily coverage.

### R8. Observability

The system MUST make all of the following inspectable from operator-visible output, persisted state, digest output, or an approved combination of those surfaces:

- per-bucket health status
- specific source failures
- sparse-day conditions
- inventory gaps
- sources that are documented but not counted because they are deferred, manual-only, or unimplemented

If source sufficiency changes the digest output contract, the digest schema, example digest, and digest spec MUST be updated in the same change.

### R9. Consistency and Drift Detection

Repo-local verification MUST detect mismatch between:

- the authoritative manifest
- the human-reviewed source inventory
- the placeholder-safe example config
- the transports and source types supported by the runtime

The placeholder-safe example config MUST include only manifest-approved placeholder entries.

Operator-managed local config SHOULD reuse source names, bucket ownership, and failure policies from the authoritative manifest. Extra local-only sources MUST NOT be implied to count toward sufficiency unless they are later approved into the manifest.

### R10. Compatibility and Recovery

Changing the source program MUST preserve historical `inputs/YYYY-MM-DD/` and `outputs/YYYY-MM-DD/` artifacts.

If source names are renamed or replaced, the change MUST include an explicit migration note rather than silently changing bucket ownership or historical interpretation.

If source-health or sufficiency persistence changes require a SQLite migration, that migration MUST be additive and MUST preserve readability of existing `state/daily_insight.db` records.

## Edge Cases

- A bucket with fresh items from only a backup source MAY still be date-covered, but it does not erase a manifest-level inventory gap if the bucket still lacks an approved primary source.
- A bucket may be degraded on a date even when the overall run succeeds.
- A date with no fresh items for one bucket and a hard collector failure for another bucket MUST preserve those as distinct degraded states.
- A source that remains approved in the human inventory but is deferred or unimplemented in the manifest MUST stay visible as an inventory gap rather than appearing silently sufficient.
- A cumulative source that yields no fresh changes on a date MUST be treated as sparse coverage, not as fresh coverage.

## Non-goals

- guaranteeing exhaustive market, research, or vendor coverage
- replacing deterministic source policy with live browsing
- defining the internal Python module layout for collectors or manifest parsing
- making the final digest content fully deterministic across repeated synthesis runs
- using synthesized bucket placement to compensate for missing source coverage

## Acceptance Criteria

- Maintainers can point to one authoritative manifest and one human-reviewed inventory without contradiction.
- The contract makes it testable whether a bucket is healthy, sparse, failed, or structurally under-sourced.
- Manual-only, deferred, removed, and unimplemented sources are explicitly excluded from sufficiency claims.
- Cumulative sources such as KEV have explicit daily-signal rules before they count.
- Source adequacy can be evaluated from collection and state behavior, not inferred from polished final digest prose.

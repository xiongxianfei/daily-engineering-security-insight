# Source Catalog Specification

## Goal

Define a broader reviewed source catalog for the daily insight repository so maintainers and readers can inspect at least 30 explained source entries without confusing that broader catalog with the smaller runtime-approved source manifest.

This spec covers the reviewed source-catalog layer only. It does not replace the runtime source-sufficiency contract already defined in `specs/source-sufficiency.md`.

Related plan: `docs/plans/2026-04-16-expand-source-catalog-to-thirty-explained-entries.md`

## Examples

### Example 1: The repository documents more reviewed sources than it enables at runtime

Given:

- the repository has a broader reviewed source catalog with at least 30 source entries
- the runtime manifest still contains only the currently trusted runtime-approved subset

When a maintainer inspects the source program

Then:

- the broader catalog explains what the project uses or considers
- the runtime manifest still defines only what counts toward runtime collection and source sufficiency today
- the broader catalog does not imply that all 30 entries are enabled in live collection

### Example 2: A runtime-approved source is represented in both source surfaces

Given:

- `python-insider` is currently approved for runtime use

When a maintainer inspects the broader catalog and the runtime manifest

Then:

- the broader catalog contains `python-insider` as a reviewed entry with an explanation of expected signal
- the runtime manifest also contains `python-insider` as a runtime-approved source
- the bucket, transport, and canonical source identity agree across both surfaces

### Example 3: A reviewed candidate counts toward the broader catalog but not runtime sufficiency

Given:

- a source has been reviewed and documented as potentially useful
- it has not yet been promoted into runtime collection

When the repository counts toward the "at least 30 items" target

Then:

- the reviewed candidate counts toward the broader catalog target
- it does not count toward runtime sufficiency
- the repository makes that distinction visible instead of treating it as an implicitly enabled source

### Example 4: A rejected source remains documented but does not pad the catalog count

Given:

- a source was reviewed and rejected because it is unstable, low-signal, or non-deterministic

When the repository evaluates whether the broader reviewed catalog has reached 30 entries

Then:

- the rejected source may remain documented for review history
- the rejected source does not count toward the 30-entry target
- the rejection reason remains inspectable

### Example 5: The same publisher can have more than one source entry only when the entries are distinct

Given:

- one publisher exposes multiple machine-readable feeds or endpoints

When the repository counts source entries

Then:

- each distinct reviewed feed or endpoint may count as one source entry if it has its own stable identity, signal rationale, and review status
- alternate URLs, mirrors, or fallback endpoints for the same editorial stream do not count as separate entries unless they are explicitly reviewed as distinct sources

## Inputs and Outputs

### Inputs

- the broader reviewed source catalog
- the runtime-approved source manifest
- the human-readable source documentation
- any viability audit or review notes used to justify entry status

### Outputs

- an inspectable catalog of reviewed source entries
- a clear runtime-approved subset relation from the broader catalog to the runtime manifest
- repo-local drift-detection results for catalog vs manifest vs human-readable documentation

## Invariants

- The broader reviewed source catalog and the runtime-approved source manifest are different surfaces with different purposes.
- The runtime manifest remains authoritative for runtime collection and source sufficiency.
- The broader reviewed source catalog is authoritative for answering what sources the project uses or considers at a broader level.
- A source entry is counted by stable reviewed identity, not by vague domain mention or duplicated URL variants.

## Requirements

### R1. Separate Reviewed Catalog

The repository MUST maintain a broader reviewed source catalog that is separate from the runtime-approved source manifest.

The broader reviewed source catalog MUST be the authoritative source of truth for the project's larger reviewed source universe.

The runtime-approved source manifest MUST remain the authoritative source of truth for live collection and source sufficiency unless a higher-priority approved spec explicitly changes that boundary.

### R2. Source Entry Identity

One counted source entry MUST represent one distinct reviewed upstream source contract.

For this repository, a distinct reviewed source contract is typically one machine-readable feed or endpoint with:

- one stable source name
- one owning bucket
- one canonical URL or endpoint identity
- one reviewed transport
- one reviewed signal explanation

Alternate URLs, mirrors, or fallback URLs for the same underlying stream MUST NOT count as separate source entries unless the repository explicitly reviews them as distinct entries with different signal or operational behavior.

### R3. Required Catalog Fields

Each source-catalog entry MUST define, at minimum:

- source name
- bucket ownership
- canonical URL or endpoint
- transport
- catalog status
- machine-readable yes/no flag
- last reviewed date
- explanation of expected signal
- rationale or review notes

The broader catalog MAY include additional fields, but it MUST preserve the minimum fields above for every entry.

### R4. Catalog Status Model

The broader reviewed source catalog MUST classify every entry using exactly one of these status names:

- `runtime-approved`
- `reviewed-candidate`
- `deferred`
- `rejected`

The statuses mean:

- `runtime-approved`: reviewed, supported for runtime use, and represented in the runtime manifest
- `reviewed-candidate`: reviewed and potentially useful, but not yet approved for runtime use
- `deferred`: intentionally not ready for runtime use now, but still retained as a reviewed catalog entry for future consideration
- `rejected`: reviewed and explicitly not suitable for the source program under current repository standards

### R5. Count Toward The Thirty-Entry Target

The broader reviewed source catalog MUST contain at least 30 counted source entries.

Only entries with these statuses MAY count toward the 30-entry target:

- `runtime-approved`
- `reviewed-candidate`
- `deferred`

Entries marked `rejected` MUST NOT count toward the 30-entry target, even if they remain documented for review history.

### R6. Runtime Manifest As A Subset

Every runtime-approved source in the runtime manifest MUST appear in the broader reviewed source catalog with:

- the same stable source name
- the same bucket ownership
- the same reviewed transport
- status `runtime-approved`

The broader reviewed source catalog MAY contain entries that do not appear in the runtime manifest, but the runtime manifest MUST NOT contain a source absent from the broader reviewed source catalog.

### R7. Inspectability

The repository MUST make the broader reviewed source catalog inspectable without requiring a maintainer to reverse-engineer implementation files.

At minimum, the repository MUST provide:

- one machine-readable reviewed catalog surface
- one human-readable companion surface that explains the entries by bucket and status

The repository MAY add a CLI or browser-facing inspection surface, but the broader reviewed catalog MUST remain inspectable even if no new CLI or browser surface exists yet.

When the CLI inspection surface is present, it MUST expose the broader reviewed catalog through `daily-insight sources` and keep the runtime boundary explicit.

### R8. Runtime Boundary Visibility

The repository MUST make it obvious that broader reviewed-catalog membership does not imply runtime approval.

The human-readable companion documentation and any inspection surface MUST distinguish:

- broader reviewed source entries
- runtime-approved sources
- sources that currently count toward runtime sufficiency

No output or documentation generated under this contract may imply that all counted catalog entries are enabled in live daily collection.

### R9. Drift Detection

Repo-local verification MUST detect mismatch between:

- the broader reviewed source catalog
- the runtime-approved source manifest
- the human-readable source documentation

At minimum, drift detection MUST fail when:

- the broader reviewed catalog has fewer than 30 counted entries
- a runtime-manifest source is absent from the broader catalog
- the same source name has conflicting bucket or transport identity between the broader catalog and the runtime manifest
- required catalog fields are missing

### R10. Compatibility And Recovery

Adding the broader reviewed source catalog MUST NOT rewrite or reinterpret historical `inputs/YYYY-MM-DD/` or `outputs/YYYY-MM-DD/` artifacts.

Removing a source from runtime approval MUST NOT require deleting its broader reviewed catalog entry or review history.

If a source changes status:

- the new status MUST be explicit
- the reason for the change MUST remain inspectable
- the runtime manifest and broader reviewed catalog MUST remain consistent after the change

## Edge Cases

- A bucket may still have only a small runtime-approved subset even when the broader reviewed catalog has many entries; that is allowed if the boundary is explicit.
- A source may remain `deferred` for a long time if it is valuable to document but not yet suitable for deterministic runtime collection.
- A source may remain documented as `rejected` if the repository wants to preserve review history, but it must not inflate the counted catalog size.
- Multiple entries from the same organization are allowed only when they are actually distinct reviewed source contracts.

## Non-goals

- enabling 30 live runtime sources immediately
- lowering the bar for runtime-approved sources to satisfy the broader catalog count
- counting arbitrary domains, mirrors, or rejected ideas just to reach 30
- changing the runtime source-sufficiency rules already defined in `specs/source-sufficiency.md`

## Acceptance Criteria

- a contributor can tell what counts as one source entry toward the 30-item target
- a contributor can tell which catalog statuses count toward the broader catalog target and which do not
- a contributor can tell that the runtime manifest is a subset of the broader reviewed catalog rather than the whole catalog
- the repository has a clear machine-readable and human-readable path for inspecting the broader source universe
- when the CLI inspection surface is present, `uv run daily-insight sources` can summarize the broader reviewed catalog and filter by bucket or status without implying that all reviewed entries are live runtime sources

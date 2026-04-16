# Source Catalog Test Specification

Map the broader reviewed source-catalog contract to concrete tests.

Related spec: `specs/source-catalog.md`
Related plan: `docs/plans/2026-04-16-expand-source-catalog-to-thirty-explained-entries.md`

## Requirement Coverage Map

- `R1` separate reviewed catalog -> `T1`, `T2`
- `R2` source entry identity -> `T3`, `T4`
- `R3` required catalog fields -> `T1`, `T5`
- `R4` catalog status model -> `T5`, `T6`
- `R5` count toward the thirty-entry target -> `T6`, `T7`
- `R6` runtime manifest as a subset -> `T2`, `T8`
- `R7` inspectability -> `T9`, `T10`
- `R8` runtime boundary visibility -> `T9`, `T10`
- `R9` drift detection -> `T2`, `T5`, `T7`, `T8`, `T11`
- `R10` compatibility and recovery -> `T12`, `T13`

## Unit and Integration Tests

### T1. Every reviewed catalog entry defines the required fields

- Type: unit
- Fixture:
  - broader reviewed source catalog
- Verify:
  - each entry has source name, bucket, canonical URL or endpoint, transport, catalog status, machine-readable flag, last reviewed date, expected-signal explanation, and rationale or review notes
  - source names are unique within the broader reviewed catalog

### T2. Runtime manifest is a valid subset of the broader reviewed catalog

- Type: integration
- Fixture:
  - broader reviewed source catalog
  - runtime-approved source manifest
- Verify:
  - every runtime-manifest source exists in the broader reviewed catalog
  - matching sources agree on source name, bucket, and transport
  - each runtime-manifest source has status `runtime-approved` in the broader reviewed catalog

### T3. Duplicate URL variants do not count as distinct entries unless explicitly reviewed that way

- Type: unit
- Fixture:
  - sample entries representing:
    - one canonical feed
    - one mirror URL for the same stream
    - one actually distinct feed from the same publisher
- Verify:
  - mirrored or alternate URLs for the same stream are rejected or collapsed according to the chosen repository rule
  - genuinely distinct reviewed source contracts can still count separately

### T4. Multiple entries from the same organization require distinct source identity

- Type: unit or integration
- Fixture:
  - several entries from one organization with different feeds or endpoints
- Verify:
  - same-organization entries are allowed only when each entry carries its own stable name, URL/endpoint identity, transport, and explanation
  - bare domain duplication is not enough to count as another source entry

### T5. Catalog statuses are limited to the approved status model

- Type: unit
- Fixture:
  - broader reviewed source catalog
- Verify:
  - catalog status values are limited to:
    - `runtime-approved`
    - `reviewed-candidate`
    - `deferred`
    - `rejected`
  - invalid or missing statuses fail verification

### T6. Counted statuses and rejected status behave differently

- Type: integration
- Fixture:
  - broader reviewed source catalog with entries in all four statuses
- Verify:
  - `runtime-approved`, `reviewed-candidate`, and `deferred` entries count toward the broader 30-entry target
  - `rejected` entries remain inspectable but do not count toward the target

### T7. Repo-local verification fails if the broader reviewed catalog drops below 30 counted entries

- Type: integration
- Fixture:
  - broader reviewed source catalog
- Verify:
  - the verification step passes when counted entries are at least 30
  - the verification step fails when counted entries fall below 30

### T8. Runtime-manifest-only additions are not allowed

- Type: integration
- Fixture:
  - runtime manifest containing a source absent from the broader reviewed catalog
- Verify:
  - drift detection fails
  - the failure message or test assertion makes clear that runtime approval cannot outrun the broader reviewed catalog

### T9. Human-readable source documentation distinguishes broader reviewed entries from runtime-approved sources

- Type: integration or doc consistency test
- Fixture:
  - broader reviewed source catalog
  - human-readable companion documentation
- Verify:
  - a maintainer can inspect sources by bucket and status
  - the documentation clearly distinguishes broader reviewed entries from runtime-approved entries
  - the documentation does not imply that all counted catalog entries are enabled in daily collection

### T10. Optional inspection surface matches the broader reviewed catalog if added

- Type: integration
- Fixture:
  - optional CLI or browser inspection surface, if implemented
- Verify:
  - `uv run daily-insight sources` exposes the broader reviewed catalog without blurring the runtime boundary
  - `uv run daily-insight sources --bucket <bucket> --status <status>` can narrow the view by bucket and status
  - the source counts and status groupings agree with the broader reviewed catalog

### T11. Drift detection catches missing required fields and conflicting identity

- Type: integration
- Fixture:
  - broader reviewed source catalog
  - runtime-approved source manifest
  - human-readable companion documentation
- Verify:
  - missing required catalog fields fail verification
  - conflicting bucket or transport identity between catalog and manifest fails verification
  - the repository passes verification when all three surfaces agree

### T12. Historical run artifacts stay untouched when the broader reviewed catalog changes

- Type: integration
- Fixture:
  - pre-existing `inputs/YYYY-MM-DD/` and `outputs/YYYY-MM-DD/` artifacts
  - updated broader reviewed source catalog
- Verify:
  - historical input and output artifacts are not rewritten just because the broader reviewed catalog changes

### T13. Source status changes preserve review history

- Type: integration
- Fixture:
  - a source that changes from:
    - `reviewed-candidate` to `runtime-approved`
    - `runtime-approved` to `deferred`
    - `reviewed-candidate` to `rejected`
- Verify:
  - the new status is explicit
  - the reason remains inspectable
  - the broader reviewed catalog and runtime manifest remain consistent after the change

## Dedicated-Machine Validation

### T14. The repository can answer the broader source question from repo artifacts alone

- Type: end-to-end or maintainer smoke test
- Fixture:
  - cloned repository on the dedicated machine
- Verify:
  - a maintainer can inspect the broader reviewed source universe from the approved machine-readable and human-readable repository surfaces
  - a maintainer can distinguish the broader catalog from the smaller runtime-approved subset without reading implementation code

## What Not To Test

- live source freshness or collection success for all 30 reviewed entries unless they are promoted into runtime use
- digest ranking quality or synthesis behavior unrelated to the source-catalog contract
- arbitrary browsing results that are not reflected in the reviewed catalog
- internal class or module names unless they become part of the user-visible inspection contract

## Open Gaps

- none at the contract level; if the CLI output format becomes part of a browser or API surface later, add contract tests for that representation too.

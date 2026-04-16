# Browser Digest Specification

## Goal

Let a user read a published daily insight comfortably in a normal web browser through a stable local HTTP path or static file path, without changing the repository's canonical `digest.json` contract or introducing a dynamic web application.

Related plan: `docs/plans/2026-04-16-browser-readable-insight-delivery.md`

## Examples

### Example 1: Publish one reviewed digest into the browser site

Given:

- `outputs/2026-04-16/digest.json` exists and is schema-valid
- the maintainer has reviewed the digest and decided it may become the visible browser version
- the generated browser site root is `site/`

When the maintainer runs:

```bash
uv run daily-insight publish-site --source-root outputs --date 2026-04-16 --site-root site
```

Then:

- `site/2026-04-16/index.html` exists
- `site/latest/index.html` exists
- `site/index.html` exists
- `site/latest/index.html` renders the same digest date as `site/2026-04-16/index.html`
- the published browser page is derived from `outputs/2026-04-16/digest.json`, not from SQLite or live source collection

### Example 2: A later publish updates `latest` but preserves older pages

Given:

- `site/2026-04-15/index.html` already exists
- `site/latest/index.html` currently reflects `2026-04-15`
- `outputs/2026-04-16/digest.json` exists and is approved for publication

When the maintainer publishes `2026-04-16`

Then:

- `site/2026-04-15/index.html` remains readable
- `site/2026-04-16/index.html` is added
- `site/latest/index.html` now reflects `2026-04-16`
- `site/index.html` lists both dates in descending order

### Example 3: Degraded coverage stays visible in the browser page

Given:

- the published `digest.json` includes:
  - `source_summary.bucket_health.software-engineering = degraded-sparse-day`
  - `source_summary.bucket_counts.software-engineering = 0`
  - a matching degraded coverage note

When the maintainer renders or publishes the browser page

Then:

- the browser page visibly shows the degraded status
- the zero count is still visible
- the degraded coverage note is still visible
- the browser page does not hide the degraded bucket behind a polished layout

### Example 4: Failed publish does not replace the visible latest page

Given:

- `site/latest/index.html` already reflects a last-known-good published digest
- a new publish attempt fails while generating the next browser site output

When `daily-insight publish-site` exits with failure

Then:

- the previously visible `site/latest/index.html` remains intact
- readers do not see a half-written `latest` page
- a later successful publish can rebuild the browser site from canonical `outputs/YYYY-MM-DD/` artifacts

### Example 5: Local smoke-test serving is separate from durable serving

Given:

- `site/` already contains published browser artifacts

When a maintainer runs:

```bash
python -m http.server 8000 --directory site
```

Then:

- the browser pages can be smoke-tested locally
- that command is treated as validation only, not as the durable serving recommendation for the dedicated machine

## Inputs and Outputs

### Inputs

- canonical date-scoped digest artifacts under `outputs/YYYY-MM-DD/`
- specifically:
  - `digest.json`
  - optionally `digest.md`
- an explicit publish date
- a generated browser site root path

### Outputs

- a generated browser site root containing only intended browser-facing artifacts
- exact browser entrypoints:
  - `site/index.html`
  - `site/latest/index.html`
  - `site/YYYY-MM-DD/index.html`

## Invariants

- `digest.json` remains the canonical source of browser content.
- Browser publication MUST NOT require live source access, SQLite state reads, or Codex at page-view time.
- The generated browser site root MUST be separate from raw `outputs/`.
- `site/latest/index.html` is a published view, not an automatic side effect of every successful `run`.
- Historical published date pages remain addressable after newer dates are published.

## Requirements

### R1. Canonical Source

Browser-readable digest pages MUST be derived from `outputs/YYYY-MM-DD/digest.json`.

Browser rendering and publication MUST NOT create a second synthesis path, and MUST NOT depend on `inputs/`, `state/daily_insight.db`, or live collection data to display the page.

### R2. Generated Site Root

The browser surface MUST be published into a dedicated generated site root that is separate from raw `outputs/`.

The contract MUST use these exact path shapes inside that site root:

- `site/index.html`
- `site/latest/index.html`
- `site/YYYY-MM-DD/index.html`

The browser contract MAY add additional files under the site root, but readers MUST be able to use the three paths above without knowing internal implementation details.

### R3. Publication Boundary

The visible browser `latest` view MUST be updated only by an explicit publication step.

The normal `daily-insight run` command MAY continue to generate canonical digest artifacts and MAY generate date-scoped browser-ready files outside the published site root, but it MUST NOT silently update:

- `site/index.html`
- `site/latest/index.html`
- any other visible published browser entrypoint

The explicit publication command MUST be the step that promotes a reviewed digest into the visible browser site.

### R4. Date-Scoped Page Content

Each published date page MUST show, at minimum:

- the digest date
- the overview section
- the top items section
- the action-now section
- the watchlist section
- the source summary section

Each top item shown in the browser page MUST visibly preserve:

- bucket
- title
- source name
- source URL
- confidence
- team relevance
- why-it-matters text
- recommended action

### R5. Source Health Visibility

The browser page MUST preserve `source_summary` visibility rather than flattening or hiding it.

At minimum, the page MUST visibly surface:

- total items seen
- top items surfaced
- source failures
- bucket counts
- bucket health
- degraded coverage notes

A bucket with zero items or degraded health MUST remain visibly explicit in the browser page.

When the digest surfaces multiple top items from the same source entry, the browser page MUST make clear that `source_summary` reflects collected source coverage rather than the expanded top-item count.

### R6. Archive and Latest Behavior

The browser site MUST provide:

- a date-specific page at `site/YYYY-MM-DD/index.html`
- an archive landing page at `site/index.html`
- a stable latest page at `site/latest/index.html`

The archive landing page MUST list published dates in descending order.

The latest page MUST clearly identify which date it represents.

Whether a degraded-but-successful digest may become `latest` MUST be an explicit policy decision in this contract; it MUST NOT be left implicit in implementation.

For this initial version, degraded-but-successful digests MAY become `latest` after explicit publication, because degraded coverage is already part of the visible contract and does not mean the digest is invalid.

### R7. Semantic HTML and Readability

The browser page MUST be readable without JavaScript.

The browser page MUST use semantic HTML sufficient to expose:

- a document title containing the digest date
- a single primary page heading
- a main content region
- section headings for the major digest sections

The page MUST include a viewport meta tag and remain readable on narrow mobile widths without horizontal scrolling as the default reading experience.

The page MUST NOT depend on external network-hosted assets.

### R8. Asset Stability

The initial browser contract SHOULD prefer self-contained HTML so historical published pages do not silently change when later styling changes are introduced.

If future versions introduce shared assets, those assets MUST be versioned in a way that does not rewrite the appearance of already-published historical pages unintentionally.

### R9. Atomic Publication

A publication attempt MUST stage its generated output before promoting it into the visible site root.

If publication fails, the previously visible:

- `site/index.html`
- `site/latest/index.html`
- already-published date pages

MUST remain intact and readable.

Readers MUST NOT be exposed to a half-written `latest` page or partially generated archive page.

### R10. Compatibility and Preservation

Publishing a new date MUST NOT rewrite canonical historical `outputs/YYYY-MM-DD/digest.json` artifacts.

Publishing a new date SHOULD preserve already-published historical date pages, except for archive navigation surfaces that are expected to change when a new page is added.

The browser page MAY link to raw digest artifacts only if those links stay inside the generated site root. The initial version does not require such links.

### R11. Error Handling

If the requested date is missing a canonical `digest.json`, publication MUST fail clearly and MUST NOT change the visible browser site.

If the digest JSON is unreadable or missing required browser-contract fields, HTML rendering or publication MUST fail clearly rather than generating a misleading partial page.

### R12. Observability

The published browser page MUST make these states inspectable to a reader without opening raw JSON:

- which digest date is being viewed
- whether the digest was degraded in any bucket
- whether any source failures or sparse-day notes were recorded

The publication workflow MUST make it possible to verify, over local HTTP, that:

- `latest` resolves to the expected published date
- the archive includes the expected dates
- degraded coverage text remains visible for degraded dates

## Edge Cases

- A digest with valid content but degraded source coverage may still be published as `latest` if the maintainer explicitly chooses to publish it.
- A digest with zero items in one or more buckets still requires a readable browser page; the page must preserve those zero counts and degraded notes.
- Re-publishing an already published date should be idempotent and should not break archive navigation.
- A later publish may change `site/index.html` and `site/latest/index.html`, but it should not orphan older date pages.
- Browser-readable output must remain understandable even when a digest has only one or two top items for the date.

## Non-goals

- building a live application server for reading digests
- exposing SQLite, `inputs/`, or local source config to browser readers
- adding comments, authentication, user accounts, or write operations
- requiring JavaScript for baseline reading functionality
- turning the browser page into a different ranking or synthesis path than the canonical digest JSON

## Acceptance Criteria

- A maintainer can generate or publish a browser-readable page from canonical digest JSON without rerunning collection or synthesis.
- A browser user can open a stable latest path and a stable date-specific path.
- The browser page preserves degraded coverage visibility instead of hiding it.
- A failed publish leaves the previously visible site intact.

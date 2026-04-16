# Source inventory

Reviewed on 2026-04-16 after the Milestone 2 viability audit, Milestone 4 runtime-support work, and Milestone 6 dedicated-machine validation across `2026-04-10`, `2026-04-15`, and `2026-04-16`. This file is the human-reviewed source allowlist for the daily digest.

The source-sufficiency contract that governs what counts toward healthy coverage, degraded coverage, and inventory gaps is defined in `specs/source-sufficiency.md`.
The authoritative reviewed source manifest lives in `configs/source-manifest.json`, and the initial live viability review is recorded in `docs/source-viability-audit.md`.

The versioned example config in `configs/sources.example.json` keeps `example.com` URLs so `--dry-run` stays placeholder-safe. Operator-managed `configs/sources.local.json` should reuse the same source names, buckets, required flags, and failure policies while substituting the real feed URLs below.
The example and local config should include only manifest-approved runtime-supported entries. As of Milestone 4, that now includes all seven approved sources, including the JSON-backed `cisa-kev-catalog`.

## Bucket coverage

| Bucket | Source | Role | Transport | URL | Implemented | Counts now | Required | Failure policy | Max items/run | Expected signal |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| software-engineering | `python-insider` | `primary` | `rss` | `https://blog.python.org/rss.xml` | yes | yes | yes | `fail` | 10 | CPython releases, deprecations, packaging/runtime changes that can require stack action |
| software-engineering | `github-changelog` | `backup` | `rss` | `https://github.blog/changelog/feed/` | yes | yes | no | `warn` | 10 | workflow, Actions, dependency, and platform changes that usually belong in the watchlist |
| security | `google-online-security-blog` | `primary` | `rss` | `https://googleonlinesecurity.blogspot.com/atom.xml` | yes | yes | yes | `warn` | 10 | defensive research, memory-safety work, supply-chain security, and web/browser hardening guidance |
| security | `cisa-kev-catalog` | `backup` | `json` | `https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json` | yes | yes | no | `warn` | 10 | action-now exploited vulnerabilities collected from the dateAdded-scoped KEV JSON delta |
| ai-for-security | `google-threat-intelligence` | `primary` | `rss` | `https://feeds.feedburner.com/threatintelligence/pvexyqv7v0v` | yes | yes | no | `warn` | 5 | adversarial AI use, defender workflows, AI-assisted intrusion analysis, and GTIG AI threat tracker updates |
| security-for-ai | `openai-news` | `primary` | `rss` | `https://openai.com/news/rss.xml` | yes | yes | no | `warn` | 5 | model safety, security, preparedness, governance, and trust updates that affect AI risk posture |
| security-for-ai | `deepmind-blog` | `backup` | `rss` | `https://deepmind.google/blog/rss.xml` | yes | yes | no | `warn` | 5 | backup source for safety, governance, and security-adjacent model-provider updates |

## Review rules

- Keep each item in exactly one primary bucket, even if the same source could plausibly fit multiple categories.
- Prefer action-now items only when the source contains explicit evidence, shipped changes, or active exploitation.
- Treat `warn` sources as degradations that must surface in `source_summary`, not as silent skips.
- Treat `fail` sources as blockers for a fully trusted daily run when the collector for that source is implemented.
- Do not add new live feeds to `configs/sources.local.json` until they are documented here with bucket, rationale, and failure handling.

## Review cadence

- Review the manifest and this inventory at least once per month, even if the daily runs are healthy.
- Re-review any source immediately after 3 consecutive `degraded-source-failure` days or 5 degraded days within a rolling 14-day window.
- If a source stays low-signal for two scheduled monthly reviews in a row, downgrade it to `backup` or remove it instead of leaving it approved by inertia.
- If a bucket keeps degrading because its only `primary` source is thin, approve a new backup or document why the bucket is intentionally single-source during the next review.
- Record source additions, retirements, and role changes in both `configs/source-manifest.json` and this file on the same day they are approved.

## Notes by source

- `python-insider`: use this as the default software-engineering action source because it most directly affects the Python 3.12 runtime this repository targets.
- `github-changelog`: review only items relevant to GitHub-hosted development workflow, Actions, dependency management, or supply-chain/security controls; ignore unrelated product launches.
- `google-online-security-blog`: this is the primary integrated security feed because it is official, high-signal, and machine-readable.
- `cisa-kev-catalog`: the approved machine-readable endpoint is the JSON feed, not the manual catalog page. The runtime now filters KEV entries by `dateAdded` so the source contributes daily deltas instead of backlog noise.
- `google-threat-intelligence`: focus the AI-for-security bucket on posts with explicit AI misuse or AI-enabled defender implications instead of general threat reporting.
- `openai-news`: prioritize safety, security, preparedness, trust, and governance updates; skip general product-marketing stories that do not change security posture. The runtime now uses a browser-like user-agent so this feed can be collected consistently.
- `deepmind-blog`: use this as the current approved backup for `security-for-ai`; it is broader than a dedicated safety feed, so later filtering should prefer safety, governance, and manipulation-risk posts over general model launches.

# Source inventory

Approved on 2026-04-16 for Milestone 3. This file is the human-reviewed source allowlist for the daily digest.

The versioned example config in `configs/sources.example.json` keeps `example.com` URLs so `--dry-run` stays placeholder-safe. Operator-managed `configs/sources.local.json` should reuse the same source names, buckets, and failure policies while substituting the real feed URLs below.

## Bucket coverage

| Bucket | Source | Transport | URL | Required | Failure policy | Max items/run | Expected signal |
| --- | --- | --- | --- | --- | --- | --- | --- |
| software-engineering | `python-insider` | `rss` | `https://blog.python.org/rss.xml` | yes | `fail` | 10 | CPython releases, deprecations, packaging/runtime changes that can require stack action |
| software-engineering | `github-changelog` | `rss` | `https://github.blog/changelog/feed/` | no | `warn` | 10 | workflow, Actions, dependency, and platform changes that usually belong in the watchlist |
| security | `google-online-security-blog` | `rss` | `https://googleonlinesecurity.blogspot.com/atom.xml` | yes | `warn` | 10 | defensive research, memory-safety work, supply-chain security, and web/browser hardening guidance |
| security | `cisa-kev-catalog` | `manual-web` | `https://www.cisa.gov/known-exploited-vulnerabilities-catalog` | yes | `warn` | n/a | action-now exploited vulnerabilities; review manually until a stable machine-readable collector is approved |
| ai-for-security | `google-threat-intelligence` | `rss` | `https://feeds.feedburner.com/threatintelligence/pvexyqv7v0v` | no | `warn` | 5 | adversarial AI use, defender workflows, AI-assisted intrusion analysis, and GTIG AI threat tracker updates |
| security-for-ai | `openai-news` | `rss` | `https://openai.com/news/rss.xml` | no | `warn` | 5 | model safety, security, preparedness, governance, and trust updates that affect AI risk posture |

## Review rules

- Keep each item in exactly one primary bucket, even if the same source could plausibly fit multiple categories.
- Prefer action-now items only when the source contains explicit evidence, shipped changes, or active exploitation.
- Treat `warn` sources as degradations that must surface in `source_summary`, not as silent skips.
- Treat `fail` sources as blockers for a fully trusted daily run when the collector for that source is implemented.
- Do not add new live feeds to `configs/sources.local.json` until they are documented here with bucket, rationale, and failure handling.

## Notes by source

- `python-insider`: use this as the default software-engineering action source because it most directly affects the Python 3.12 runtime this repository targets.
- `github-changelog`: review only items relevant to GitHub-hosted development workflow, Actions, dependency management, or supply-chain/security controls; ignore unrelated product launches.
- `google-online-security-blog`: this is the primary integrated security feed because it is official, high-signal, and machine-readable.
- `cisa-kev-catalog`: keep it in the approved inventory even before collector support exists because exploited-vulnerability evidence is too important to treat as an optional future idea.
- `google-threat-intelligence`: focus the AI-for-security bucket on posts with explicit AI misuse or AI-enabled defender implications instead of general threat reporting.
- `openai-news`: prioritize safety, security, preparedness, trust, and governance updates; skip general product-marketing stories that do not change security posture.

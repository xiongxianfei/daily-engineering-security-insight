# Source Viability Audit

2026-04-16 live viability review for approved and candidate sources before manifest/config/runtime alignment.

## Probe summary

| Source | Bucket | Decision | Live probe result | Review notes |
| --- | --- | --- | --- | --- |
| `python-insider` | software-engineering | approve as `primary` | `200 application/xml` | High-signal CPython runtime feed. |
| `github-changelog` | software-engineering | approve as `backup` | `200 application/rss+xml` | Viable backup for GitHub workflow, Actions, code scanning, SBOM, and supply-chain changes. |
| `google-online-security-blog` | security | approve as `primary` | `200 text/xml` | Current primary security feed. |
| `cisa-kev-catalog` | security | keep approved as `backup`, but non-counting until implementation | `200 application/json` and `200 text/csv` | Replace the old manual-web assumption with the machine-readable JSON endpoint; requires collector and delta handling before it counts. |
| `google-threat-intelligence` | ai-for-security | approve as `primary` | `200 text/xml` | Current primary AI-for-security feed. |
| `openai-news` | security-for-ai | keep approved as `primary`, but non-counting until runtime fix | `403` with default urllib; `200 text/xml` with browser-like user-agent | Feed is live, but current runtime access pattern is not sufficient. |
| `deepmind-blog` | security-for-ai | approve as `backup` | `200 text/xml` | Viable official backup feed with mixed but relevant safety/governance/security-adjacent posts. |
| `anthropic-news-rss` | security-for-ai | reject for now | `404` | No working RSS endpoint found during the 2026-04-16 audit. |
| `anthropic-sitemap` | security-for-ai | reject for now | `200 application/xml` | Sitemap is not a reviewed feed contract for deterministic daily collection. |
| `deepmind-discover-feed` | security-for-ai | reject for now | `404` | Wrong endpoint; keep the working blog feed instead. |

## Bucket decisions

### software-engineering

- `python-insider` is the approved `primary`.
- `github-changelog` is the approved `backup`.
- Bucket disposition after this audit: inventory-sufficient once config alignment lands.

### security

- `google-online-security-blog` is the approved `primary`.
- `cisa-kev-catalog` stays approved as the desired `backup`, but it does not count yet because collector and delta support are still missing.
- Bucket disposition after this audit: not yet fully sufficient for exploited-vulnerability coverage.

### ai-for-security

- `google-threat-intelligence` is the approved `primary`.
- no approved backup yet
- Approved rationale: the audit did not find another official machine-readable source that is both high-signal and clearly aligned to the AI-for-security bucket without broadening into generic threat reporting.
- Bucket disposition after this audit: acceptable with explicit no-backup rationale, pending future review.

### security-for-ai

- `openai-news` remains the desired `primary`, but it does not count yet because the current runtime access pattern gets `HTTP 403: Forbidden`.
- `deepmind-blog` is the approved `backup` and counts toward sufficiency.
- Bucket disposition after this audit: still not fully sufficient because the bucket lacks a counted `primary` source today.

## Follow-up decisions recorded from this audit

- third dedicated-machine validation date: 2026-04-10
- keep `openai-news` in the approved program, but treat it as blocked by runtime behavior rather than feed disappearance
- switch the approved KEV machine-readable URL to the JSON endpoint and defer counting it until delta handling is implemented

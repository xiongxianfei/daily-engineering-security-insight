# Source Viability Audit

2026-04-16 live viability review after the Milestone 2 catalog expansion. This audit now covers the full reviewed source catalog, not only the smaller runtime-approved manifest.

The purpose of this audit is to separate:

- sources that are already runtime-approved
- reviewed candidates that look technically viable enough to consider later
- deferred entries that remain worth documenting but are not ready for deterministic runtime use

## High-level decision

No immediate promotions into the runtime manifest.

Why:

- the current runtime manifest already provides a stable ten-source deterministic program after the Milestone 4 promotions
- several additional feeds are technically live, but they still need filtering or prioritization decisions before they deserve runtime approval
- `ai-for-security` still has no feed-ready reviewed-candidate addition that is clearly strong enough to promote without broadening into product or generic threat-marketing material

Milestone 4 implementation outcome:

- `django-blog` was promoted to the runtime manifest
- `cisa-advisories` was promoted to the runtime manifest
- `github-security-blog` was promoted to the runtime manifest
- `cloudflare-security-blog`, `google-ai-blog`, and `huggingface-blog` remain reviewed candidates, not runtime-approved sources

## Promotion shortlist for Milestone 4

These are the reviewed candidates most likely to justify later runtime work:

- `django-blog`
- `cisa-advisories`
- `github-security-blog`
- `cloudflare-security-blog`
- `google-ai-blog`
- `huggingface-blog`

They are shortlist items, not runtime approvals.

## Probe summary by bucket

### software-engineering

| Source | Catalog status after audit | Live probe result | Decision | Review notes |
| --- | --- | --- | --- | --- |
| `python-insider` | `runtime-approved` | `200 application/xml` | keep runtime-approved | High-signal CPython runtime feed already in stable runtime use. |
| `github-changelog` | `runtime-approved` | `200 application/rss+xml` | keep runtime-approved | Viable backup for GitHub workflow, Actions, code scanning, SBOM, and supply-chain changes. |
| `django-blog` | `runtime-approved` | `200 application/rss+xml` | promoted in Milestone 4 | Official Django feed; promoted as a low-risk Python-adjacent runtime addition. |
| `nodejs-blog` | `reviewed-candidate` | `200 application/xml` | keep reviewed-candidate | Official Node.js feed; viable and machine-readable, but not obviously more relevant than the current Python-centric runtime stack. |
| `rust-blog` | `reviewed-candidate` | `200 application/xml` | keep reviewed-candidate | Official Rust feed; technically viable and high-signal, but would broaden runtime scope materially. |
| `go-blog` | `reviewed-candidate` | `200 application/atom+xml` | keep reviewed-candidate | Official Go feed; viable, but would require transport/selection decisions before runtime adoption. |
| `typescript-blog` | `reviewed-candidate` | `200 application/rss+xml` | keep reviewed-candidate | Official TypeScript feed; strong candidate for broader dev-platform visibility, but not yet justified for runtime promotion. |
| `kubernetes-blog` | `reviewed-candidate` | `200 application/xml` | keep reviewed-candidate | Official Kubernetes feed; viable, but broader than the current runtime scope and likely noisy without tighter filtering. |
| `ruby-news` | `reviewed-candidate` | `200 application/rss+xml` | keep reviewed-candidate | Official Ruby feed; technically viable, but lower priority for current runtime needs. |
| `dotnet-blog` | `reviewed-candidate` | `200 application/rss+xml` | keep reviewed-candidate | Official .NET engineering feed; viable and useful, but not yet prioritized for runtime collection. |
| `docker-blog` | `reviewed-candidate` | `200 application/rss+xml` | keep reviewed-candidate | Official Docker feed; viable but mixed-signal and likely needs stronger filtering before runtime use. |
| `gitlab-blog` | `reviewed-candidate` | `200 application/xml` | keep reviewed-candidate | Official GitLab feed; technically viable, but runtime promotion would broaden the platform surface without a strong current need. |

### security

| Source | Catalog status after audit | Live probe result | Decision | Review notes |
| --- | --- | --- | --- | --- |
| `google-online-security-blog` | `runtime-approved` | `200 text/xml` | keep runtime-approved | Current primary security source and still strong enough to remain the default integrated security feed. |
| `cisa-kev-catalog` | `runtime-approved` | `200 application/json` | keep runtime-approved | Current backup action-now source with implemented dateAdded-scoped delta handling. |
| `cisa-advisories` | `runtime-approved` | `200 application/rss+xml` | promoted in Milestone 4 | Official CISA advisory feed promoted as a low-risk security backup. |
| `github-security-blog` | `runtime-approved` | `200 application/rss+xml` | promoted in Milestone 4 | Official GitHub security feed promoted as a low-risk developer-adjacent security backup. |
| `mozilla-security-blog` | `deferred` | `403 Forbidden` | keep deferred | The feed exists, but the Milestone 3 probe path hit access friction; defer until collection behavior is better understood. |
| `chrome-releases` | `reviewed-candidate` | `200 text/xml` via FeedBurner redirect | keep reviewed-candidate | Live and potentially high-signal for browser patch awareness, but release-channel noise still needs policy review. |
| `aws-security-bulletins` | `reviewed-candidate` | `200 application/rss+xml` | keep reviewed-candidate | Official cloud-provider security feed; viable, but promotion is optional rather than urgent. |
| `cloudflare-security-blog` | `reviewed-candidate` | `200 application/xml` | keep reviewed-candidate | Strong web and internet-infrastructure security candidate with live machine-readable access. |
| `redhat-security-data` | `reviewed-candidate` | `200 application/json` | keep reviewed-candidate | Valuable enterprise Linux security data source, but runtime use would need explicit API-oriented collection policy. |

### ai-for-security

| Source | Catalog status after audit | Live probe result | Decision | Review notes |
| --- | --- | --- | --- | --- |
| `google-threat-intelligence` | `runtime-approved` | `200 text/xml` | keep runtime-approved | Still the clearest official machine-readable AI-for-security source in the current program. |
| `microsoft-security-copilot` | `deferred` | `403 Forbidden` | keep deferred | Official product source, but not machine-readable and access-constrained under the probe path. |
| `crowdstrike-charlotte-ai` | `deferred` | `200 text/html` | keep deferred | Official page and useful for catalog breadth, but not suitable for deterministic runtime collection today. |
| `google-cloud-security-ai` | `deferred` | `200 text/html` | keep deferred | Official source, but still a reviewed HTML product page rather than a feed. |
| `wiz-blog-main` | `deferred` | `200 text/html`; guessed RSS endpoint returned `404` | keep deferred | Worth documenting, but the lack of a working feed keeps it out of runtime consideration for now. |

ai-for-security still has no feed-ready reviewed-candidate addition.

The bucket remains acceptable in the broader catalog, but its runtime expansion path is still weak compared with the other three buckets.

### security-for-ai

| Source | Catalog status after audit | Live probe result | Decision | Review notes |
| --- | --- | --- | --- | --- |
| `openai-news` | `runtime-approved` | `200 text/xml` with browser-like user-agent | keep runtime-approved | Primary runtime source remains valid after the user-agent collection fix. |
| `deepmind-blog` | `runtime-approved` | `200 text/xml` | keep runtime-approved | Backup runtime source remains viable and high-signal enough for the current program. |
| `anthropic-news` | `deferred` | `200 text/html` | keep deferred | Official news page is live, but there is still no approved deterministic feed contract for runtime use. |
| `google-ai-blog` | `reviewed-candidate` | `200 application/xml` | keep reviewed-candidate | Live and machine-readable, but broader AI/news scope means runtime promotion would require stronger filtering rules. |
| `huggingface-blog` | `reviewed-candidate` | `200 application/rss+xml` | keep reviewed-candidate | Official feed with relevant safety and evaluation material, but likely mixed-signal without topic filtering. |
| `nist-ai-rmf` | `deferred` | `200 text/html` | keep deferred | Important standards source for AI governance, but currently a reviewed page rather than a feed. |
| `owasp-genai` | `deferred` | `200 text/html` | keep deferred | Valuable guidance source for GenAI application risk, but not yet a deterministic feed. |
| `mitre-atlas` | `deferred` | `200 text/html` | keep deferred | High-value AI threat reference source, but still a reviewed HTML surface rather than a collection-ready feed. |

## Bucket decisions

### software-engineering

- Runtime posture: `python-insider`, `github-changelog`, and `django-blog`.
- Broader catalog outcome: strong bench of viable reviewed candidates exists.
- Promotion view: `django-blog` is now the cleanest implemented Python-adjacent runtime expansion; other software candidates remain reviewed-candidate only.

### security

- Runtime posture: `google-online-security-blog`, `cisa-kev-catalog`, `cisa-advisories`, and `github-security-blog`.
- Broader catalog outcome: this is the healthiest expansion area after software-engineering.
- Promotion view: `cisa-advisories` and `github-security-blog` are now implemented runtime expansions; `cloudflare-security-blog` remains the clearest next candidate.

### ai-for-security

- Runtime posture: keep `google-threat-intelligence` as the only runtime-approved source for now.
- Broader catalog outcome: reviewed breadth improved, but mostly through deferred official HTML/product sources.
- Promotion view: no immediate promotion justified; keep the explicit no approved backup yet note from the runtime inventory.
- no approved backup yet

### security-for-ai

- Runtime posture: keep `openai-news` + `deepmind-blog` unchanged.
- Broader catalog outcome: there are now viable reviewed candidates beyond the runtime pair.
- Promotion view: `google-ai-blog` and `huggingface-blog` are the most plausible future candidates, but both would need topic filtering before runtime use.

## Follow-up decisions recorded from this audit

- No immediate runtime manifest changes land in Milestone 3.
- Promotion decisions move to Milestone 4, where runtime additions can be implemented in small reviewed slices.
- third dedicated-machine validation date: 2026-04-10
- keep the runtime manifest focused on the ten-source stable subset until a candidate source materially improves coverage without introducing obvious noise
- preserve the broader reviewed catalog as the source of truth for what the project uses or considers at a wider level

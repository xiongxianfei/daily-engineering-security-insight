# Source catalog

Reviewed on 2026-04-16. This file is the human-readable companion to [configs/source-catalog.json](/home/xiongxianfei/data/20260415-daily-engineering-security-insight/configs/source-catalog.json).

Quick inspection command:
```bash
uv run daily-insight sources
uv run daily-insight sources --bucket security --status runtime-approved
```

This is the **broader reviewed source catalog**, not the runtime allowlist. The **runtime-approved subset** still lives in [configs/source-manifest.json](/home/xiongxianfei/data/20260415-daily-engineering-security-insight/configs/source-manifest.json) and is explained in [docs/source-inventory.md](/home/xiongxianfei/data/20260415-daily-engineering-security-insight/docs/source-inventory.md).

Counted toward the 30-entry catalog target:
- `runtime-approved`
- `reviewed-candidate`
- `deferred`

Not counted toward the 30-entry target:
- `rejected`

Current reviewed catalog count: `34`

Status summary:
- `runtime-approved`: `10`
- `reviewed-candidate`: `15`
- `deferred`: `9`
- `rejected`: `0`

Bucket summary:
- `software-engineering`: `12`
- `security`: `9`
- `ai-for-security`: `5`
- `security-for-ai`: `8`

## Software engineering

| Source | Status | Transport | Machine-readable | URL | Expected signal | Review notes |
| --- | --- | --- | --- | --- | --- | --- |
| `python-insider` | `runtime-approved` | `rss` | yes | `https://blog.python.org/rss.xml` | CPython runtime, packaging, deprecation, and release signals that can require stack action. | Current primary runtime-approved software-engineering source. |
| `github-changelog` | `runtime-approved` | `rss` | yes | `https://github.blog/changelog/feed/` | GitHub platform, Actions, code scanning, dependency, and workflow changes. | Current backup runtime-approved software-engineering source. |
| `django-blog` | `runtime-approved` | `rss` | yes | `https://www.djangoproject.com/rss/weblog/` | Django release, security, and framework lifecycle updates relevant to Python web stacks. | Promoted in Milestone 4 as a low-risk runtime-approved Python-adjacent framework source. |
| `nodejs-blog` | `reviewed-candidate` | `rss` | yes | `https://nodejs.org/en/feed/blog.xml` | Node.js runtime, release, and ecosystem updates that can affect build and service tooling. | Official runtime feed; good candidate if broader language-runtime coverage is needed. |
| `rust-blog` | `reviewed-candidate` | `rss` | yes | `https://blog.rust-lang.org/feed.xml` | Rust release, tooling, and language evolution updates with build-system impact. | Official language feed; high-signal but not yet approved for runtime collection. |
| `go-blog` | `reviewed-candidate` | `atom` | yes | `https://go.dev/blog/feed.atom` | Go language, tooling, and platform updates that can affect backend services and CI. | Official feed; broad but still relevant to runtime and toolchain monitoring. |
| `typescript-blog` | `reviewed-candidate` | `rss` | yes | `https://devblogs.microsoft.com/typescript/feed/` | TypeScript release and compiler changes that affect frontend and tooling workflows. | Official language-team feed; useful candidate for broader developer-platform coverage. |
| `kubernetes-blog` | `reviewed-candidate` | `rss` | yes | `https://kubernetes.io/feed.xml` | Kubernetes release, API, and platform operations updates relevant to infrastructure engineering. | Official project feed; broad but high-signal for teams running container platforms. |
| `ruby-news` | `reviewed-candidate` | `rss` | yes | `https://www.ruby-lang.org/en/feeds/news.rss` | Ruby release and language news for teams with Ruby services or automation. | Official language feed; candidate for broader runtime visibility. |
| `dotnet-blog` | `reviewed-candidate` | `rss` | yes | `https://devblogs.microsoft.com/dotnet/feed/` | .NET runtime, SDK, and framework updates for application and build environments. | Official engineering feed; likely useful if the software bucket expands beyond Python-centric sources. |
| `docker-blog` | `reviewed-candidate` | `rss` | yes | `https://www.docker.com/feed/` | Container tooling, desktop, build, and registry workflow updates. | Official vendor feed; mixed-signal but relevant to developer platform operations. |
| `gitlab-blog` | `reviewed-candidate` | `atom` | yes | `https://about.gitlab.com/atom.xml` | GitLab workflow, CI/CD, and developer-platform changes with operational impact. | Official feed; candidate source for teams that use or monitor GitLab-driven workflows. |

## Security

| Source | Status | Transport | Machine-readable | URL | Expected signal | Review notes |
| --- | --- | --- | --- | --- | --- | --- |
| `google-online-security-blog` | `runtime-approved` | `rss` | yes | `https://googleonlinesecurity.blogspot.com/atom.xml` | Defensive research, memory-safety, supply-chain, and browser-hardening guidance. | Current primary runtime-approved security source. |
| `cisa-kev-catalog` | `runtime-approved` | `json` | yes | `https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json` | Known exploited vulnerability deltas for action-now prioritization. | Current backup runtime-approved security source with dateAdded-scoped delta handling. |
| `cisa-advisories` | `runtime-approved` | `rss` | yes | `https://www.cisa.gov/cybersecurity-advisories/all.xml` | Official CISA advisories and alerting updates beyond KEV-only exploited-vulnerability scope. | Promoted in Milestone 4 as a runtime-approved official advisory feed that broadens security signal. |
| `github-security-blog` | `runtime-approved` | `rss` | yes | `https://github.blog/security/feed/` | Supply-chain, code scanning, and application-security research from GitHub's security organization. | Promoted in Milestone 4 as a runtime-approved developer-adjacent security source. |
| `mozilla-security-blog` | `deferred` | `rss` | yes | `https://blog.mozilla.org/security/feed/` | Browser and web-platform security updates from Mozilla. | Feed exists but returned `HTTP 403` under the basic Milestone 2 probe path; keep documented as deferred until viability handling is reviewed. |
| `chrome-releases` | `reviewed-candidate` | `rss` | yes | `https://chromereleases.googleblog.com/atom.xml` | Chrome release and channel changes that can carry urgent browser-security relevance. | Feed redirects through FeedBurner but is live and potentially high-signal for browser patch tracking. |
| `aws-security-bulletins` | `reviewed-candidate` | `rss` | yes | `https://aws.amazon.com/security/security-bulletins/rss/feed/` | AWS security bulletins affecting cloud workloads and managed-service risk posture. | Official provider feed; useful candidate if cloud-provider security coverage is expanded. |
| `cloudflare-security-blog` | `reviewed-candidate` | `rss` | yes | `https://blog.cloudflare.com/tag/security/rss/` | Cloudflare's security research and edge/web defense updates. | Official tag feed; good candidate for web and internet infrastructure security signal. |
| `redhat-security-data` | `reviewed-candidate` | `api` | yes | `https://access.redhat.com/hydra/rest/securitydata/cve.json` | Machine-readable Red Hat security and CVE data relevant to enterprise Linux environments. | API-style endpoint rather than feed; strong candidate if API collectors are expanded further. |

## AI for security

| Source | Status | Transport | Machine-readable | URL | Expected signal | Review notes |
| --- | --- | --- | --- | --- | --- | --- |
| `google-threat-intelligence` | `runtime-approved` | `rss` | yes | `https://feeds.feedburner.com/threatintelligence/pvexyqv7v0v` | Adversarial AI use, defender workflows, and AI-enabled threat intelligence. | Current primary runtime-approved AI-for-security source. |
| `microsoft-security-copilot` | `deferred` | `html` | no | `https://www.microsoft.com/en-us/security/business/ai-machine-learning/microsoft-security-copilot` | Product and workflow material about AI-assisted defensive operations and analyst productivity. | Official source of record for Microsoft's security-assistant product, but not a feed and access-constrained in the basic probe path. |
| `crowdstrike-charlotte-ai` | `deferred` | `html` | no | `https://www.crowdstrike.com/en-us/platform/charlotte-ai/` | Official vendor material about AI-guided security operations and investigation workflows. | Stable product page, but not yet a machine-readable candidate for deterministic collection. |
| `google-cloud-security-ai` | `deferred` | `html` | no | `https://cloud.google.com/security/ai` | Official Google Cloud Security material about AI-enabled defense and security tooling. | Useful reviewed source for AI-for-security direction, but currently a product page rather than a deterministic feed. |
| `wiz-blog-main` | `deferred` | `html` | no | `https://www.wiz.io/blog` | Cloud-security research and AI-enabled remediation narratives from Wiz. | Main blog is live, but the guessed RSS endpoint returned `404`; keep reviewed and deferred pending better machine-readable access. |

## Security for AI

| Source | Status | Transport | Machine-readable | URL | Expected signal | Review notes |
| --- | --- | --- | --- | --- | --- | --- |
| `openai-news` | `runtime-approved` | `rss` | yes | `https://openai.com/news/rss.xml` | OpenAI safety, preparedness, trust, and governance updates affecting AI risk posture. | Current primary runtime-approved security-for-AI source. |
| `deepmind-blog` | `runtime-approved` | `rss` | yes | `https://deepmind.google/blog/rss.xml` | Model-provider safety, governance, and security-adjacent AI updates. | Current backup runtime-approved security-for-AI source. |
| `anthropic-news` | `deferred` | `html` | no | `https://www.anthropic.com/news` | Anthropic safety, governance, and model-program updates relevant to AI security posture. | News page is live, but prior RSS endpoint assumptions were wrong; keep as deferred until a deterministic collection path is approved. |
| `google-ai-blog` | `reviewed-candidate` | `rss` | yes | `https://blog.google/innovation-and-ai/technology/ai/rss/` | Google AI updates that can include safety, policy, and governance signals relevant to AI security. | Live machine-readable feed with broader AI scope; would need filtering if promoted into runtime use. |
| `huggingface-blog` | `reviewed-candidate` | `rss` | yes | `https://huggingface.co/blog/feed.xml` | Open model, evaluation, safety, and governance updates relevant to AI ecosystem risk. | Live official feed; broad and mixed-signal, but a plausible reviewed candidate. |
| `nist-ai-rmf` | `deferred` | `html` | no | `https://www.nist.gov/itl/ai-risk-management-framework` | Standards and governance guidance for AI risk management and control expectations. | Important standards source for security-for-AI reasoning, but currently tracked as a reviewed HTML page rather than a feed. |
| `owasp-genai` | `deferred` | `html` | no | `https://genai.owasp.org/` | OWASP guidance on GenAI and LLM risk patterns such as prompt injection and insecure design. | Useful governance and application-security reference source, but not a deterministic feed today. |
| `mitre-atlas` | `deferred` | `html` | no | `https://atlas.mitre.org/` | MITRE ATLAS threat knowledge and adversarial-AI technique mapping for AI security work. | High-value reference source for security-for-AI, but currently a reviewed HTML surface rather than a feed. |

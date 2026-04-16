# daily-engineering-security-insight

A Codex CLI-oriented repository for generating a daily insight brief across four buckets:

- software engineering
- security
- AI for Security
- Security for AI

This repository is designed for a dedicated Codex machine that runs a deterministic collection step first, then asks Codex to synthesize the normalized input into a structured daily digest.

## Why this repo exists

The goal is to make daily insight generation repeatable, reviewable, and safe:

- freeze inputs before synthesis
- keep Codex focused on analysis, ranking, and explanation
- produce both machine-readable JSON and human-readable Markdown
- keep the contract in specs and the operating rules in `AGENTS.md`

## Repository layout

```text
.
├── AGENTS.md
├── .codex/PLANS.md
├── .agents/skills/
├── .github/
├── .python-version
├── collectors/
├── configs/
├── daily_insight/
├── docs/
│   ├── plan.md
│   ├── roadmap.md
│   ├── workflows.md
│   └── plans/
├── examples/
├── ops/
│   └── systemd/
├── outputs/
├── inputs/
├── prompts/
├── pyproject.toml
├── schemas/
├── scripts/
├── specs/
└── tests/
```

## Quick start

1. Read `docs/source-inventory.md`, `docs/workflows.md`, and `docs/codex-machine-setup.md`.
2. Install dependencies:
   ```bash
   uv sync --dev
   ```
3. Review the CLI surface and repo-local checks:
   ```bash
   uv run daily-insight --help
   uv run daily-insight collect --dry-run --config configs/sources.example.json
   uv run daily-insight source-health --date 2026-04-15 --state-db state/daily_insight.db
   bash scripts/ci.sh
   ```
4. Create the operator-managed live source config:
   ```bash
   cp configs/sources.example.json configs/sources.local.json
   ```
5. Derive `configs/sources.local.json` from the reviewed manifest:
   - keep the same source names, buckets, required flags, and failure policies recorded in `configs/source-manifest.json`
   - replace only the placeholder URLs with the approved live feeds from `docs/source-inventory.md`
   - keep `cisa-kev-catalog` in the local config once you replace its placeholder JSON URL with the approved live endpoint
6. Run one date-scoped digest on the dedicated Linux Codex machine:
   ```bash
   uv run daily-insight run --date 2026-04-15 --config configs/sources.local.json
   ```

## Daily workflow

- `uv run daily-insight collect` gathers normalized items into `inputs/YYYY-MM-DD/items.jsonl`
- `uv run daily-insight collect` also writes deterministic source-health metadata into `inputs/YYYY-MM-DD/source_summary.json`
- Codex reads the frozen input and produces `outputs/YYYY-MM-DD/digest.json`
- `uv run daily-insight render` extracts a clean `outputs/YYYY-MM-DD/digest.md`
- `uv run daily-insight render-html` can render a self-contained browser page from canonical `digest.json`
- `uv run daily-insight publish-site` publishes a reviewed digest into the generated `site/` browser root without serving raw `outputs/` directly
- SQLite-backed operational state is recorded under `state/daily_insight.db`
- `uv run daily-insight source-health --date YYYY-MM-DD` inspects the persisted per-bucket source-health state
- tests and schema checks keep the output stable

## Browser delivery

Browser reading is a static publication step, not a live app:

1. Generate or review the canonical digest under `outputs/YYYY-MM-DD/`.
2. Publish the reviewed date into the generated browser site root:
   ```bash
   uv run daily-insight publish-site --source-root outputs --date 2026-04-16 --site-root site
   ```
3. Smoke-test the browser output locally:
   ```bash
   python -m http.server 8000 --directory site
   curl http://127.0.0.1:8000/latest/
   ```

The published browser contract is:

- `site/index.html`
- `site/latest/index.html`
- `site/YYYY-MM-DD/index.html`

Serve only `site/`. Do not point a static server at the repository root, `outputs/`, `inputs/`, `state/`, or `configs/`.

## Publication handoff

Before the first public push:

1. Replace the placeholder maintainer and security contact details in `SECURITY.md`.
2. Confirm `configs/sources.local.json` and `state/` remain local-only artifacts.
3. Run the documented verification path:
   ```bash
   bash scripts/ci.sh
   systemd-analyze verify ops/systemd/daily-insight.service ops/systemd/daily-insight.timer
   uv run daily-insight run --date 2026-04-15 --config configs/sources.local.json
   uv run daily-insight publish-site --source-root outputs --date 2026-04-15 --site-root site
   ```
4. Connect this workspace to the empty GitHub repository only after the checks above succeed:
   ```bash
   git init
   git branch -M main
   git remote add origin git@github.com:xiongxianfei/daily-engineering-security-insight.git
   git add .
   git commit -m "Initial daily insight repository"
   git push -u origin main
   ```

`git push` is a publication step, not a correctness check.

## Naming

For an open source repo, prefer a clear, scope-revealing name. Recommended name:

- `daily-engineering-security-insight`

Shorter alternative if you want less typing:

- `daily-engsec-insight`

Avoid personal names like `my-daily-insight`; they make the repo feel private and do not reveal the subject.

## Suggested next customization steps

- replace the sample source config with your approved feeds and APIs
- keep approved live feeds documented in `docs/source-inventory.md`
- tune the scoring rubric in `specs/daily-digest.md`
- connect delivery to email, Slack, or an internal portal only after the digest quality is stable
- replace placeholder maintainer and security contacts

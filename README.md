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
   bash scripts/ci.sh
   ```
4. Create the operator-managed live source config:
   ```bash
   cp configs/sources.example.json configs/sources.local.json
   ```
5. Replace the placeholder URLs in `configs/sources.local.json` with the approved live feeds from `docs/source-inventory.md`.
6. Run one date-scoped digest on the dedicated Linux Codex machine:
   ```bash
   uv run daily-insight run --date 2026-04-15 --config configs/sources.local.json
   ```
7. If a run already froze `inputs/YYYY-MM-DD/items.jsonl` but synthesis timed out or failed, resume from the frozen bundle instead of recollecting:
   ```bash
   uv run daily-insight synthesize \
     --date 2026-04-15 \
     --in-dir inputs/2026-04-15 \
     --out-dir outputs/2026-04-15
   ```

## Daily workflow

- `uv run daily-insight collect` gathers normalized items into `inputs/YYYY-MM-DD/items.jsonl`
- `uv run daily-insight run` reuses an existing frozen input for the same date instead of recollecting, and it no-ops when both final outputs are already complete
- `uv run daily-insight synthesize` is the recovery command for a frozen input bundle that already exists
- Codex produces `outputs/YYYY-MM-DD/digest.json`, then the renderer writes `outputs/YYYY-MM-DD/digest.md`
- the default synthesis timeout is `900` seconds; override it with `--timeout-seconds` or `DAILY_INSIGHT_SYNTHESIS_TIMEOUT_SECONDS`
- SQLite-backed operational state is recorded under `state/daily_insight.db`
- tests and schema checks keep the output stable

## Publication handoff

Before the first public push:

1. Replace the placeholder maintainer and security contact details in `SECURITY.md`.
2. Confirm `configs/sources.local.json` and `state/` remain local-only artifacts.
3. Run the documented verification path:
   ```bash
   bash scripts/ci.sh
   systemd-analyze verify ops/systemd/daily-insight.service ops/systemd/daily-insight.timer
   uv run daily-insight run --date 2026-04-15 --config configs/sources.local.json
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

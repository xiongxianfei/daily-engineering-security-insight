# Dedicated Codex machine setup

This repository assumes a dedicated machine for Codex CLI runs.

## Suggested local setup

1. Install Python 3.12 and `uv` on the Linux host.
2. Sign in to Codex CLI on the dedicated machine and verify the session:
   ```bash
   codex login status
   ```
3. Clone the repository.
4. Sync the project:
   ```bash
   uv sync --dev
   ```
5. Copy `configs/sources.example.json` to `configs/sources.local.json` and replace placeholder URLs with the approved live URLs from `docs/source-inventory.md`.
6. Verify the repo-local workflow before enabling the timer:
   ```bash
   bash scripts/ci.sh
   uv run daily-insight run --date 2026-04-15 --config configs/sources.local.json
   ```

## Suggested runtime commands

```bash
uv sync --dev
uv run daily-insight --help
uv run daily-insight collect --dry-run --config configs/sources.example.json
uv run daily-insight run --date 2026-04-15 --config configs/sources.local.json
```

## Example `~/.codex/config.toml`

```toml
model = "gpt-5.4"
approval_policy = "on-request"
sandbox_mode = "workspace-write"
web_search = "cached"

[sandbox_workspace_write]
network_access = false
writable_roots = ["/srv/daily-engineering-security-insight"]
```

## Example `~/.codex/AGENTS.md`

```md
# ~/.codex/AGENTS.md

## Working agreements

- Prefer frozen local inputs over live browsing when both exist.
- Keep daily digests concise, evidence-backed, and action-oriented.
- Do not upgrade speculation into high-confidence findings.
- Ask before broadening scope beyond the current date or configured sources.
```

## Scheduling

Use `systemd` with the sample files in `ops/systemd/`.

Example operator flow:

```bash
cp configs/sources.example.json configs/sources.local.json
# Replace example URLs with the approved live URLs from docs/source-inventory.md
systemd-analyze verify ops/systemd/daily-insight.service ops/systemd/daily-insight.timer
systemctl daemon-reload
systemctl enable --now daily-insight.timer
```

Do not assume GitHub Actions can use your ChatGPT plan; this repository is designed for a dedicated Codex machine.

## Recovery notes

- Disable the timer before debugging repeated failures:
  ```bash
  systemctl disable --now daily-insight.timer
  ```
- If a run fails after collection, inspect `inputs/YYYY-MM-DD/items.jsonl` first; it is the frozen synthesis input.
- If the SQLite state under `state/daily_insight.db` becomes inconsistent with on-disk artifacts, treat the date-scoped JSON files as the source of truth and repair the state DB separately.

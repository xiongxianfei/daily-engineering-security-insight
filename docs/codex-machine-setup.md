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
5. Copy `configs/sources.example.json` to `configs/sources.local.json` and derive the live file from `configs/source-manifest.json`:
   - keep the same source names, buckets, required flags, and failure policies
   - replace only the placeholder URLs with the approved live URLs from `docs/source-inventory.md`
   - keep `cisa-kev-catalog` in the local config once you replace its placeholder JSON URL with the approved live endpoint
6. Verify the repo-local workflow before enabling the timer:
   ```bash
   bash scripts/ci.sh
   uv run daily-insight run --date 2026-04-15 --config configs/sources.local.json
   uv run daily-insight source-health --date 2026-04-15 --state-db state/daily_insight.db
   uv run daily-insight publish-site --source-root outputs --date 2026-04-15 --site-root site
   ```

## Suggested runtime commands

```bash
uv sync --dev
uv run daily-insight --help
uv run daily-insight collect --dry-run --config configs/sources.example.json
uv run daily-insight run --date 2026-04-15 --config configs/sources.local.json
uv run daily-insight source-health --date 2026-04-15 --state-db state/daily_insight.db
uv run daily-insight publish-site --source-root outputs --date 2026-04-15 --site-root site
```

## Browser serving

Use a generated browser site root, not the repository root:

```bash
uv run daily-insight publish-site --source-root outputs --date 2026-04-15 --site-root site
python -m http.server 8000 --directory site
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/latest/
```

`python -m http.server` is a smoke-test only. For durable Linux serving, use a static server such as NGINX rooted at `site/`, not at the repository root. A sample config is in `ops/nginx/daily-insight-site.conf`.

Never serve:

- `inputs/`
- `state/`
- `configs/sources.local.json`
- the raw repository root

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
# Keep the same source names, buckets, required flags, and failure policies from configs/source-manifest.json
# Replace example URLs with the approved live URLs from docs/source-inventory.md
# Keep `cisa-kev-catalog` in place and replace its placeholder JSON URL with the approved live endpoint
systemd-analyze verify ops/systemd/daily-insight.service ops/systemd/daily-insight.timer
systemctl daemon-reload
systemctl enable --now daily-insight.timer
```

If you want browser delivery from the same machine, publish reviewed dates into `site/` and point NGINX only at that generated site root.

Do not assume GitHub Actions can use your ChatGPT plan; this repository is designed for a dedicated Codex machine.

## Recovery notes

- Disable the timer before debugging repeated failures:
  ```bash
  systemctl disable --now daily-insight.timer
  ```
- If a run fails after collection, inspect `inputs/YYYY-MM-DD/items.jsonl` first; it is the frozen synthesis input.
- If the SQLite state under `state/daily_insight.db` becomes inconsistent with on-disk artifacts, treat the date-scoped JSON files as the source of truth and repair the state DB separately.

## Source review cadence

- Review `docs/source-inventory.md` and `configs/source-manifest.json` at least monthly on the dedicated machine.
- If `uv run daily-insight source-health --date YYYY-MM-DD --state-db state/daily_insight.db` shows the same source failing for 3 consecutive days, review that source before trusting another unattended run.
- If a bucket degrades repeatedly because it has only one healthy source, approve a new backup or record the no-backup rationale during the next monthly review.

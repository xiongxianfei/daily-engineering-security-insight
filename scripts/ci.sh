#!/usr/bin/env bash
set -euo pipefail

uv run ruff check .
uv run python -m json.tool schemas/daily_insight.schema.json >/dev/null
uv run daily-insight collect --dry-run --config configs/sources.example.json
uv run daily-insight render examples/sample_digest.json /tmp/digest.md
uv run pytest -q

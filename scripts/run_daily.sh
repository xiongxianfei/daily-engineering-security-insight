#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATE="${1:-$(date +%F)}"
CONFIG_PATH="${ROOT}/configs/sources.local.json"
PROMPT_PATH="${ROOT}/prompts/daily_digest_prompt.md"
OUT_DIR="${ROOT}/outputs/${DATE}"
IN_DIR="${ROOT}/inputs/${DATE}"
STATE_DB="${ROOT}/state/daily_insight.db"

if command -v uv >/dev/null 2>&1; then
  UV_BIN="uv"
elif [[ -x "${HOME}/.local/bin/uv" ]]; then
  UV_BIN="${HOME}/.local/bin/uv"
else
  echo "missing uv in PATH and ${HOME}/.local/bin/uv" >&2
  exit 1
fi

if [[ ! -f "${CONFIG_PATH}" ]]; then
  echo "missing ${CONFIG_PATH}; copy configs/sources.example.json first" >&2
  exit 1
fi

cd "${ROOT}"
exec "${UV_BIN}" run daily-insight run \
  --date "${DATE}" \
  --config "${CONFIG_PATH}" \
  --prompt-path "${PROMPT_PATH}" \
  --in-dir "${IN_DIR}" \
  --out-dir "${OUT_DIR}" \
  --state-db "${STATE_DB}"

#!/usr/bin/env bash
set -euo pipefail

bash scripts/ci.sh

test -f README.md
test -f AGENTS.md
test -f docs/workflows.md
test -f specs/daily-digest.md
test -f specs/daily-digest.test.md

echo "release verification skeleton complete"

# Contributing

Keep contributions deterministic, reviewable, and contract-driven.

## Before changing behavior

1. Read `AGENTS.md`.
2. Read `docs/plan.md` and the active plan in `docs/plans/`.
3. Read the relevant spec and test spec in `specs/`.
4. Use `plan -> spec -> test-spec -> implement -> verify -> docs -> review` for behavior-changing work.
5. Keep diffs scoped and reviewable.

## Planning guidance

For multi-file or behavior-changing work, add or update a plan under `docs/plans/` and index it in `docs/plan.md`.

## Local setup and verification

```bash
uv sync --dev
uv run daily-insight --help
bash scripts/ci.sh
```

If you change the operator workflow or Linux scheduling examples, also run:

```bash
systemd-analyze verify ops/systemd/daily-insight.service ops/systemd/daily-insight.timer
```

## Contribution rules

- List the commands you actually ran in your PR or handoff note.
- Update specs, test specs, docs, and examples in the same change when a contract changes.
- Do not commit `configs/sources.local.json`, `state/`, or generated date-scoped `inputs/` and `outputs/`.
- Keep live-source changes aligned with `docs/source-inventory.md`.

# AGENTS.md

This repository uses Codex CLI on a dedicated machine to produce a daily insight brief.

Optimize for deterministic collection, explicit contracts, small reviewable diffs, and schema-validated outputs over clever one-off prompts.

## Instruction precedence

When instructions conflict, follow this order:

1. direct user request
2. approved feature spec in `specs/`
3. matching test spec in `specs/`
4. active execution plan file in `docs/plans/`
5. `docs/workflows.md`
6. this file

Do not silently blend conflicting higher-priority instructions. State the conflict, explain the impact, and follow the highest-priority source that already implies the answer.

## Repository defaults

- Prefer deterministic collection before synthesis.
- Prefer the smallest change that fully satisfies the request.
- Do not add unrelated refactors while implementing a scoped task.
- Preserve existing human-authored notes and source snapshots unless explicitly asked to regenerate them.
- Keep `AGENTS.md` practical. Put workflow detail in `docs/workflows.md` and behavior detail in `specs/`.
- When a schema or contract changes, update specs, tests, and examples in the same change.
- When a frozen daily input already exists for a date, analyze that input before suggesting live browsing.

## Planning and workflow

Use a plan first for multi-file, risky, ambiguous, architecture-affecting, or automation-heavy work.

Default workflow for behavior-changing work:

`plan -> spec -> test-spec -> implement -> verify -> docs -> review`

Use `bugfix` for defects, `ci` for GitHub Actions or automation changes, and `pr` only when the branch is ready for review.

## Plan file policy

- `docs/roadmap.md` stores future ideas and unapproved work.
- `docs/plan.md` is an index of active and closed execution plans. It is not the body of a plan.
- Every approved initiative gets its own living plan file under `docs/plans/YYYY-MM-DD-slug.md`.
- Never overwrite an older plan when starting a new initiative.
- If a new plan replaces an older one, keep the older file and mark it as superseded.
- Execution plans should follow `.codex/PLANS.md`.

## Required reading before implementation

Before implementing behavior-changing work, read in this order when the files exist:

1. `docs/plan.md`, then the active plan file in `docs/plans/`
2. the relevant feature spec in `specs/`
3. the matching test spec in `specs/`
4. `docs/workflows.md`
5. the files you expect to modify

If the work changes externally observable behavior and no relevant spec exists, create or request the missing spec before coding the contract into the implementation.

## Daily digest rules

- Treat source collection as deterministic infrastructure and Codex synthesis as the reasoning layer.
- Keep the four primary buckets distinct:
  - software engineering
  - security
  - AI for Security
  - Security for AI
- Every surfaced item must include source metadata and a confidence estimate.
- Prefer explicit evidence over broad trend language.
- Mark speculation as low confidence instead of upgrading it into a claim.
- Keep “action now” separate from “watchlist”.

## Verification expectations

Use the real commands in this repo and report exactly what ran.

Minimum expected verification for most changes:

- `python -m pytest -q`
- `python -m json.tool schemas/daily_insight.schema.json > /dev/null`
- `python collectors/collect_sources.py --dry-run --config configs/sources.example.json`
- `python scripts/render_digest.py examples/sample_digest.json /tmp/digest.md`

Do not report success without naming the commands actually run.

## Definition of done

A task is not done unless all of the following are true:

- the implementation matches the current contract
- relevant verification was run, or any inability to run it is stated clearly
- named edge cases and failure paths are handled or explicitly deferred
- the active plan reflects what actually happened when a plan was used
- meaningful assumptions and open questions are called out in the final response

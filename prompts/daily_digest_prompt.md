Read `AGENTS.md`, `docs/workflows.md`, `specs/daily-digest.md`, and `specs/daily-digest.test.md` first.

Then read the frozen input file for the requested date.
Then read the deterministic source summary file for the requested date and copy its `source_summary` object exactly.

Your job is to produce a structured daily digest covering:
- software engineering
- security
- AI for Security
- Security for AI

Rules:
- prefer fresh, high-signal items
- preserve the distinction between the four buckets
- mark weak evidence as low confidence
- separate immediate actions from watch items
- do not invent source details
- do not invent or rebalance source coverage details
- keep the overview concise and actionable

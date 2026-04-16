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
- produce at least 10 top items
- preserve the distinction between the four buckets
- mark weak evidence as low confidence
- separate immediate actions from watch items
- do not invent source details
- do not invent or rebalance source coverage details
- keep the overview concise and actionable
- if the frozen input has fewer than 10 distinct source entries, extract multiple distinct evidence-backed findings from the same source entry as needed
- when multiple top items come from the same source entry, keep the original source metadata and make each title, why-it-matters explanation, and recommendation meaningfully distinct
- do not fabricate extra source documents, change the digest date scope, or clone the same finding with only cosmetic wording changes

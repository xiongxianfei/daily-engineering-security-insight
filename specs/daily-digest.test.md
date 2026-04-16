# Daily digest test specification

Map each spec requirement to verification.

## Contract mapping

- overview summary -> validate sample JSON contains `overview_markdown`
- source metadata on top items -> validate schema requires `source` and `source_url`
- confidence labels -> validate schema requires `confidence`
- immediate action vs watch separation -> validate schema requires `action_now` and `watchlist`
- preserved date scope -> verify the daily-run command passes the requested date path into the prompt
- no invented source details -> review prompt and renderer expectations
- source failures visible -> validate schema requires `source_summary.source_failures`
- empty bucket coverage stays explicit -> validate `source_summary.bucket_counts` keeps zero-count buckets and `source_summary.source_failures` explains missing coverage
- bucket health stays explicit -> validate schema requires `source_summary.bucket_health` with the approved status names
- degraded coverage notes stay explicit -> validate schema requires `source_summary.coverage_notes`

## Expected checks

- `uv run python -m json.tool schemas/daily_insight.schema.json > /dev/null`
- `uv run daily-insight render examples/sample_digest.json /tmp/digest.md`
- `uv run pytest -q`

## Future tests

- add collector tests for source config parsing and normalization
- add regression tests for duplicate suppression and bucket balance
- add a regression test for digests that preserve explicit zero-count buckets when a source fails or a category has no frozen-input items

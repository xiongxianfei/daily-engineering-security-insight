from __future__ import annotations

import json
from pathlib import Path

from jsonschema import validate

ROOT = Path(__file__).resolve().parents[1]


def test_sample_digest_matches_schema() -> None:
    schema = json.loads(
        (ROOT / "schemas" / "daily_insight.schema.json").read_text(encoding="utf-8")
    )
    payload = json.loads((ROOT / "examples" / "sample_digest.json").read_text(encoding="utf-8"))
    validate(instance=payload, schema=schema)


def test_schema_requires_at_least_ten_top_items() -> None:
    schema = json.loads(
        (ROOT / "schemas" / "daily_insight.schema.json").read_text(encoding="utf-8")
    )

    assert schema["properties"]["top_items"]["minItems"] == 10


def test_sample_digest_has_at_least_ten_top_items() -> None:
    payload = json.loads((ROOT / "examples" / "sample_digest.json").read_text(encoding="utf-8"))

    assert len(payload["top_items"]) >= 10

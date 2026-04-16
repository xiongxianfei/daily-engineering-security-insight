from __future__ import annotations

import json
from pathlib import Path

from daily_insight.render import render_markdown

ROOT = Path(__file__).resolve().parents[1]


def test_render_markdown_includes_bucket_health_and_coverage_notes() -> None:
    payload = json.loads((ROOT / "examples" / "sample_digest.json").read_text(encoding="utf-8"))

    rendered = render_markdown(payload)

    assert "Bucket health" in rendered
    assert "security: degraded-sparse-day" in rendered
    assert "Coverage notes" in rendered

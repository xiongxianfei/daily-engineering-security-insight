from __future__ import annotations

import json
from pathlib import Path

import pytest

from daily_insight.render import render_html, render_markdown

ROOT = Path(__file__).resolve().parents[1]


def test_render_markdown_includes_bucket_health_and_coverage_notes() -> None:
    payload = json.loads((ROOT / "examples" / "sample_digest.json").read_text(encoding="utf-8"))

    rendered = render_markdown(payload)

    assert "Bucket health" in rendered
    assert "security: degraded-sparse-day" in rendered
    assert "Coverage notes" in rendered
    assert "Total collected source entries seen: 3" in rendered
    assert "Top items surfaced: 10" in rendered
    assert "Source summary reflects collected source entries" in rendered


def test_render_html_includes_semantic_sections_and_digest_content() -> None:
    payload = json.loads((ROOT / "examples" / "sample_digest.json").read_text(encoding="utf-8"))

    rendered = render_html(payload)

    assert "<!DOCTYPE html>" in rendered
    assert '<meta name="viewport" content="width=device-width, initial-scale=1">' in rendered
    assert "<title>Daily insight for 2026-04-15</title>" in rendered
    assert "<main>" in rendered
    assert "<h1>Daily insight for 2026-04-15</h1>" in rendered
    assert '<section aria-labelledby="top-items-heading">' in rendered
    assert "Example engineering item" in rendered
    assert "security: degraded-sparse-day" in rendered
    assert "Coverage notes" in rendered
    assert "Track the change and decide whether it affects your toolchain." in rendered
    assert "Total collected source entries seen:" in rendered
    assert "Top items surfaced:" in rendered
    assert "Source summary reflects collected source entries" in rendered


def test_render_html_includes_every_top_item() -> None:
    payload = json.loads((ROOT / "examples" / "sample_digest.json").read_text(encoding="utf-8"))

    rendered = render_html(payload)

    assert rendered.count('<article class="top-item">') == len(payload["top_items"])


def test_render_html_requires_browser_contract_fields() -> None:
    with pytest.raises(KeyError):
        render_html({"date": "2026-04-15"})

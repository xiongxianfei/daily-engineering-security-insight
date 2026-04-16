from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from daily_insight.config import load_source_configs, required_source_configs

ROOT = Path(__file__).resolve().parents[1]


def test_load_source_configs_returns_typed_entries() -> None:
    sources = load_source_configs(ROOT / "configs" / "sources.example.json")

    assert [source.bucket for source in sources] == [
        "software-engineering",
        "software-engineering",
        "security",
        "security",
        "ai-for-security",
        "security-for-ai",
        "security-for-ai",
    ]
    assert [source.transport for source in sources] == [
        "rss",
        "rss",
        "rss",
        "json",
        "rss",
        "rss",
        "rss",
    ]
    assert all(source.enabled is True for source in sources)
    assert [source.required_for_daily_run for source in sources] == [
        True,
        False,
        True,
        False,
        False,
        False,
        False,
    ]
    assert [source.failure_policy for source in sources] == [
        "fail",
        "warn",
        "warn",
        "warn",
        "warn",
        "warn",
        "warn",
    ]
    assert [source.max_items_per_source for source in sources] == [10, 10, 10, 10, 5, 5, 5]
    assert [source.name for source in required_source_configs(sources)] == [
        "python-insider",
        "google-online-security-blog",
    ]


def test_load_source_configs_accepts_json_transport(tmp_path: Path) -> None:
    config_path = tmp_path / "sources.json"
    config_path.write_text(
        json.dumps(
            [
                {
                    "name": "cisa-kev-catalog",
                    "transport": "json",
                    "url": "https://example.com/known-exploited-vulnerabilities.json",
                    "bucket": "security",
                    "enabled": True,
                    "required_for_daily_run": False,
                    "failure_policy": "warn",
                }
            ]
        ),
        encoding="utf-8",
    )

    sources = load_source_configs(config_path)

    assert len(sources) == 1
    assert sources[0].transport == "json"


def test_load_source_configs_rejects_unknown_transport(tmp_path: Path) -> None:
    config_path = tmp_path / "sources.json"
    config_path.write_text(
        json.dumps(
            [
                {
                    "name": "invalid-feed",
                    "transport": "csv",
                    "url": "https://example.com/feed.json",
                    "bucket": "security",
                    "enabled": True,
                }
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValidationError):
        load_source_configs(config_path)


def test_load_source_configs_rejects_unknown_failure_policy(tmp_path: Path) -> None:
    config_path = tmp_path / "sources.json"
    config_path.write_text(
        json.dumps(
            [
                {
                    "name": "invalid-feed",
                    "transport": "rss",
                    "url": "https://example.com/feed.xml",
                    "bucket": "security",
                    "enabled": True,
                    "required_for_daily_run": True,
                    "failure_policy": "ignore",
                }
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValidationError):
        load_source_configs(config_path)


def test_example_config_source_names_follow_reviewed_manifest_order() -> None:
    sources = load_source_configs(ROOT / "configs" / "sources.example.json")

    assert [source.name for source in sources] == [
        "python-insider",
        "github-changelog",
        "google-online-security-blog",
        "cisa-kev-catalog",
        "google-threat-intelligence",
        "openai-news",
        "deepmind-blog",
    ]

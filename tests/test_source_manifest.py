from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_manifest() -> dict[str, object]:
    return json.loads((ROOT / "configs" / "source-manifest.json").read_text(encoding="utf-8"))


def _load_example_config() -> list[dict[str, object]]:
    return json.loads((ROOT / "configs" / "sources.example.json").read_text(encoding="utf-8"))


def _load_inventory_table() -> dict[str, dict[str, str]]:
    inventory = (ROOT / "docs" / "source-inventory.md").read_text(encoding="utf-8")
    rows: dict[str, dict[str, str]] = {}
    pattern = re.compile(
        r"^\| (?P<bucket>[^|]+) \| `(?P<name>[^`]+)` \| `(?P<role>[^`]+)` \| "
        r"`(?P<transport>[^`]+)` \| (?P<url>[^|]+) \| (?P<implemented>[^|]+) \| "
        r"(?P<counts_now>[^|]+) \| (?P<required>[^|]+) \| `(?P<failure_policy>[^`]+)` \|",
        re.MULTILINE,
    )
    for match in pattern.finditer(inventory):
        rows[match.group("name")] = {
            "bucket": match.group("bucket").strip(),
            "role": match.group("role"),
            "transport": match.group("transport"),
            "implemented": match.group("implemented").strip(),
            "counts_now": match.group("counts_now").strip(),
            "required": match.group("required").strip(),
            "failure_policy": match.group("failure_policy"),
        }
    return rows


def test_source_manifest_defines_reviewed_sources_and_required_metadata() -> None:
    manifest = _load_manifest()

    assert manifest["reviewed_at"] == "2026-04-16"

    sources = manifest["sources"]
    assert isinstance(sources, list)

    names = [entry["name"] for entry in sources]
    assert names == [
        "python-insider",
        "github-changelog",
        "django-blog",
        "google-online-security-blog",
        "cisa-kev-catalog",
        "cisa-advisories",
        "github-security-blog",
        "google-threat-intelligence",
        "openai-news",
        "deepmind-blog",
    ]
    assert len(names) == len(set(names))

    for entry in sources:
        assert set(entry) >= {
            "name",
            "bucket",
            "transport",
            "disposition",
            "required_for_daily_run",
            "failure_policy",
            "freshness_mode",
            "machine_readable",
            "implemented_status",
            "counts_toward_sufficiency",
            "live_probe_result",
            "last_reviewed",
        }
        assert entry["disposition"] in {"primary", "backup", "deferred", "removed"}


def test_source_manifest_records_expected_live_probe_and_sufficiency_decisions() -> None:
    sources = {entry["name"]: entry for entry in _load_manifest()["sources"]}

    assert sources["python-insider"]["live_probe_result"] == "200 application/xml"
    assert sources["github-changelog"]["disposition"] == "backup"
    assert sources["django-blog"]["disposition"] == "backup"
    assert sources["google-online-security-blog"]["counts_toward_sufficiency"] is True
    assert sources["cisa-kev-catalog"]["transport"] == "json"
    assert sources["cisa-kev-catalog"]["implemented_status"] == "implemented"
    assert sources["cisa-kev-catalog"]["counts_toward_sufficiency"] is True
    assert sources["cisa-advisories"]["disposition"] == "backup"
    assert sources["cisa-advisories"]["counts_toward_sufficiency"] is True
    assert sources["github-security-blog"]["disposition"] == "backup"
    assert sources["openai-news"]["implemented_status"] == "implemented"
    assert sources["openai-news"]["counts_toward_sufficiency"] is True
    assert sources["deepmind-blog"]["disposition"] == "backup"


def test_source_viability_audit_references_manifest_sources_and_bucket_decisions() -> None:
    audit = (ROOT / "docs" / "source-viability-audit.md").read_text(encoding="utf-8")
    sources = _load_manifest()["sources"]

    assert "2026-04-16 live viability review" in audit
    assert "software-engineering" in audit
    assert "security" in audit
    assert "ai-for-security" in audit
    assert "security-for-ai" in audit

    for entry in sources:
        assert entry["name"] in audit

    assert "no approved backup yet" in audit
    assert "third dedicated-machine validation date: 2026-04-10" in audit


def test_source_inventory_table_matches_manifest_decisions() -> None:
    manifest_sources = {entry["name"]: entry for entry in _load_manifest()["sources"]}
    inventory_rows = _load_inventory_table()

    assert set(inventory_rows) == set(manifest_sources)

    for name, manifest_source in manifest_sources.items():
        row = inventory_rows[name]
        assert row["bucket"] == manifest_source["bucket"]
        assert row["role"] == manifest_source["disposition"]
        assert row["transport"] == manifest_source["transport"]
        assert row["failure_policy"] == manifest_source["failure_policy"]
        assert row["required"] == ("yes" if manifest_source["required_for_daily_run"] else "no")
        assert row["counts_now"] == (
            "yes" if manifest_source["counts_toward_sufficiency"] else "no"
        )


def test_example_config_tracks_supported_manifest_sources() -> None:
    manifest_sources = _load_manifest()["sources"]
    supported_sources = {
        entry["name"]: entry
        for entry in manifest_sources
        if entry["disposition"] != "removed" and entry["implemented_status"] == "implemented"
    }
    example_config = _load_example_config()

    assert [entry["name"] for entry in example_config] == list(supported_sources)

    for entry in example_config:
        manifest_source = supported_sources[entry["name"]]
        assert entry["bucket"] == manifest_source["bucket"]
        assert entry["transport"] == manifest_source["transport"]
        assert entry["required_for_daily_run"] == manifest_source["required_for_daily_run"]
        assert entry["failure_policy"] == manifest_source["failure_policy"]
        assert entry["url"].startswith("https://example.com/")


def test_operator_config_guidance_references_manifest_alignment() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    setup = (ROOT / "docs" / "codex-machine-setup.md").read_text(encoding="utf-8")

    expected_snippets = [
        "configs/source-manifest.json",
        "same source names, buckets, required flags, and failure policies",
        "replace only the placeholder URLs",
        "`cisa-kev-catalog`",
    ]

    for snippet in expected_snippets:
        assert snippet in readme
        assert snippet in setup

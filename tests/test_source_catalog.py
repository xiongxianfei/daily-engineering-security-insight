from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

COUNTED_STATUSES = {"runtime-approved", "reviewed-candidate", "deferred"}
VALID_STATUSES = COUNTED_STATUSES | {"rejected"}


def _load_catalog() -> dict[str, object]:
    return json.loads((ROOT / "configs" / "source-catalog.json").read_text(encoding="utf-8"))


def _load_manifest() -> dict[str, object]:
    return json.loads((ROOT / "configs" / "source-manifest.json").read_text(encoding="utf-8"))


def _counted_catalog_entries(catalog: dict[str, object]) -> list[dict[str, object]]:
    return [
        entry
        for entry in catalog["sources"]
        if entry["catalog_status"] in COUNTED_STATUSES
    ]


def test_source_catalog_defines_required_fields_and_unique_names() -> None:
    catalog = _load_catalog()

    assert catalog["reviewed_at"] == "2026-04-16"
    assert isinstance(catalog["sources"], list)

    names = [entry["name"] for entry in catalog["sources"]]
    assert len(names) == len(set(names))

    for entry in catalog["sources"]:
        assert set(entry) >= {
            "name",
            "bucket",
            "url",
            "transport",
            "catalog_status",
            "machine_readable",
            "last_reviewed",
            "expected_signal",
            "review_notes",
        }
        assert entry["catalog_status"] in VALID_STATUSES


def test_source_catalog_has_at_least_thirty_counted_entries() -> None:
    catalog = _load_catalog()

    counted_entries = _counted_catalog_entries(catalog)

    assert len(counted_entries) >= 30
    assert all(entry["catalog_status"] != "rejected" for entry in counted_entries)


def test_runtime_manifest_sources_are_runtime_approved_catalog_entries() -> None:
    catalog_sources = {entry["name"]: entry for entry in _load_catalog()["sources"]}
    manifest_sources = _load_manifest()["sources"]

    for manifest_entry in manifest_sources:
        catalog_entry = catalog_sources[manifest_entry["name"]]
        assert catalog_entry["catalog_status"] == "runtime-approved"
        assert catalog_entry["bucket"] == manifest_entry["bucket"]
        assert catalog_entry["transport"] == manifest_entry["transport"]
        assert catalog_entry["machine_readable"] is True


def test_source_catalog_doc_is_human_readable_companion() -> None:
    catalog_doc = (ROOT / "docs" / "source-catalog.md").read_text(encoding="utf-8")
    catalog = _load_catalog()

    assert "runtime-approved subset" in catalog_doc
    assert "reviewed source catalog" in catalog_doc

    for entry in catalog["sources"]:
        assert entry["name"] in catalog_doc


def test_source_viability_audit_covers_catalog_and_explicit_promotion_decision() -> None:
    audit = (ROOT / "docs" / "source-viability-audit.md").read_text(encoding="utf-8")
    catalog = _load_catalog()

    assert "No immediate promotions into the runtime manifest" in audit
    assert "Promotion shortlist for Milestone 4" in audit
    assert "ai-for-security still has no feed-ready reviewed-candidate addition" in audit

    for entry in catalog["sources"]:
        assert entry["name"] in audit

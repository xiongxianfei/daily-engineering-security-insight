from __future__ import annotations

from daily_insight.normalize import normalize_item
from daily_insight.source_health import compute_source_summary


def _manifest_entry(
    *,
    name: str,
    bucket: str,
    implemented_status: str = "implemented",
    disposition: str = "primary",
    machine_readable: bool = True,
) -> dict[str, object]:
    return {
        "name": name,
        "bucket": bucket,
        "transport": "rss",
        "disposition": disposition,
        "required_for_daily_run": False,
        "failure_policy": "warn",
        "freshness_mode": "published-date",
        "machine_readable": machine_readable,
        "implemented_status": implemented_status,
        "counts_toward_sufficiency": implemented_status == "implemented",
        "live_probe_result": "200 text/xml",
        "last_reviewed": "2026-04-16",
    }


def test_compute_source_summary_distinguishes_all_bucket_health_statuses() -> None:
    manifest = {
        "sources": [
            _manifest_entry(name="python-insider", bucket="software-engineering"),
            _manifest_entry(name="google-online-security-blog", bucket="security"),
            _manifest_entry(name="google-threat-intelligence", bucket="ai-for-security"),
            _manifest_entry(
                name="openai-news",
                bucket="security-for-ai",
                implemented_status="not-implemented",
            ),
        ]
    }
    attempts = [
        {
            "source_name": "python-insider",
            "bucket": "software-engineering",
            "status": "collected",
            "detail": "1 of 1 items kept",
        },
        {
            "source_name": "google-online-security-blog",
            "bucket": "security",
            "status": "failed",
            "detail": "HTTP 403",
        },
        {
            "source_name": "google-threat-intelligence",
            "bucket": "ai-for-security",
            "status": "collected",
            "detail": "0 of 0 items kept",
        },
    ]
    items = [
        normalize_item(
            source_name="python-insider",
            bucket="software-engineering",
            title="Python 3.12.13 released",
            url="https://example.com/python-3-12-13",
            summary="Bugfix release",
            published_at="2026-04-16T00:00:00Z",
            tags=["release"],
        )
    ]

    summary = compute_source_summary(manifest=manifest, source_attempts=attempts, items=items)

    assert summary["bucket_health"] == {
        "software-engineering": "healthy",
        "security": "degraded-source-failure",
        "ai-for-security": "degraded-sparse-day",
        "security-for-ai": "degraded-no-approved-source",
    }
    assert summary["source_failures"] == ["google-online-security-blog: HTTP 403"]
    assert any("security: failed eligible sources" in note for note in summary["coverage_notes"])
    assert any(
        "ai-for-security: eligible sources produced zero fresh items" in note
        for note in summary["coverage_notes"]
    )
    assert any(
        "security-for-ai: no eligible approved source" in note
        for note in summary["coverage_notes"]
    )

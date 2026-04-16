from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from daily_insight.models import BucketName, NormalizedItem

BUCKETS: tuple[BucketName, ...] = (
    "software-engineering",
    "security",
    "ai-for-security",
    "security-for-ai",
)


@dataclass(frozen=True)
class BucketHealthRecord:
    bucket: BucketName
    status: str
    item_count: int
    detail: str


def _default_manifest_path() -> Path:
    return Path(__file__).resolve().parents[1] / "configs" / "source-manifest.json"


def load_source_manifest(path: Path | None = None) -> dict[str, object]:
    manifest_path = path or _default_manifest_path()
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _is_eligible_source(entry: Mapping[str, object]) -> bool:
    return (
        entry.get("machine_readable") is True
        and entry.get("implemented_status") == "implemented"
        and entry.get("disposition") not in {"deferred", "removed"}
    )


def _bucket_counts(items: list[NormalizedItem]) -> dict[BucketName, int]:
    counts: dict[BucketName, int] = {bucket: 0 for bucket in BUCKETS}
    for item in items:
        counts[item.bucket_hint] += 1
    return counts


def _source_failures(source_attempts: list[Mapping[str, object]]) -> list[str]:
    failures: list[str] = []
    seen: set[str] = set()
    for attempt in source_attempts:
        if attempt.get("status") != "failed":
            continue
        detail = str(attempt.get("detail") or "failed").strip()
        message = f"{attempt['source_name']}: {detail}"
        if message not in seen:
            failures.append(message)
            seen.add(message)
    return failures


def compute_bucket_health(
    *,
    manifest: Mapping[str, object],
    source_attempts: list[Mapping[str, object]],
    items: list[NormalizedItem],
) -> list[BucketHealthRecord]:
    counts = _bucket_counts(items)
    manifest_sources = manifest.get("sources", [])
    if not isinstance(manifest_sources, list):
        raise ValueError("manifest must define a sources list")

    records: list[BucketHealthRecord] = []
    for bucket in BUCKETS:
        bucket_sources = [
            source
            for source in manifest_sources
            if isinstance(source, Mapping) and source.get("bucket") == bucket
        ]
        eligible_sources = [source for source in bucket_sources if _is_eligible_source(source)]
        eligible_names = {str(source["name"]) for source in eligible_sources}
        relevant_attempts = [
            attempt
            for attempt in source_attempts
            if str(attempt.get("source_name")) in eligible_names
        ]
        failed_attempts = [
            attempt for attempt in relevant_attempts if attempt.get("status") == "failed"
        ]
        item_count = counts[bucket]

        if not eligible_sources:
            if bucket_sources:
                detail = "no eligible approved source; non-counting manifest entries: " + ", ".join(
                    (
                        f"{source['name']} "
                        f"({source.get('implemented_status')}, {source.get('disposition')})"
                    )
                    for source in bucket_sources
                )
            else:
                detail = "no eligible approved source; manifest has no entries"
            records.append(
                BucketHealthRecord(
                    bucket=bucket,
                    status="degraded-no-approved-source",
                    item_count=item_count,
                    detail=detail,
                )
            )
            continue

        if item_count > 0:
            records.append(
                BucketHealthRecord(
                    bucket=bucket,
                    status="healthy",
                    item_count=item_count,
                    detail=f"{item_count} fresh item(s) collected",
                )
            )
            continue

        if failed_attempts:
            detail = "failed eligible sources: " + "; ".join(
                f"{attempt['source_name']} ({attempt.get('detail') or 'failed'})"
                for attempt in failed_attempts
            )
            records.append(
                BucketHealthRecord(
                    bucket=bucket,
                    status="degraded-source-failure",
                    item_count=item_count,
                    detail=detail,
                )
            )
            continue

        if relevant_attempts:
            attempted_sources = ", ".join(
                str(attempt["source_name"])
                for attempt in relevant_attempts
                if attempt.get("status") in {"collected", "dry-run"}
            )
            detail = "eligible sources produced zero fresh items"
            if attempted_sources:
                detail = f"{detail}: {attempted_sources}"
            records.append(
                BucketHealthRecord(
                    bucket=bucket,
                    status="degraded-sparse-day",
                    item_count=item_count,
                    detail=detail,
                )
            )
            continue

        records.append(
            BucketHealthRecord(
                bucket=bucket,
                status="degraded-source-failure",
                item_count=item_count,
                detail="no eligible source attempt recorded",
            )
        )

    return records


def compute_source_summary(
    *,
    manifest: Mapping[str, object],
    source_attempts: list[Mapping[str, object]],
    items: list[NormalizedItem],
) -> dict[str, object]:
    bucket_health = compute_bucket_health(
        manifest=manifest,
        source_attempts=source_attempts,
        items=items,
    )

    return {
        "total_items_seen": len(items),
        "source_failures": _source_failures(source_attempts),
        "bucket_counts": _bucket_counts(items),
        "bucket_health": {record.bucket: record.status for record in bucket_health},
        "coverage_notes": [
            f"{record.bucket}: {record.detail}"
            for record in bucket_health
            if record.status != "healthy"
        ],
    }


def write_source_summary(path: Path, summary: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def apply_deterministic_source_summary(digest_path: Path, summary_path: Path) -> None:
    payload = json.loads(digest_path.read_text(encoding="utf-8"))
    payload["source_summary"] = json.loads(summary_path.read_text(encoding="utf-8"))
    digest_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

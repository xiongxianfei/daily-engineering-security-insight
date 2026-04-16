from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from daily_insight.models import BucketName, CatalogStatus, SourceCatalog, SourceCatalogEntry

CATALOG_STATUSES: tuple[CatalogStatus, ...] = (
    "runtime-approved",
    "reviewed-candidate",
    "deferred",
    "rejected",
)
COUNTED_CATALOG_STATUSES: tuple[CatalogStatus, ...] = (
    "runtime-approved",
    "reviewed-candidate",
    "deferred",
)
BUCKETS: tuple[BucketName, ...] = (
    "software-engineering",
    "security",
    "ai-for-security",
    "security-for-ai",
)


def default_catalog_path() -> Path:
    return Path(__file__).resolve().parents[1] / "configs" / "source-catalog.json"


def load_source_catalog(path: Path | None = None) -> SourceCatalog:
    catalog_path = path or default_catalog_path()
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    return SourceCatalog.model_validate(payload)


def filter_catalog_entries(
    entries: list[SourceCatalogEntry],
    *,
    bucket: BucketName | None = None,
    status: CatalogStatus | None = None,
) -> list[SourceCatalogEntry]:
    filtered = entries
    if bucket is not None:
        filtered = [entry for entry in filtered if entry.bucket == bucket]
    if status is not None:
        filtered = [entry for entry in filtered if entry.catalog_status == status]
    return filtered


def bucket_counts(entries: list[SourceCatalogEntry]) -> dict[BucketName, int]:
    counts = Counter(entry.bucket for entry in entries)
    return {bucket: counts.get(bucket, 0) for bucket in BUCKETS}


def status_counts(entries: list[SourceCatalogEntry]) -> dict[CatalogStatus, int]:
    counts = Counter(entry.catalog_status for entry in entries)
    return {status: counts.get(status, 0) for status in CATALOG_STATUSES}

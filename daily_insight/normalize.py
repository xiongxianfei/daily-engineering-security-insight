from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256

from daily_insight.models import BucketName, NormalizedItem


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_item(
    *,
    source_name: str,
    bucket: BucketName,
    title: str,
    url: str,
    summary: str = "",
    published_at: str | None = None,
    tags: list[str] | None = None,
) -> NormalizedItem:
    stable_key = f"{source_name}|{title}|{url}"
    item_id = sha256(stable_key.encode("utf-8")).hexdigest()[:16]
    return NormalizedItem(
        id=item_id,
        source=source_name,
        bucket_hint=bucket,
        title=title.strip(),
        url=url.strip(),
        summary=summary.strip(),
        published_at=published_at,
        collected_at=utc_now_iso(),
        tags=tags or [],
    )

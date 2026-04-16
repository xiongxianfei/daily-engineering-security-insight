from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Sequence
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

from daily_insight.config import enabled_source_configs, load_source_configs
from daily_insight.models import NormalizedItem, SourceConfig
from daily_insight.normalize import normalize_item
from daily_insight.source_health import (
    compute_bucket_health,
    compute_source_summary,
    load_source_manifest,
    write_source_summary,
)
from daily_insight.storage import StateStore

_BROWSER_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
)
_CISA_KEV_HUMAN_URL = "https://www.cisa.gov/known-exploited-vulnerabilities-catalog"


def _find_text(element: ET.Element, names: list[str]) -> str:
    for name in names:
        child = element.find(name)
        if child is not None and child.text:
            return child.text.strip()
    return ""


def _fetch_payload(source: SourceConfig) -> bytes:
    request = Request(
        str(source.url),
        headers={
            "User-Agent": _BROWSER_USER_AGENT,
            "Accept": (
                "application/rss+xml, application/atom+xml, application/json, "
                "text/xml, application/xml, */*"
            ),
        },
    )
    with urlopen(request, timeout=20) as response:
        return response.read()


def _parse_published_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if not text:
        return None

    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        pass

    try:
        return parsedate_to_datetime(text)
    except (TypeError, ValueError):
        return None


def _filter_items_for_freshness(
    items: list[NormalizedItem], *, digest_date: str, freshness_mode: str
) -> list[NormalizedItem]:
    if freshness_mode != "published-date":
        return items

    fresh_items: list[NormalizedItem] = []
    for item in items:
        parsed = _parse_published_datetime(item.published_at)
        if parsed is None:
            continue
        if parsed.tzinfo is not None:
            normalized_date = parsed.astimezone(timezone.utc).date().isoformat()
        else:
            normalized_date = parsed.date().isoformat()
        if normalized_date == digest_date:
            fresh_items.append(item)
    return fresh_items


def collect_rss(source: SourceConfig) -> list[NormalizedItem]:
    payload = _fetch_payload(source)
    root = ET.fromstring(payload)
    items: list[NormalizedItem] = []

    rss_items = root.findall("./channel/item")
    if rss_items:
        for entry in rss_items:
            items.append(
                normalize_item(
                    source_name=source.name,
                    bucket=source.bucket,
                    title=_find_text(entry, ["title"]),
                    url=_find_text(entry, ["link"]),
                    summary=_find_text(entry, ["description"]),
                    published_at=_find_text(entry, ["pubDate"]) or None,
                    tags=[],
                )
            )
        return items

    atom_entries = root.findall("{http://www.w3.org/2005/Atom}entry") or root.findall("entry")
    for entry in atom_entries:
        link = ""
        for link_node in entry.findall("{http://www.w3.org/2005/Atom}link") + entry.findall("link"):
            href = link_node.attrib.get("href")
            if href:
                link = href.strip()
                break
        items.append(
            normalize_item(
                source_name=source.name,
                bucket=source.bucket,
                title=_find_text(entry, ["{http://www.w3.org/2005/Atom}title", "title"]),
                url=link,
                summary=_find_text(
                    entry,
                    [
                        "{http://www.w3.org/2005/Atom}summary",
                        "{http://www.w3.org/2005/Atom}content",
                        "summary",
                        "content",
                    ],
                ),
                published_at=_find_text(
                    entry,
                    [
                        "{http://www.w3.org/2005/Atom}updated",
                        "{http://www.w3.org/2005/Atom}published",
                        "updated",
                        "published",
                    ],
                )
                or None,
                tags=[],
            )
        )
    return items


def _collect_cisa_kev(
    source: SourceConfig, payload: dict[str, object], *, digest_date: str
) -> list[NormalizedItem]:
    entries = payload.get("vulnerabilities")
    if not isinstance(entries, list):
        raise ValueError("KEV payload missing vulnerabilities list")

    items: list[NormalizedItem] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        date_added = str(entry.get("dateAdded", "")).strip()
        if date_added != digest_date:
            continue

        cve_id = str(entry.get("cveID", "")).strip()
        vendor = str(entry.get("vendorProject", "")).strip()
        product = str(entry.get("product", "")).strip()
        vulnerability_name = str(entry.get("vulnerabilityName", "")).strip()
        title_parts = [part for part in [cve_id, vendor, product] if part]
        title = " ".join(title_parts)
        if vulnerability_name:
            title = f"{title}: {vulnerability_name}" if title else vulnerability_name

        summary_parts = [
            str(entry.get("shortDescription", "")).strip(),
            (
                f"Required action: {str(entry.get('requiredAction', '')).strip()}"
                if str(entry.get("requiredAction", "")).strip()
                else ""
            ),
            (
                f"Due date: {str(entry.get('dueDate', '')).strip()}"
                if str(entry.get("dueDate", "")).strip()
                else ""
            ),
        ]
        summary = " ".join(part for part in summary_parts if part)
        tags = ["kev"]
        if cve_id:
            tags.append(cve_id)

        items.append(
            normalize_item(
                source_name=source.name,
                bucket=source.bucket,
                title=title,
                url=_CISA_KEV_HUMAN_URL,
                summary=summary,
                published_at=date_added or None,
                tags=tags,
            )
        )
    return items


def collect_json(source: SourceConfig, *, digest_date: str) -> list[NormalizedItem]:
    payload = json.loads(_fetch_payload(source))

    if source.name == "cisa-kev-catalog":
        return _collect_cisa_kev(source, payload, digest_date=digest_date)

    raise ValueError(f"unsupported json source: {source.name}")


def collect_sources(
    *,
    date: str,
    config_path: Path,
    out_dir: Path | None = None,
    dry_run: bool = False,
    state_db_path: Path | None = None,
) -> int:
    sources = enabled_source_configs(load_source_configs(config_path))
    manifest = load_source_manifest()
    manifest_sources_by_name = {
        str(entry["name"]): entry
        for entry in manifest.get("sources", [])
        if isinstance(entry, dict) and "name" in entry
    }
    state_store = StateStore(state_db_path or Path("state") / "daily_insight.db")
    run_id = state_store.record_run(digest_date=date, status="started")

    total_items = 0
    all_items: list[NormalizedItem] = []
    blocking_failure = False
    source_attempts: list[dict[str, object]] = []

    for source in sources:
        if dry_run and "example.com" in str(source.url):
            detail = "placeholder-safe example source"
            state_store.record_source_attempt(
                run_id=run_id,
                source_name=source.name,
                bucket=source.bucket,
                status="dry-run",
                detail=detail,
            )
            source_attempts.append(
                {
                    "source_name": source.name,
                    "bucket": source.bucket,
                    "status": "dry-run",
                    "detail": detail,
                }
            )
            print(f"dry-run source ok: {source.name}")
            continue

        try:
            if source.transport == "rss":
                items = collect_rss(source)
            else:
                items = collect_json(source, digest_date=date)
        except Exception as exc:
            detail = str(exc)
            state_store.record_source_attempt(
                run_id=run_id,
                source_name=source.name,
                bucket=source.bucket,
                status="failed",
                detail=detail,
            )
            source_attempts.append(
                {
                    "source_name": source.name,
                    "bucket": source.bucket,
                    "status": "failed",
                    "detail": detail,
                }
            )
            print(f"source failed: {source.name}: {exc}")
            if source.failure_policy == "fail":
                blocking_failure = True
            continue

        manifest_source = manifest_sources_by_name.get(source.name, {})
        fresh_items = _filter_items_for_freshness(
            items,
            digest_date=date,
            freshness_mode=str(manifest_source.get("freshness_mode", "")),
        )
        capped_items = fresh_items[: source.max_items_per_source]
        detail = f"{len(capped_items)} of {len(items)} items kept"
        state_store.record_source_attempt(
            run_id=run_id,
            source_name=source.name,
            bucket=source.bucket,
            status="collected",
            detail=detail,
        )
        source_attempts.append(
            {
                "source_name": source.name,
                "bucket": source.bucket,
                "status": "collected",
                "detail": detail,
            }
        )
        all_items.extend(capped_items)
        total_items += len(capped_items)
        print(f"collected {len(capped_items)} items from {source.name}")

    bucket_health = compute_bucket_health(
        manifest=manifest,
        source_attempts=source_attempts,
        items=all_items,
    )
    source_summary = compute_source_summary(
        manifest=manifest,
        source_attempts=source_attempts,
        items=all_items,
    )
    for record in bucket_health:
        state_store.record_bucket_health(
            run_id=run_id,
            bucket=record.bucket,
            status=record.status,
            item_count=record.item_count,
            detail=record.detail,
        )
    print("source health summary:")
    for record in bucket_health:
        detail = f" ({record.detail})" if record.status != "healthy" else ""
        print(
            f"  {record.bucket}: {record.status} "
            f"[{record.item_count} item(s)]{detail}"
        )

    if dry_run:
        state_store.update_run_status(
            run_id=run_id,
            status="failed" if blocking_failure else "completed",
        )
        print(f"dry-run ok; normalized {total_items} items")
        return 1 if blocking_failure else 0

    if blocking_failure:
        state_store.update_run_status(run_id=run_id, status="failed")
        return 1

    resolved_out_dir = out_dir if out_dir is not None else Path("inputs") / date
    resolved_out_dir.mkdir(parents=True, exist_ok=True)
    out_path = resolved_out_dir / "items.jsonl"
    summary_path = resolved_out_dir / "source_summary.json"

    with out_path.open("w", encoding="utf-8") as handle:
        for item in all_items:
            handle.write(json.dumps(item.model_dump(mode="json"), ensure_ascii=False) + "\n")
            state_store.record_dedupe_item(
                item_id=item.id,
                source_name=item.source,
                latest_url=str(item.url),
            )
    write_source_summary(summary_path, source_summary)

    state_store.update_run_status(run_id=run_id, status="completed")
    print(f"wrote {total_items} items to {out_path}")
    print(f"wrote source summary to {summary_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Collect and normalize daily insight sources.")
    parser.add_argument("--date", default="1970-01-01", help="Digest date (YYYY-MM-DD)")
    parser.add_argument("--config", required=True, help="Path to source config JSON")
    parser.add_argument("--out-dir", help="Output directory; defaults to inputs/<date>")
    parser.add_argument("--state-db", help="SQLite path for local collection state")
    parser.add_argument(
        "--dry-run", action="store_true", help="Validate config without writing output"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    out_dir = Path(args.out_dir) if args.out_dir else None
    state_db_path = Path(args.state_db) if args.state_db else None
    return collect_sources(
        date=args.date,
        config_path=Path(args.config),
        out_dir=out_dir,
        dry_run=args.dry_run,
        state_db_path=state_db_path,
    )

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence
from urllib.request import urlopen
from xml.etree import ElementTree as ET

from daily_insight.config import enabled_source_configs, load_source_configs
from daily_insight.models import NormalizedItem, SourceConfig
from daily_insight.normalize import normalize_item
from daily_insight.storage import StateStore


def _find_text(element: ET.Element, names: list[str]) -> str:
    for name in names:
        child = element.find(name)
        if child is not None and child.text:
            return child.text.strip()
    return ""


def collect_rss(source: SourceConfig) -> list[NormalizedItem]:
    with urlopen(str(source.url), timeout=20) as response:
        payload = response.read()

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


def collect_sources(
    *,
    date: str,
    config_path: Path,
    out_dir: Path | None = None,
    dry_run: bool = False,
    state_db_path: Path | None = None,
) -> int:
    sources = enabled_source_configs(load_source_configs(config_path))
    state_store = StateStore(state_db_path or Path("state") / "daily_insight.db")
    run_id = state_store.record_run(digest_date=date, status="started")

    total_items = 0
    all_items: list[NormalizedItem] = []
    blocking_failure = False

    for source in sources:
        if dry_run and "example.com" in str(source.url):
            state_store.record_source_attempt(
                run_id=run_id,
                source_name=source.name,
                bucket=source.bucket,
                status="dry-run",
                detail="placeholder-safe example source",
            )
            print(f"dry-run source ok: {source.name}")
            continue

        try:
            items = collect_rss(source)
        except Exception as exc:
            state_store.record_source_attempt(
                run_id=run_id,
                source_name=source.name,
                bucket=source.bucket,
                status="failed",
                detail=str(exc),
            )
            print(f"source failed: {source.name}: {exc}")
            if source.failure_policy == "fail":
                blocking_failure = True
            continue

        capped_items = items[: source.max_items_per_source]
        state_store.record_source_attempt(
            run_id=run_id,
            source_name=source.name,
            bucket=source.bucket,
            status="collected",
            detail=f"{len(capped_items)} of {len(items)} items kept",
        )
        all_items.extend(capped_items)
        total_items += len(capped_items)
        print(f"collected {len(capped_items)} items from {source.name}")

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

    with out_path.open("w", encoding="utf-8") as handle:
        for item in all_items:
            handle.write(json.dumps(item.model_dump(mode="json"), ensure_ascii=False) + "\n")
            state_store.record_dedupe_item(
                item_id=item.id,
                source_name=item.source,
                latest_url=str(item.url),
            )

    state_store.update_run_status(run_id=run_id, status="completed")
    print(f"wrote {total_items} items to {out_path}")
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

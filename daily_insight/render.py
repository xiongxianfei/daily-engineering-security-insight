from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence


def render_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(payload["overview_markdown"].rstrip())
    lines.append("")
    lines.append("## Top items")
    lines.append("")
    for item in payload["top_items"]:
        lines.append(f"### [{item['bucket']}] {item['title']}")
        lines.append(f"- Source: {item['source']}")
        lines.append(f"- URL: {item['source_url']}")
        if item.get("published_at"):
            lines.append(f"- Published: {item['published_at']}")
        lines.append(f"- Confidence: {item['confidence']}")
        lines.append(f"- Relevance: {item['team_relevance']}")
        lines.append(f"- Why it matters: {item['why_it_matters']}")
        lines.append(f"- Recommended action: {item['recommended_action']}")
        lines.append("")
    lines.append("## Action now")
    lines.append("")
    for action in payload["action_now"]:
        lines.append(
            f"- **{action['title']}** - {action['reason']} (owner hint: {action['owner_hint']})"
        )
    lines.append("")
    lines.append("## Watchlist")
    lines.append("")
    for watch in payload["watchlist"]:
        lines.append(
            f"- **{watch['title']}** - {watch['reason']} "
            f"(revisit in {watch['revisit_in_days']} days)"
        )
    lines.append("")
    lines.append("## Source summary")
    lines.append("")
    lines.append(f"- Total items seen: {payload['source_summary']['total_items_seen']}")
    failures = payload["source_summary"]["source_failures"]
    lines.append(f"- Source failures: {', '.join(failures) if failures else 'none'}")
    lines.append("- Bucket counts:")
    for bucket, count in payload["source_summary"]["bucket_counts"].items():
        lines.append(f"  - {bucket}: {count}")
    lines.append("- Bucket health:")
    for bucket, status in payload["source_summary"]["bucket_health"].items():
        lines.append(f"  - {bucket}: {status}")
    notes = payload["source_summary"]["coverage_notes"]
    lines.append(f"- Coverage notes: {', '.join(notes) if notes else 'none'}")
    return "\n".join(lines).rstrip() + "\n"


def render_digest(input_path: Path, output_path: Path) -> Path:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_markdown(payload), encoding="utf-8")
    print(f"rendered {output_path}")
    return output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render a Markdown digest from the structured JSON report."
    )
    parser.add_argument("input_json", help="Path to the structured digest JSON")
    parser.add_argument("output_md", help="Path to the rendered Markdown file")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    render_digest(Path(args.input_json), Path(args.output_md))
    return 0

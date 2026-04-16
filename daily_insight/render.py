from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any, Sequence


def _escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _render_overview_html(overview_markdown: str) -> str:
    blocks: list[str] = []
    for raw_line in overview_markdown.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("# "):
            blocks.append(f"<h2>{_escape(line[2:])}</h2>")
        elif line.startswith("## "):
            blocks.append(f"<h3>{_escape(line[3:])}</h3>")
        else:
            blocks.append(f"<p>{_escape(line)}</p>")
    return "\n        ".join(blocks)


def _render_top_item_html(item: dict[str, Any]) -> str:
    item_lines = [
        "        <article class=\"top-item\">",
        f"          <h3>[{_escape(item['bucket'])}] {_escape(item['title'])}</h3>",
        "          <ul>",
        f"            <li><strong>Source:</strong> {_escape(item['source'])}</li>",
        (
            "            <li><strong>URL:</strong> "
            f"<a href=\"{_escape(item['source_url'])}\">{_escape(item['source_url'])}</a></li>"
        ),
    ]
    if item.get("published_at"):
        item_lines.append(
            "            <li><strong>Published:</strong> "
            f"{_escape(item['published_at'])}</li>"
        )
    item_lines.extend(
        [
            "            <li><strong>Confidence:</strong> "
            f"{_escape(item['confidence'])}</li>",
            "            <li><strong>Relevance:</strong> "
            f"{_escape(item['team_relevance'])}</li>",
            "            <li><strong>Why it matters:</strong> "
            f"{_escape(item['why_it_matters'])}</li>",
            "            <li><strong>Recommended action:</strong> "
            f"{_escape(item['recommended_action'])}</li>",
            "          </ul>",
            "        </article>",
        ]
    )
    return "\n".join(item_lines)


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
    lines.append(
        "- Source summary reflects collected source entries for the requested date, "
        "not the expanded top-item count."
    )
    lines.append(
        f"- Total collected source entries seen: {payload['source_summary']['total_items_seen']}"
    )
    lines.append(f"- Top items surfaced: {len(payload['top_items'])}")
    failures = payload["source_summary"]["source_failures"]
    lines.append(f"- Source failures: {', '.join(failures) if failures else 'none'}")
    lines.append("- Collected source entries by bucket:")
    for bucket, count in payload["source_summary"]["bucket_counts"].items():
        lines.append(f"  - {bucket}: {count}")
    lines.append("- Bucket health:")
    for bucket, status in payload["source_summary"]["bucket_health"].items():
        lines.append(f"  - {bucket}: {status}")
    notes = payload["source_summary"]["coverage_notes"]
    lines.append(f"- Coverage notes: {', '.join(notes) if notes else 'none'}")
    return "\n".join(lines).rstrip() + "\n"


def render_html(payload: dict[str, Any]) -> str:
    date = _escape(payload["date"])
    overview_html = _render_overview_html(payload["overview_markdown"])

    top_items = "\n".join([_render_top_item_html(item) for item in payload["top_items"]])

    action_now = "\n".join(
        [
            (
                "        <li>"
                f"<strong>{_escape(item['title'])}</strong> - {_escape(item['reason'])} "
                f"(owner hint: {_escape(item['owner_hint'])})"
                "</li>"
            )
            for item in payload["action_now"]
        ]
    )

    watchlist = "\n".join(
        [
            (
                "        <li>"
                f"<strong>{_escape(item['title'])}</strong> - {_escape(item['reason'])} "
                f"(revisit in {_escape(item['revisit_in_days'])} days)"
                "</li>"
            )
            for item in payload["watchlist"]
        ]
    )

    bucket_counts = "\n".join(
        [
            f"          <li>{_escape(bucket)}: {_escape(count)}</li>"
            for bucket, count in payload["source_summary"]["bucket_counts"].items()
        ]
    )
    bucket_health = "\n".join(
        [
            f"          <li>{_escape(bucket)}: {_escape(status)}</li>"
            for bucket, status in payload["source_summary"]["bucket_health"].items()
        ]
    )
    source_failures = payload["source_summary"]["source_failures"]
    coverage_notes = payload["source_summary"]["coverage_notes"]
    source_failures_text = ", ".join(source_failures) if source_failures else "none"
    coverage_notes_html = "\n".join(
        [f"          <li>{_escape(note)}</li>" for note in coverage_notes]
    )
    if not coverage_notes_html:
        coverage_notes_html = "          <li>none</li>"

    return (
        "<!DOCTYPE html>\n"
        "<html lang=\"en\">\n"
        "  <head>\n"
        "    <meta charset=\"utf-8\">\n"
        "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"    <title>Daily insight for {date}</title>\n"
        "    <style>\n"
        "      :root { color-scheme: light; }\n"
        "      body { margin: 0; font-family: Georgia, 'Times New Roman', serif;\n"
        "             background: #f5f1e8; color: #1e1a16; }\n"
        "      main { max-width: 900px; margin: 0 auto; padding: 2rem 1rem 4rem; }\n"
        "      h1, h2, h3 { line-height: 1.2; }\n"
        "      h1 { margin-bottom: 0.5rem; }\n"
        "      section { background: #fffdf8; border: 1px solid #d7cfc1;\n"
        "                border-radius: 12px; padding: 1rem 1.25rem; margin: 1rem 0; }\n"
        "      article { border-top: 1px solid #e5dece; padding-top: 1rem; margin-top: 1rem; }\n"
        "      article:first-of-type { border-top: 0; padding-top: 0; margin-top: 0; }\n"
        "      ul { padding-left: 1.25rem; }\n"
        "      li { margin: 0.35rem 0; overflow-wrap: anywhere; }\n"
        "      a { color: #0b5c7a; }\n"
        "      .lede { color: #5a5146; margin-top: 0; }\n"
        "      @media (max-width: 640px) {\n"
        "        body { font-size: 16px; }\n"
        "        section { padding: 0.9rem 1rem; }\n"
        "      }\n"
        "    </style>\n"
        "  </head>\n"
        "  <body>\n"
        "    <main>\n"
        f"      <h1>Daily insight for {date}</h1>\n"
        "      <p class=\"lede\">Browser-readable view derived from canonical digest JSON.</p>\n"
        "      <section aria-labelledby=\"overview-heading\">\n"
        "        <h2 id=\"overview-heading\">Overview</h2>\n"
        f"        {overview_html}\n"
        "      </section>\n"
        "      <section aria-labelledby=\"top-items-heading\">\n"
        "        <h2 id=\"top-items-heading\">Top items</h2>\n"
        f"{top_items}\n"
        "      </section>\n"
        "      <section aria-labelledby=\"action-now-heading\">\n"
        "        <h2 id=\"action-now-heading\">Action now</h2>\n"
        "        <ul>\n"
        f"{action_now}\n"
        "        </ul>\n"
        "      </section>\n"
        "      <section aria-labelledby=\"watchlist-heading\">\n"
        "        <h2 id=\"watchlist-heading\">Watchlist</h2>\n"
        "        <ul>\n"
        f"{watchlist}\n"
        "        </ul>\n"
        "      </section>\n"
        "      <section aria-labelledby=\"source-summary-heading\">\n"
        "        <h2 id=\"source-summary-heading\">Source summary</h2>\n"
        "        <p>Source summary reflects collected source entries for the requested date, "
        "not the expanded top-item count.</p>\n"
        "        <ul>\n"
        "          <li><strong>Total collected source entries seen:</strong> "
        f"{_escape(payload['source_summary']['total_items_seen'])}</li>\n"
        "          <li><strong>Top items surfaced:</strong> "
        f"{_escape(len(payload['top_items']))}</li>\n"
        "          <li><strong>Source failures:</strong> "
        f"{_escape(source_failures_text)}</li>\n"
        "        </ul>\n"
        "        <h3>Collected source entries by bucket</h3>\n"
        "        <ul>\n"
        f"{bucket_counts}\n"
        "        </ul>\n"
        "        <h3>Bucket health</h3>\n"
        "        <ul>\n"
        f"{bucket_health}\n"
        "        </ul>\n"
        "        <h3>Coverage notes</h3>\n"
        "        <ul>\n"
        f"{coverage_notes_html}\n"
        "        </ul>\n"
        "      </section>\n"
        "    </main>\n"
        "  </body>\n"
        "</html>\n"
    )


def render_digest(input_path: Path, output_path: Path) -> Path:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_markdown(payload), encoding="utf-8")
    print(f"rendered {output_path}")
    return output_path


def render_html_digest(input_path: Path, output_path: Path) -> Path:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_html(payload), encoding="utf-8")
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

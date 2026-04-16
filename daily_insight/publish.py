from __future__ import annotations

import json
import os
import shutil
import tempfile
from datetime import date as date_type
from pathlib import Path
from typing import Any

from daily_insight.render import render_html


def _load_digest_payload(source_root: Path, date: str) -> dict[str, Any]:
    digest_path = source_root / date / "digest.json"
    if not digest_path.is_file():
        raise FileNotFoundError(f"missing canonical digest JSON: {digest_path}")
    return json.loads(digest_path.read_text(encoding="utf-8"))


def _is_published_date_dir(path: Path) -> bool:
    if not path.is_dir():
        return False
    try:
        date_type.fromisoformat(path.name)
    except ValueError:
        return False
    return (path / "index.html").is_file()


def _render_archive_html(published_dates: list[str], latest_date: str) -> str:
    date_links = "\n".join(
        [
            (
                "          <li>"
                f"<a href=\"./{date}/\">{date}</a>"
                f"{' <strong>(latest)</strong>' if date == latest_date else ''}"
                "</li>"
            )
            for date in published_dates
        ]
    )
    return (
        "<!DOCTYPE html>\n"
        "<html lang=\"en\">\n"
        "  <head>\n"
        "    <meta charset=\"utf-8\">\n"
        "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        "    <title>Daily insight archive</title>\n"
        "    <style>\n"
        "      :root { color-scheme: light; }\n"
        "      body { margin: 0; font-family: Georgia, 'Times New Roman', serif;\n"
        "             background: #f5f1e8; color: #1e1a16; }\n"
        "      main { max-width: 720px; margin: 0 auto; padding: 2rem 1rem 4rem; }\n"
        "      section { background: #fffdf8; border: 1px solid #d7cfc1;\n"
        "                border-radius: 12px; padding: 1rem 1.25rem; margin: 1rem 0; }\n"
        "      ul { padding-left: 1.25rem; }\n"
        "      li { margin: 0.4rem 0; }\n"
        "      a { color: #0b5c7a; }\n"
        "      .lede { color: #5a5146; margin-top: 0; }\n"
        "    </style>\n"
        "  </head>\n"
        "  <body>\n"
        "    <main>\n"
        "      <h1>Daily insight archive</h1>\n"
        "      <p class=\"lede\">Published browser views derived from canonical digest JSON.</p>\n"
        "      <section aria-labelledby=\"latest-heading\">\n"
        "        <h2 id=\"latest-heading\">Latest published digest</h2>\n"
        f"        <p><a href=\"./latest/\">{latest_date}</a></p>\n"
        "      </section>\n"
        "      <section aria-labelledby=\"published-dates-heading\">\n"
        "        <h2 id=\"published-dates-heading\">Published dates</h2>\n"
        "        <ul>\n"
        f"{date_links}\n"
        "        </ul>\n"
        "      </section>\n"
        "    </main>\n"
        "  </body>\n"
        "</html>\n"
    )


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _build_staging_site(
    source_root: Path,
    date: str,
    site_root: Path,
    staging_root: Path,
) -> None:
    if site_root.exists():
        shutil.copytree(site_root, staging_root, dirs_exist_ok=True)

    payload = _load_digest_payload(source_root=source_root, date=date)
    rendered_digest = render_html(payload)
    _write_text(staging_root / date / "index.html", rendered_digest)
    _write_text(staging_root / "latest" / "index.html", rendered_digest)

    published_dates = sorted(
        [path.name for path in staging_root.iterdir() if _is_published_date_dir(path)],
        reverse=True,
    )
    _write_text(
        staging_root / "index.html",
        _render_archive_html(published_dates=published_dates, latest_date=date),
    )


def publish_site(source_root: Path, date: str, site_root: Path) -> Path:
    _load_digest_payload(source_root=source_root, date=date)
    site_root.parent.mkdir(parents=True, exist_ok=True)

    staging_root = Path(
        tempfile.mkdtemp(prefix=f".{site_root.name}.staging-", dir=site_root.parent)
    )
    backup_root = site_root.parent / f".{site_root.name}.backup"
    backup_created = False

    try:
        _build_staging_site(
            source_root=source_root,
            date=date,
            site_root=site_root,
            staging_root=staging_root,
        )
        if site_root.exists():
            if backup_root.exists():
                shutil.rmtree(backup_root)
            os.replace(site_root, backup_root)
            backup_created = True
            try:
                os.replace(staging_root, site_root)
            except Exception:
                os.replace(backup_root, site_root)
                backup_created = False
                raise
        else:
            os.replace(staging_root, site_root)

        return site_root
    finally:
        if staging_root.exists():
            shutil.rmtree(staging_root, ignore_errors=True)
        if backup_created and backup_root.exists():
            shutil.rmtree(backup_root, ignore_errors=True)

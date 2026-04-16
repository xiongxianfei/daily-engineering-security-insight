from __future__ import annotations

import subprocess
from datetime import date as date_type
from json import JSONDecodeError
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError

from daily_insight.collect import collect_sources
from daily_insight.publish import publish_site
from daily_insight.render import render_digest, render_html_digest
from daily_insight.source_catalog import (
    BUCKETS,
    CATALOG_STATUSES,
    bucket_counts,
    filter_catalog_entries,
    load_source_catalog,
    status_counts,
)
from daily_insight.source_health import apply_deterministic_source_summary
from daily_insight.storage import StateStore

app = typer.Typer(
    add_completion=False,
    help="Daily engineering and security insight tooling.",
    no_args_is_help=True,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _prompt_path(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _validate_bucket(bucket: str | None) -> str | None:
    if bucket is None:
        return None
    if bucket not in BUCKETS:
        raise typer.BadParameter(f"bucket must be one of: {', '.join(BUCKETS)}")
    return bucket


def _validate_catalog_status(status: str | None) -> str | None:
    if status is None:
        return None
    if status not in CATALOG_STATUSES:
        raise typer.BadParameter(f"status must be one of: {', '.join(CATALOG_STATUSES)}")
    return status


@app.command()
def collect(
    config: Annotated[Path, typer.Option(help="Path to the source config JSON")],
    date: Annotated[str, typer.Option(help="Digest date (YYYY-MM-DD)")] = "1970-01-01",
    out_dir: Annotated[
        Path | None, typer.Option(help="Output directory; defaults to inputs/<date>")
    ] = None,
    state_db: Annotated[
        Path | None, typer.Option(help="SQLite path for local collection state")
    ] = None,
    dry_run: Annotated[bool, typer.Option(help="Validate config without writing output")] = False,
) -> None:
    raise typer.Exit(
        collect_sources(
            date=date,
            config_path=config,
            out_dir=out_dir,
            dry_run=dry_run,
            state_db_path=state_db,
        )
    )


@app.command()
def render(
    input_json: Annotated[Path, typer.Argument(help="Path to the structured digest JSON")],
    output_md: Annotated[Path, typer.Argument(help="Path to the rendered Markdown file")],
) -> None:
    render_digest(input_json, output_md)


@app.command("render-html")
def render_html(
    input_json: Annotated[Path, typer.Argument(help="Path to the structured digest JSON")],
    output_html: Annotated[Path, typer.Argument(help="Path to the rendered HTML file")],
) -> None:
    try:
        render_html_digest(input_json, output_html)
    except (
        FileNotFoundError,
        JSONDecodeError,
        KeyError,
        TypeError,
        ValueError,
        subprocess.CalledProcessError,
    ) as exc:
        typer.echo(f"browser HTML render failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc


@app.command()
def sources(
    bucket: Annotated[str | None, typer.Option(help="Filter by owning bucket")] = None,
    status: Annotated[str | None, typer.Option(help="Filter by catalog status")] = None,
    catalog: Annotated[
        Path | None, typer.Option(help="Path to the reviewed source catalog JSON")
    ] = None,
) -> None:
    validated_bucket = _validate_bucket(bucket)
    validated_status = _validate_catalog_status(status)

    try:
        source_catalog = load_source_catalog(catalog)
    except (FileNotFoundError, JSONDecodeError, ValidationError, ValueError) as exc:
        typer.echo(f"source catalog load failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    entries = filter_catalog_entries(
        source_catalog.sources,
        bucket=validated_bucket,
        status=validated_status,
    )
    resolved_catalog = catalog or (
        Path(__file__).resolve().parents[1] / "configs" / "source-catalog.json"
    )

    typer.echo("reviewed source catalog")
    typer.echo(
        "runtime-approved subset remains the only set that drives live collection "
        "and source sufficiency."
    )
    typer.echo(f"catalog path: {resolved_catalog}")
    typer.echo(f"total reviewed entries: {len(source_catalog.sources)}")
    typer.echo(f"filtered sources: {len(entries)}")
    typer.echo(
        f"filters: bucket={validated_bucket or 'all'}, status={validated_status or 'all'}"
    )
    typer.echo("status summary:")
    for current_status, count in status_counts(entries).items():
        typer.echo(f"- {current_status}: {count}")
    typer.echo("bucket summary:")
    for current_bucket, count in bucket_counts(entries).items():
        typer.echo(f"- {current_bucket}: {count}")
    typer.echo("sources:")
    for entry in entries:
        machine_readable = "yes" if entry.machine_readable else "no"
        typer.echo(
            f"- {entry.name} | bucket={entry.bucket} | status={entry.catalog_status} "
            f"| transport={entry.transport} | machine-readable={machine_readable}"
        )


@app.command("publish-site")
def publish_browser_site(
    date: Annotated[str, typer.Option(help="Digest date (YYYY-MM-DD)")],
    source_root: Annotated[
        Path, typer.Option(help="Root directory containing canonical digest outputs")
    ] = Path("outputs"),
    site_root: Annotated[
        Path, typer.Option(help="Generated browser site root")
    ] = Path("site"),
) -> None:
    try:
        published_root = publish_site(source_root=source_root, date=date, site_root=site_root)
    except (FileNotFoundError, JSONDecodeError, KeyError, TypeError, ValueError, OSError) as exc:
        typer.echo(f"site publish failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"published browser site: {published_root}")


@app.command("source-health")
def source_health(
    date: Annotated[str, typer.Option(help="Digest date (YYYY-MM-DD)")],
    state_db: Annotated[
        Path | None, typer.Option(help="SQLite path for local collection state")
    ] = None,
) -> None:
    root = _repo_root()
    resolved_state_db = state_db or (root / "state" / "daily_insight.db")
    store = StateStore(resolved_state_db)
    latest_run = store.latest_run_for_date(digest_date=date)
    if latest_run is None:
        typer.echo(f"no recorded run for {date}", err=True)
        raise typer.Exit(code=1)

    run_id, run_status = latest_run
    bucket_rows = store.bucket_health_for_run(run_id=run_id)
    if not bucket_rows:
        typer.echo(f"no bucket health recorded for {date}", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"source health for {date} (run status: {run_status})")
    for bucket, status, item_count, detail in bucket_rows:
        line = f"- {bucket}: {status} [{item_count} item(s)]"
        if detail:
            line = f"{line} - {detail}"
        typer.echo(line)


@app.command()
def run(
    date: Annotated[
        str, typer.Option(help="Digest date (YYYY-MM-DD)")
    ] = date_type.today().isoformat(),
    config: Annotated[Path | None, typer.Option(help="Path to the source config JSON")] = None,
    prompt_path: Annotated[
        Path | None, typer.Option(help="Prompt file for the Codex synthesis step")
    ] = None,
    out_dir: Annotated[
        Path | None, typer.Option(help="Directory for rendered digest outputs")
    ] = None,
    in_dir: Annotated[
        Path | None, typer.Option(help="Directory for frozen collected inputs")
    ] = None,
    state_db: Annotated[
        Path | None, typer.Option(help="SQLite path for local collection state")
    ] = None,
) -> None:
    root = _repo_root()
    resolved_config = config or (root / "configs" / "sources.local.json")
    resolved_prompt = prompt_path or (root / "prompts" / "daily_digest_prompt.md")
    resolved_out_dir = out_dir or (root / "outputs" / date)
    resolved_in_dir = in_dir or (root / "inputs" / date)

    if not resolved_config.is_file():
        typer.echo(f"missing {resolved_config}; copy configs/sources.example.json first", err=True)
        raise typer.Exit(code=1)

    collect_exit_code = collect_sources(
        date=date,
        config_path=resolved_config,
        out_dir=resolved_in_dir,
        dry_run=False,
        state_db_path=state_db,
    )
    if collect_exit_code != 0:
        raise typer.Exit(code=collect_exit_code)

    resolved_out_dir.mkdir(parents=True, exist_ok=True)
    digest_json = resolved_out_dir / "digest.json"
    digest_md = resolved_out_dir / "digest.md"
    source_summary_json = resolved_in_dir / "source_summary.json"
    frozen_input_jsonl = resolved_in_dir / "items.jsonl"
    prompt = resolved_prompt.read_text(encoding="utf-8")
    subprocess.run(
        [
            "codex",
            "exec",
            "-C",
            str(root),
            "--skip-git-repo-check",
            "--full-auto",
            "--json",
            "--output-schema",
            str(root / "schemas" / "daily_insight.schema.json"),
            "--output-last-message",
            str(digest_json),
            (
                f"{prompt}\n\n"
                f"Digest date: {date}\n"
                f"Frozen input file: {_prompt_path(root, frozen_input_jsonl)}\n"
                f"Source summary file: {_prompt_path(root, source_summary_json)}\n\n"
                "Copy the source_summary object from the source summary file exactly. "
                "Do not change its counts, status names, or coverage notes.\n\n"
                "Wait for all requested work before returning. "
                "Produce only the final structured report."
            ),
        ],
        check=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
    )
    apply_deterministic_source_summary(digest_json, source_summary_json)
    render_digest(digest_json, digest_md)
    typer.echo("daily digest ready:")
    typer.echo(f"  {digest_json}")
    typer.echo(f"  {digest_md}")


def main() -> None:
    app()

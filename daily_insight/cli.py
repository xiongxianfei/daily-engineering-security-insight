from __future__ import annotations

from datetime import date as date_type
from pathlib import Path
from typing import Annotated

import typer

from daily_insight.collect import collect_sources
from daily_insight.render import render_digest
from daily_insight.synthesize import (
    EXIT_COLLECTION_FAILED,
    LifecycleCommandError,
    outputs_are_complete,
    synthesize_digest,
)

app = typer.Typer(
    add_completion=False,
    help="Daily engineering and security insight tooling.",
    no_args_is_help=True,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _resolve_state_db(root: Path, state_db: Path | None) -> Path | None:
    if state_db is not None:
        return state_db
    default_state_db = root / "state" / "daily_insight.db"
    if default_state_db.exists():
        return default_state_db
    return None


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
    timeout_seconds: Annotated[
        int | None,
        typer.Option(help="Synthesis timeout in seconds; defaults to env or 900"),
    ] = None,
) -> None:
    root = _repo_root()
    resolved_config = config or (root / "configs" / "sources.local.json")
    resolved_prompt = prompt_path or (root / "prompts" / "daily_digest_prompt.md")
    resolved_out_dir = out_dir or (root / "outputs" / date)
    resolved_in_dir = in_dir or (root / "inputs" / date)
    digest_json = resolved_out_dir / "digest.json"
    digest_md = resolved_out_dir / "digest.md"

    if outputs_are_complete(
        digest_json=digest_json,
        digest_md=digest_md,
        schema_path=root / "schemas" / "daily_insight.schema.json",
    ):
        typer.echo(f"date {date} is already complete")
        raise typer.Exit(code=0)

    if not (resolved_in_dir / "items.jsonl").is_file():
        if not resolved_config.is_file():
            typer.echo(
                f"missing {resolved_config}; copy configs/sources.example.json first",
                err=True,
            )
            raise typer.Exit(code=11)
        collect_exit_code = collect_sources(
            date=date,
            config_path=resolved_config,
            out_dir=resolved_in_dir,
            dry_run=False,
            state_db_path=state_db,
        )
        if collect_exit_code != 0:
            raise typer.Exit(code=EXIT_COLLECTION_FAILED)
    else:
        typer.echo(f"reusing frozen input bundle at {resolved_in_dir / 'items.jsonl'}")

    try:
        outcome = synthesize_digest(
            root=root,
            date=date,
            prompt_path=resolved_prompt,
            in_dir=resolved_in_dir,
            out_dir=resolved_out_dir,
            state_db_path=_resolve_state_db(root, state_db),
            timeout_seconds=timeout_seconds,
        )
    except LifecycleCommandError as exc:
        typer.echo(exc.message, err=True)
        raise typer.Exit(code=exc.exit_code) from exc

    if outcome.already_complete:
        typer.echo(f"date {date} is already complete")
        raise typer.Exit(code=0)

    typer.echo("daily digest ready:")
    typer.echo(f"  {outcome.digest_json}")
    typer.echo(f"  {outcome.digest_md}")


@app.command()
def synthesize(
    date: Annotated[
        str, typer.Option(help="Digest date (YYYY-MM-DD)")
    ] = date_type.today().isoformat(),
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
    timeout_seconds: Annotated[
        int | None,
        typer.Option(help="Synthesis timeout in seconds; defaults to env or 900"),
    ] = None,
) -> None:
    root = _repo_root()
    resolved_prompt = prompt_path or (root / "prompts" / "daily_digest_prompt.md")
    resolved_out_dir = out_dir or (root / "outputs" / date)
    resolved_in_dir = in_dir or (root / "inputs" / date)

    try:
        outcome = synthesize_digest(
            root=root,
            date=date,
            prompt_path=resolved_prompt,
            in_dir=resolved_in_dir,
            out_dir=resolved_out_dir,
            state_db_path=_resolve_state_db(root, state_db),
            timeout_seconds=timeout_seconds,
        )
    except LifecycleCommandError as exc:
        typer.echo(exc.message, err=True)
        raise typer.Exit(code=exc.exit_code) from exc

    if outcome.already_complete:
        typer.echo(f"date {date} is already complete")
        raise typer.Exit(code=0)

    typer.echo("daily digest ready:")
    typer.echo(f"  {outcome.digest_json}")
    typer.echo(f"  {outcome.digest_md}")


def main() -> None:
    app()

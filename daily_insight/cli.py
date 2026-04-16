from __future__ import annotations

import subprocess
from datetime import date as date_type
from pathlib import Path
from typing import Annotated

import typer

from daily_insight.collect import collect_sources
from daily_insight.render import render_digest

app = typer.Typer(
    add_completion=False,
    help="Daily engineering and security insight tooling.",
    no_args_is_help=True,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


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
                f"Frozen input file: inputs/{date}/items.jsonl\n\n"
                "Wait for all requested work before returning. "
                "Produce only the final structured report."
            ),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    render_digest(digest_json, digest_md)
    typer.echo("daily digest ready:")
    typer.echo(f"  {digest_json}")
    typer.echo(f"  {digest_md}")


def main() -> None:
    app()

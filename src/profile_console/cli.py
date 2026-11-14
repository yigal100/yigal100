"""Unified CLI entrypoint for profile-console."""

import pathlib
from typing import Annotated

import typer

from profile_console.fetch import fetch_data
from profile_console.readme import update_readme
from profile_console.render import render_svgs

app = typer.Typer(
    name="profile",
    help="GitHub Profile Console CLI",
    no_args_is_help=True,
    add_completion=False,
)


@app.command()
def fetch() -> None:
    """Fetch latest stats into data/*.json."""
    fetch_data()


@app.command()
def render(
    data: Annotated[
        pathlib.Path | None,
        typer.Option("--data", help="Folder with stats.json and articles.json"),
    ] = None,
    out: Annotated[
        pathlib.Path | None,
        typer.Option("--out", help="Folder to write the SVGs into"),
    ] = None,
) -> None:
    """Render profile SVGs from data/*.json."""
    render_svgs(data_dir=data, out_dir=out)


@app.command()
def readme() -> None:
    """Synchronize dynamic README.md blocks."""
    update_readme()


@app.command()
def update() -> None:
    """Render SVGs and synchronize README.md."""
    render_svgs()
    update_readme()


@app.command()
def sync() -> None:
    """Fetch fresh data, render SVGs, and synchronize README.md."""
    fetch_data()
    render_svgs()
    update_readme()


def main() -> None:
    app()


if __name__ == "__main__":
    main()

"""Unified CLI entrypoint for profile-console."""

import pathlib
from typing import Annotated

import typer

from profile_console.fetch import main as fetch_main
from profile_console.readme import main as readme_main
from profile_console.render import main as render_main

app = typer.Typer(
    name="profile",
    help="GitHub Profile Console CLI",
    no_args_is_help=True,
    add_completion=False,
)


@app.command()
def fetch() -> None:
    """Fetch latest stats into data/*.json."""
    fetch_main()


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
    render_main(data_dir=data, out_dir=out)


@app.command()
def readme() -> None:
    """Synchronize dynamic README.md blocks."""
    readme_main()


@app.command()
def update() -> None:
    """Render SVGs and synchronize README.md."""
    render_main()
    readme_main()


def full_sync() -> None:
    """Fetch fresh data, render SVGs, and synchronize README."""
    fetch_main()
    render_main()
    readme_main()


@app.command()
def sync() -> None:
    """Fetch fresh data, render SVGs, and synchronize README.md."""
    full_sync()


def main() -> None:
    app()


if __name__ == "__main__":
    main()

"""Unified CLI entrypoint for profile-console."""

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

app.command(name="fetch")(fetch_data)
app.command(name="render")(render_svgs)
app.command(name="readme")(update_readme)


def main() -> None:
    app()


if __name__ == "__main__":
    main()

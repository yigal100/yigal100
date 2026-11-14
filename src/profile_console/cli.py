"""Unified CLI entrypoint for profile-console."""

import argparse

from profile_console.fetch import main as fetch_main
from profile_console.readme import main as readme_main
from profile_console.render import main as render_main


def update():
    """Renders SVGs and synchronizes README."""
    render_main()
    readme_main()


def full_sync():
    """Fetches fresh data, renders SVGs, and synchronizes README."""
    fetch_main()
    render_main()
    readme_main()


def main():
    parser = argparse.ArgumentParser(prog="profile", description="GitHub Profile Console CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("fetch", help="Fetch latest stats into data/*.json")

    sub_render = subparsers.add_parser("render", help="Render profile SVGs from data/*.json")
    sub_render.add_argument("--data", type=str, default=None, help="Folder with stats.json and articles.json")
    sub_render.add_argument("--out", type=str, default=None, help="Folder to write the SVGs into")

    subparsers.add_parser("readme", help="Synchronize dynamic README.md blocks")
    subparsers.add_parser("update", help="Render SVGs and synchronize README.md")
    subparsers.add_parser("sync", help="Fetch fresh data, render SVGs, and synchronize README.md")

    args = parser.parse_args()
    if args.command == "fetch":
        fetch_main()
    elif args.command == "render":
        render_main(data_dir=args.data, out_dir=args.out)
    elif args.command == "readme":
        readme_main()
    elif args.command == "update":
        update()
    elif args.command == "sync":
        full_sync()


if __name__ == "__main__":
    main()

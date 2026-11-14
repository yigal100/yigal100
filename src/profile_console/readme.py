"""Updates the dynamic parts of README.md from data/*.json and profile.toml.

- the links row between <!-- links:start --> and <!-- links:end -->
- the project cards between <!-- projects:start --> and <!-- projects:end -->
- the latest-articles block between <!-- writing:start --> and <!-- writing:end -->
- the alt text of the stats and contribution-city images

Everything else in the README is left exactly as it is.
"""

from __future__ import annotations

import datetime
import html
import json
import pathlib
import re
import sys
from typing import Annotated

import typer

from profile_console.config import LinkItem, Paths, ProjectItem, load_config
from profile_console.sections.links import link_slice_bounds
from profile_console.svg import Theme


def links_block(links: tuple[LinkItem, ...], total_width: int) -> str:
    """Build the clickable links row matching the rendered link slice widths."""
    n = len(links)
    tags = []
    for i, link in enumerate(links):
        _, seg = link_slice_bounds(i, n, total_width)
        pct = seg / total_width * 100
        width = f"{pct:g}%" if pct.is_integer() else f"{pct:.4f}%"
        tags.append(
            f'<a href="{html.escape(link.url, quote=True)}"><img src="./assets/links/{link.filename}.svg" '
            f'width="{width}" align="top" alt="{html.escape(link.label, quote=True)}"></a>'
        )
    return "<!-- links:start -->\n" + "".join(tags) + "\n<!-- links:end -->"


def projects_block(projects: tuple[ProjectItem, ...]) -> str:
    """Build the project cards grid (2-up rows, with full-width final card if odd)."""
    n = len(projects)
    rows = []
    for i in range(0, n, 2):
        pair = projects[i : i + 2]
        if len(pair) == 2:
            line = "".join(
                f'<a href="{html.escape(p.url, quote=True)}"><img src="./assets/card-{p.slug}.svg" '
                f'width="50%" align="top" alt="{html.escape(p.name, quote=True)} — {html.escape(p.desc, quote=True)}"></a>'
                for p in pair
            )
        else:
            p = pair[0]
            line = (
                f'<a href="{html.escape(p.url, quote=True)}"><img src="./assets/card-{p.slug}.svg" '
                f'width="100%" align="top" alt="{html.escape(p.name, quote=True)} — {html.escape(p.desc, quote=True)}"></a>'
            )
        rows.append(line)
    return "<!-- projects:start -->\n" + "\n".join(rows) + "\n<!-- projects:end -->"


def writing_block(articles: list[dict]) -> str:
    """Build the markdown/HTML block for the latest 5 articles."""
    lines = []
    for i, a in enumerate(articles[:5], 1):
        alt = html.escape(
            f"{a['title']} — published {a['published_at'][:10]}, {a['reactions']} reactions, {a['comments']} comments",
            quote=True,
        )
        lines.append(
            f'<a href="{html.escape(a["url"], quote=True)}"><img src="./assets/writing/post-{i}.svg" '
            f'width="100%" align="top" alt="{alt}"></a>'
        )
    return "<!-- writing:start -->\n" + "\n".join(lines) + "\n<!-- writing:end -->"


def _days(n: int) -> str:
    return f"{n} day" if n == 1 else f"{n} days"


def stats_alt(d: dict) -> str:
    """Build accessible alt text summarizing GitHub and DEV stats."""
    since = datetime.date.fromisoformat(d["created_at"][:10])
    langs = sorted(d["languages"].items(), key=lambda kv: -kv[1])[:5]
    parts = [
        f"{d['stars']} total stars",
        (
            f"{d['contributions_year']} contributions in {d['year']}, {d['contributions_all']} all time"
            if "contributions_year" in d
            else f"{d['commits_year']} commits in {d['year']}, {d['commits_all']} all time"
        ),
        f"{d['prs']} pull requests ({d['prs_merged']} merged)",
        f"current streak {_days(d['streak_current'])}, longest {_days(d['streak_longest'])}",
        f"{d['followers']} followers",
        f"{d['forks']} forks",
        f"member since {since:%B %Y}",
    ]
    text = "Stats: " + "; ".join(parts) + ". Top languages: " + ", ".join(k for k, _ in langs) + "."
    dev = {k: v for k, v in (d.get("dev") or {}).items() if v is not None}
    if dev:
        text += " DEV Community: " + ", ".join(f"{v:,} {k}" for k, v in dev.items()) + "."
    return html.escape(text, quote=True)


def city_alt(calendar: list[list]) -> str:
    """Build accessible alt text summarizing the contribution city skyline."""
    total = sum(n for _, n in calendar)
    busiest = max(calendar, key=lambda t: t[1]) if calendar else None
    text = (
        f"Contribution city: an isometric night skyline with one building per day of the last year. "
        f"{total:,} contributions"
    )
    if busiest and busiest[1]:
        d = datetime.date.fromisoformat(busiest[0])
        text += f", busiest day {d:%B} {d.day} with {busiest[1]}"
    return html.escape(text + ".", quote=True)


def _replace_block(content: str, name: str, replacement: str) -> str:
    updated, n = re.subn(
        rf"<!-- {name}:start -->.*?<!-- {name}:end -->",
        lambda _: replacement,
        content,
        flags=re.DOTALL,
    )
    if n != 1:
        sys.exit(f"error: README needs exactly one <!-- {name}:start --> … <!-- {name}:end --> block")
    return updated


def update_readme(
    data: Annotated[
        pathlib.Path | None,
        typer.Option("--data", help="Folder with stats.json and articles.json"),
    ] = None,
) -> None:
    """Synchronize dynamic README.md blocks."""
    paths = Paths.resolve(data_dir=data)
    cfg = load_config(paths.config_path)
    theme = Theme()
    stats = json.loads((paths.data_dir / "stats.json").read_text(encoding="utf-8"))
    articles = json.loads((paths.data_dir / "articles.json").read_text(encoding="utf-8"))
    s = paths.readme_path.read_text(encoding="utf-8")

    s = _replace_block(s, "links", links_block(cfg.links, theme.width))
    s = _replace_block(s, "projects", projects_block(cfg.projects))
    s = _replace_block(s, "writing", writing_block(articles))

    s, n = re.subn(
        r'(<img src="\./assets/stats\.svg"[^>]*?alt=")[^"]*(")',
        lambda m: m.group(1) + stats_alt(stats) + m.group(2),
        s,
    )
    if n != 1:
        sys.exit("error: README needs exactly one stats.svg image with an alt attribute")

    cal_file = paths.data_dir / "calendar.json"
    if cal_file.exists():
        s = re.sub(
            r'(<img src="\./assets/contribution-city\.svg"[^>]*?alt=")[^"]*(")',
            lambda mm: mm.group(1) + city_alt(json.loads(cal_file.read_text(encoding="utf-8"))) + mm.group(2),
            s,
        )

    paths.readme_path.write_text(s, encoding="utf-8")
    print("README updated")


if __name__ == "__main__":
    typer.run(update_readme)

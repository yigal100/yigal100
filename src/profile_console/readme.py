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

from profile_console.config import LinkItem, Paths, ProfileConfig, ProjectItem, load_config
from profile_console.sections.links import link_slice_bounds
from profile_console.svg import Theme


def _img_tag(stem: str, width: str, alt: str, *, adaptive: bool) -> str:
    """Return an <img> or adaptive <picture> element for an SVG slice."""
    if not adaptive:
        return f'<img src="./assets/{stem}.svg" width="{width}" align="top" alt="{alt}">'
    return (
        f'<picture>'
        f'<source media="(prefers-color-scheme: dark)" srcset="./assets/{stem}-dark.svg">'
        f'<source media="(prefers-color-scheme: light)" srcset="./assets/{stem}-light.svg">'
        f'<img src="./assets/{stem}-dark.svg" width="{width}" align="top" alt="{alt}">'
        f"</picture>"
    )


def links_block(links: tuple[LinkItem, ...], total_width: int, *, adaptive: bool = False) -> str:
    """Build the clickable links row matching the rendered link slice widths."""
    n = len(links)
    tags = []
    for i, link in enumerate(links):
        _, seg = link_slice_bounds(i, n, total_width)
        pct = seg / total_width * 100
        width = f"{pct:g}%" if pct.is_integer() else f"{pct:.4f}%"
        img = _img_tag(f"links/{link.filename}", width, html.escape(link.label, quote=True), adaptive=adaptive)
        tags.append(f'<a href="{html.escape(link.url, quote=True)}">{img}</a>')
    return "<!-- links:start -->\n" + "".join(tags) + "\n<!-- links:end -->"


def projects_block(projects: tuple[ProjectItem, ...], *, adaptive: bool = False) -> str:
    """Build the project cards grid (2-up rows, with full-width final card if odd)."""
    n = len(projects)
    rows = []
    for i in range(0, n, 2):
        pair = projects[i : i + 2]
        if len(pair) == 2:
            line = "".join(
                f'<a href="{html.escape(p.url, quote=True)}">'
                f'{_img_tag(f"card-{p.slug}", "50%", html.escape(f"{p.name} — {p.desc}", quote=True), adaptive=adaptive)}</a>'
                for p in pair
            )
        else:
            p = pair[0]
            line = (
                f'<a href="{html.escape(p.url, quote=True)}">'
                f'{_img_tag(f"card-{p.slug}", "100%", html.escape(f"{p.name} — {p.desc}", quote=True), adaptive=adaptive)}</a>'
            )
        rows.append(line)
    return "<!-- projects:start -->\n" + "\n".join(rows) + "\n<!-- projects:end -->"


def writing_block(articles: list[dict], *, adaptive: bool = False) -> str:
    """Build the markdown/HTML block for the latest 5 articles."""
    lines = []
    for i, a in enumerate(articles[:5], 1):
        alt = html.escape(
            f"{a['title']} — published {a['published_at'][:10]}, {a['reactions']} reactions, {a['comments']} comments",
            quote=True,
        )
        lines.append(
            f'<a href="{html.escape(a["url"], quote=True)}">'
            f'{_img_tag(f"writing/post-{i}", "100%", alt, adaptive=adaptive)}</a>'
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


def city_alt(calendar: list[list], *, astrometrics: bool = False) -> str:
    """Build accessible alt text summarizing the contribution visualization."""
    total = sum(n for _, n in calendar)
    busiest = max(calendar, key=lambda t: t[1]) if calendar else None
    if astrometrics:
        text = (
            f"Orbital contribution chart: a 3D-perspective star chart of the last 365 days. "
            f"{total:,} contributions"
        )
    else:
        text = (
            f"Contribution city: an isometric night skyline with one building per day of the last year. "
            f"{total:,} contributions"
        )
    if busiest and busiest[1]:
        d = datetime.date.fromisoformat(busiest[0])
        text += f", busiest day {d:%B} {d.day} with {busiest[1]}"
    return html.escape(text + ".", quote=True)


def _console_block(
    cfg: ProfileConfig,
    stats: dict,
    articles: list[dict],
    calendar: list[list] | None,
    width: int,
) -> str:
    """Build the complete <p align='center'>...</p> SVG console stack."""
    adaptive = cfg.theme.name == "astrometrics" and cfg.theme.mode == "adaptive"
    is_astro = cfg.theme.name == "astrometrics"
    header_alt = html.escape(f"{cfg.profile.header_title} — {cfg.profile.header_desc}", quote=True)
    stack_alt = html.escape(
        "Tech stack: " + ", ".join(c.category for c in cfg.stack) + ".",
        quote=True,
    )
    all_url = html.escape(articles[0]["url"], quote=True) if articles else html.escape(cfg.links[0].url, quote=True)

    lines = [
        "<!-- console:start -->",
        '<p align="center">',
        _img_tag("header", "100%", header_alt, adaptive=adaptive),
        _img_tag("links", "100%", "Links", adaptive=adaptive),
        links_block(cfg.links, width, adaptive=adaptive),
        _img_tag("stats", "100%", stats_alt(stats), adaptive=adaptive),
    ]
    if calendar is not None:
        stem = "orbital-chart" if is_astro else "contribution-city"
        lines.append(_img_tag(stem, "100%", city_alt(calendar, astrometrics=is_astro), adaptive=adaptive))
    lines.extend(
        [
            _img_tag("projects", "100%", "Projects", adaptive=adaptive),
            projects_block(cfg.projects, adaptive=adaptive),
            _img_tag("stack", "100%", stack_alt, adaptive=adaptive),
            _img_tag("writing", "100%", "Writing &amp; Insights: Recommended reading and articles", adaptive=adaptive),
            writing_block(articles, adaptive=adaptive),
            f'<a href="{all_url}">{_img_tag("writing/all-articles", "100%", "Read articles &amp; insights", adaptive=adaptive)}</a>',
            _img_tag("footer", "100%", "End of transmission." if is_astro else "Connection closed.", adaptive=adaptive),
            "</p>",
            "<!-- console:end -->",
        ]
    )
    return "\n".join(lines)


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
    theme = Theme.from_preset(cfg.theme.name, scifi_labels=cfg.theme.scifi_labels)
    stats = json.loads((paths.data_dir / "stats.json").read_text(encoding="utf-8"))
    articles = json.loads((paths.data_dir / "articles.json").read_text(encoding="utf-8"))
    cal_file = paths.data_dir / "calendar.json"
    calendar = json.loads(cal_file.read_text(encoding="utf-8")) if cal_file.exists() else None
    s = paths.readme_path.read_text(encoding="utf-8")

    s = _replace_block(s, "console", _console_block(cfg, stats, articles, calendar, theme.width))

    paths.readme_path.write_text(s, encoding="utf-8")
    print("README updated")


if __name__ == "__main__":
    typer.run(update_readme)

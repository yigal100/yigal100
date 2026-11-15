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

from profile_console.config import (
    VALID_THEMES,
    LinkItem,
    Paths,
    ProfileConfig,
    ProjectItem,
    ReadingItem,
    ThemeMode,
    ThemeName,
    ThemeStrategy,
    load_config,
)
from profile_console.sections.links import link_slice_bounds
from profile_console.svg import Theme


def _img_tag(stem: str, width: str, alt: str, *, adaptive: bool, assets_prefix: str = "./assets") -> str:
    """Return an <img> or adaptive <picture> element for an SVG slice."""
    if not adaptive:
        return f'<img src="{assets_prefix}/{stem}.svg" width="{width}" align="top" alt="{alt}">'
    return (
        f"<picture>"
        f'<source media="(prefers-color-scheme: dark)" srcset="{assets_prefix}/{stem}-dark.svg">'
        f'<source media="(prefers-color-scheme: light)" srcset="{assets_prefix}/{stem}-light.svg">'
        f'<img src="{assets_prefix}/{stem}-dark.svg" width="{width}" align="top" alt="{alt}">'
        f"</picture>"
    )


def links_block(
    links: tuple[LinkItem, ...],
    total_width: int,
    *,
    adaptive: bool = False,
    assets_prefix: str = "./assets",
) -> str:
    """Build the clickable links row matching the rendered link slice widths."""
    n = len(links)
    tags = []
    for i, link in enumerate(links):
        _, seg = link_slice_bounds(i, n, total_width)
        pct = seg / total_width * 100
        width = f"{pct:g}%" if pct.is_integer() else f"{pct:.4f}%"
        img = _img_tag(
            f"links/{link.filename}",
            width,
            html.escape(link.label, quote=True),
            adaptive=adaptive,
            assets_prefix=assets_prefix,
        )
        tags.append(f'<a href="{html.escape(link.url, quote=True)}">{img}</a>')
    return "<!-- links:start -->\n" + "".join(tags) + "\n<!-- links:end -->"


def projects_block(
    projects: tuple[ProjectItem, ...],
    *,
    adaptive: bool = False,
    assets_prefix: str = "./assets",
) -> str:
    """Build the project cards grid (2-up rows, with full-width final card if odd)."""
    n = len(projects)
    rows = []
    for i in range(0, n, 2):
        pair = projects[i : i + 2]
        if len(pair) == 2:
            line = "".join(
                f'<a href="{html.escape(p.url, quote=True)}">'
                f'{_img_tag(f"card-{p.slug}", "50%", html.escape(f"{p.name} — {p.desc}", quote=True), adaptive=adaptive, assets_prefix=assets_prefix)}</a>'
                for p in pair
            )
        else:
            p = pair[0]
            line = (
                f'<a href="{html.escape(p.url, quote=True)}">'
                f'{_img_tag(f"card-{p.slug}", "100%", html.escape(f"{p.name} — {p.desc}", quote=True), adaptive=adaptive, assets_prefix=assets_prefix)}</a>'
            )
        rows.append(line)
    return "<!-- projects:start -->\n" + "\n".join(rows) + "\n<!-- projects:end -->"


def writing_block(
    articles: list[dict],
    *,
    adaptive: bool = False,
    assets_prefix: str = "./assets",
) -> str:
    """Build the markdown/HTML block for the latest 5 articles."""
    lines = []
    for i, a in enumerate(articles[:5], 1):
        alt = html.escape(
            f"{a['title']} — published {a['published_at'][:10]}, {a['reactions']} reactions, {a['comments']} comments",
            quote=True,
        )
        lines.append(
            f'<a href="{html.escape(a["url"], quote=True)}">'
            f'{_img_tag(f"writing/post-{i}", "100%", alt, adaptive=adaptive, assets_prefix=assets_prefix)}</a>'
        )
    return "<!-- writing:start -->\n" + "\n".join(lines) + "\n<!-- writing:end -->"


def reading_block(
    reading: tuple[ReadingItem, ...],
    *,
    adaptive: bool = False,
    assets_prefix: str = "./assets",
) -> str:
    """Build the markdown/HTML block for recommended reading links."""
    lines = []
    for i, item in enumerate(reading, 1):
        alt = html.escape(
            f"{item.title} ({item.source})" if item.source else item.title,
            quote=True,
        )
        lines.append(
            f'<a href="{html.escape(item.url, quote=True)}">'
            f'{_img_tag(f"reading/item-{i}", "100%", alt, adaptive=adaptive, assets_prefix=assets_prefix)}</a>'
        )
    return "<!-- reading:start -->\n" + "\n".join(lines) + "\n<!-- reading:end -->"


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


def city_alt(calendar: list[list], *, theme: Theme) -> str:
    """Build accessible alt text summarizing the contribution visualization."""
    total = sum(n for _, n in calendar)
    busiest = max(calendar, key=lambda t: t[1]) if calendar else None
    text = f"{theme.spec['centerpiece_alt']} {total:,} contributions"
    if busiest and busiest[1]:
        d = datetime.date.fromisoformat(busiest[0])
        text += f", busiest day {d:%B} {d.day} with {busiest[1]}"
    return html.escape(text + ".", quote=True)


def _console_block(
    cfg: ProfileConfig,
    stats: dict,
    articles: list[dict],
    calendar: list[list] | None,
    theme: Theme,
    *,
    mode: str,
    assets_prefix: str = "./assets",
) -> str:
    """Build the complete <p align='center'>...</p> SVG console stack."""
    adaptive = mode == "adaptive"
    header_alt = html.escape(f"{cfg.profile.header_title} — {cfg.profile.header_desc}", quote=True)
    stack_alt = html.escape(
        "Tech stack: " + ", ".join(c.category for c in cfg.stack) + ".",
        quote=True,
    )
    all_url = html.escape(articles[0]["url"], quote=True) if articles else html.escape(cfg.links[0].url, quote=True)

    lines = [
        "<!-- console:start -->",
        '<p align="center">',
        _img_tag("header", "100%", header_alt, adaptive=adaptive, assets_prefix=assets_prefix),
        _img_tag("links", "100%", "Links", adaptive=adaptive, assets_prefix=assets_prefix),
        links_block(cfg.links, theme.width, adaptive=adaptive, assets_prefix=assets_prefix),
        _img_tag("stats", "100%", stats_alt(stats), adaptive=adaptive, assets_prefix=assets_prefix),
    ]
    if calendar is not None:
        stem = theme.spec["centerpiece_stem"]
        lines.append(
            _img_tag(stem, "100%", city_alt(calendar, theme=theme), adaptive=adaptive, assets_prefix=assets_prefix)
        )
    lines.extend(
        [
            _img_tag("projects", "100%", "Projects", adaptive=adaptive, assets_prefix=assets_prefix),
            projects_block(cfg.projects, adaptive=adaptive, assets_prefix=assets_prefix),
            _img_tag("stack", "100%", stack_alt, adaptive=adaptive, assets_prefix=assets_prefix),
        ]
    )
    if articles:
        lines.extend(
            [
                _img_tag(
                    "writing",
                    "100%",
                    "Writing &amp; Insights: Articles and posts",
                    adaptive=adaptive,
                    assets_prefix=assets_prefix,
                ),
                writing_block(articles, adaptive=adaptive, assets_prefix=assets_prefix),
                f'<a href="{all_url}">{_img_tag("writing/all-articles", "100%", "Read articles &amp; insights", adaptive=adaptive, assets_prefix=assets_prefix)}</a>',
            ]
        )
    if cfg.reading:
        lines.extend(
            [
                _img_tag(
                    "reading",
                    "100%",
                    "Recommended Reading: Curated articles and references",
                    adaptive=adaptive,
                    assets_prefix=assets_prefix,
                ),
                reading_block(cfg.reading, adaptive=adaptive, assets_prefix=assets_prefix),
            ]
        )
    lines.extend(
        [
            _img_tag(
                "footer",
                "100%",
                "End of transmission." if theme.uses_chevron_prompt else "Connection closed.",
                adaptive=adaptive,
                assets_prefix=assets_prefix,
            ),
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


def _write_preview_readmes(
    out_root: pathlib.Path,
    cfg: ProfileConfig,
    stats: dict,
    articles: list[dict],
    calendar: list[list] | None,
    *,
    mode: str,
) -> None:
    """Write preview/README.md (all themes) and preview/<theme>/README.md (individual)."""
    out_root.mkdir(parents=True, exist_ok=True)
    toc = " · ".join(f"[{name}](#{name})" for name in VALID_THEMES)
    sections = [
        "# Theme Previews",
        "",
        f"Mode: `{mode}`",
        "",
        toc,
    ]
    for name in VALID_THEMES:
        theme = Theme.from_preset(name, themed_labels=cfg.theme.themed_labels)
        theme_dir = out_root / name
        theme_dir.mkdir(parents=True, exist_ok=True)
        single = f"# {name}\n\n" + _console_block(
            cfg, stats, articles, calendar, theme, mode=mode, assets_prefix="."
        )
        (theme_dir / "README.md").write_text(single + "\n", encoding="utf-8")

        sections.extend(
            [
                "",
                "---",
                "",
                f"## {name}",
                "",
                _console_block(cfg, stats, articles, calendar, theme, mode=mode, assets_prefix=f"./{name}"),
            ]
        )
    (out_root / "README.md").write_text("\n".join(sections) + "\n", encoding="utf-8")


def update_readme(
    data: Annotated[
        pathlib.Path | None,
        typer.Option("--data", "-d", help="Folder with stats.json and articles.json (default: data)"),
    ] = None,
    out: Annotated[
        pathlib.Path | None,
        typer.Option("--out", "-o", help="Preview output folder when --all is set (default: preview)"),
    ] = None,
    config: Annotated[
        pathlib.Path | None,
        typer.Option("--config", "-c", help="Path to profile.toml (default: profile.toml)"),
    ] = None,
    theme_name: Annotated[
        ThemeName | None,
        typer.Option("--theme", "-t", help="Override theme preset (default: from .theme.json or strategy)"),
    ] = None,
    mode: Annotated[
        ThemeMode | None,
        typer.Option("--mode", "-m", help="Override color mode (default: from .theme.json or profile.toml)"),
    ] = None,
    strategy: Annotated[
        ThemeStrategy | None,
        typer.Option("--strategy", "-s", help="Theme selection strategy (default: rotate)"),
    ] = None,
    all_themes: Annotated[
        bool,
        typer.Option("--all", "-a", help="Generate preview README.md files for all themes into <out>"),
    ] = False,
) -> None:
    """Synchronize dynamic README.md blocks."""
    paths = Paths.resolve(data_dir=data, config_path=config)
    cfg = load_config(paths.config_path)
    stats = json.loads((paths.data_dir / "stats.json").read_text(encoding="utf-8"))
    articles = json.loads((paths.data_dir / "articles.json").read_text(encoding="utf-8"))
    cal_file = paths.data_dir / "calendar.json"
    calendar = json.loads(cal_file.read_text(encoding="utf-8")) if cal_file.exists() else None

    if all_themes:
        out_root = pathlib.Path(out) if out is not None else paths.root / "preview"
        _, resolved_mode = cfg.theme.resolve(mode_override=mode)
        _write_preview_readmes(out_root, cfg, stats, articles, calendar, mode=resolved_mode)
        print(f"wrote preview README.md for {len(VALID_THEMES)} themes into {out_root} (mode={resolved_mode})")
        return

    meta_file = paths.assets_dir / ".theme.json"
    if theme_name is None and strategy is None and meta_file.exists():
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        resolved_name = str(meta.get("name") or cfg.theme.resolve()[0])
        resolved_mode = (mode or str(meta.get("mode") or cfg.theme.mode)).lower()
    else:
        resolved_name, resolved_mode = cfg.theme.resolve(
            theme_override=theme_name,
            mode_override=mode,
            strategy_override=strategy,
        )
    theme = Theme.from_preset(resolved_name, themed_labels=cfg.theme.themed_labels)
    s = paths.readme_path.read_text(encoding="utf-8")

    s = _replace_block(
        s,
        "console",
        _console_block(cfg, stats, articles, calendar, theme, mode=resolved_mode),
    )

    paths.readme_path.write_text(s, encoding="utf-8")
    print(f"README updated (theme={resolved_name}, mode={resolved_mode})")


if __name__ == "__main__":
    typer.run(update_readme)

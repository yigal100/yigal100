"""Renders the profile README's SVG slices into assets/."""

from __future__ import annotations

import json
import pathlib
from typing import Annotated

import typer

from profile_console.config import Paths, load_config
from profile_console.sections.city import build_city
from profile_console.sections.header import build_footer, build_header
from profile_console.sections.links import build_link_button, build_links_head
from profile_console.sections.projects import build_card, build_projects_head
from profile_console.sections.stack import build_stack
from profile_console.sections.stats import build_stats
from profile_console.sections.writing import build_article_row, build_writing_head, build_writing_more
from profile_console.svg import Theme


def _write_svg(out_dir: pathlib.Path, rel: str, svg: str) -> None:
    path = out_dir / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")


def render_svgs(
    data: Annotated[
        pathlib.Path | None,
        typer.Option("--data", help="Folder with stats.json and articles.json"),
    ] = None,
    out: Annotated[
        pathlib.Path | None,
        typer.Option("--out", help="Folder to write the SVGs into"),
    ] = None,
    config: Annotated[
        pathlib.Path | None,
        typer.Option("--config", help="Path to profile.toml"),
    ] = None,
) -> None:
    """Render profile SVGs from data/*.json."""
    paths = Paths.resolve(data_dir=data, out_dir=out, config_path=config)
    cfg = load_config(paths.config_path)
    theme = Theme(fonts_dir=paths.fonts_dir)

    stats = json.loads((paths.data_dir / "stats.json").read_text(encoding="utf-8"))
    articles = json.loads((paths.data_dir / "articles.json").read_text(encoding="utf-8"))
    icons = json.loads(paths.icons_path.read_text(encoding="utf-8"))
    stars = stats.get("repo_stars", {})

    _write_svg(paths.assets_dir, "header.svg", build_header(cfg.profile, theme))
    _write_svg(paths.assets_dir, "links.svg", build_links_head(cfg.profile, theme))
    for i, link in enumerate(cfg.links):
        _write_svg(
            paths.assets_dir,
            f"links/{link.filename}.svg",
            build_link_button(i, link, len(cfg.links), icons, theme),
        )
    _write_svg(paths.assets_dir, "stats.svg", build_stats(stats, cfg.profile, theme))
    cal_file = paths.data_dir / "calendar.json"
    if cal_file.exists():
        calendar = json.loads(cal_file.read_text(encoding="utf-8"))
        _write_svg(paths.assets_dir, "contribution-city.svg", build_city(calendar, stats["updated"], theme))
    _write_svg(paths.assets_dir, "projects.svg", build_projects_head(theme))
    n_projects = len(cfg.projects)
    for i, project in enumerate(cfg.projects):
        side = "F" if n_projects % 2 == 1 and i == n_projects - 1 else ("L" if i % 2 == 0 else "R")
        _write_svg(
            paths.assets_dir,
            f"card-{project.slug}.svg",
            build_card(project, side, 0.3 + i * 0.12, theme, stars),
        )
    _write_svg(paths.assets_dir, "stack.svg", build_stack(cfg.stack, theme))
    _write_svg(paths.assets_dir, "writing.svg", build_writing_head(theme))
    for i, article in enumerate(articles[:5]):
        _write_svg(paths.assets_dir, f"writing/post-{i + 1}.svg", build_article_row(article, i, theme))
    _write_svg(paths.assets_dir, "writing/all-articles.svg", build_writing_more(theme))
    _write_svg(paths.assets_dir, "footer.svg", build_footer(cfg.profile, theme))
    print("rendered", len(list(paths.assets_dir.rglob("*.svg"))), "SVGs into", paths.assets_dir)


if __name__ == "__main__":
    typer.run(render_svgs)

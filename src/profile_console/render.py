"""Renders the profile README's SVG slices into assets/."""

from __future__ import annotations

import json
import pathlib
from typing import Annotated

import typer

from profile_console.config import (
    VALID_THEMES,
    Paths,
    ProfileConfig,
    ThemeMode,
    ThemeName,
    ThemeStrategy,
    load_config,
)
from profile_console.sections.aurora import build_aurora, build_radar
from profile_console.sections.city import build_city
from profile_console.sections.header import build_footer, build_header
from profile_console.sections.links import build_link_button, build_links_head
from profile_console.sections.orbital import build_orbital
from profile_console.sections.projects import build_card, build_projects_head
from profile_console.sections.reading import build_reading_head, build_reading_row
from profile_console.sections.stack import build_stack
from profile_console.sections.stats import build_stats
from profile_console.sections.terrain import build_spectrum, build_terrain
from profile_console.sections.writing import build_article_row, build_writing_head, build_writing_more
from profile_console.svg import Theme

CENTERPIECE_BUILDERS = {
    "orbital": build_orbital,
    "terrain": build_terrain,
    "spectrum": build_spectrum,
    "city": build_city,
    "aurora": build_aurora,
    "radar": build_radar,
}


def _write_svg(out_dir: pathlib.Path, rel: str, svg: str) -> None:
    path = out_dir / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")


def _render_variant(
    cfg: ProfileConfig,
    out_dir: pathlib.Path,
    stats: dict,
    articles: list,
    icons: dict[str, str],
    calendar: list | None,
    theme: Theme,
    suffix: str = "",
) -> None:
    """Render all SVG slices for a single theme variant (optionally suffixed e.g. '-dark')."""
    stars = stats.get("repo_stars", {})

    def name(stem: str) -> str:
        return f"{stem}{suffix}.svg"

    _write_svg(out_dir, name("header"), build_header(cfg.profile, theme))
    _write_svg(out_dir, name("links"), build_links_head(cfg.profile, theme))
    for i, link in enumerate(cfg.links):
        _write_svg(
            out_dir,
            name(f"links/{link.filename}"),
            build_link_button(i, link, len(cfg.links), icons, theme),
        )
    _write_svg(out_dir, name("stats"), build_stats(stats, cfg.profile, theme))
    if calendar is not None:
        stem = theme.spec["centerpiece_stem"]
        builder = CENTERPIECE_BUILDERS[theme.spec["centerpiece"]]
        _write_svg(out_dir, name(stem), builder(calendar, stats["updated"], theme))
    _write_svg(out_dir, name("projects"), build_projects_head(theme))
    n_projects = len(cfg.projects)
    for i, project in enumerate(cfg.projects):
        side = "F" if n_projects % 2 == 1 and i == n_projects - 1 else ("L" if i % 2 == 0 else "R")
        _write_svg(
            out_dir,
            name(f"card-{project.slug}"),
            build_card(project, side, 0.3 + i * 0.12, theme, stars),
        )
    _write_svg(out_dir, name("stack"), build_stack(cfg.stack, theme))
    if articles:
        _write_svg(out_dir, name("writing"), build_writing_head(theme))
        for i, article in enumerate(articles[:5]):
            _write_svg(out_dir, name(f"writing/post-{i + 1}"), build_article_row(article, i, theme))
        _write_svg(out_dir, name("writing/all-articles"), build_writing_more(theme))
    if cfg.reading:
        reading_sec_num = 7 if articles else 6
        _write_svg(out_dir, name("reading"), build_reading_head(theme, section_num=reading_sec_num))
        for i, item in enumerate(cfg.reading):
            _write_svg(out_dir, name(f"reading/item-{i + 1}"), build_reading_row(item, i, theme))
    _write_svg(out_dir, name("footer"), build_footer(cfg.profile, theme))


def _render_theme(
    cfg: ProfileConfig,
    paths: Paths,
    out_dir: pathlib.Path,
    stats: dict,
    articles: list,
    icons: dict[str, str],
    calendar: list | None,
    theme_name: str,
    mode: str,
) -> None:
    """Render adaptive (dark + light) or single-mode SVG slices for one theme."""
    if mode == "adaptive":
        for variant in ("dark", "light"):
            theme = Theme.from_preset(
                theme_name,
                variant,
                themed_labels=cfg.theme.themed_labels,
                fonts_dir=paths.fonts_dir,
            )
            _render_variant(cfg, out_dir, stats, articles, icons, calendar, theme, suffix=f"-{variant}")
    else:
        theme = Theme.from_preset(
            theme_name,
            mode,
            themed_labels=cfg.theme.themed_labels,
            fonts_dir=paths.fonts_dir,
        )
        _render_variant(cfg, out_dir, stats, articles, icons, calendar, theme)


def render_svgs(
    data: Annotated[
        pathlib.Path | None,
        typer.Option("--data", "-d", help="Folder with stats.json and articles.json (default: data)"),
    ] = None,
    out: Annotated[
        pathlib.Path | None,
        typer.Option("--out", "-o", help="Folder to write the SVGs into (default: assets, or preview with --all)"),
    ] = None,
    config: Annotated[
        pathlib.Path | None,
        typer.Option("--config", "-c", help="Path to profile.toml (default: profile.toml)"),
    ] = None,
    theme_name: Annotated[
        ThemeName | None,
        typer.Option("--theme", "-t", help="Override theme preset (default: from strategy)"),
    ] = None,
    mode: Annotated[
        ThemeMode | None,
        typer.Option("--mode", "-m", help="Override color mode (default: from profile.toml)"),
    ] = None,
    strategy: Annotated[
        ThemeStrategy | None,
        typer.Option("--strategy", "-s", help="Theme selection strategy (default: rotate)"),
    ] = None,
    all_themes: Annotated[
        bool,
        typer.Option("--all", "-a", help="Render all themes into <out>/<theme>/ for local preview"),
    ] = False,
) -> None:
    """Render profile SVGs from data/*.json."""
    paths = Paths.resolve(data_dir=data, out_dir=out, config_path=config)
    cfg = load_config(paths.config_path)

    stats = json.loads((paths.data_dir / "stats.json").read_text(encoding="utf-8"))
    articles = json.loads((paths.data_dir / "articles.json").read_text(encoding="utf-8"))
    icons = json.loads(paths.icons_path.read_text(encoding="utf-8"))
    cal_file = paths.data_dir / "calendar.json"
    calendar = json.loads(cal_file.read_text(encoding="utf-8")) if cal_file.exists() else None

    if all_themes:
        out_root = pathlib.Path(out) if out is not None else paths.root / "preview"
        _, resolved_mode = cfg.theme.resolve(mode_override=mode)
        for name in VALID_THEMES:
            _render_theme(cfg, paths, out_root / name, stats, articles, icons, calendar, name, resolved_mode)
        print(
            f"rendered {len(list(out_root.rglob('*.svg')))} SVGs across {len(VALID_THEMES)} themes "
            f"into {out_root} (mode={resolved_mode})"
        )
        return

    resolved_name, resolved_mode = cfg.theme.resolve(
        theme_override=theme_name,
        mode_override=mode,
        strategy_override=strategy,
    )
    _render_theme(cfg, paths, paths.assets_dir, stats, articles, icons, calendar, resolved_name, resolved_mode)

    paths.assets_dir.mkdir(parents=True, exist_ok=True)
    (paths.assets_dir / ".theme.json").write_text(
        json.dumps({"name": resolved_name, "mode": resolved_mode, "themed_labels": cfg.theme.themed_labels}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    print(
        f"rendered {len(list(paths.assets_dir.rglob('*.svg')))} SVGs into {paths.assets_dir} "
        f"(theme={resolved_name}, mode={resolved_mode})"
    )


if __name__ == "__main__":
    typer.run(render_svgs)

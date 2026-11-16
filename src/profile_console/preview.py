"""Local multi-theme preview generator (index.html, bundle.html, and per-theme READMEs)."""

from __future__ import annotations

import base64
import json
import pathlib
import shutil
from typing import Annotated

import typer

from profile_console.config import VALID_THEMES, Paths, ProfileConfig, ThemeMode, load_config
from profile_console.readme import _console_block
from profile_console.render import render_svgs
from profile_console.svg import Theme


def _preview_html(
    cfg: ProfileConfig,
    articles: list[dict],
    calendar: list[list] | None,
    *,
    mode: str,
    out_root: pathlib.Path | None = None,
    bundle: bool = False,
) -> str:
    """Build a self-contained interactive HTML gallery for previewing all themes."""
    themes_meta = [
        {
            "name": name,
            "centerpiece": Theme.from_preset(name, themed_labels=cfg.theme.themed_labels).spec["centerpiece_stem"],
        }
        for name in VALID_THEMES
    ]
    links_stems = [f"links/{link.filename}" for link in cfg.links]
    project_slugs = [f"card-{p.slug}" for p in cfg.projects]
    writing_stems = [f"writing/post-{i + 1}" for i in range(len(articles[:5]))]
    reading_stems = [f"reading/item-{i + 1}" for i in range(len(cfg.reading))]
    payload = json.dumps(
        {
            "themes": themes_meta,
            "mode": mode,
            "hasCalendar": calendar is not None,
            "links": links_stems,
            "projects": project_slugs,
            "writing": writing_stems,
            "reading": reading_stems,
        }
    )

    svgs_json = "null"
    if bundle and out_root is not None:
        svgs_map: dict[str, str] = {}
        for name in VALID_THEMES:
            t_dir = out_root / name
            if not t_dir.is_dir():
                continue
            for svg_path in sorted(t_dir.rglob("*.svg")):
                rel = f"{name}/{svg_path.relative_to(t_dir).as_posix()}"
                svgs_map[rel] = base64.b64encode(svg_path.read_bytes()).decode("ascii")
        svgs_json = json.dumps(svgs_map)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Profile Console — Theme Preview</title>
<style>
  :root {{ --bg: #0d1117; --panel: #161b22; --border: #30363d; --fg: #e6edf3; --muted: #8b949e; --acc: #58a6ff; }}
  body.light {{ --bg: #ffffff; --panel: #f6f8fa; --border: #d0d7de; --fg: #1f2328; --muted: #656d76; --acc: #0969da; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; font-family: ui-sans-serif, system-ui, -apple-system, sans-serif; background: var(--bg); color: var(--fg); transition: background .15s, color .15s; }}
  header {{ position: sticky; top: 0; z-index: 10; display: flex; flex-wrap: wrap; align-items: center; gap: 10px; padding: 10px 18px; background: var(--panel); border-bottom: 1px solid var(--border); }}
  .themes {{ display: flex; flex-wrap: wrap; gap: 6px; flex: 1; }}
  button {{ cursor: pointer; font: inherit; font-size: 12.5px; padding: 5px 10px; border-radius: 6px; border: 1px solid var(--border); background: transparent; color: var(--fg); }}
  button:hover {{ border-color: var(--acc); }}
  button.active {{ background: var(--acc); color: #fff; border-color: var(--acc); font-weight: 600; }}
  .controls {{ display: flex; gap: 6px; align-items: center; }}
  main {{ max-width: 980px; margin: 22px auto 48px; padding: 0 16px; }}
  .stack {{ display: flex; flex-direction: column; align-items: center; gap: 0; }}
  .stack img {{ width: 100%; display: block; }}
  .row-links {{ display: flex; width: 100%; }}
  .row-links img {{ flex: 1; min-width: 0; }}
  .grid-projects {{ display: grid; grid-template-columns: 1fr 1fr; width: 100%; }}
  .grid-projects img.full {{ grid-column: 1 / -1; }}
</style>
</head>
<body>
<header>
  <div class="themes" id="theme-bar"></div>
  <div class="controls">
    <button id="btn-view" title="Toggle centerpiece vs full console">Centerpiece</button>
    <button id="btn-mode" title="Toggle dark / light">Dark</button>
    <button id="btn-replay" title="Replay SVG animations">↻ Replay</button>
  </div>
</header>
<main><div class="stack" id="stage"></div></main>
<script>
const CFG = {payload};
const SVGS = {svgs_json};
let curTheme = location.hash.slice(1);
if (!CFG.themes.some(t => t.name === curTheme)) curTheme = CFG.themes[0].name;
let curVariant = CFG.mode === "light" ? "light" : "dark";
let viewMode = "centerpiece";
let bust = 0;

const bar = document.getElementById("theme-bar");
const stage = document.getElementById("stage");
const btnView = document.getElementById("btn-view");
const btnMode = document.getElementById("btn-mode");
const btnReplay = document.getElementById("btn-replay");
if (CFG.mode !== "adaptive") btnMode.style.display = "none";

function svgSrc(theme, stem) {{
  const suf = CFG.mode === "adaptive" ? "-" + curVariant : "";
  const rel = `${{theme}}/${{stem}}${{suf}}.svg`;
  if (SVGS) return "data:image/svg+xml;base64," + (SVGS[rel] || "");
  return `./${{rel}}${{bust ? "?t=" + bust : ""}}`;
}}

function img(theme, stem, cls) {{
  const el = document.createElement("img");
  el.src = svgSrc(theme, stem);
  if (cls) el.className = cls;
  return el;
}}

function render() {{
  document.body.classList.toggle("light", curVariant === "light");
  btnMode.textContent = curVariant === "dark" ? "Dark" : "Light";
  btnView.textContent = viewMode === "centerpiece" ? "View: Centerpiece" : "View: Full Console";
  for (const b of bar.children) b.classList.toggle("active", b.dataset.theme === curTheme);

  const meta = CFG.themes.find(t => t.name === curTheme);
  stage.innerHTML = "";
  if (viewMode === "centerpiece") {{
    if (CFG.hasCalendar) stage.appendChild(img(curTheme, meta.centerpiece));
    return;
  }}

  stage.appendChild(img(curTheme, "header"));
  stage.appendChild(img(curTheme, "links"));
  if (CFG.links.length) {{
    const row = document.createElement("div");
    row.className = "row-links";
    for (const s of CFG.links) row.appendChild(img(curTheme, s));
    stage.appendChild(row);
  }}
  stage.appendChild(img(curTheme, "stats"));
  if (CFG.hasCalendar) stage.appendChild(img(curTheme, meta.centerpiece));
  stage.appendChild(img(curTheme, "projects"));
  if (CFG.projects.length) {{
    const grid = document.createElement("div");
    grid.className = "grid-projects";
    CFG.projects.forEach((s, i) => {{
      const isLastOdd = CFG.projects.length % 2 === 1 && i === CFG.projects.length - 1;
      grid.appendChild(img(curTheme, s, isLastOdd ? "full" : ""));
    }});
    stage.appendChild(grid);
  }}
  stage.appendChild(img(curTheme, "stack"));
  if (CFG.writing.length) {{
    stage.appendChild(img(curTheme, "writing"));
    for (const s of CFG.writing) stage.appendChild(img(curTheme, s));
    stage.appendChild(img(curTheme, "writing/all-articles"));
  }}
  if (CFG.reading.length) {{
    stage.appendChild(img(curTheme, "reading"));
    for (const s of CFG.reading) stage.appendChild(img(curTheme, s));
  }}
  stage.appendChild(img(curTheme, "footer"));
}}

for (const t of CFG.themes) {{
  const b = document.createElement("button");
  b.textContent = t.name;
  b.dataset.theme = t.name;
  b.onclick = () => {{ curTheme = t.name; location.hash = t.name; render(); }};
  bar.appendChild(b);
}}
btnView.onclick = () => {{ viewMode = viewMode === "centerpiece" ? "full" : "centerpiece"; render(); }};
btnMode.onclick = () => {{ curVariant = curVariant === "dark" ? "light" : "dark"; render(); }};
btnReplay.onclick = () => {{
  if (SVGS) {{ stage.innerHTML = ""; requestAnimationFrame(render); return; }}
  bust = Date.now();
  render();
}};
window.addEventListener("keydown", e => {{
  if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
  const idx = CFG.themes.findIndex(t => t.name === curTheme);
  const next = (idx + (e.key === "ArrowRight" ? 1 : -1) + CFG.themes.length) % CFG.themes.length;
  curTheme = CFG.themes[next].name;
  location.hash = curTheme;
  render();
}});
render();
</script>
</body>
</html>
'''


def _write_preview_files(
    out_root: pathlib.Path,
    cfg: ProfileConfig,
    stats: dict,
    articles: list[dict],
    calendar: list[list] | None,
    *,
    mode: str,
    bundle: bool = False,
) -> None:
    """Write preview/index.html, compact preview/README.md, preview/<theme>/README.md, and optional bundle.html."""
    out_root.mkdir(parents=True, exist_ok=True)
    index_rows = [
        "# Theme Previews",
        "",
        f"Mode: `{mode}` · Open [index.html](./index.html) in a browser for the interactive theme/mode switcher.",
        "",
        "| Theme | Centerpiece | Individual README |",
        "| --- | --- | --- |",
    ]
    for name in VALID_THEMES:
        theme = Theme.from_preset(name, themed_labels=cfg.theme.themed_labels)
        theme_dir = out_root / name
        theme_dir.mkdir(parents=True, exist_ok=True)
        single = f"# {name}\n\n" + _console_block(
            cfg, stats, articles, calendar, theme, mode=mode, assets_prefix="."
        )
        (theme_dir / "README.md").write_text(single + "\n", encoding="utf-8")
        index_rows.append(
            f"| `{name}` | `{theme.spec['centerpiece_stem']}` | [preview](./{name}/README.md) |"
        )

    (out_root / "README.md").write_text("\n".join(index_rows) + "\n", encoding="utf-8")
    (out_root / "index.html").write_text(
        _preview_html(cfg, articles, calendar, mode=mode), encoding="utf-8"
    )
    if bundle:
        bundle_path = out_root / "bundle.html"
        bundle_path.write_text(
            _preview_html(cfg, articles, calendar, mode=mode, out_root=out_root, bundle=True),
            encoding="utf-8",
        )
        size_mb = bundle_path.stat().st_size / (1024 * 1024)
        print(f"wrote self-contained {bundle_path} ({size_mb:.1f} MB)")


def build_preview(
    data: Annotated[
        pathlib.Path | None,
        typer.Option("--data", "-d", help="Folder with stats.json and articles.json (default: data)"),
    ] = None,
    out: Annotated[
        pathlib.Path | None,
        typer.Option("--out", "-o", help="Preview output folder (default: preview)"),
    ] = None,
    config: Annotated[
        pathlib.Path | None,
        typer.Option("--config", "-c", help="Path to profile.toml (default: profile.toml)"),
    ] = None,
    mode: Annotated[
        ThemeMode | None,
        typer.Option("--mode", "-m", help="Override color mode (default: from profile.toml)"),
    ] = None,
    bundle: Annotated[
        bool,
        typer.Option("--bundle", "-b", help="Inline SVGs into a single self-contained <out>/bundle.html"),
    ] = False,
    skip_render: Annotated[
        bool,
        typer.Option("--skip-render", help="Reuse existing SVGs in <out> instead of re-rendering"),
    ] = False,
) -> None:
    """Render all themes and build the interactive preview gallery."""
    paths = Paths.resolve(data_dir=data, config_path=config)
    cfg = load_config(paths.config_path)
    out_root = pathlib.Path(out) if out is not None else paths.root / "preview"
    _, resolved_mode = cfg.theme.resolve(mode_override=mode)

    if not skip_render:
        if out_root.exists():
            shutil.rmtree(out_root)
        render_svgs(data=data, out=out_root, config=config, mode=mode, all_themes=True)

    stats = json.loads((paths.data_dir / "stats.json").read_text(encoding="utf-8"))
    articles = json.loads((paths.data_dir / "articles.json").read_text(encoding="utf-8"))
    cal_file = paths.data_dir / "calendar.json"
    calendar = json.loads(cal_file.read_text(encoding="utf-8")) if cal_file.exists() else None

    _write_preview_files(out_root, cfg, stats, articles, calendar, mode=resolved_mode, bundle=bundle)
    print(f"wrote preview gallery for {len(VALID_THEMES)} themes into {out_root} (mode={resolved_mode})")


if __name__ == "__main__":
    typer.run(build_preview)

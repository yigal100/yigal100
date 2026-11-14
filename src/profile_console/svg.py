"""Shared SVG primitives, theme configuration, and deterministic font subsetting."""

from __future__ import annotations

import base64
import functools
import html
import io
import math
import pathlib
import re
import tomllib
from dataclasses import dataclass
from typing import TypedDict

from fontTools import subset
from fontTools.ttLib import TTFont

PACKAGE_DIR = pathlib.Path(__file__).resolve().parent
THEMES_DIR = PACKAGE_DIR / "themes"


class _Palette(TypedDict):
    bg: str
    surface: str
    surface_alt: str
    border: str
    fg: str
    wh: str
    dim: str
    muted: str
    cyan: str
    magenta: str
    green: str
    amber: str
    violet: str


class _ThemeSpec(TypedDict):
    card_rx: int
    grid_style: str
    frame_style: str
    heading_style: str
    use_glow: bool
    centerpiece_stem: str
    centerpiece_alt: str
    kicker: str
    footer_status: str
    footer_tag: str
    labels: dict[str, str]


@functools.lru_cache(maxsize=16)
def _load_theme_toml(preset: str) -> tuple[_ThemeSpec, dict[str, _Palette]]:
    """Load and cache theme spec and dark/light palettes from themes/<preset>.toml."""
    path = THEMES_DIR / f"{preset}.toml"
    if not path.exists():
        raise ValueError(f"Unknown theme preset {preset!r}: missing {path}")
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    spec: _ThemeSpec = {
        "card_rx": int(raw["card_rx"]),
        "grid_style": str(raw["grid_style"]),
        "frame_style": str(raw["frame_style"]),
        "heading_style": str(raw["heading_style"]),
        "use_glow": bool(raw["use_glow"]),
        "centerpiece_stem": str(raw["centerpiece_stem"]),
        "centerpiece_alt": str(raw["centerpiece_alt"]),
        "kicker": str(raw["kicker"]),
        "footer_status": str(raw["footer_status"]),
        "footer_tag": str(raw["footer_tag"]),
        "labels": {str(k): str(v) for k, v in raw.get("labels", {}).items()},
    }
    palettes: dict[str, _Palette] = {
        variant: {
            "bg": str(pal["bg"]),
            "surface": str(pal["surface"]),
            "surface_alt": str(pal["surface_alt"]),
            "border": str(pal["border"]),
            "fg": str(pal["fg"]),
            "wh": str(pal["wh"]),
            "dim": str(pal["dim"]),
            "muted": str(pal["muted"]),
            "cyan": str(pal["cyan"]),
            "magenta": str(pal["magenta"]),
            "green": str(pal["green"]),
            "amber": str(pal["amber"]),
            "violet": str(pal["violet"]),
        }
        for variant, pal in raw["palettes"].items()
    }
    return spec, palettes


@dataclass(frozen=True)
class Theme:
    """Visual palette and slice layout constants for profile console themes."""

    preset: str = "cyberpunk"
    variant: str = "dark"
    scifi_labels: bool = False
    bg: str = "#03040a"
    surface: str = "#090d16"
    surface_alt: str = "#11161d"
    border: str = "#1e293b"
    fg: str = "#c9d1d9"
    wh: str = "#f0fbff"
    dim: str = "#8b949e"
    muted: str = "#484f58"
    cyan: str = "#00d9ff"
    magenta: str = "#ff2bd6"
    green: str = "#3fb950"
    amber: str = "#e3b341"
    violet: str = "#bc8cff"
    width: int = 880
    margin: int = 16
    text_x: int = 52
    fonts_dir: pathlib.Path = PACKAGE_DIR / "fonts"

    @classmethod
    def from_preset(
        cls,
        preset: str = "cyberpunk",
        variant: str = "dark",
        *,
        scifi_labels: bool = False,
        fonts_dir: pathlib.Path | None = None,
    ) -> Theme:
        """Build a Theme from a named preset and light/dark variant."""
        resolved_fonts = fonts_dir or (PACKAGE_DIR / "fonts")
        _, palettes = _load_theme_toml(preset)
        palette = palettes.get(variant)
        if palette is None:
            raise ValueError(f"Unknown variant {variant!r} for theme {preset!r}")
        return cls(
            preset=preset,
            variant=variant,
            scifi_labels=scifi_labels,
            fonts_dir=resolved_fonts,
            **palette,
        )

    @property
    def spec(self) -> _ThemeSpec:
        spec, _ = _load_theme_toml(self.preset)
        return spec

    @property
    def is_astrometrics(self) -> bool:
        return self.preset == "astrometrics"

    @property
    def is_arcane(self) -> bool:
        return self.preset == "arcane-architect"

    @property
    def is_studio(self) -> bool:
        return self.preset == "studio"

    @property
    def is_cyberpunk(self) -> bool:
        return self.preset == "cyberpunk"

    @property
    def is_modern(self) -> bool:
        """True for all non-cyberpunk themes."""
        return self.preset != "cyberpunk"

    @property
    def card_rx(self) -> int:
        return self.spec["card_rx"]

    @property
    def is_light(self) -> bool:
        return self.variant == "light"

    def section_label(self, key: str, default: str | None = None) -> str:
        """Return the theme's custom section label when themed labels are enabled, else default."""
        fallback = default if default is not None else key
        if not self.scifi_labels:
            return fallback
        return self.spec["labels"].get(key, fallback)

    @property
    def frame_left(self) -> int:
        return self.margin

    @property
    def frame_right(self) -> int:
        return self.width - self.margin

    @property
    def half_width(self) -> int:
        return self.width // 2

    def resolve_color(self, name: str) -> str:
        """Map named palette tokens (e.g. 'green') to hex colors, or pass through hex."""
        return {
            "cyan": self.cyan,
            "magenta": self.magenta,
            "green": self.green,
            "amber": self.amber,
            "violet": self.violet,
        }.get(name.lower(), name)

    @property
    def base_css(self) -> str:
        return (
            f"text{{font-family:'JBM',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:15px}}\n"
            f".dim{{fill:{self.dim}}}.cy{{fill:{self.cyan}}}.fg{{fill:{self.fg}}}"
            f".gr{{fill:{self.green}}}.wh{{fill:{self.wh}}}.am{{fill:{self.amber}}}.vi{{fill:{self.violet}}}\n"
            "@keyframes fadein{from{opacity:0;transform:translateX(-6px)}to{opacity:1;transform:none}}\n"
            "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}\n"
            "@keyframes pulse{0%,100%{opacity:1}50%{opacity:.35}}\n"
            ".ln{animation:fadein .35s ease-out both}\n"
            ".cursor{animation:blink 1.05s step-end infinite}\n"
            ".dot{animation:pulse 2s ease-in-out infinite}"
        )

    def grid_pattern(self, x_offset: int = 0) -> str:
        """Build the SVG <pattern id='grid'> element for this theme."""
        x_attr = f' x="{x_offset}"' if x_offset else ""
        gs = self.spec["grid_style"]
        if gs == "none":
            return f'<pattern id="grid"{x_attr} width="40" height="40" patternUnits="userSpaceOnUse"></pattern>'
        if gs == "blueprint":
            op = ".07" if self.is_light else ".05"
            return (
                f'<pattern id="grid"{x_attr} width="40" height="40" patternUnits="userSpaceOnUse">'
                f'<path d="M40 0H0V40" fill="none" stroke="{self.amber}" stroke-opacity="{op}"/>'
                f'<path d="M20 0V40M0 20H40" fill="none" stroke="{self.amber}" stroke-opacity=".025"/></pattern>'
            )
        if gs == "dot":
            dot_op = ".12" if self.is_light else ".14"
            grid_op = ".06" if self.is_light else ".045"
            return (
                f'<pattern id="grid"{x_attr} width="40" height="40" patternUnits="userSpaceOnUse">'
                f'<path d="M40 0H0V40" fill="none" stroke="{self.cyan}" stroke-opacity="{grid_op}"/>'
                f'<circle cx="0" cy="0" r="1" fill="{self.cyan}" fill-opacity="{dot_op}"/></pattern>'
            )
        op = ".08" if self.is_light else ".06"
        return (
            f'<pattern id="grid"{x_attr} width="40" height="40" patternUnits="userSpaceOnUse">'
            f'<path d="M40 0H0V40" fill="none" stroke="{self.cyan}" stroke-opacity="{op}"/></pattern>'
        )

    def rail_style(self) -> tuple[str, str, bool]:
        """Return (rail_color, rail_opacity, show_glow) for slice borders."""
        fs = self.spec["frame_style"]
        if self.is_light or fs == "clean":
            return (self.cyan if fs == "brackets" else self.border), "1", False
        if fs == "diamonds":
            return self.amber, ".45", self.spec["use_glow"]
        if fs == "reticles":
            return self.cyan, ".45", self.spec["use_glow"]
        return self.cyan, "1", self.spec["use_glow"]

    @property
    def base_defs(self) -> str:
        glow_std = "6" if self.spec["frame_style"] == "brackets" else "4"
        g_std = "4" if self.spec["frame_style"] == "brackets" else "2"
        return (
            f"{self.grid_pattern()}\n"
            f'<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="{glow_std}"/></filter>\n'
            f'<filter id="g" x="-20%" y="-60%" width="140%" height="220%"><feGaussianBlur stdDeviation="{g_std}"/></filter>'
        )


def esc(value: str) -> str:
    """HTML-escape text for SVG markup."""
    return html.escape(value)


def fmt_num(n: int | None) -> str:
    """Format an integer with thousands separators, or an em-dash if missing."""
    return "—" if n is None else f"{n:,}"


def visible(markup: str) -> str:
    """Return the visible characters in SVG markup so the font subset never misses one."""
    return html.unescape(re.sub(r"<[^>]+>", "", markup))


def faces(text: str, fonts_dir: pathlib.Path, weights: tuple[int, ...] = (400, 700)) -> str:
    """Embed deterministically subsetted JetBrains Mono @font-face rules."""
    text += "0123456789"
    out = []
    for weight in weights:
        font = TTFont(fonts_dir / f"jetbrains-mono-latin-{weight}-normal.woff2", recalcTimestamp=False)
        opts = subset.Options()
        opts.flavor = "woff2"
        opts.layout_features = []
        subsetter = subset.Subsetter(opts)
        subsetter.populate(text=text)
        subsetter.subset(font)
        buf = io.BytesIO()
        font.flavor = "woff2"
        font.save(buf)
        b64 = base64.b64encode(buf.getvalue()).decode()
        out.append(
            f"@font-face{{font-family:'JBM';font-weight:{weight};"
            f"src:url(data:font/woff2;base64,{b64}) format('woff2')}}"
        )
    return "".join(out)


def up40(v: float) -> int:
    """Round up to the nearest 40px grid multiple."""
    return int(math.ceil(v / 40) * 40)


def slice_svg(
    h: int,
    body: str,
    *,
    title: str,
    desc: str,
    text: str,
    theme: Theme,
    top: bool = False,
    bottom: bool = False,
    css: str = "",
    defs: str = "",
    weights: tuple[int, ...] = (400, 700),
) -> str:
    """Wrap section SVG markup in a full-width console slice frame."""
    assert h % 40 == 0, h
    w, m, fl, fr = theme.width, theme.margin, theme.frame_left, theme.frame_right
    y0 = m if top else 0
    y1 = h - m if bottom else h
    rails = f"M{fl} {y0}V{y1}M{fr} {y0}V{y1}"
    if top:
        rails += f"M{fl} {y0}H{fr}"
    if bottom:
        rails += f"M{fl} {y1}H{fr}"
    gy0 = y0 if top else -40
    gy1 = y1 if bottom else h + 40
    glow = (
        f"M{fl} {gy0}V{gy1}M{fr} {gy0}V{gy1}"
        + (f"M{fl} {y0}H{fr}" if top else "")
        + (f"M{fl} {y1}H{fr}" if bottom else "")
    )
    fs = theme.spec["frame_style"]
    rail_color, rail_op, show_glow = theme.rail_style()
    corners = ""
    if fs == "reticles":
        if top:
            corners += (
                f'<circle cx="{fl}" cy="{y0}" r="3.5" fill="{theme.amber}"/>'
                f'<circle cx="{fr}" cy="{y0}" r="3.5" fill="{theme.cyan}"/>'
                f'<path d="M{fl + 8} {y0 - 4}H{fl + 24}M{fr - 24} {y0 - 4}H{fr - 8}" stroke="{theme.dim}" stroke-width="1"/>'
            )
        if bottom:
            corners += (
                f'<circle cx="{fl}" cy="{y1}" r="3.5" fill="{theme.cyan}"/>'
                f'<circle cx="{fr}" cy="{y1}" r="3.5" fill="{theme.amber}"/>'
            )
    elif fs == "diamonds":
        def _diamond(cx: float, cy: float, col: str) -> str:
            return f'<path d="M{cx} {cy - 5}L{cx + 5} {cy}L{cx} {cy + 5}L{cx - 5} {cy}Z" fill="{col}"/>'

        if top:
            corners += _diamond(fl, y0, theme.amber) + _diamond(fr, y0, theme.amber)
        if bottom:
            corners += _diamond(fl, y1, theme.amber) + _diamond(fr, y1, theme.amber)
    elif fs == "brackets":
        bracket_parts = ""
        if top:
            bracket_parts += (
                f'<path d="M{fl - 7} {y0 + 18}V{y0 - 7}H{fl + 18}"/><path d="M{fr - 18} {y0 - 7}H{fr + 7}V{y0 + 18}"/>'
            )
        if bottom:
            bracket_parts += (
                f'<path d="M{fl - 7} {y1 - 18}V{y1 + 7}H{fl + 18}"/><path d="M{fr - 18} {y1 + 7}H{fr + 7}V{y1 - 18}"/>'
            )
        corners = f'<g fill="none" stroke="{rail_color}" stroke-width="2">{bracket_parts}</g>'

    glow_w, glow_op = ("3", ".55") if fs == "brackets" else ("2", ".2")
    glow_markup = (
        f'<path d="{glow}" fill="none" stroke="{rail_color}" stroke-width="{glow_w}" opacity="{glow_op}" filter="url(#glow)"/>\n'
        if show_glow
        else ""
    )
    corner_wrap = corners if fs == "brackets" else f"<g>{corners}</g>"
    rail_markup = f'<path d="{rails}" fill="none" stroke="{rail_color}" stroke-opacity="{rail_op}" stroke-width="1.2"/>\n{corner_wrap}'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d">
<title id="t">{esc(title)}</title>
<desc id="d">{esc(desc)}</desc>
<style>
{faces(text + visible(body), theme.fonts_dir, weights)}
{theme.base_css}
{css}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
</style>
<defs>
{theme.base_defs}
{defs}
</defs>
{glow_markup}<rect x="{fl}" y="{y0}" width="{fr - fl}" height="{y1 - y0}" fill="{theme.bg}"/>
<rect x="{fl}" y="{y0}" width="{fr - fl}" height="{y1 - y0}" fill="url(#grid)"/>
{body}
{rail_markup}
</svg>
'''


def half_slice(
    h: int,
    side: str,
    body: str,
    *,
    title: str,
    desc: str,
    text: str,
    theme: Theme,
    weights: tuple[int, ...] = (400, 700),
) -> str:
    """Left or right half of a full-width row; only its outer side has a rail."""
    assert h % 40 == 0
    hw, m, fl = theme.half_width, theme.margin, theme.frame_left
    rx = fl if side == "L" else hw - m
    bx0, bx1 = (fl, hw) if side == "L" else (0, hw - m)
    rail_color, rail_op, show_glow = theme.rail_style()
    glow_w, glow_op = ("3", ".55") if theme.spec["frame_style"] == "brackets" else ("2", ".2")
    glow_markup = (
        f'<path d="M{rx} -40V{h + 40}" fill="none" stroke="{rail_color}" stroke-width="{glow_w}" opacity="{glow_op}" filter="url(#glow)"/>\n'
        if show_glow
        else ""
    )
    rail_markup = f'<path d="M{rx} 0V{h}" fill="none" stroke="{rail_color}" stroke-opacity="{rail_op}" stroke-width="1.2"/>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{hw}" height="{h}" viewBox="0 0 {hw} {h}" role="img" aria-labelledby="t d">
<title id="t">{esc(title)}</title>
<desc id="d">{esc(desc)}</desc>
<style>
{faces(text + visible(body), theme.fonts_dir, weights)}
{theme.base_css}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
</style>
<defs>
{theme.base_defs}
</defs>
{glow_markup}<rect x="{bx0}" y="0" width="{bx1 - bx0}" height="{h}" fill="{theme.bg}"/>
<rect x="{bx0}" y="0" width="{bx1 - bx0}" height="{h}" fill="url(#grid)"/>
{body}
{rail_markup}
</svg>
'''


def heading(y: int, name: str, counter: str, theme: Theme) -> str:
    """Render a section heading bar with counter."""
    x, fr, cyan = theme.text_x, theme.frame_right, theme.cyan
    hs = theme.spec["heading_style"]
    idx = counter.replace("/", "").strip()
    if hs == "capsule":
        pill_w = 34
        return (
            f'<rect x="{x}" y="{y - 16}" width="{pill_w}" height="18" rx="9" fill="{theme.amber}" fill-opacity=".18" stroke="{theme.amber}" stroke-opacity=".7"/>'
            f'<text x="{x + pill_w / 2}" y="{y - 3}" text-anchor="middle" font-weight="700" fill="{theme.amber}" style="font-size:11px">{esc(idx)}</text>'
            f'<circle cx="{x + pill_w + 14}" cy="{y - 7}" r="3.5" fill="{cyan}"/>'
            f'<text x="{x + pill_w + 26}" y="{y}" font-weight="700" letter-spacing="1.2" class="wh" style="font-size:18px">{esc(name.upper())}</text>'
            f'<line x1="{x}" y1="{y + 14}" x2="{fr - 36}" y2="{y + 14}" stroke="{theme.border}" stroke-width="1"/>'
            f'<line x1="{x}" y1="{y + 14}" x2="{x + 110}" y2="{y + 14}" stroke="{cyan}" stroke-width="2.5" stroke-linecap="round"/>'
        )
    if hs == "diamond":
        return (
            f'<path d="M{x + 6} {y - 13}L{x + 12} {y - 7}L{x + 6} {y - 1}L{x} {y - 7}Z" fill="{theme.amber}"/>'
            f'<text x="{x + 22}" y="{y}" font-weight="700" letter-spacing="1.6" class="wh" style="font-size:18px">{esc(name.upper())}</text>'
            f'<text x="{fr - 36}" y="{y}" text-anchor="end" letter-spacing="2" fill="{theme.amber}" style="font-size:12px">◆ {esc(idx)}</text>'
            f'<line x1="{x}" y1="{y + 14}" x2="{fr - 36}" y2="{y + 14}" stroke="{theme.amber}" stroke-opacity=".35"/>'
            f'<line x1="{x}" y1="{y + 14}" x2="{x + 120}" y2="{y + 14}" stroke="{theme.amber}" stroke-width="2"/>'
        )
    if hs == "block":
        return (
            f'<rect x="{x}" y="{y - 17}" width="30" height="20" rx="2" fill="{cyan}"/>'
            f'<text x="{x + 15}" y="{y - 2}" text-anchor="middle" font-weight="700" fill="{theme.bg}" style="font-size:11.5px">{esc(idx)}</text>'
            f'<text x="{x + 42}" y="{y}" font-weight="800" letter-spacing="1.5" class="wh" style="font-size:18px">{esc(name.upper())}</text>'
            f'<line x1="{x}" y1="{y + 14}" x2="{fr - 36}" y2="{y + 14}" stroke="{theme.border}" stroke-width="1.5"/>'
        )
    glow_t = "" if theme.is_light else f'<text x="{x}" y="{y}" font-weight="700" fill="{cyan}" filter="url(#g)" opacity=".8" style="font-size:20px">~/</text>\n'
    glow_l = "" if theme.is_light else f'\n<line x1="{x}" y1="{y + 14}" x2="{x + 120}" y2="{y + 14}" stroke="{cyan}" stroke-width="3" filter="url(#g)"/>'
    return f'''{glow_t}<text x="{x}" y="{y}" font-weight="700" style="font-size:20px"><tspan class="cy">~/</tspan><tspan class="wh">{esc(name)}</tspan></text>
<text x="{fr - 36}" y="{y}" text-anchor="end" letter-spacing="2" fill="{theme.dim}" style="font-size:12px">{esc(counter)}</text>
<line x1="{x}" y1="{y + 14}" x2="{fr - 36}" y2="{y + 14}" stroke="{cyan}" stroke-opacity=".4"/>
<line x1="{x}" y1="{y + 14}" x2="{x + 120}" y2="{y + 14}" stroke="{cyan}" stroke-width="2"/>{glow_l}'''


def stagger(rows: list[str | None], y0: int, lh: int, delay0: float = 0.15, step: float = 0.12) -> tuple[str, int]:
    """Stagger fade-in animations across lines with {y} placeholders."""
    out, y, i = [], y0, 0
    for r in rows:
        if r is None:
            y += 14
            continue
        i += 1
        out.append(
            f'<g class="ln" style="animation-delay:{delay0 + i * step:.2f}s">' + r.replace("{y}", str(y)) + "</g>"
        )
        y += lh
    return "\n".join(out), y

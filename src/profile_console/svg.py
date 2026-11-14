"""Shared SVG primitives, theme configuration, and deterministic font subsetting."""

from __future__ import annotations

import base64
import html
import io
import math
import pathlib
import re
from dataclasses import dataclass

from fontTools import subset
from fontTools.ttLib import TTFont

PACKAGE_DIR = pathlib.Path(__file__).resolve().parent


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
        if preset == "cyberpunk":
            return cls(
                preset="cyberpunk",
                variant="dark",
                scifi_labels=scifi_labels,
                fonts_dir=resolved_fonts,
            )
        if preset == "astrometrics":
            if variant == "light":
                return cls(
                    preset="astrometrics",
                    variant="light",
                    scifi_labels=scifi_labels,
                    bg="#f8fafc",
                    surface="#ffffff",
                    surface_alt="#e2e8f0",
                    border="#cbd5e1",
                    fg="#1e293b",
                    wh="#0f172a",
                    dim="#475569",
                    muted="#94a3b8",
                    cyan="#0284c7",
                    magenta="#db2777",
                    green="#15803d",
                    amber="#d97706",
                    violet="#7c3aed",
                    fonts_dir=resolved_fonts,
                )
            return cls(
                preset="astrometrics",
                variant="dark",
                scifi_labels=scifi_labels,
                bg="#090d16",
                surface="#0f1624",
                surface_alt="#162033",
                border="#1e2d45",
                fg="#e2e8f0",
                wh="#f8fafc",
                dim="#94a3b8",
                muted="#64748b",
                cyan="#38bdf8",
                magenta="#f472b6",
                green="#4ade80",
                amber="#fbbf24",
                violet="#a78bfa",
                fonts_dir=resolved_fonts,
            )
        raise ValueError(f"Unknown theme preset: {preset!r}")

    @property
    def is_astrometrics(self) -> bool:
        return self.preset == "astrometrics"

    @property
    def is_light(self) -> bool:
        return self.variant == "light"

    def section_label(self, standard: str, scifi: str) -> str:
        """Return opt-in sci-fi section label when enabled, otherwise standard label."""
        return scifi if self.scifi_labels else standard

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

    @property
    def base_defs(self) -> str:
        if self.is_astrometrics:
            dot_op = ".12" if self.is_light else ".14"
            grid_op = ".06" if self.is_light else ".045"
            return (
                f'<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">'
                f'<path d="M40 0H0V40" fill="none" stroke="{self.cyan}" stroke-opacity="{grid_op}"/>'
                f'<circle cx="0" cy="0" r="1" fill="{self.cyan}" fill-opacity="{dot_op}"/></pattern>\n'
                '<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="4"/></filter>\n'
                '<filter id="g" x="-20%" y="-60%" width="140%" height="220%"><feGaussianBlur stdDeviation="2.5"/></filter>'
            )
        return (
            f'<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">'
            f'<path d="M40 0H0V40" fill="none" stroke="{self.cyan}" stroke-opacity=".06"/></pattern>\n'
            '<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="6"/></filter>\n'
            '<filter id="g" x="-20%" y="-60%" width="140%" height="220%"><feGaussianBlur stdDeviation="4"/></filter>'
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
    corners = ""
    if theme.is_astrometrics:
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
        rail_color = theme.border if theme.is_light else theme.cyan
        rail_op = "1" if theme.is_light else ".45"
        glow_markup = (
            ""
            if theme.is_light
            else f'<path d="{glow}" fill="none" stroke="{theme.cyan}" stroke-width="2" opacity=".25" filter="url(#glow)"/>\n'
        )
        rail_markup = f'<path d="{rails}" fill="none" stroke="{rail_color}" stroke-opacity="{rail_op}" stroke-width="1.2"/>\n<g>{corners}</g>'
    else:
        if top:
            corners += (
                f'<path d="M{fl - 7} {y0 + 18}V{y0 - 7}H{fl + 18}"/><path d="M{fr - 18} {y0 - 7}H{fr + 7}V{y0 + 18}"/>'
            )
        if bottom:
            corners += (
                f'<path d="M{fl - 7} {y1 - 18}V{y1 + 7}H{fl + 18}"/><path d="M{fr - 18} {y1 + 7}H{fr + 7}V{y1 - 18}"/>'
            )
        glow_markup = f'<path d="{glow}" fill="none" stroke="{theme.cyan}" stroke-width="3" opacity=".55" filter="url(#glow)"/>\n'
        rail_markup = f'<path d="{rails}" fill="none" stroke="{theme.cyan}" stroke-width="1.2"/>\n<g fill="none" stroke="{theme.cyan}" stroke-width="2">{corners}</g>'
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
    if theme.is_astrometrics:
        rail_color = theme.border if theme.is_light else theme.cyan
        rail_op = "1" if theme.is_light else ".45"
        glow_markup = (
            ""
            if theme.is_light
            else f'<path d="M{rx} -40V{h + 40}" fill="none" stroke="{theme.cyan}" stroke-width="2" opacity=".25" filter="url(#glow)"/>\n'
        )
        rail_markup = f'<path d="M{rx} 0V{h}" fill="none" stroke="{rail_color}" stroke-opacity="{rail_op}" stroke-width="1.2"/>'
    else:
        glow_markup = f'<path d="M{rx} -40V{h + 40}" fill="none" stroke="{theme.cyan}" stroke-width="3" opacity=".55" filter="url(#glow)"/>\n'
        rail_markup = f'<path d="M{rx} 0V{h}" fill="none" stroke="{theme.cyan}" stroke-width="1.2"/>'
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
    if theme.is_astrometrics:
        idx = counter.replace("/", "").strip()
        pill_w = 34
        return (
            f'<rect x="{x}" y="{y - 16}" width="{pill_w}" height="18" rx="9" fill="{theme.amber}" fill-opacity=".18" stroke="{theme.amber}" stroke-opacity=".7"/>'
            f'<text x="{x + pill_w / 2}" y="{y - 3}" text-anchor="middle" font-weight="700" fill="{theme.amber}" style="font-size:11px">{esc(idx)}</text>'
            f'<circle cx="{x + pill_w + 14}" cy="{y - 7}" r="3.5" fill="{cyan}"/>'
            f'<text x="{x + pill_w + 26}" y="{y}" font-weight="700" letter-spacing="1.2" class="wh" style="font-size:18px">{esc(name.upper())}</text>'
            f'<line x1="{x}" y1="{y + 14}" x2="{fr - 36}" y2="{y + 14}" stroke="{theme.border}" stroke-width="1"/>'
            f'<line x1="{x}" y1="{y + 14}" x2="{x + 110}" y2="{y + 14}" stroke="{cyan}" stroke-width="2.5" stroke-linecap="round"/>'
        )
    return f'''<text x="{x}" y="{y}" font-weight="700" fill="{cyan}" filter="url(#g)" opacity=".8" style="font-size:20px">~/</text>
<text x="{x}" y="{y}" font-weight="700" style="font-size:20px"><tspan class="cy">~/</tspan><tspan class="wh">{esc(name)}</tspan></text>
<text x="{fr - 36}" y="{y}" text-anchor="end" letter-spacing="2" fill="#6e7681" style="font-size:12px">{esc(counter)}</text>
<line x1="{x}" y1="{y + 14}" x2="{fr - 36}" y2="{y + 14}" stroke="{cyan}" stroke-opacity=".4"/>
<line x1="{x}" y1="{y + 14}" x2="{x + 120}" y2="{y + 14}" stroke="{cyan}" stroke-width="2"/>
<line x1="{x}" y1="{y + 14}" x2="{x + 120}" y2="{y + 14}" stroke="{cyan}" stroke-width="3" filter="url(#g)"/>'''


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

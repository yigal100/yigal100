"""Outrun 1-point perspective horizon and 3D wireframe canyon slice builder for synthwave."""

from __future__ import annotations

import math

from profile_console.sections._common import busiest_summary, telemetry_cards, weekly_buckets
from profile_console.svg import Theme, heading, slice_svg


def build_outrun(calendar: list[list], updated: str, theme: Theme) -> str:
    """Render the synthwave 1-point perspective outrun horizon, sliced sun, and 3D canyon."""
    x0, fr = theme.text_x, theme.frame_right
    weeks, total, active_days, busiest = weekly_buckets(calendar)
    peak_w = max((n for _, n in weeks), default=1) or 1

    left_x, right_x = float(x0 + 8), 592.0
    vp_x, vp_y = (left_x + right_x) / 2, 268.0
    y_bot = 462.0
    sun_r = 76.0
    sun_cy = vp_y - 10.0

    # Sliced neon sun (above horizon) with horizontal scanline cutouts
    sun_slices: list[str] = []
    # Build sun bands from top to horizon
    cutouts = [(226.0, 230.0), (236.0, 241.0), (247.0, 253.0), (259.0, 266.0)]
    y_top = sun_cy - sun_r
    solid_bands: list[tuple[float, float]] = []
    cur = y_top
    for c0, c1 in cutouts:
        if c0 > cur:
            solid_bands.append((cur, c0))
        cur = c1
    if cur < vp_y:
        solid_bands.append((cur, vp_y))

    for idx, (b0, b1) in enumerate(solid_bands):
        sun_slices.append(
            f'<clipPath id="sun-b{idx}"><rect x="{vp_x - sun_r - 2:.1f}" y="{b0:.1f}" '
            f'width="{sun_r * 2 + 4:.1f}" height="{b1 - b0:.1f}"/></clipPath>'
        )
    sun_defs = (
        f'<defs>'
        f'<linearGradient id="outrun-sun" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{theme.amber}"/>'
        f'<stop offset="55%" stop-color="{theme.magenta}"/>'
        f'<stop offset="100%" stop-color="{theme.violet}"/>'
        f"</linearGradient>"
        f'{"".join(sun_slices)}'
        f"</defs>"
    )
    sun_els = "".join(
        f'<circle cx="{vp_x:.1f}" cy="{sun_cy:.1f}" r="{sun_r:.1f}" '
        f'fill="url(#outrun-sun)" opacity="{0.82 if theme.is_light else 0.92}" clip-path="url(#sun-b{idx})"/>'
        for idx in range(len(solid_bands))
    )

    # 1-point perspective neon ground grid
    grid: list[str] = []
    grid_col = theme.magenta
    n_scroll = 8
    for i in range(n_scroll):
        grid.append(
            f'<line class="grid-scroll" x1="{left_x:.1f}" y1="{vp_y:.1f}" x2="{right_x:.1f}" y2="{vp_y:.1f}" '
            f'stroke="{grid_col}" stroke-width=".9" style="animation-delay:{-i * (4.0 / n_scroll):.2f}s"/>'
        )
    for k in range(-6, 7):
        bx = vp_x + k * 48.0
        # Clip ray to [left_x, right_x]
        if bx < left_x:
            t_edge = (left_x - vp_x) / (bx - vp_x)
            ex, ey = left_x, vp_y + t_edge * (y_bot - vp_y)
        elif bx > right_x:
            t_edge = (right_x - vp_x) / (bx - vp_x)
            ex, ey = right_x, vp_y + t_edge * (y_bot - vp_y)
        else:
            ex, ey = bx, y_bot
        grid.append(
            f'<line x1="{vp_x:.1f}" y1="{vp_y:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" '
            f'stroke="{grid_col}" stroke-width=".9" stroke-opacity=".38"/>'
        )
    grid.append(
        f'<line class="horizon-glow" x1="{left_x:.1f}" y1="{vp_y:.1f}" x2="{right_x:.1f}" y2="{vp_y:.1f}" '
        f'stroke="{theme.cyan}" stroke-width="1.3" stroke-opacity=".75"/>'
    )

    # 3D wireframe canyon walls: left = first 26 weeks, right = last 26 weeks
    n_depth = 26
    h1 = weeks[:n_depth]
    h2 = weeks[n_depth : n_depth * 2]
    while len(h1) < n_depth:
        h1.append((weeks[-1][0], 0))
    while len(h2) < n_depth:
        h2.append((weeks[-1][0], 0))

    canyon_els: list[str] = []
    for side, series, stroke_col in ((-1, h1, theme.cyan), (1, h2, theme.magenta)):
        ridge_pts: list[tuple[float, float]] = []
        base_pts: list[tuple[float, float]] = []
        for idx, (_, val) in enumerate(series):
            # Depth t goes from 0.08 (near horizon) to 1.0 (foreground)
            t = 0.08 + 0.92 * ((idx / max(n_depth - 1, 1)) ** 1.35)
            # Highway corridor widens with perspective; canyon sits outside the corridor
            corridor_half = 18.0 + t * 92.0
            outer_half = 45.0 + t * 212.0
            by = vp_y + t * (y_bot - vp_y)
            bx_inner = vp_x + side * corridor_half
            bx_outer = vp_x + side * outer_half
            norm = math.sqrt(val / peak_w) if val > 0 else 0.0
            peak_h = (12.0 + 96.0 * t) * norm + 6.0 * t
            px = (bx_inner + bx_outer) * 0.5
            py = by - peak_h
            base_pts.append((bx_inner, by))
            ridge_pts.append((px, py))

        # Draw back-to-front wireframe canyon ribs and crest
        poly_pts = ridge_pts + list(reversed(base_pts))
        poly_str = " ".join(f"{px:.1f},{py:.1f}" for px, py in poly_pts)
        canyon_els.append(
            f'<polygon class="canyon-crest" points="{poly_str}" fill="{theme.surface}" fill-opacity=".82" '
            f'stroke="{stroke_col}" stroke-width="1.3" stroke-opacity=".88" '
            f'style="animation-delay:{0.0 if side == -1 else 1.8:.1f}s"/>'
        )
        for (rx_p, ry_p), (bx_p, by_p) in zip(ridge_pts, base_pts, strict=True):
            canyon_els.append(
                f'<line x1="{bx_p:.1f}" y1="{by_p:.1f}" x2="{rx_p:.1f}" y2="{ry_p:.1f}" '
                f'stroke="{stroke_col}" stroke-width=".8" stroke-opacity=".42"/>'
            )

    dy_grid = y_bot - vp_y
    css = (
        f"@keyframes grid-scroll{{0%{{transform:translateY(0);opacity:0}}12%{{opacity:.22}}100%{{transform:translateY({dy_grid:.1f}px);opacity:.62}}}}\n"
        "@keyframes sun-breath{0%,100%{opacity:.95}50%{opacity:.78}}\n"
        "@keyframes horizon-glow{0%,100%{stroke-opacity:.65}50%{stroke-opacity:1}}\n"
        "@keyframes canyon-crest{0%,100%{stroke-opacity:.72}50%{stroke-opacity:1}}\n"
        ".grid-scroll{animation:grid-scroll 4s cubic-bezier(.55,.05,.85,.25) infinite}\n"
        ".sun-wrap{animation:sun-breath 5s ease-in-out infinite}\n"
        ".horizon-glow{animation:horizon-glow 3.5s ease-in-out infinite}\n"
        ".canyon-crest{animation:canyon-crest 4.2s ease-in-out infinite}"
    )

    rx_card = 626
    rw = (fr - 36) - rx_card
    busiest_val, busiest_sub = busiest_summary(busiest)
    cards = [
        ("TOTAL BOOST", f"{total:,}", "last 365 days", theme.magenta),
        ("ACTIVE DAYS", f"{active_days}", f"of {len(calendar)} days", theme.cyan),
        ("PEAK OVERDRIVE", busiest_val, busiest_sub, theme.amber),
    ]
    telemetry = telemetry_cards(cards, rx_card, rw, theme)

    sec_title = theme.section_label("centerpiece", "outrun-horizon")
    body = (
        heading(44, sec_title, "// 03", theme)
        + f'''
{sun_defs}
<g class="ln" style="animation-delay:.15s"><text x="{x0}" y="96" class="dim"><tspan class="cy">›</tspan> outrun horizon · 3d wireframe canyon · 52w</text></g>
<g><g class="sun-wrap">{sun_els}</g>{"".join(grid)}{"".join(canyon_els)}</g>
{telemetry}'''
    )
    return slice_svg(
        520,
        body,
        title="Outrun horizon",
        desc=f"3D perspective outrun horizon and wireframe canyon of the last 365 days: {total:,} contributions across {active_days} active days.",
        text=f"{sec_title}03outrun horizon3d wireframe canyon52wTOTAL BOOSTACTIVE DAYSPEAK OVERDRIVE{total}{active_days}{busiest_val}",
        theme=theme,
        css=css,
    )

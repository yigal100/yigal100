"""Aurora harmonic fjord (nordic-fjord) and phosphor radar sweep (retro-amber) slice builders."""

from __future__ import annotations

import math

from profile_console.sections._common import busiest_summary, smooth_path, telemetry_cards, weekly_buckets
from profile_console.svg import Theme, heading, slice_svg


def build_aurora(calendar: list[list], updated: str, theme: Theme) -> str:
    """Render a multi-band harmonic aurora over a fjord silhouette with water reflection."""
    x0, fr = theme.text_x, theme.frame_right
    weeks, total, active_days, busiest = weekly_buckets(calendar)
    peak_w = max((n for _, n in weeks), default=1) or 1

    chart_x0, chart_w = x0 + 10.0, 540.0
    horizon_y = 388.0
    band_specs = [
        (theme.violet, 0.20, 0.72, 200.0, 0.0),
        (theme.cyan, 0.25, 0.86, 160.0, 0.9),
        (theme.green, 0.28, 0.94, 122.0, 1.8),
    ]

    ribbons: list[str] = []
    # Subtle horizontal altitude ticks
    for frac, label in ((0.33, "LOW"), (0.66, "MID"), (1.0, "PEAK")):
        gy = horizon_y - frac * 205.0
        ribbons.append(
            f'<line x1="{chart_x0:.1f}" y1="{gy:.1f}" x2="{chart_x0 + chart_w:.1f}" y2="{gy:.1f}" '
            f'stroke="{theme.border}" stroke-dasharray="3 5" stroke-opacity=".55"/>'
            f'<text x="{chart_x0:.1f}" y="{gy - 5:.1f}" class="dim" style="font-size:9px">{label}</text>'
        )

    n_weeks = max(len(weeks) - 1, 1)
    peak_markers: list[str] = []
    curtains: list[str] = []
    reflection_pts: list[tuple[float, float]] = []

    for band_idx, (col, fill_op, stroke_op, max_amp, phase) in enumerate(band_specs):
        pts: list[tuple[float, float]] = []
        for i, (_, val) in enumerate(weeks):
            px = chart_x0 + (i / n_weeks) * chart_w
            norm = math.sqrt(val / peak_w) if val > 0 else 0.0
            harmonic = 0.82 + 0.18 * math.sin(i * 0.45 + phase)
            py = horizon_y - max_amp * norm * harmonic
            pts.append((px, py))

            # Vertical aurora curtain striations on upper bands
            if band_idx in (1, 2) and val > 0 and i % 2 == 0:
                ray_h = 18.0 + 28.0 * norm
                curtains.append(
                    f'<line x1="{px:.1f}" y1="{py:.1f}" x2="{px:.1f}" y2="{max(132.0, py - ray_h):.1f}" '
                    f'stroke="{col}" stroke-width="1.4" stroke-opacity="{0.14 + 0.22 * norm:.2f}"/>'
                )
            if band_idx == 2:
                reflection_pts.append((px, horizon_y + 6.0 + 42.0 * norm * harmonic))
                if val >= peak_w * 0.65:
                    peak_markers.append(
                        f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.2" fill="{theme.accent_color}"/>'
                        f'<circle cx="{px:.1f}" cy="{py:.1f}" r="6.5" fill="none" stroke="{theme.accent_color}" stroke-opacity=".45"/>'
                    )

        curve = smooth_path(pts)
        area = f"{curve}L{chart_x0 + chart_w:.1f},{horizon_y:.1f}L{chart_x0:.1f},{horizon_y:.1f}Z"
        ribbons.append(
            f'<path d="{area}" fill="{col}" fill-opacity="{fill_op * (0.75 if theme.is_light else 1.0):.2f}"/>'
            f'<path d="{curve}" fill="none" stroke="{col}" stroke-width="2" stroke-opacity="{stroke_op:.2f}"/>'
        )

    # Fjord mountain silhouette along the horizon
    ridge_pts = [
        (0.00, 0), (0.08, 18), (0.17, 10), (0.26, 28), (0.35, 14),
        (0.46, 8), (0.57, 24), (0.68, 12), (0.79, 31), (0.90, 15), (1.00, 0),
    ]
    mtn_d = "M" + "L".join(f"{chart_x0 + fx * chart_w:.1f},{horizon_y - dy:.1f}" for fx, dy in ridge_pts) + "Z"
    mtn_col = "#cbd5e1" if theme.is_light else "#091018"
    fjord = (
        f'<path d="{mtn_d}" fill="{mtn_col}" stroke="{theme.border}" stroke-width="1"/>'
        f'<line x1="{chart_x0:.1f}" y1="{horizon_y:.1f}" x2="{chart_x0 + chart_w:.1f}" y2="{horizon_y:.1f}" '
        f'stroke="{theme.cyan}" stroke-width="1.1" stroke-opacity=".55"/>'
    )

    # Subtle water reflection below the horizon
    if reflection_pts:
        refl_curve = smooth_path(reflection_pts)
        refl_area = f"{refl_curve}L{chart_x0 + chart_w:.1f},{horizon_y + 4:.1f}L{chart_x0:.1f},{horizon_y + 4:.1f}Z"
        fjord += (
            f'<path d="{refl_area}" fill="{theme.cyan}" fill-opacity=".08"/>'
            f'<path d="{refl_curve}" fill="none" stroke="{theme.cyan}" stroke-width="1" stroke-opacity=".28" stroke-dasharray="4 3"/>'
        )

    rx_card = 626
    rw = (fr - 36) - rx_card
    busiest_val, busiest_sub = busiest_summary(busiest)
    cards = [
        ("TOTAL OUTPUT", f"{total:,}", "last 365 days", theme.accent_color),
        ("ACTIVE DAYS", f"{active_days}", f"of {len(calendar)} days", theme.green),
        ("PEAK CREST", busiest_val, busiest_sub, theme.cyan),
    ]
    telemetry = telemetry_cards(cards, rx_card, rw, theme)

    sec_title = theme.section_label("centerpiece", "fjord-aurora")
    body = (
        heading(44, sec_title, "// 03", theme)
        + f'''
<g class="ln" style="animation-delay:.15s"><text x="{x0}" y="96" class="dim"><tspan class="cy">›</tspan> harmonic aurora · fjord reflection · 52w</text></g>
<g>{"".join(curtains)}{"".join(ribbons)}{fjord}{"".join(peak_markers)}</g>
{telemetry}'''
    )
    return slice_svg(
        520,
        body,
        title="Fjord aurora",
        desc=f"Harmonic aurora ribbons over a fjord of the last 365 days: {total:,} contributions across {active_days} active days.",
        text=f"{sec_title}03harmonic aurorafjord reflection52wLOWMIDPEAKTOTAL OUTPUTACTIVE DAYSPEAK CREST{total}{active_days}{busiest_val}",
        theme=theme,
    )


def build_radar(calendar: list[list], updated: str, theme: Theme) -> str:
    """Render a 52-week phosphor CRT polar radar sweep chart of annual activity."""
    x0, fr = theme.text_x, theme.frame_right
    weeks, total, active_days, busiest = weekly_buckets(calendar)
    peak_w = max((n for _, n in weeks), default=1) or 1

    cx, cy = 320.0, 304.0
    r_inner, r_outer = 34.0, 168.0
    accent = theme.accent_color

    grid: list[str] = []
    for frac in (0.25, 0.5, 0.75, 1.0):
        rr = r_inner + frac * (r_outer - r_inner)
        grid.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rr:.1f}" fill="none" '
            f'stroke="{theme.border}" stroke-dasharray="{"none" if frac == 1.0 else "3 4"}" stroke-opacity=".8"/>'
        )
    for angle_deg in (0, 90, 180, 270):
        rad = math.radians(angle_deg)
        x1 = cx + r_inner * math.cos(rad)
        y1 = cy + r_inner * math.sin(rad)
        x2 = cx + r_outer * math.cos(rad)
        y2 = cy + r_outer * math.sin(rad)
        grid.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{theme.border}" stroke-opacity=".75"/>')

    # Subtle CRT phosphor scanlines clipped to the radar scope
    scanlines: list[str] = []
    for sy in range(int(cy - r_outer), int(cy + r_outer), 4):
        dy = abs(sy - cy)
        if dy < r_outer:
            dx = math.sqrt(r_outer * r_outer - dy * dy)
            scanlines.append(
                f'<line x1="{cx - dx:.1f}" y1="{sy}" x2="{cx + dx:.1f}" y2="{sy}" '
                f'stroke="{theme.border}" stroke-width=".6" stroke-opacity=".24"/>'
            )

    n_weeks = max(len(weeks), 1)
    poly_pts: list[tuple[float, float]] = []
    spokes: list[str] = []
    blips: list[str] = []
    for i, (_, val) in enumerate(weeks):
        angle = -math.pi / 2 + (2 * math.pi * i) / n_weeks
        norm = math.sqrt(val / peak_w) if val > 0 else 0.0
        r_val = r_inner + norm * (r_outer - r_inner)
        px = cx + r_val * math.cos(angle)
        py = cy + r_val * math.sin(angle)
        poly_pts.append((px, py))

        sx = cx + r_inner * math.cos(angle)
        sy = cy + r_inner * math.sin(angle)
        col = accent if val >= peak_w * 0.6 else (theme.cyan if val > 0 else theme.muted)
        spokes.append(
            f'<line x1="{sx:.1f}" y1="{sy:.1f}" x2="{px:.1f}" y2="{py:.1f}" '
            f'stroke="{col}" stroke-width="2.2" stroke-linecap="round" stroke-opacity="{0.85 if val > 0 else 0.35}"/>'
        )
        if val >= peak_w * 0.65:
            # Target-lock crosshair reticle around peak echo blips
            blips.append(
                f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.2" fill="{accent}"/>'
                f'<circle cx="{px:.1f}" cy="{py:.1f}" r="7.5" fill="none" stroke="{accent}" stroke-opacity=".55" stroke-dasharray="3 2"/>'
                f'<path d="M{px - 10:.1f},{py:.1f}h4M{px + 6:.1f},{py:.1f}h4M{px:.1f},{py - 10:.1f}v4M{px:.1f},{py + 6:.1f}v4" '
                f'stroke="{accent}" stroke-width="1" stroke-opacity=".7"/>'
            )

    poly_str = " ".join(f"{px:.1f},{py:.1f}" for px, py in poly_pts)
    poly_el = (
        f'<polygon points="{poly_str}" fill="{theme.cyan}" fill-opacity=".12" '
        f'stroke="{theme.cyan}" stroke-width="1.4" stroke-opacity=".7"/>'
        if poly_pts
        else ""
    )

    css = "@keyframes sweep{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}.sweep{transform-origin:320px 304px;animation:sweep 14s linear infinite}"
    # Multi-step fading phosphor persistence trail behind the sweep arm
    trail_wedges: list[str] = []
    for step_idx, (deg_start, deg_end, op) in enumerate(((0, 16, 0.14), (16, 32, 0.08), (32, 50, 0.04))):
        a0 = -math.pi / 2 + math.radians(deg_start)
        a1 = -math.pi / 2 + math.radians(deg_end)
        x0_s, y0_s = cx + r_outer * math.cos(a0), cy + r_outer * math.sin(a0)
        x1_s, y1_s = cx + r_outer * math.cos(a1), cy + r_outer * math.sin(a1)
        trail_wedges.append(
            f'<path d="M{cx:.1f},{cy:.1f} L{x0_s:.1f},{y0_s:.1f} A{r_outer:.1f},{r_outer:.1f} 0 0,1 {x1_s:.1f},{y1_s:.1f} Z" '
            f'fill="{accent}" fill-opacity="{op}"/>'
        )
    sweep = (
        f'<g class="sweep">{"".join(trail_wedges)}'
        f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{cx:.1f}" y2="{cy - r_outer:.1f}" stroke="{accent}" stroke-width="1.4" stroke-opacity=".75"/>'
        f"</g>"
    )

    rx_card = 626
    rw = (fr - 36) - rx_card
    busiest_val, busiest_sub = busiest_summary(busiest)
    cards = [
        ("TOTAL SIGNALS", f"{total:,}", "last 365 days", accent),
        ("ACTIVE DAYS", f"{active_days}", f"of {len(calendar)} days", theme.green),
        ("PEAK ECHO", busiest_val, busiest_sub, theme.cyan),
    ]
    telemetry = telemetry_cards(cards, rx_card, rw, theme)

    sec_title = theme.section_label("centerpiece", "contribution-radar")
    prompt = '<tspan class="gr">$</tspan> radar --scan 52w' if not theme.uses_chevron_prompt else '<tspan class="cy">›</tspan> polar sweep · 52 weekly sectors'
    body = (
        heading(44, sec_title, "// 03", theme)
        + f'''
<g class="ln" style="animation-delay:.15s"><text x="{x0}" y="96" class="dim">{prompt}</text></g>
<g>{"".join(scanlines)}{"".join(grid)}{poly_el}{"".join(spokes)}{sweep}{"".join(blips)}</g>
<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4" fill="{accent}"/>
{telemetry}'''
    )
    return slice_svg(
        520,
        body,
        title="Contribution radar",
        desc=f"Polar radar sweep of the last 365 days: {total:,} contributions across {active_days} active days.",
        text=f"{sec_title}03polar sweep52 weekly sectorsradarscan 52wTOTAL SIGNALSACTIVE DAYSPEAK ECHO{total}{active_days}{busiest_val}",
        theme=theme,
        css=css,
    )

"""Aurora harmonic wave and polar radar sweep centerpiece slice builders."""

from __future__ import annotations

import math

from profile_console.sections.terrain import _weekly_buckets
from profile_console.svg import Theme, esc, heading, slice_svg


def _telemetry_cards(
    cards: list[tuple[str, str, str, str]],
    rx_card: int,
    rw: int,
    theme: Theme,
) -> str:
    """Render the 3 right-hand telemetry summary cards styled for the active theme."""
    parts: list[str] = []
    for i, (lab, val, sub, acc) in enumerate(cards):
        y = 150 + i * 96
        if theme.uses_surface_cards:
            box = (
                f'<rect x="{rx_card}" y="{y}" width="{rw}" height="80" rx="{theme.card_rx}" '
                f'fill="{theme.surface}" stroke="{theme.border}"/>'
                f'<rect x="{rx_card}" y="{y + 12}" width="4" height="56" rx="2" fill="{acc}"/>'
            )
        else:
            box = (
                f'<rect x="{rx_card}" y="{y}" width="{rw}" height="80" '
                f'fill="{acc}" fill-opacity=".04" stroke="{acc}" stroke-opacity=".38"/>'
                f'<path d="M{rx_card} {y + 12}V{y}H{rx_card + 12}" fill="none" stroke="{acc}" stroke-width="2"/>'
            )
        parts.append(
            f'<g class="ln" style="animation-delay:{0.2 + i * 0.1:.2f}s">'
            f"{box}"
            f'<text x="{rx_card + 16}" y="{y + 24}" letter-spacing="1.2" class="dim" style="font-size:10px">{esc(lab)}</text>'
            f'<text x="{rx_card + 16}" y="{y + 50}" font-weight="700" fill="{acc}" style="font-size:22px">{esc(val)}</text>'
            f'<text x="{rx_card + 16}" y="{y + 68}" class="dim" style="font-size:11px">{esc(sub)}</text>'
            "</g>"
        )
    return "".join(parts)


def _smooth_path(pts: list[tuple[float, float]]) -> str:
    """Build a smooth SVG cubic-Bezier spline through (x, y) control points."""
    if not pts:
        return ""
    if len(pts) == 1:
        return f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
    cmds = [f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"]
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        mx = (x0 + x1) / 2
        cmds.append(f"C{mx:.1f},{y0:.1f} {mx:.1f},{y1:.1f} {x1:.1f},{y1:.1f}")
    return "".join(cmds)


def build_aurora(calendar: list[list], updated: str, theme: Theme) -> str:
    """Render a multi-band harmonic aurora ribbon chart of 52 weekly buckets."""
    x0, fr = theme.text_x, theme.frame_right
    weeks, total, active_days, busiest = _weekly_buckets(calendar)
    peak_w = max((n for _, n in weeks), default=1) or 1

    chart_x0, chart_w = x0 + 10.0, 540.0
    base_y = 448.0
    band_specs = [
        (theme.violet, 0.22, 0.72, 235.0, 0.0),
        (theme.cyan, 0.26, 0.85, 190.0, 0.9),
        (theme.green, 0.30, 0.92, 145.0, 1.8),
    ]

    ribbons: list[str] = []
    # Subtle horizontal baseline ticks
    for frac, label in ((0.25, "25%"), (0.5, "50%"), (0.75, "75%"), (1.0, "PEAK")):
        gy = base_y - frac * 245.0
        ribbons.append(
            f'<line x1="{chart_x0:.1f}" y1="{gy:.1f}" x2="{chart_x0 + chart_w:.1f}" y2="{gy:.1f}" '
            f'stroke="{theme.border}" stroke-dasharray="3 5" stroke-opacity=".7"/>'
            f'<text x="{chart_x0:.1f}" y="{gy - 5:.1f}" class="dim" style="font-size:9px">{label}</text>'
        )

    n_weeks = max(len(weeks) - 1, 1)
    peak_markers: list[str] = []
    for band_idx, (col, fill_op, stroke_op, max_amp, phase) in enumerate(band_specs):
        pts: list[tuple[float, float]] = []
        for i, (_, val) in enumerate(weeks):
            px = chart_x0 + (i / n_weeks) * chart_w
            norm = math.sqrt(val / peak_w) if val > 0 else 0.0
            harmonic = 0.82 + 0.18 * math.sin(i * 0.45 + phase)
            py = base_y - max_amp * norm * harmonic
            pts.append((px, py))
            if band_idx == 2 and val >= peak_w * 0.65:
                peak_markers.append(
                    f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.2" fill="{theme.accent_color}"/>'
                    f'<circle cx="{px:.1f}" cy="{py:.1f}" r="6.5" fill="none" stroke="{theme.accent_color}" stroke-opacity=".45"/>'
                )
        curve = _smooth_path(pts)
        area = f"{curve}L{chart_x0 + chart_w:.1f},{base_y:.1f}L{chart_x0:.1f},{base_y:.1f}Z"
        ribbons.append(
            f'<path d="{area}" fill="{col}" fill-opacity="{fill_op * (0.75 if theme.is_light else 1.0):.2f}"/>'
            f'<path d="{curve}" fill="none" stroke="{col}" stroke-width="2" stroke-opacity="{stroke_op:.2f}"/>'
        )
    ribbons.append(
        f'<line x1="{chart_x0:.1f}" y1="{base_y:.1f}" x2="{chart_x0 + chart_w:.1f}" y2="{base_y:.1f}" '
        f'stroke="{theme.border}" stroke-width="1.2"/>'
    )

    rx_card = 626
    rw = (fr - 36) - rx_card
    busiest_val = f"{busiest[0]:%b} {busiest[0].day}" if busiest and busiest[1] else "—"
    busiest_sub = f"{busiest[1]} contributions" if busiest and busiest[1] else "no activity"
    cards = [
        ("TOTAL OUTPUT", f"{total:,}", "last 365 days", theme.accent_color),
        ("ACTIVE DAYS", f"{active_days}", f"of {len(calendar)} days", theme.green),
        ("PEAK CREST", busiest_val, busiest_sub, theme.cyan),
    ]
    telemetry = _telemetry_cards(cards, rx_card, rw, theme)

    sec_title = theme.section_label("centerpiece", "contribution-aurora")
    body = (
        heading(44, sec_title, "// 03", theme)
        + f'''
<g class="ln" style="animation-delay:.15s"><text x="{x0}" y="96" class="dim"><tspan class="cy">›</tspan> harmonic bands · 52 weekly signals</text></g>
<g>{"".join(ribbons)}{"".join(peak_markers)}</g>
{telemetry}'''
    )
    return slice_svg(
        520,
        body,
        title="Contribution aurora",
        desc=f"Harmonic aurora ribbons of the last 365 days: {total:,} contributions across {active_days} active days.",
        text=f"{sec_title}03harmonic bands52 weekly signalsTOTAL OUTPUTACTIVE DAYSPEAK CREST{total}{active_days}{busiest_val}",
        theme=theme,
    )


def build_radar(calendar: list[list], updated: str, theme: Theme) -> str:
    """Render a 52-week polar radar sweep chart of annual activity."""
    x0, fr = theme.text_x, theme.frame_right
    weeks, total, active_days, busiest = _weekly_buckets(calendar)
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
            blips.append(
                f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.5" fill="{accent}"/>'
                f'<circle cx="{px:.1f}" cy="{py:.1f}" r="7" fill="none" stroke="{accent}" stroke-opacity=".5"/>'
            )

    poly_str = " ".join(f"{px:.1f},{py:.1f}" for px, py in poly_pts)
    poly_el = (
        f'<polygon points="{poly_str}" fill="{theme.cyan}" fill-opacity=".12" '
        f'stroke="{theme.cyan}" stroke-width="1.4" stroke-opacity=".7"/>'
        if poly_pts
        else ""
    )

    css = "@keyframes sweep{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}.sweep{transform-origin:320px 304px;animation:sweep 14s linear infinite}"
    sweep_x = cx + r_outer * math.cos(-math.pi / 4)
    sweep_y = cy + r_outer * math.sin(-math.pi / 4)
    sweep = (
        f'<g class="sweep">'
        f'<path d="M{cx:.1f},{cy:.1f} L{cx:.1f},{cy - r_outer:.1f} A{r_outer:.1f},{r_outer:.1f} 0 0,1 {sweep_x:.1f},{sweep_y:.1f} Z" '
        f'fill="{accent}" fill-opacity=".10"/>'
        f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{cx:.1f}" y2="{cy - r_outer:.1f}" stroke="{accent}" stroke-width="1.2" stroke-opacity=".6"/>'
        f"</g>"
    )

    rx_card = 626
    rw = (fr - 36) - rx_card
    busiest_val = f"{busiest[0]:%b} {busiest[0].day}" if busiest and busiest[1] else "—"
    busiest_sub = f"{busiest[1]} contributions" if busiest and busiest[1] else "no activity"
    cards = [
        ("TOTAL SIGNALS", f"{total:,}", "last 365 days", accent),
        ("ACTIVE DAYS", f"{active_days}", f"of {len(calendar)} days", theme.green),
        ("PEAK ECHO", busiest_val, busiest_sub, theme.cyan),
    ]
    telemetry = _telemetry_cards(cards, rx_card, rw, theme)

    sec_title = theme.section_label("centerpiece", "contribution-radar")
    prompt = '<tspan class="gr">$</tspan> radar --scan 52w' if not theme.uses_chevron_prompt else '<tspan class="cy">›</tspan> polar sweep · 52 weekly sectors'
    body = (
        heading(44, sec_title, "// 03", theme)
        + f'''
<g class="ln" style="animation-delay:.15s"><text x="{x0}" y="96" class="dim">{prompt}</text></g>
<g>{"".join(grid)}{poly_el}{"".join(spokes)}{sweep}{"".join(blips)}</g>
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

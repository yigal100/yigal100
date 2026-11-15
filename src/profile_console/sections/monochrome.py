"""Unknown Pleasures-inspired stacked joyplot slice builder for monochrome-ink."""

from __future__ import annotations

import datetime
import math

from profile_console.sections._common import busiest_summary, smooth_path, telemetry_cards
from profile_console.svg import Theme, heading, slice_svg


def build_joyplot(calendar: list[list], updated: str, theme: Theme) -> str:
    """Render a 14-band stacked ink joyplot of the last 365 days."""
    x0, fr = theme.text_x, theme.frame_right
    days = [(datetime.date.fromisoformat(d), n) for d, n in calendar]
    total = sum(n for _, n in days)
    active_days = sum(1 for _, n in days if n > 0)
    busiest = max(days, key=lambda t: t[1]) if days else None
    peak_d = max((n for _, n in days), default=1) or 1

    n_bands = 14
    band_len = max(1, math.ceil(len(days) / n_bands))
    chart_x0, chart_w = float(x0 + 10), 540.0
    base_y0, band_dy, max_amp = 168.0, 21.5, 48.0

    waves: list[str] = []
    for b in range(n_bands):
        chunk = days[b * band_len : (b + 1) * band_len]
        if not chunk:
            continue
        by = base_y0 + b * band_dy
        n_pts = len(chunk)
        pts: list[tuple[float, float]] = []
        band_peak = max((n for _, n in chunk), default=0)

        for idx, (_, val) in enumerate(chunk):
            px = chart_x0 + (idx / max(n_pts - 1, 1)) * chart_w
            # Taper edges smoothly to baseline like classic pulsar plots
            edge_u = idx / max(n_pts - 1, 1)
            envelope = math.sin(math.pi * edge_u) ** 0.55 if n_pts > 2 else 1.0
            norm = math.sqrt(val / peak_d) if val > 0 else 0.0
            amp = max_amp * norm * envelope
            pts.append((px, by - amp))

        curve = smooth_path(pts)
        area = f"{curve}L{chart_x0 + chart_w:.1f},{by + 2:.1f}L{chart_x0:.1f},{by + 2:.1f}Z"
        is_hot = band_peak >= peak_d * 0.72
        stroke_col = theme.accent_color if is_hot else theme.fg
        stroke_op = ".95" if is_hot else ".82"
        waves.append(
            f'<path d="{area}" fill="{theme.bg}"/>'
            f'<path d="{curve}" fill="none" stroke="{stroke_col}" stroke-width="1.35" stroke-opacity="{stroke_op}"/>'
        )

    rx_card = 626
    rw = (fr - 36) - rx_card
    busiest_val, busiest_sub = busiest_summary(busiest)
    cards = [
        ("TOTAL PLATES", f"{total:,}", "last 365 days", theme.fg),
        ("ACTIVE DAYS", f"{active_days}", f"of {len(calendar)} days", theme.dim),
        ("PEAK CREST", busiest_val, busiest_sub, theme.accent_color),
    ]
    telemetry = telemetry_cards(cards, rx_card, rw, theme)

    sec_title = theme.section_label("centerpiece", "plate")
    body = (
        heading(44, sec_title, "// 03", theme)
        + f'''
<g class="ln" style="animation-delay:.15s"><text x="{x0}" y="96" class="dim"><tspan class="cy">›</tspan> stacked ink ridgelines · 14 plates · 365d</text></g>
<g>{"".join(waves)}</g>
{telemetry}'''
    )
    return slice_svg(
        520,
        body,
        title="Ink ridgelines",
        desc=f"Stacked ink ridgelines of the last 365 days: {total:,} contributions across {active_days} active days.",
        text=f"{sec_title}03stacked ink ridgelines14 plates365dTOTAL PLATESACTIVE DAYSPEAK CREST{total}{active_days}{busiest_val}",
        theme=theme,
    )

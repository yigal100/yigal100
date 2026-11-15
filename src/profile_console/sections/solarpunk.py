"""Dendrochronology tree growth rings and canopy nodes slice builder for solarpunk."""

from __future__ import annotations

import math

from profile_console.sections._common import busiest_summary, telemetry_cards, weekly_buckets
from profile_console.svg import Theme, heading, slice_svg


def build_rings(calendar: list[list], updated: str, theme: Theme) -> str:
    """Render 12 organic concentric tree growth rings and canopy nodes for solarpunk."""
    x0, fr = theme.text_x, theme.frame_right
    weeks, total, active_days, busiest = weekly_buckets(calendar)
    peak_w = max((n for _, n in weeks), default=1) or 1

    cx, cy = 320.0, 304.0
    r_inner, r_outer = 22.0, 162.0
    n_rings = 12
    n_samples = 48

    # Split 52 weeks into 12 growth bands (inner = oldest, outer = most recent)
    band_size = max(1, math.ceil(len(weeks) / n_rings))
    rings: list[str] = []
    for ring_idx in range(n_rings):
        chunk = weeks[ring_idx * band_size : (ring_idx + 1) * band_size]
        ring_avg = (sum(v for _, v in chunk) / len(chunk)) if chunk else 0.0
        growth_ratio = math.sqrt(ring_avg / peak_w) if ring_avg > 0 else 0.0
        base_r = r_inner + ((ring_idx + 1) / n_rings) * (r_outer - r_inner)
        wobble_amp = 2.0 + 4.5 * growth_ratio

        pts: list[str] = []
        for s in range(n_samples):
            theta = (2 * math.pi * s) / n_samples
            # Organic dendrochronology undulation deterministic per ring & angle
            undul = (
                0.55 * math.sin(3 * theta + ring_idx * 0.9)
                + 0.30 * math.cos(5 * theta - ring_idx * 0.6)
                + 0.15 * math.sin(7 * theta + ring_idx * 1.3)
            )
            rr = base_r + wobble_amp * undul
            px = cx + rr * math.cos(theta)
            py = cy + rr * math.sin(theta)
            pts.append(f"{px:.1f},{py:.1f}")

        if ring_idx >= 9:
            col = theme.green
        elif ring_idx >= 5:
            col = theme.cyan
        else:
            col = theme.amber
        stroke_op = 0.35 + 0.55 * (0.4 + 0.6 * growth_ratio)
        rings.append(
            f'<polygon points="{" ".join(pts)}" fill="{col}" fill-opacity="{0.03 + 0.04 * growth_ratio:.3f}" '
            f'stroke="{col}" stroke-width="{1.0 + 0.8 * growth_ratio:.2f}" stroke-opacity="{stroke_op:.2f}"/>'
        )

    # 52 weekly vascular rays and outer canopy leaf/seed nodes
    rays: list[str] = []
    nodes: list[str] = []
    n_weeks = max(len(weeks), 1)
    for i, (_, val) in enumerate(weeks):
        angle = -math.pi / 2 + (2 * math.pi * i) / n_weeks
        norm = math.sqrt(val / peak_w) if val > 0 else 0.0
        x_in = cx + r_inner * math.cos(angle)
        y_in = cy + r_inner * math.sin(angle)
        x_out = cx + r_outer * math.cos(angle)
        y_out = cy + r_outer * math.sin(angle)
        rays.append(
            f'<line x1="{x_in:.1f}" y1="{y_in:.1f}" x2="{x_out:.1f}" y2="{y_out:.1f}" '
            f'stroke="{theme.border}" stroke-width=".6" stroke-opacity="{0.35 + 0.4 * norm:.2f}"/>'
        )
        if val > 0:
            r_node = r_outer + 7.0 + 14.0 * norm
            nx = cx + r_node * math.cos(angle)
            ny = cy + r_node * math.sin(angle)
            node_col = theme.amber if norm >= 0.72 else theme.green
            node_r = 2.0 + 2.8 * norm
            nodes.append(
                f'<line x1="{x_out:.1f}" y1="{y_out:.1f}" x2="{nx:.1f}" y2="{ny:.1f}" '
                f'stroke="{node_col}" stroke-width=".9" stroke-opacity=".55"/>'
                f'<circle cx="{nx:.1f}" cy="{ny:.1f}" r="{node_r:.1f}" fill="{node_col}" fill-opacity=".9"/>'
            )

    # Cardinal quarter labels
    q_labels: list[str] = []
    for q_idx, deg in enumerate((-90, 0, 90, 180)):
        rad = math.radians(deg)
        lx = cx + (r_outer + 28.0) * math.cos(rad)
        ly = cy + (r_outer + 28.0) * math.sin(rad) + 3.0
        q_labels.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" class="dim" style="font-size:9px">Q{q_idx + 1}</text>'
        )

    rx_card = 626
    rw = (fr - 36) - rx_card
    busiest_val, busiest_sub = busiest_summary(busiest)
    cards = [
        ("ANNUAL GROWTH", f"{total:,}", "last 365 days", theme.green),
        ("ACTIVE DAYS", f"{active_days}", f"of {len(calendar)} days", theme.cyan),
        ("PEAK BLOOM", busiest_val, busiest_sub, theme.amber),
    ]
    telemetry = telemetry_cards(cards, rx_card, rw, theme)

    sec_title = theme.section_label("centerpiece", "solar-rings")
    body = (
        heading(44, sec_title, "// 03", theme)
        + f'''
<g class="ln" style="animation-delay:.15s"><text x="{x0}" y="96" class="dim"><tspan class="cy">›</tspan> dendrochronology · 12 growth rings · 52w canopy</text></g>
<g>{"".join(rays)}{"".join(rings)}{"".join(nodes)}{"".join(q_labels)}</g>
<circle cx="{cx:.1f}" cy="{cy:.1f}" r="5" fill="{theme.amber}"/>
{telemetry}'''
    )
    return slice_svg(
        520,
        body,
        title="Solar growth rings",
        desc=f"Concentric tree growth rings of the last 365 days: {total:,} contributions across {active_days} active days.",
        text=f"{sec_title}03dendrochronology12 growth rings52w canopyQ1Q2Q3Q4ANNUAL GROWTHACTIVE DAYSPEAK BLOOM{total}{active_days}{busiest_val}",
        theme=theme,
    )

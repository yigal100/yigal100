"""Gently tilted concentric tree growth rings slice builder for solarpunk."""

from __future__ import annotations

import math

from profile_console.sections._common import busiest_summary, project_tilted, telemetry_cards, weekly_buckets
from profile_console.svg import Theme, heading, slice_svg


def build_rings(calendar: list[list], updated: str, theme: Theme) -> str:
    """Render 12 gently tilted concentric tree growth rings with subtle depth and canopy nodes."""
    x0, fr = theme.text_x, theme.frame_right
    weeks, total, active_days, busiest = weekly_buckets(calendar)
    peak_w = max((n for _, n in weeks), default=1) or 1

    cx, cy = 320.0, 308.0
    r_inner, r_outer = 22.0, 168.0
    tilt, roll_deg = 0.74, -6.0
    n_rings = 12
    n_samples = 48

    # Split 52 weeks into 12 organic growth rings with subtle terraced elevation
    band_size = max(1, math.ceil(len(weeks) / n_rings))
    rings: list[str] = []
    for ring_idx in range(n_rings - 1, -1, -1):
        chunk = weeks[ring_idx * band_size : (ring_idx + 1) * band_size]
        ring_avg = (sum(v for _, v in chunk) / len(chunk)) if chunk else 0.0
        growth_ratio = math.sqrt(ring_avg / peak_w) if ring_avg > 0 else 0.0
        base_r = r_inner + ((ring_idx + 1) / n_rings) * (r_outer - r_inner)
        wobble_amp = 2.0 + 4.5 * growth_ratio
        # Subtle terraced lift toward the inner heartwood for gentle 3D depth
        ring_cy = cy - (n_rings - 1 - ring_idx) * 1.1

        pts: list[str] = []
        for s in range(n_samples):
            theta = (2 * math.pi * s) / n_samples
            undul = (
                0.55 * math.sin(3 * theta + ring_idx * 0.9)
                + 0.30 * math.cos(5 * theta - ring_idx * 0.6)
                + 0.15 * math.sin(7 * theta + ring_idx * 1.3)
            )
            rr = base_r + wobble_amp * undul
            px, py, _ = project_tilted(cx, ring_cy, rr, theta, tilt, roll_deg)
            pts.append(f"{px:.1f},{py:.1f}")

        if ring_idx >= 9:
            col = theme.green
        elif ring_idx >= 5:
            col = theme.cyan
        else:
            col = theme.amber
        stroke_op = 0.36 + 0.54 * (0.4 + 0.6 * growth_ratio)
        rings.append(
            f'<polygon class="sol-ring" points="{" ".join(pts)}" fill="{col}" fill-opacity="{0.03 + 0.04 * growth_ratio:.3f}" '
            f'stroke="{col}" stroke-width="{1.0 + 0.8 * growth_ratio:.2f}" stroke-opacity="{stroke_op:.2f}" '
            f'style="transform-origin:{cx:.1f}px {ring_cy:.1f}px;animation-delay:{ring_idx * 0.18:.2f}s"/>'
        )

    # 52 weekly vascular rays and outer canopy leaf/seed nodes on the tilted plane
    rays: list[str] = []
    nodes: list[tuple[float, str]] = []
    n_weeks = max(len(weeks), 1)
    core_cy = cy - (n_rings - 1) * 1.1
    for i, (_, val) in enumerate(weeks):
        angle = -math.pi / 2 + (2 * math.pi * i) / n_weeks
        norm = math.sqrt(val / peak_w) if val > 0 else 0.0
        x_in, y_in, _ = project_tilted(cx, core_cy, r_inner, angle, tilt, roll_deg)
        x_out, y_out, depth = project_tilted(cx, cy, r_outer, angle, tilt, roll_deg)
        rays.append(
            f'<line class="sol-ray" x1="{x_in:.1f}" y1="{y_in:.1f}" x2="{x_out:.1f}" y2="{y_out:.1f}" '
            f'stroke="{theme.border}" stroke-width=".7" stroke-dasharray="6 14" stroke-opacity="{0.40 + 0.45 * norm:.2f}" '
            f'style="animation-delay:{(i % 6) * -0.3:.2f}s"/>'
        )
        if val > 0:
            r_node = r_outer + 7.0 + 14.0 * norm
            nx, ny, _ = project_tilted(cx, cy, r_node, angle, tilt, roll_deg)
            ny_lifted = ny - 3.5 * norm
            node_col = theme.amber if norm >= 0.72 else theme.green
            node_r = 2.0 + 2.8 * norm
            op = 0.94 if depth >= 0 else 0.68
            ping_el = (
                f'<circle class="sol-ping" cx="{nx:.1f}" cy="{ny_lifted:.1f}" r="{node_r + 1.5:.1f}" '
                f'fill="none" stroke="{node_col}" '
                f'style="transform-origin:{nx:.1f}px {ny_lifted:.1f}px;animation-delay:{i * 0.08:.2f}s"/>'
                if norm >= 0.72
                else ""
            )
            nodes.append(
                (
                    depth,
                    f'<line x1="{x_out:.1f}" y1="{y_out:.1f}" x2="{nx:.1f}" y2="{ny_lifted:.1f}" '
                    f'stroke="{node_col}" stroke-width=".9" stroke-opacity=".55"/>'
                    f'<circle cx="{nx:.1f}" cy="{ny_lifted:.1f}" r="{node_r:.1f}" fill="{node_col}" opacity="{op:.2f}"/>'
                    f"{ping_el}",
                )
            )

    nodes.sort(key=lambda item: item[0])
    nodes_svg = "".join(el for _, el in nodes)

    # Cardinal quarter labels projected around the tilted canopy
    q_labels: list[str] = []
    for q_idx, deg in enumerate((-90, 0, 90, 180)):
        rad = math.radians(deg)
        lx, ly, _ = project_tilted(cx, cy, r_outer + 28.0, rad, tilt, roll_deg)
        q_labels.append(
            f'<text x="{lx:.1f}" y="{ly + 3.0:.1f}" text-anchor="middle" class="dim" style="font-size:9px">Q{q_idx + 1}</text>'
        )

    css = (
        "@keyframes sol-ring{0%,100%{transform:scale(1);stroke-opacity:.42}50%{transform:scale(1.028);stroke-opacity:1}}\n"
        "@keyframes sol-ray{from{stroke-dashoffset:0}to{stroke-dashoffset:-20}}\n"
        "@keyframes sol-ping{0%{transform:scale(1);opacity:.9}100%{transform:scale(2.6);opacity:0}}\n"
        "@keyframes sol-core{0%,100%{transform:scale(1);opacity:.85}50%{transform:scale(1.38);opacity:1}}\n"
        ".sol-ring{animation:sol-ring 3.6s ease-in-out infinite}\n"
        ".sol-ray{animation:sol-ray 1.8s linear infinite}\n"
        ".sol-ping{animation:sol-ping 2.4s ease-out infinite}\n"
        f".sol-core{{transform-origin:{cx:.1f}px {core_cy:.1f}px;animation:sol-core 2.8s ease-in-out infinite}}"
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
<g>{"".join(rays)}{"".join(rings)}{nodes_svg}{"".join(q_labels)}</g>
<circle class="sol-core" cx="{cx:.1f}" cy="{core_cy:.1f}" r="5" fill="{theme.amber}"/>
{telemetry}'''
    )
    return slice_svg(
        520,
        body,
        title="Solar growth rings",
        desc=f"Concentric tree growth rings of the last 365 days: {total:,} contributions across {active_days} active days.",
        text=f"{sec_title}03dendrochronology12 growth rings52w canopyQ1Q2Q3Q4ANNUAL GROWTHACTIVE DAYSPEAK BLOOM{total}{active_days}{busiest_val}",
        theme=theme,
        css=css,
    )

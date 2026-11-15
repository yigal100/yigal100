"""3D isometric citadel (arcane-architect) and hardware spec spectrum (studio) slice builders."""

from __future__ import annotations

import datetime
import math

from profile_console.sections._common import busiest_summary, smooth_path, telemetry_cards, weekly_buckets
from profile_console.svg import Theme, esc, heading, slice_svg


def _p(x: float, y: float) -> str:
    return f"{x:.1f},{y:.1f}"


def build_terrain(calendar: list[list], updated: str, theme: Theme) -> str:
    """Render the arcane-architect 3D isometric stepped citadel heightfield slice."""
    x0, fr = theme.text_x, theme.frame_right
    days = [(datetime.date.fromisoformat(d), n) for d, n in calendar]
    total = sum(n for _, n in days)
    active_days = sum(1 for _, n in days if n > 0)
    busiest = max(days, key=lambda t: t[1]) if days else None

    # Aggregate 365 days into 26 biweekly columns x 7 days of week
    n_cols = 26
    grid_vals: list[list[int]] = [[0] * 7 for _ in range(n_cols)]
    start = days[0][0] if days else datetime.date.today()
    for d, n in days:
        idx = (d - start).days
        col = min(n_cols - 1, idx // 14)
        dow = (d.weekday() + 1) % 7
        grid_vals[col][dow] += n

    peak_cell = max((v for col in grid_vals for v in col), default=1) or 1
    tw, th = 26.0, 13.0
    ox, oy = 154.0, 228.0
    h_max = 90.0

    face_l = "#cbd5e1" if theme.is_light else "#181e2c"
    face_r = "#94a3b8" if theme.is_light else "#10141f"
    roof_mid = "#e2e8f0" if theme.is_light else "#1e2638"

    cells = [(c, r, grid_vals[c][r]) for c in range(n_cols) for r in range(7)]
    cells.sort(key=lambda item: (item[0] + item[1], item[0]))

    shapes: list[str] = []
    beacons: list[str] = []
    for c, r, val in cells:
        cx = ox + (c - r) * tw / 2
        cy = oy + (c + r) * th / 2
        L = (cx - tw / 2, cy)
        R = (cx + tw / 2, cy)
        T = (cx, cy - th / 2)
        B = (cx, cy + th / 2)
        if val == 0:
            shapes.append(
                f'<path d="M{_p(*T)}L{_p(*R)}L{_p(*B)}L{_p(*L)}Z" '
                f'fill="none" stroke="{theme.border}" stroke-width=".6" stroke-opacity=".5"/>'
            )
            continue

        ratio = val / peak_cell
        h = 8.0 + h_max * math.sqrt(ratio)
        Tu, Ru, Bu, Lu = [(px, py - h) for px, py in (T, R, B, L)]
        edge_col = theme.amber if ratio >= 0.55 else (theme.cyan if ratio >= 0.25 else theme.border)
        roof_col = theme.amber if ratio >= 0.72 else roof_mid
        roof_op = ".28" if ratio >= 0.72 else ".92"

        shapes.append(
            f'<path d="M{_p(*L)}L{_p(*B)}L{_p(*Bu)}L{_p(*Lu)}Z" fill="{face_l}" stroke="{theme.border}" stroke-width=".45"/>'
            f'<path d="M{_p(*B)}L{_p(*R)}L{_p(*Ru)}L{_p(*Bu)}Z" fill="{face_r}" stroke="{theme.border}" stroke-width=".45"/>'
            f'<path d="M{_p(*Tu)}L{_p(*Ru)}L{_p(*Bu)}L{_p(*Lu)}Z" fill="{roof_col}" fill-opacity="{roof_op}" stroke="{edge_col}" stroke-width=".9"/>'
        )
        # Inner blueprint contour diamond on mid-to-high monoliths
        if ratio >= 0.35:
            itw, ith = tw * 0.45, th * 0.45
            cy_u = cy - h
            shapes.append(
                f'<path d="M{cx:.1f},{cy_u - ith / 2:.1f}L{cx + itw / 2:.1f},{cy_u:.1f}'
                f'L{cx:.1f},{cy_u + ith / 2:.1f}L{cx - itw / 2:.1f},{cy_u:.1f}Z" '
                f'fill="none" stroke="{edge_col}" stroke-width=".7" stroke-opacity=".7"/>'
            )
        # Arcane beacon spire + floating diamond sigil on peak summits
        if ratio >= 0.68:
            cy_u = cy - h
            beacons.append(
                f'<line x1="{cx:.1f}" y1="{cy_u:.1f}" x2="{cx:.1f}" y2="{cy_u - 16:.1f}" '
                f'stroke="{theme.amber}" stroke-width="1" stroke-opacity=".75"/>'
                f'<polygon points="{cx:.1f},{cy_u - 22:.1f} {cx + 4:.1f},{cy_u - 17:.1f} '
                f'{cx:.1f},{cy_u - 12:.1f} {cx - 4:.1f},{cy_u - 17:.1f}" fill="{theme.amber}"/>'
            )

    rx_card = 626
    rw = (fr - 36) - rx_card
    busiest_val, busiest_sub = busiest_summary(busiest)
    cards = [
        ("TOTAL QUESTS", f"{total:,}", "last 365 days", theme.amber),
        ("ACTIVE DAYS", f"{active_days}", f"of {len(calendar)} days", theme.green),
        ("PEAK SUMMIT", busiest_val, busiest_sub, theme.cyan),
    ]
    telemetry = telemetry_cards(cards, rx_card, rw, theme)

    sec_title = theme.section_label("centerpiece", "contribution-citadel")
    body = (
        heading(44, sec_title, "// 03", theme)
        + f'''
<g class="ln" style="animation-delay:.15s"><text x="{x0}" y="96" class="dim"><tspan class="am">◆</tspan> isometric citadel · 26×7 elevation matrix</text></g>
<g>{"".join(shapes)}{"".join(beacons)}</g>
{telemetry}'''
    )
    return slice_svg(
        520,
        body,
        title="Contribution citadel",
        desc=f"3D isometric heightfield of the last 365 days: {total:,} contributions across {active_days} active days.",
        text=f"{sec_title}03isometric citadel26x7 elevation matrixTOTAL QUESTSACTIVE DAYSPEAK SUMMIT{total}{active_days}{busiest_val}",
        theme=theme,
    )


def build_spectrum(calendar: list[list], updated: str, theme: Theme) -> str:
    """Render the studio Braun-inspired hardware spec weekly signal spectrum slice."""
    x0, fr = theme.text_x, theme.frame_right
    weeks, total, active_days, busiest = weekly_buckets(calendar)
    peak_w = max((n for _, n in weeks), default=1) or 1

    bx0, by_base, max_h = x0 + 4, 412.0, 224.0
    bw = (fr - 36) - bx0
    step = bw / max(len(weeks), 1)
    bar_w = max(4.0, step - 3.5)

    parts: list[str] = []
    # Horizontal reference scale lines
    for frac, label in ((0.25, "25%"), (0.50, "50%"), (0.75, "75%"), (1.00, "MAX")):
        gy = by_base - frac * max_h
        parts.append(
            f'<line x1="{bx0:.1f}" y1="{gy:.1f}" x2="{bx0 + bw:.1f}" y2="{gy:.1f}" '
            f'stroke="{theme.border}" stroke-dasharray="2 5" stroke-opacity=".75"/>'
            f'<text x="{bx0 + bw:.1f}" y="{gy - 4:.1f}" text-anchor="end" class="dim" style="font-size:9px">{label}</text>'
        )

    parts.append(
        f'<line x1="{bx0:.1f}" y1="{by_base:.1f}" x2="{bx0 + bw:.1f}" y2="{by_base:.1f}" '
        f'stroke="{theme.border}" stroke-width="1.5"/>'
    )

    # 4-week moving average points + signal bars
    ma_pts: list[tuple[float, float]] = []
    for i, (_, val) in enumerate(weeks):
        x = bx0 + i * step
        cx = x + bar_w / 2
        window = [w_val for _, w_val in weeks[max(0, i - 3) : i + 1]]
        avg = sum(window) / len(window)
        ma_pts.append((cx, by_base - max_h * (avg / peak_w)))

        if val == 0:
            parts.append(
                f'<rect x="{x:.1f}" y="{by_base - 3}" width="{bar_w:.1f}" height="3" fill="{theme.surface_alt}"/>'
            )
            continue
        h = max(8.0, max_h * (val / peak_w))
        ratio = val / peak_w
        col = theme.cyan if ratio >= 0.65 else (theme.magenta if ratio >= 0.3 else theme.fg)
        parts.append(
            f'<rect x="{x:.1f}" y="{by_base - h:.1f}" width="{bar_w:.1f}" height="{h:.1f}" rx="1" fill="{col}" fill-opacity=".88"/>'
        )
        # Peak-hold cap tick above top bars
        if ratio >= 0.65:
            parts.append(
                f'<rect x="{x:.1f}" y="{by_base - h - 5:.1f}" width="{bar_w:.1f}" height="2" fill="{theme.amber}"/>'
            )

    # Quarter vernier ticks along baseline
    for q_idx in range(4):
        qx = bx0 + (q_idx / 4) * bw
        parts.append(
            f'<line x1="{qx:.1f}" y1="{by_base:.1f}" x2="{qx:.1f}" y2="{by_base + 7:.1f}" stroke="{theme.dim}" stroke-width="1"/>'
            f'<text x="{qx + 4:.1f}" y="{by_base + 17:.1f}" class="dim" style="font-size:9px">Q{q_idx + 1}</text>'
        )

    # Moving average spline overlay
    if ma_pts:
        parts.append(
            f'<path d="{smooth_path(ma_pts)}" fill="none" stroke="{theme.amber}" stroke-width="1.8" stroke-opacity=".9"/>'
        )

    busiest_str = f"{busiest[0]:%b} {busiest[0].day} ({busiest[1]})" if busiest and busiest[1] else "—"
    meta = (
        f'<text x="{x0}" y="468" class="dim" style="font-size:12px">'
        f'<tspan class="wh" font-weight="700">{total:,}</tspan> CONTRIBUTIONS  ·  '
        f'<tspan class="wh" font-weight="700">{active_days}</tspan> ACTIVE DAYS  ·  '
        f'PEAK <tspan class="cy" font-weight="700">{esc(busiest_str)}</tspan>  ·  '
        f'<tspan class="am">━</tspan> 4W AVG</text>'
    )
    sec_title = theme.section_label("centerpiece", "signal-spectrum")
    body = (
        heading(44, sec_title, "// 03", theme)
        + f'''
<g class="ln" style="animation-delay:.15s"><text x="{x0}" y="96" class="dim"><tspan class="cy">■</tspan> 52-week contribution cadence · 4w moving average</text></g>
<g>{"".join(parts)}</g>
{meta}'''
    )
    return slice_svg(
        520,
        body,
        title="Contribution spectrum",
        desc=f"52-week contribution spectrum: {total:,} contributions across {active_days} active days.",
        text=f"{sec_title}0352-week contribution cadence4w moving averageQ1Q2Q3Q4MAXCONTRIBUTIONSACTIVE DAYSPEAKAVG{total}{active_days}{busiest_str}",
        theme=theme,
    )

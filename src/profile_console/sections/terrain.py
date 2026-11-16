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
                f'<path class="cit-rune" d="M{cx:.1f},{cy_u - ith / 2:.1f}L{cx + itw / 2:.1f},{cy_u:.1f}'
                f'L{cx:.1f},{cy_u + ith / 2:.1f}L{cx - itw / 2:.1f},{cy_u:.1f}Z" '
                f'fill="none" stroke="{edge_col}" stroke-width=".8" '
                f'style="animation-delay:{c * 0.11:.2f}s"/>'
            )
        # Arcane beacon spire + floating diamond sigil on peak summits
        if ratio >= 0.68:
            cy_u = cy - h
            b_delay = (c * 0.14 + r * 0.21) % 2.4
            beacons.append(
                f'<line class="cit-spire" x1="{cx:.1f}" y1="{cy_u:.1f}" x2="{cx:.1f}" y2="{cy_u - 16:.1f}" '
                f'stroke="{theme.amber}" stroke-width="1.1" style="animation-delay:{b_delay:.2f}s"/>'
                f'<g class="cit-sigil" style="animation-delay:{b_delay:.2f}s">'
                f'<polygon points="{cx:.1f},{cy_u - 22:.1f} {cx + 4:.1f},{cy_u - 17:.1f} '
                f'{cx:.1f},{cy_u - 12:.1f} {cx - 4:.1f},{cy_u - 17:.1f}" fill="{theme.amber}"/>'
                f"</g>"
                f'<circle class="cit-ping" cx="{cx:.1f}" cy="{cy_u - 17:.1f}" r="4.5" fill="none" '
                f'stroke="{theme.amber}" style="transform-origin:{cx:.1f}px {cy_u - 17:.1f}px;animation-delay:{b_delay:.2f}s"/>'
            )

    css = (
        "@keyframes cit-rune{0%,100%{stroke-opacity:.22}50%{stroke-opacity:1}}\n"
        "@keyframes cit-spire{0%,100%{stroke-opacity:.4}50%{stroke-opacity:1}}\n"
        "@keyframes cit-sigil{0%,100%{transform:translateY(0)}50%{transform:translateY(-7px)}}\n"
        "@keyframes cit-ping{0%{transform:scale(1);opacity:.85}100%{transform:scale(2.6);opacity:0}}\n"
        ".cit-rune{animation:cit-rune 3.2s ease-in-out infinite}\n"
        ".cit-spire{animation:cit-spire 2.6s ease-in-out infinite}\n"
        ".cit-sigil{animation:cit-sigil 2.6s ease-in-out infinite}\n"
        ".cit-ping{animation:cit-ping 2.6s ease-out infinite}"
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
        css=css,
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

    # 4-week moving average points + 3D extruded oblique hardware signal bars
    dx3, dy3 = 4.2, -4.2
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
        yt = by_base - h
        xr = x + bar_w
        # Front face, shaded right face, and lit top cap
        parts.append(
            f'<rect x="{x:.1f}" y="{yt:.1f}" width="{bar_w:.1f}" height="{h:.1f}" fill="{col}" fill-opacity=".86"/>'
            f'<polygon points="{xr:.1f},{yt:.1f} {xr + dx3:.1f},{yt + dy3:.1f} {xr + dx3:.1f},{by_base + dy3:.1f} {xr:.1f},{by_base:.1f}" '
            f'fill="{col}" fill-opacity=".46"/>'
            f'<polygon points="{x:.1f},{yt:.1f} {x + dx3:.1f},{yt + dy3:.1f} {xr + dx3:.1f},{yt + dy3:.1f} {xr:.1f},{yt:.1f}" '
            f'fill="{col}" fill-opacity=".64"/>'
        )
        # 3D floating peak-hold cap above top bars
        if ratio >= 0.65:
            yc = yt - 6.0
            parts.append(
                f'<polygon points="{x:.1f},{yc:.1f} {x + dx3:.1f},{yc + dy3:.1f} {xr + dx3:.1f},{yc + dy3:.1f} {xr:.1f},{yc:.1f}" '
                f'fill="{theme.amber}"/>'
            )

    # Quarter vernier ticks along baseline
    for q_idx in range(4):
        qx = bx0 + (q_idx / 4) * bw
        parts.append(
            f'<line x1="{qx:.1f}" y1="{by_base:.1f}" x2="{qx:.1f}" y2="{by_base + 7:.1f}" stroke="{theme.dim}" stroke-width="1"/>'
            f'<text x="{qx + 4:.1f}" y="{by_base + 17:.1f}" class="dim" style="font-size:9px">Q{q_idx + 1}</text>'
        )

    # Moving average spline overlay + traveling signal pulse
    if ma_pts:
        ma_d = smooth_path(ma_pts)
        parts.append(
            f'<path d="{ma_d}" fill="none" stroke="{theme.amber}" stroke-width="1.8" stroke-opacity=".55"/>'
            f'<path class="ma-pulse" d="{ma_d}" fill="none" stroke="{theme.amber}" stroke-width="2.4" '
            f'stroke-dasharray="28 140" stroke-linecap="round"/>'
        )

    # Subtle Braun hardware playhead / telemetry scanline sweeping across the spectrum
    scan_top = by_base - max_h - 8.0
    parts.append(
        f'<g class="spec-scan">'
        f'<line x1="{bx0:.1f}" y1="{scan_top:.1f}" x2="{bx0:.1f}" y2="{by_base:.1f}" '
        f'stroke="{theme.cyan}" stroke-width="1" stroke-opacity=".55" stroke-dasharray="3 3"/>'
        f'<polygon points="{bx0:.1f},{scan_top - 4:.1f} {bx0 + 3.5:.1f},{scan_top:.1f} {bx0 - 3.5:.1f},{scan_top:.1f}" '
        f'fill="{theme.cyan}" fill-opacity=".85"/>'
        f"</g>"
    )

    css = (
        "@keyframes ma-pulse{from{stroke-dashoffset:0}to{stroke-dashoffset:-168}}\n"
        f"@keyframes spec-scan{{0%{{transform:translateX(0);opacity:0}}8%,92%{{opacity:1}}100%{{transform:translateX({bw:.1f}px);opacity:0}}}}\n"
        ".ma-pulse{animation:ma-pulse 3.2s linear infinite}\n"
        ".spec-scan{animation:spec-scan 12s linear infinite}"
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
        css=css,
    )

"""Aurora harmonic fjord (nordic-fjord) and phosphor radar sweep (retro-amber) slice builders."""

from __future__ import annotations

import math

from profile_console.sections._common import busiest_summary, smooth_path, telemetry_cards, weekly_buckets
from profile_console.svg import Theme, heading, slice_svg


def build_aurora(calendar: list[list], updated: str, theme: Theme) -> str:
    """Render floating Aurora Borealis light curtains over a fjord silhouette with water reflection."""
    x0, fr = theme.text_x, theme.frame_right
    weeks, total, active_days, busiest = weekly_buckets(calendar)
    peak_w = max((n for _, n in weeks), default=1) or 1

    chart_x0, chart_w = x0 + 10.0, 540.0
    horizon_y = 392.0
    n_weeks = max(len(weeks) - 1, 1)

    # Vertical gradients: vivid green/cyan at lower curtain edge fading upward into violet/transparent
    defs = (
        f'<linearGradient id="aur-g0" x1="0" y1="1" x2="0" y2="0">'
        f'<stop offset="0%" stop-color="{theme.green}" stop-opacity="{0.42 if theme.is_light else 0.58}"/>'
        f'<stop offset="45%" stop-color="{theme.cyan}" stop-opacity="{0.22 if theme.is_light else 0.32}"/>'
        f'<stop offset="100%" stop-color="{theme.violet}" stop-opacity="0"/>'
        f"</linearGradient>"
        f'<linearGradient id="aur-g1" x1="0" y1="1" x2="0" y2="0">'
        f'<stop offset="0%" stop-color="{theme.cyan}" stop-opacity="{0.36 if theme.is_light else 0.52}"/>'
        f'<stop offset="55%" stop-color="{theme.violet}" stop-opacity="{0.18 if theme.is_light else 0.28}"/>'
        f'<stop offset="100%" stop-color="{theme.violet}" stop-opacity="0"/>'
        f"</linearGradient>"
        f'<linearGradient id="aur-refl" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{theme.green}" stop-opacity="{0.24 if theme.is_light else 0.34}"/>'
        f'<stop offset="65%" stop-color="{theme.cyan}" stop-opacity="0.08"/>'
        f'<stop offset="100%" stop-color="{theme.bg}" stop-opacity="0"/>'
        f"</linearGradient>"
        f'<clipPath id="aur-sky"><rect x="{chart_x0:.1f}" y="118" width="{chart_w:.1f}" height="{horizon_y - 118.0:.1f}"/></clipPath>'
    )

    # Subtle arctic night stars in the upper sky
    stars: list[str] = []
    for s_idx in range(28):
        sx = chart_x0 + ((s_idx * 73 + 19) % 530)
        sy = 128.0 + ((s_idx * 47 + 11) % 210)
        sr = 0.7 if s_idx % 3 else 1.1
        star_cls = f"s{s_idx % 3}"
        stars.append(
            f'<circle class="{star_cls}" cx="{sx:.1f}" cy="{sy:.1f}" r="{sr}" fill="{theme.dim}" opacity="{0.22 + (s_idx % 4) * 0.1:.2f}"/>'
        )

    # Two sweeping, floating aurora borealis curtains (back veil + front bright curtain)
    curtain_specs = [
        ("aur-g1", theme.cyan, 294.0, 128.0, 0.0, 0.55),
        ("aur-g0", theme.green, 326.0, 142.0, 1.35, 0.90),
    ]

    curtain_groups: list[str] = []
    peak_markers: list[str] = []
    reflection_pts: list[tuple[float, float]] = []

    for c_idx, (grad_id, edge_col, base_sky_y, max_curtain_h, phase, edge_op) in enumerate(curtain_specs):
        lower_pts: list[tuple[float, float]] = []
        upper_pts: list[tuple[float, float]] = []
        curtain_rays: list[str] = []

        for i, (_, val) in enumerate(weeks):
            px = chart_x0 + (i / n_weeks) * chart_w
            norm = math.sqrt(val / peak_w) if val > 0 else 0.0
            # Graceful S-curve drift across the arctic sky
            drift = 22.0 * math.sin(i * 0.16 + phase) + 9.0 * math.cos(i * 0.34 - phase)
            y_low = base_sky_y + drift
            curtain_h = 26.0 + max_curtain_h * (0.22 + 0.78 * norm) * (0.85 + 0.15 * math.sin(i * 0.4 + phase))
            y_high = max(124.0, y_low - curtain_h)

            lower_pts.append((px, y_low))
            upper_pts.append((px, y_high))

            # Shimmering vertical light striations inside the curtain
            if val > 0:
                ray_col = theme.green if (c_idx == 1 and i % 3 != 0) else theme.cyan
                ray_delay = i * 0.08 + c_idx * 0.6
                curtain_rays.append(
                    f'<line class="aur-ray" x1="{px:.1f}" y1="{y_low:.1f}" x2="{px:.1f}" y2="{y_high + 6.0:.1f}" '
                    f'stroke="{ray_col}" stroke-width="2.2" stroke-opacity="{0.22 + 0.36 * norm:.2f}" '
                    f'style="animation-delay:{ray_delay:.2f}s"/>'
                )

            if c_idx == 1:
                reflection_pts.append((px, horizon_y + 10.0 + 48.0 * norm))
                if val >= peak_w * 0.65:
                    peak_markers.append(
                        f'<circle cx="{px:.1f}" cy="{y_low:.1f}" r="3.0" fill="{theme.accent_color}"/>'
                        f'<circle class="aur-peak" cx="{px:.1f}" cy="{y_low:.1f}" r="6.5" fill="none" '
                        f'stroke="{theme.accent_color}" stroke-opacity=".45" '
                        f'style="transform-origin:{px:.1f}px {y_low:.1f}px;animation-delay:{(i % 4) * 0.6:.2f}s"/>'
                    )

        low_curve = smooth_path(lower_pts)
        high_rev = list(reversed(upper_pts))
        high_curve_cmds = smooth_path(high_rev).replace("M", "L", 1)
        curtain_d = f"{low_curve}{high_curve_cmds}Z"
        curtain_cls = "aur-back" if c_idx == 0 else "aur-front"
        curtain_groups.append(
            f'<g class="{curtain_cls}">'
            f'<path d="{curtain_d}" fill="url(#{grad_id})"/>'
            f'<path d="{low_curve}" fill="none" stroke="{edge_col}" stroke-width="2.1" stroke-opacity="{edge_op:.2f}"/>'
            f'{"".join(curtain_rays)}'
            f"</g>"
        )

    # Fjord mountain silhouette along the horizon
    ridge_pts = [
        (0.00, 0), (0.08, 22), (0.17, 11), (0.26, 32), (0.35, 16),
        (0.46, 9), (0.57, 27), (0.68, 13), (0.79, 35), (0.90, 17), (1.00, 0),
    ]
    mtn_d = "M" + "L".join(f"{chart_x0 + fx * chart_w:.1f},{horizon_y - dy:.1f}" for fx, dy in ridge_pts) + "Z"
    mtn_col = "#cbd5e1" if theme.is_light else "#070c14"
    fjord = (
        f'<path d="{mtn_d}" fill="{mtn_col}" stroke="{theme.border}" stroke-width="1"/>'
        f'<line x1="{chart_x0:.1f}" y1="{horizon_y:.1f}" x2="{chart_x0 + chart_w:.1f}" y2="{horizon_y:.1f}" '
        f'stroke="{theme.cyan}" stroke-width="1.1" stroke-opacity=".55"/>'
    )

    # Calm fjord water reflection below the horizon
    if reflection_pts:
        refl_curve = smooth_path(reflection_pts)
        refl_area = f"{refl_curve}L{chart_x0 + chart_w:.1f},{horizon_y + 2:.1f}L{chart_x0:.1f},{horizon_y + 2:.1f}Z"
        fjord += f'<path d="{refl_area}" fill="url(#aur-refl)"/>'
        for r_idx in range(4):
            ry = horizon_y + 10.0 + r_idx * 11.0
            refl_cls = "refl-a" if r_idx % 2 == 0 else "refl-b"
            fjord += (
                f'<line class="{refl_cls}" x1="{chart_x0 + 24 + r_idx * 18:.1f}" y1="{ry:.1f}" '
                f'x2="{chart_x0 + chart_w - 28 - r_idx * 14:.1f}" y2="{ry:.1f}" '
                f'stroke="{theme.green if r_idx % 2 == 0 else theme.cyan}" stroke-width="1.3" '
                f'stroke-dasharray="14 10 6 14" stroke-opacity="{0.42 - r_idx * 0.06:.2f}" '
                f'style="animation-delay:{r_idx * 0.45:.2f}s"/>'
            )

    css = (
        "@keyframes tw{0%,100%{opacity:.9}50%{opacity:.12}}\n"
        "@keyframes aur-back{0%,100%{transform:translate(-14px,3px) scaleY(.95)}50%{transform:translate(16px,-6px) scaleY(1.07)}}\n"
        "@keyframes aur-front{0%,100%{transform:translate(15px,-4px) scaleY(1.06)}50%{transform:translate(-15px,5px) scaleY(.94)}}\n"
        "@keyframes aur-ray{0%,100%{opacity:.15;transform:translateY(4px)}50%{opacity:1;transform:translateY(-6px)}}\n"
        "@keyframes aur-peak{0%{transform:scale(1);opacity:.9}100%{transform:scale(2.6);opacity:0}}\n"
        "@keyframes refl-a{from{stroke-dashoffset:0}to{stroke-dashoffset:-44}}\n"
        "@keyframes refl-b{from{stroke-dashoffset:0}to{stroke-dashoffset:44}}\n"
        ".s0{animation:tw 2.6s infinite}.s1{animation:tw 3.7s infinite .9s}.s2{animation:tw 4.8s infinite 1.8s}\n"
        ".aur-back{transform-origin:320px 330px;animation:aur-back 6.5s ease-in-out infinite}\n"
        ".aur-front{transform-origin:320px 330px;animation:aur-front 5.2s ease-in-out infinite}\n"
        ".aur-ray{animation:aur-ray 2.4s ease-in-out infinite}\n"
        ".aur-peak{animation:aur-peak 2.2s ease-out infinite}\n"
        ".refl-a{animation:refl-a 2.8s linear infinite}\n"
        ".refl-b{animation:refl-b 3.4s linear infinite}"
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
<g class="ln" style="animation-delay:.15s"><text x="{x0}" y="96" class="dim"><tspan class="cy">›</tspan> aurora borealis · fjord reflection · 52w</text></g>
<g>{"".join(stars)}<g clip-path="url(#aur-sky)">{"".join(curtain_groups)}</g>{fjord}{"".join(peak_markers)}</g>
{telemetry}'''
    )
    return slice_svg(
        520,
        body,
        title="Fjord aurora",
        desc=f"Aurora borealis light curtains over a fjord of the last 365 days: {total:,} contributions across {active_days} active days.",
        text=f"{sec_title}03aurora borealisfjord reflection52wTOTAL OUTPUTACTIVE DAYSPEAK CREST{total}{active_days}{busiest_val}",
        theme=theme,
        defs=defs,
        css=css,
    )


def build_radar(calendar: list[list], updated: str, theme: Theme) -> str:
    """Render a 52-week phosphor CRT polar radar sweep chart of annual activity."""
    x0, fr = theme.text_x, theme.frame_right
    weeks, total, active_days, busiest = weekly_buckets(calendar)
    peak_w = max((n for _, n in weeks), default=1) or 1

    cx, cy = 320.0, 304.0
    r_inner, r_outer = 34.0, 162.0
    r_daily = r_outer + 9.5
    accent = theme.accent_color

    # Phosphor CRT vignette gradient inside the circular scope
    defs = (
        f'<radialGradient id="crt-vig" cx="50%" cy="50%" r="50%">'
        f'<stop offset="0%" stop-color="{accent}" stop-opacity="{0.08 if theme.is_light else 0.14}"/>'
        f'<stop offset="70%" stop-color="{accent}" stop-opacity="0.03"/>'
        f'<stop offset="100%" stop-color="{theme.bg}" stop-opacity="0"/>'
        f"</radialGradient>"
    )

    # Chamfered hardware CRT bezel frame with corner mounting screws
    bx0, by0, bx1, by1, ch = cx - 184.0, cy - 182.0, cx + 184.0, cy + 182.0, 16.0
    bezel_d = (
        f"M{bx0 + ch:.1f},{by0:.1f}L{bx1 - ch:.1f},{by0:.1f}L{bx1:.1f},{by0 + ch:.1f}"
        f"L{bx1:.1f},{by1 - ch:.1f}L{bx1 - ch:.1f},{by1:.1f}L{bx0 + ch:.1f},{by1:.1f}"
        f"L{bx0:.1f},{by1 - ch:.1f}L{bx0:.1f},{by0 + ch:.1f}Z"
    )
    bezel_els = [
        f'<path d="{bezel_d}" fill="{theme.surface}" fill-opacity=".42" stroke="{theme.border}" stroke-width="1.2"/>',
        f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r_outer:.1f}" fill="url(#crt-vig)"/>',
    ]
    for sx_b, sy_b in ((bx0 + 14, by0 + 14), (bx1 - 14, by0 + 14), (bx0 + 14, by1 - 14), (bx1 - 14, by1 - 14)):
        bezel_els.append(
            f'<circle cx="{sx_b:.1f}" cy="{sy_b:.1f}" r="3.2" fill="none" stroke="{theme.border}" stroke-width=".9"/>'
            f'<line x1="{sx_b - 2:.1f}" y1="{sy_b:.1f}" x2="{sx_b + 2:.1f}" y2="{sy_b:.1f}" stroke="{theme.dim}" stroke-width=".8"/>'
        )

    grid: list[str] = []
    for frac, label in ((0.25, "25%"), (0.5, "50%"), (0.75, "75%"), (1.0, "")):
        rr = r_inner + frac * (r_outer - r_inner)
        grid.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rr:.1f}" fill="none" '
            f'stroke="{theme.border}" stroke-dasharray="{"none" if frac == 1.0 else "3 4"}" stroke-opacity=".8"/>'
        )
        if label:
            lx = cx + rr * math.cos(-math.pi / 4) + 3.0
            ly = cy + rr * math.sin(-math.pi / 4) - 2.0
            grid.append(f'<text x="{lx:.1f}" y="{ly:.1f}" class="dim" style="font-size:8px">{label}</text>')

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

    # 365-day outer perimeter cadence ring
    n_days = max(len(calendar), 1)
    daily_dots: list[str] = []
    for d_idx, (_, d_val) in enumerate(calendar):
        ang = -math.pi / 2 + (2 * math.pi * d_idx) / n_days
        dx = cx + r_daily * math.cos(ang)
        dy = cy + r_daily * math.sin(ang)
        if d_val == 0:
            daily_dots.append(f'<circle cx="{dx:.1f}" cy="{dy:.1f}" r=".85" fill="{theme.muted}" opacity=".32"/>')
        else:
            d_col = accent if d_val >= 8 else theme.cyan
            daily_dots.append(f'<circle cx="{dx:.1f}" cy="{dy:.1f}" r="1.2" fill="{d_col}" opacity=".85"/>')

    n_weeks = max(len(weeks), 1)
    poly_pts: list[tuple[float, float]] = []
    spokes: list[str] = []
    blips: list[str] = []
    peak_candidates: list[tuple[int, int, float, float, float]] = []
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
            peak_candidates.append((val, i + 1, px, py, angle))
            # Target-lock crosshair reticle around peak echo blips
            blips.append(
                f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.2" fill="{accent}"/>'
                f'<circle cx="{px:.1f}" cy="{py:.1f}" r="7.5" fill="none" stroke="{accent}" stroke-opacity=".55" stroke-dasharray="3 2"/>'
                f'<path d="M{px - 10:.1f},{py:.1f}h4M{px + 6:.1f},{py:.1f}h4M{px:.1f},{py - 10:.1f}v4M{px:.1f},{py + 6:.1f}v4" '
                f'stroke="{accent}" stroke-width="1" stroke-opacity=".7"/>'
            )

    # Target callout leader tags for top 2 peak sectors
    callouts: list[str] = []
    peak_candidates.sort(key=lambda item: item[0], reverse=True)
    for rank, (_, wk_num, px, py, angle) in enumerate(peak_candidates[:2]):
        dx_dir = 1.0 if math.cos(angle) >= 0 else -1.0
        dy_dir = 1.0 if math.sin(angle) >= 0 else -1.0
        ex = px + dx_dir * 16.0
        ey = py + dy_dir * 14.0
        tx = ex + dx_dir * 18.0
        anchor = "start" if dx_dir > 0 else "end"
        tag = f"PK-0{rank + 1}:W{wk_num:02d}"
        callouts.append(
            f'<polyline points="{px:.1f},{py:.1f} {ex:.1f},{ey:.1f} {tx:.1f},{ey:.1f}" '
            f'fill="none" stroke="{accent}" stroke-width=".9" stroke-opacity=".78"/>'
            f'<text x="{tx + dx_dir * 3:.1f}" y="{ey + 3:.1f}" text-anchor="{anchor}" '
            f'fill="{accent}" style="font-size:8.5px;font-weight:700">{tag}</text>'
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
    for deg_start, deg_end, op in ((0, 16, 0.14), (16, 32, 0.08), (32, 50, 0.04)):
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
<g>{"".join(bezel_els)}{"".join(scanlines)}{"".join(grid)}{"".join(daily_dots)}{poly_el}{"".join(spokes)}{sweep}{"".join(blips)}{"".join(callouts)}</g>
<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4" fill="{accent}"/>
{telemetry}'''
    )
    return slice_svg(
        520,
        body,
        title="Contribution radar",
        desc=f"Polar radar sweep of the last 365 days: {total:,} contributions across {active_days} active days.",
        text=f"{sec_title}03polar sweep52 weekly sectorsradarscan 52w25%50%75%PK-01PK-02:W0123456789TOTAL SIGNALSACTIVE DAYSPEAK ECHO{total}{active_days}{busiest_val}",
        theme=theme,
        css=css,
        defs=defs,
    )

"""Mountain ridgeline (arcane-architect) and Swiss signal spectrum (studio) slice builders."""

from __future__ import annotations

import datetime
import math

from profile_console.svg import Theme, esc, heading, slice_svg


def _weekly_buckets(calendar: list[list]) -> tuple[list[tuple[datetime.date, int]], int, int, tuple[datetime.date, int] | None]:
    """Aggregate daily calendar entries into 52-53 weekly totals plus summary stats."""
    days = [(datetime.date.fromisoformat(d), n) for d, n in calendar]
    total = sum(n for _, n in days)
    active = sum(1 for _, n in days if n > 0)
    busiest = max(days, key=lambda t: t[1]) if days else None
    weeks: list[tuple[datetime.date, int]] = []
    for i in range(0, len(days), 7):
        chunk = days[i : i + 7]
        if chunk:
            weeks.append((chunk[0][0], sum(n for _, n in chunk)))
    return weeks, total, active, busiest


def build_terrain(calendar: list[list], updated: str, theme: Theme) -> str:
    """Render the arcane-architect layered mountain ridgeline slice."""
    x0, fr = theme.text_x, theme.frame_right
    weeks, total, active_days, busiest = _weekly_buckets(calendar)
    peak_w = max((n for _, n in weeks), default=1) or 1

    # Split 52-53 weeks into 4 layered ridges (back to front)
    n_layers = 4
    layer_size = max(1, math.ceil(len(weeks) / n_layers))
    chart_x0, chart_w = x0 + 10, 540.0
    base_y0, layer_dy, max_amp = 250.0, 56.0, 74.0

    ridges: list[str] = []
    beacons: list[str] = []
    for layer in range(n_layers):
        chunk = weeks[layer * layer_size : (layer + 1) * layer_size]
        if not chunk:
            continue
        by = base_y0 + layer * layer_dy
        pts: list[tuple[float, float, int]] = []
        for idx, (_, val) in enumerate(chunk):
            px = chart_x0 + (idx / max(len(chunk) - 1, 1)) * chart_w
            amp = max_amp * math.sqrt(val / peak_w) if val > 0 else 0.0
            pts.append((px, by - amp, val))

        top_line = "L".join(f"{px:.1f},{py:.1f}" for px, py, _ in pts)
        poly = f"M{chart_x0:.1f},{by:.1f}L{top_line}L{chart_x0 + chart_w:.1f},{by:.1f}Z"
        stroke_col = theme.amber if layer >= 2 else theme.cyan
        ridges.append(
            f'<path d="{poly}" fill="{theme.bg}" fill-opacity=".92"/>'
            f'<path d="M{top_line}" fill="none" stroke="{stroke_col}" stroke-width="1.6" stroke-opacity="{0.55 + layer * 0.12:.2f}"/>'
        )
        for px, py, val in pts:
            if val >= peak_w * 0.55:
                beacons.append(
                    f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.2" fill="{theme.amber}"/>'
                    f'<circle cx="{px:.1f}" cy="{py:.1f}" r="6.5" fill="none" stroke="{theme.amber}" stroke-opacity=".45"/>'
                )

    rx_card = 626
    rw = (fr - 36) - rx_card
    busiest_val = f"{busiest[0]:%b} {busiest[0].day}" if busiest and busiest[1] else "—"
    busiest_sub = f"{busiest[1]} contributions" if busiest and busiest[1] else "no activity"
    cards = [
        ("TOTAL QUESTS", f"{total:,}", "last 365 days", theme.amber),
        ("ACTIVE DAYS", f"{active_days}", f"of {len(calendar)} days", theme.green),
        ("PEAK SUMMIT", busiest_val, busiest_sub, theme.cyan),
    ]
    telemetry = "".join(
        f'<g class="ln" style="animation-delay:{0.2 + i * 0.1:.2f}s">'
        f'<rect x="{rx_card}" y="{150 + i * 96}" width="{rw}" height="80" rx="{theme.card_rx}" fill="{theme.surface}" stroke="{theme.border}"/>'
        f'<rect x="{rx_card}" y="{150 + i * 96 + 12}" width="4" height="56" rx="2" fill="{acc}"/>'
        f'<text x="{rx_card + 16}" y="{150 + i * 96 + 24}" letter-spacing="1.2" class="dim" style="font-size:10px">{esc(lab)}</text>'
        f'<text x="{rx_card + 16}" y="{150 + i * 96 + 50}" font-weight="700" fill="{acc}" style="font-size:22px">{esc(val)}</text>'
        f'<text x="{rx_card + 16}" y="{150 + i * 96 + 68}" class="dim" style="font-size:11px">{esc(sub)}</text>'
        f"</g>"
        for i, (lab, val, sub, acc) in enumerate(cards)
    )

    body = (
        heading(44, "contribution-terrain", "// 03", theme)
        + f'''
<g class="ln" style="animation-delay:.15s"><text x="{x0}" y="96" class="dim"><tspan class="am">◆</tspan> elevation map · 52 weekly ridges</text></g>
<g>{"".join(ridges)}{"".join(beacons)}</g>
{telemetry}'''
    )
    return slice_svg(
        520,
        body,
        title="Contribution terrain",
        desc=f"Layered mountain ridgelines of the last 365 days: {total:,} contributions across {active_days} active days.",
        text=f"contribution-terrain03elevation map52 weekly ridgesTOTAL QUESTSACTIVE DAYSPEAK SUMMIT{total}{active_days}{busiest_val}",
        theme=theme,
    )


def build_spectrum(calendar: list[list], updated: str, theme: Theme) -> str:
    """Render the studio Swiss editorial weekly signal spectrum slice."""
    x0, fr = theme.text_x, theme.frame_right
    weeks, total, active_days, busiest = _weekly_buckets(calendar)
    peak_w = max((n for _, n in weeks), default=1) or 1

    bx0, by_base, max_h = x0 + 4, 420.0, 220.0
    bw = (fr - 36) - bx0
    step = bw / max(len(weeks), 1)
    bar_w = max(4.0, step - 3.5)

    bars: list[str] = [
        f'<line x1="{bx0}" y1="{by_base}" x2="{bx0 + bw:.1f}" y2="{by_base}" stroke="{theme.border}" stroke-width="1.5"/>'
    ]
    for i, (_, val) in enumerate(weeks):
        x = bx0 + i * step
        if val == 0:
            bars.append(f'<rect x="{x:.1f}" y="{by_base - 3}" width="{bar_w:.1f}" height="3" fill="{theme.surface_alt}"/>')
            continue
        h = max(8.0, max_h * (val / peak_w))
        ratio = val / peak_w
        col = theme.cyan if ratio >= 0.65 else (theme.magenta if ratio >= 0.3 else theme.fg)
        bars.append(f'<rect x="{x:.1f}" y="{by_base - h:.1f}" width="{bar_w:.1f}" height="{h:.1f}" rx="1" fill="{col}"/>')

    busiest_str = f"{busiest[0]:%b} {busiest[0].day} ({busiest[1]})" if busiest and busiest[1] else "—"
    meta = (
        f'<text x="{x0}" y="468" class="dim" style="font-size:12px">'
        f'<tspan class="wh" font-weight="700">{total:,}</tspan> CONTRIBUTIONS  ·  '
        f'<tspan class="wh" font-weight="700">{active_days}</tspan> ACTIVE DAYS  ·  '
        f'PEAK <tspan class="cy" font-weight="700">{esc(busiest_str)}</tspan></text>'
    )
    body = (
        heading(44, "signal-spectrum", "// 03", theme)
        + f'''
<g class="ln" style="animation-delay:.15s"><text x="{x0}" y="96" class="dim"><tspan class="cy">■</tspan> 52-week contribution cadence</text></g>
<g>{"".join(bars)}</g>
{meta}'''
    )
    return slice_svg(
        520,
        body,
        title="Contribution spectrum",
        desc=f"52-week contribution spectrum: {total:,} contributions across {active_days} active days.",
        text=f"signal-spectrum0352-week contribution cadenceCONTRIBUTIONSACTIVE DAYSPEAK{total}{active_days}{busiest_str}",
        theme=theme,
    )

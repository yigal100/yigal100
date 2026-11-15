"""Shared helpers for centerpiece SVG section builders."""

from __future__ import annotations

import datetime
import math

from profile_console.svg import Theme, esc


def weekly_buckets(
    calendar: list[list],
) -> tuple[list[tuple[datetime.date, int]], int, int, tuple[datetime.date, int] | None]:
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


def busiest_summary(busiest: tuple[datetime.date, int] | None) -> tuple[str, str]:
    """Format the peak day date and contribution count for telemetry cards."""
    if busiest and busiest[1]:
        return f"{busiest[0]:%b} {busiest[0].day}", f"{busiest[1]} contributions"
    return "—", "no activity"


def telemetry_cards(
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


def smooth_path(pts: list[tuple[float, float]]) -> str:
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


def project_tilted(
    cx: float,
    cy: float,
    r: float,
    theta: float,
    tilt: float = 0.48,
    roll_deg: float = -8.0,
) -> tuple[float, float, float]:
    """Project polar (r, theta) onto a tilted 3D-perspective plane, returning (x, y, depth)."""
    lx = r * math.cos(theta)
    ly = r * tilt * math.sin(theta)
    roll = math.radians(roll_deg)
    cos_r, sin_r = math.cos(roll), math.sin(roll)
    px = cx + lx * cos_r - ly * sin_r
    py = cy + lx * sin_r + ly * cos_r
    return px, py, math.sin(theta)

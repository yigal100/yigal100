"""3D-perspective orbital star chart slice builder for the astrometrics theme."""

from __future__ import annotations

import datetime
import hashlib
import math
from collections.abc import Iterator

from profile_console.svg import Theme, esc, heading, slice_svg

ORBIT_RADII = (108.0, 154.0, 200.0, 246.0)
ORBIT_TILT = 0.43  # vertical foreshortening for 3D perspective
ORBIT_ROLL = math.radians(-11.0)  # slight axial tilt


def _rng(seed: str) -> Iterator[float]:
    """Deterministic PRNG so the same calendar data always renders identical starfields."""
    state = int(hashlib.sha256(seed.encode()).hexdigest()[:16], 16)
    while True:
        state = (state * 6364136223846793005 + 1442695040888963407) % 2**64
        yield (state >> 11) / 2**53


def _levels(counts: list[int]) -> list[int]:
    """Quartile thresholds over non-zero contribution days."""
    nz = sorted(c for c in counts if c > 0)
    if not nz:
        return [1, 1, 1]

    def q(f: float) -> int:
        return nz[min(len(nz) - 1, int(len(nz) * f))]

    return [q(0.25), q(0.5), q(0.75)]


def _project(cx: float, cy: float, rx: float, theta: float) -> tuple[float, float, float]:
    """Project an orbital angle onto tilted 3D-perspective screen coordinates, returning (x, y, depth)."""
    lx = rx * math.cos(theta)
    ly = rx * ORBIT_TILT * math.sin(theta)
    cos_r, sin_r = math.cos(ORBIT_ROLL), math.sin(ORBIT_ROLL)
    px = cx + lx * cos_r - ly * sin_r
    py = cy + lx * sin_r + ly * cos_r
    return px, py, math.sin(theta)


def _arc_path(cx: float, cy: float, rx: float, start_deg: int, end_deg: int, step: int = 6) -> str:
    """Build a smooth polyline path for a segment of a tilted ellipse."""
    pts = []
    for deg in range(start_deg, end_deg + 1, step):
        px, py, _ = _project(cx, cy, rx, math.radians(deg))
        pts.append(f"{px:.1f},{py:.1f}")
    return "M" + "L".join(pts)


def build_orbital(calendar: list[list], updated: str, theme: Theme) -> str:
    """Render the 3D-perspective orbital contribution star chart slice."""
    x0, fr = theme.text_x, theme.frame_right
    days = [(datetime.date.fromisoformat(d), n) for d, n in calendar]
    counts = [n for _, n in days]
    total = sum(counts)
    peak = max(counts) if counts else 0
    active_days = sum(1 for n in counts if n > 0)
    lv = _levels(counts)
    rnd = _rng(f"orbit-{updated}-{total}")

    cx, cy = 344.0, 326.0
    n_days = max(len(days), 1)
    ring_colors = [theme.cyan, theme.violet, theme.amber, theme.magenta]

    # Subtle background starfield inside the chart region
    stars: list[str] = []
    for i in range(52):
        sx = x0 + 8 + next(rnd) * 555
        sy = 128 + next(rnd) * 390
        r = (0.6, 0.8, 1.1)[i % 3]
        op = 0.18 + next(rnd) * 0.35
        cls = f' class="s{i % 3}"' if i % 4 == 0 else ""
        stars.append(f'<circle{cls} cx="{sx:.1f}" cy="{sy:.1f}" r="{r}" fill="{theme.dim}" opacity="{op:.2f}"/>')

    # Back halves of orbits (theta in [180, 360] -> sin(theta) <= 0)
    back_arcs: list[str] = []
    front_arcs: list[str] = []
    ring_op_back = ".16" if theme.is_light else ".18"
    ring_op_front = ".42" if theme.is_light else ".48"
    for idx, rx in enumerate(ORBIT_RADII):
        stroke = theme.border if theme.is_light else theme.cyan
        back_arcs.append(
            f'<path d="{_arc_path(cx, cy, rx, 180, 360)}" fill="none" stroke="{stroke}" '
            f'stroke-opacity="{ring_op_back}" stroke-width="1" stroke-dasharray="3 4"/>'
        )
        front_arcs.append(
            f'<path d="{_arc_path(cx, cy, rx, 0, 180)}" fill="none" stroke="{stroke}" '
            f'stroke-opacity="{ring_op_front}" stroke-width="1.2"/>'
        )
        # Quarter label on outer edge
        lx, ly, _ = _project(cx, cy, rx + 11, math.radians(18))
        back_arcs.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" class="dim" opacity=".65" style="font-size:9px">Q{idx + 1}</text>'
        )

    # Map days onto the 4 concentric orbits
    back_edges: list[str] = []
    front_edges: list[str] = []
    back_nodes: list[str] = []
    front_nodes: list[str] = []

    prev_ring = -1
    prev_pt: tuple[float, float, float] | None = None

    for i, (_, n) in enumerate(days):
        ring_idx = min(3, int(i * 4 / n_days))
        ring_start = int(ring_idx * n_days / 4)
        ring_end = int((ring_idx + 1) * n_days / 4)
        ring_span = max(ring_end - ring_start, 1)
        frac = (i - ring_start) / ring_span
        theta = frac * 2 * math.pi - math.pi / 2
        px, py, depth = _project(cx, cy, ORBIT_RADII[ring_idx], theta)
        is_front = depth >= 0

        if n > 0 and prev_pt is not None and prev_ring == ring_idx:
            edge = (
                f'<line x1="{prev_pt[0]:.1f}" y1="{prev_pt[1]:.1f}" x2="{px:.1f}" y2="{py:.1f}" '
                f'stroke="{theme.cyan}" stroke-opacity="{"0.45" if is_front else "0.22"}" stroke-width="1"/>'
            )
            (front_edges if is_front else back_edges).append(edge)

        if n == 0:
            node = (
                f'<circle cx="{px:.1f}" cy="{py:.1f}" r="1.1" '
                f'fill="{theme.muted}" opacity="{"0.35" if is_front else "0.16"}"/>'
            )
            (front_nodes if is_front else back_nodes).append(node)
            prev_ring = -1
            prev_pt = None
            continue

        level = sum(n > t for t in lv)
        color = ring_colors[level]
        radius = 2.0 + 4.4 * math.sqrt(n / max(peak, 1))
        op = 0.95 if is_front else 0.65
        parts = []
        if level == 3:
            parts.append(
                f'<circle class="pulse-node" cx="{px:.1f}" cy="{py:.1f}" r="{radius + 3.5:.1f}" '
                f'fill="none" stroke="{color}" stroke-opacity=".45" stroke-width="1"/>'
            )
        parts.append(
            f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{radius:.1f}" fill="{color}" opacity="{op:.2f}"/>'
        )
        (front_nodes if is_front else back_nodes).extend(parts)
        prev_ring = ring_idx
        prev_pt = (px, py, depth)

    # Central star core
    core = f'''<circle cx="{cx:.1f}" cy="{cy:.1f}" r="36" fill="url(#coreglow)"/>
<circle cx="{cx:.1f}" cy="{cy:.1f}" r="11" fill="{theme.amber}" opacity=".9"/>
<circle cx="{cx:.1f}" cy="{cy:.1f}" r="5" fill="{theme.wh}"/>
<path d="M{cx - 20:.1f} {cy:.1f}H{cx - 13:.1f}M{cx + 13:.1f} {cy:.1f}H{cx + 20:.1f}M{cx:.1f} {cy - 20:.1f}V{cy - 13:.1f}M{cx:.1f} {cy + 13:.1f}V{cy + 20:.1f}" stroke="{theme.amber}" stroke-opacity=".6" stroke-width="1"/>'''

    # Right-hand telemetry summary cards
    busiest_d, busiest_n = max(days, key=lambda t: t[1]) if days else (None, 0)
    busiest_val = f"{busiest_d:%b} {busiest_d.day}" if busiest_d and busiest_n else "—"
    busiest_sub = f"{busiest_n} contributions" if busiest_n else "no activity"

    rx_card = 626
    rw = (fr - 36) - rx_card
    cards_data = [
        ("TOTAL ORBIT", f"{total:,}", "last 365 days", theme.cyan),
        ("ACTIVE DAYS", f"{active_days}", f"of {len(days)} days", theme.green),
        ("PEAK BURST", busiest_val, busiest_sub, theme.amber),
    ]
    telemetry_cards = []
    for idx, (lab, val, sub, acc) in enumerate(cards_data):
        cy_top = 160 + idx * 96
        telemetry_cards.append(
            f'<g class="ln" style="animation-delay:{0.25 + idx * 0.1:.2f}s">'
            f'<rect x="{rx_card}" y="{cy_top}" width="{rw}" height="80" rx="8" fill="{theme.surface}" stroke="{theme.border}" stroke-width="1"/>'
            f'<rect x="{rx_card}" y="{cy_top + 12}" width="4" height="56" rx="2" fill="{acc}"/>'
            f'<text x="{rx_card + 16}" y="{cy_top + 24}" letter-spacing="1.2" class="dim" style="font-size:10px">{esc(lab)}</text>'
            f'<text x="{rx_card + 16}" y="{cy_top + 50}" font-weight="700" fill="{acc}" style="font-size:22px">{esc(val)}</text>'
            f'<text x="{rx_card + 16}" y="{cy_top + 68}" class="dim" style="font-size:11px">{esc(sub)}</text>'
            f"</g>"
        )

    # Magnitude legend
    ly_leg = 472
    legend_nodes = "".join(
        f'<circle cx="{rx_card + 52 + i * 22}" cy="{ly_leg}" r="{2.2 + i * 1.1:.1f}" fill="{c}"/>'
        for i, c in enumerate(ring_colors)
    )
    legend = (
        f'<text x="{rx_card}" y="{ly_leg + 4}" class="dim" style="font-size:10.5px">quiet</text>'
        f"{legend_nodes}"
        f'<text x="{rx_card + 52 + 4 * 22}" y="{ly_leg + 4}" class="dim" style="font-size:10.5px">supernova</text>'
    )

    sec_title = theme.section_label("centerpiece", "orbital-activity")
    sub_line = (
        "astrometrics · 3d orbital telemetry · last 365 days"
        if theme.themed_labels
        else "3d orbital activity · last 365 days"
    )

    body = (
        heading(44, sec_title, "// 03", theme)
        + f'''
<g class="ln" style="animation-delay:.15s"><text x="{x0}" y="96" class="dim"><tspan class="cy">›</tspan> {esc(sub_line)}</text></g>
<g>{"".join(stars)}</g>
<g>{"".join(back_arcs)}{"".join(back_edges)}{"".join(back_nodes)}</g>
{core}
<g>{"".join(front_arcs)}{"".join(front_edges)}{"".join(front_nodes)}</g>
{"".join(telemetry_cards)}
{legend}'''
    )

    css = (
        "@keyframes tw{0%,100%{opacity:.8}50%{opacity:.15}}\n"
        "@keyframes pulse-ring{0%,100%{opacity:.55;transform:scale(1)}50%{opacity:.15}}\n"
        ".s0{animation:tw 3.2s infinite}.s1{animation:tw 4.5s infinite 1s}.s2{animation:tw 5.8s infinite 2s}\n"
        ".pulse-node{animation:pulse-ring 2.6s ease-in-out infinite}"
    )
    defs = (
        f'<radialGradient id="coreglow">'
        f'<stop offset="0" stop-color="{theme.amber}" stop-opacity=".45"/>'
        f'<stop offset=".5" stop-color="{theme.cyan}" stop-opacity=".15"/>'
        f'<stop offset="1" stop-color="{theme.bg}" stop-opacity="0"/>'
        f"</radialGradient>"
    )
    busiest_desc = (
        f", busiest day {busiest_d:%B} {busiest_d.day} with {busiest_n}" if busiest_d is not None and busiest_n else ""
    )
    desc = (
        f"Orbital contribution chart: a 3D-perspective star chart of the last 365 days. "
        f"{total:,} contributions across {active_days} active days{busiest_desc}."
    )
    return slice_svg(
        560,
        body,
        title="Orbital contribution chart",
        desc=desc,
        text=f"{sec_title}03{sub_line}TOTAL ORBITACTIVE DAYSPEAK BURSTquietsupernova",
        theme=theme,
        css=css,
        defs=defs,
    )

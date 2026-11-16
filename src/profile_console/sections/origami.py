"""3D isometric Kusudama origami star polyhedron centerpiece slice builder for origami."""

from __future__ import annotations

import math

from profile_console.sections._common import busiest_summary, telemetry_cards, weekly_buckets
from profile_console.svg import Theme, heading, slice_svg


def _scale(v: tuple[float, float, float], s: float) -> tuple[float, float, float]:
    return (v[0] * s, v[1] * s, v[2] * s)


def _norm(v: tuple[float, float, float]) -> tuple[float, float, float]:
    length = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) or 1.0
    return (v[0] / length, v[1] / length, v[2] / length)


def _sub(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _dot(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _rotate_iso(v: tuple[float, float, float]) -> tuple[float, float, float]:
    """Rotate 3D point into an isometric-style view (yaw + pitch + slight roll)."""
    x, y, z = v
    # Yaw around Y (38 deg)
    cy, sy = math.cos(math.radians(38.0)), math.sin(math.radians(38.0))
    x1 = x * cy + z * sy
    y1 = y
    z1 = -x * sy + z * cy
    # Pitch around X (28 deg)
    cp, sp = math.cos(math.radians(28.0)), math.sin(math.radians(28.0))
    x2 = x1
    y2 = y1 * cp - z1 * sp
    z2 = y1 * sp + z1 * cp
    return (x2, y2, z2)


def _lerp_hex(c0: str, c1: str, t: float) -> str:
    t = max(0.0, min(1.0, t))
    r0, g0, b0 = int(c0[1:3], 16), int(c0[3:5], 16), int(c0[5:7], 16)
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r = round(r0 + (r1 - r0) * t)
    g = round(g0 + (g1 - g0) * t)
    b = round(b0 + (b1 - b0) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def _icosahedron() -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]:
    """Return unit-sphere vertices and 20 outward-wound triangular faces of an icosahedron."""
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    raw = [
        (-1, phi, 0), (1, phi, 0), (-1, -phi, 0), (1, -phi, 0),
        (0, -1, phi), (0, 1, phi), (0, -1, -phi), (0, 1, -phi),
        (phi, 0, -1), (phi, 0, 1), (-phi, 0, -1), (-phi, 0, 1),
    ]
    verts = [_norm((float(x), float(y), float(z))) for x, y, z in raw]
    faces = [
        (0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
        (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
        (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
        (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1),
    ]
    return verts, faces


def build_origami(calendar: list[list], updated: str, theme: Theme) -> str:
    """Render a 3D isometric Kusudama origami star polyhedron of the last 365 days."""
    x0, fr = theme.text_x, theme.frame_right
    weeks, total, active_days, busiest = weekly_buckets(calendar)

    # Aggregate 52 weeks into 20 icosahedral star modules
    n_mods = 20
    mod_vals = [0] * n_mods
    for i, (_, val) in enumerate(weeks):
        bucket = min(n_mods - 1, int(i * n_mods / max(len(weeks), 1)))
        mod_vals[bucket] += val
    peak_mod = max(mod_vals, default=1) or 1

    verts, faces = _icosahedron()
    r_core = 82.0
    cx, cy = 320.0, 294.0
    light_dir = _norm((-0.55, -0.65, 0.52))

    # Paper shade endpoints (shadow -> lit) for normal and peak modules
    lo_dark = "#101622" if not theme.is_light else "#cfc5b2"
    lo_lit = "#243045" if not theme.is_light else "#fcfaf4"
    hi_dark = "#2a1b24" if not theme.is_light else "#d8b4aa"
    hi_lit = "#6e3236" if not theme.is_light else "#f7e3dc"

    # Collect all 3D triangular facets + peak apex markers for painter's depth sorting
    render_items: list[tuple[float, str]] = []
    for f_idx, (i0, i1, i2) in enumerate(faces):
        v0 = _scale(verts[i0], r_core)
        v1 = _scale(verts[i1], r_core)
        v2 = _scale(verts[i2], r_core)

        val = mod_vals[f_idx]
        ratio = val / peak_mod
        is_peak = ratio >= 0.65
        spike_h = 16.0 + 74.0 * (math.sqrt(ratio) if val > 0 else 0.0)

        face_dir = _norm((v0[0] + v1[0] + v2[0], v0[1] + v1[1] + v2[1], v0[2] + v1[2] + v2[2]))
        apex = (
            face_dir[0] * (r_core + spike_h),
            face_dir[1] * (r_core + spike_h),
            face_dir[2] * (r_core + spike_h),
        )

        # Rotate all 4 points of this 3D origami pyramid into isometric camera space
        p0 = _rotate_iso(v0)
        p1 = _rotate_iso(v1)
        p2 = _rotate_iso(v2)
        pa = _rotate_iso(apex)

        dark_c = hi_dark if is_peak else lo_dark
        lit_c = hi_lit if is_peak else lo_lit
        stroke_c = theme.magenta if is_peak else theme.border

        for ta, tb, tc in ((p0, p1, pa), (p1, p2, pa), (p2, p0, pa)):
            # Compute camera-space normal; backface cull triangles facing away
            normal = _cross(_sub(tb, ta), _sub(tc, ta))
            if normal[2] <= 0:
                continue
            n_unit = _norm(normal)
            shade = 0.5 + 0.5 * _dot(n_unit, light_dir)
            fill_c = _lerp_hex(dark_c, lit_c, shade)
            depth = (ta[2] + tb[2] + tc[2]) / 3.0
            pts_str = f"{cx + ta[0]:.1f},{cy + ta[1]:.1f} {cx + tb[0]:.1f},{cy + tb[1]:.1f} {cx + tc[0]:.1f},{cy + tc[1]:.1f}"
            poly = (
                f'<polygon points="{pts_str}" fill="{fill_c}" '
                f'stroke="{stroke_c}" stroke-width=".85" stroke-linejoin="round" stroke-opacity=".85"/>'
            )
            render_items.append((depth, poly))

        # Vermilion hanko dot on outward-facing peak apexes
        if is_peak and pa[2] > 0:
            hx, hy = cx + pa[0], cy + pa[1]
            delay = (f_idx % 5) * 0.55
            dot = (
                f'<circle cx="{hx:.1f}" cy="{hy:.1f}" r="2.8" fill="{theme.magenta}"/>'
                f'<circle class="hanko-ring" cx="{hx:.1f}" cy="{hy:.1f}" r="5.5" '
                f'fill="none" stroke="{theme.magenta}" stroke-opacity=".45" '
                f'style="transform-origin:{hx:.1f}px {hy:.1f}px;animation-delay:{delay:.2f}s"/>'
            )
            render_items.append((pa[2] + 1.0, dot))

    render_items.sort(key=lambda item: item[0])
    polyhedron = "".join(el for _, el in render_items)

    # Isometric ground shadow & compass ring beneath the floating Kusudama
    shadow_y = cy + 148.0
    shadow = (
        f'<ellipse class="kusu-ring" cx="{cx:.1f}" cy="{shadow_y:.1f}" rx="124" ry="34" '
        f'fill="none" stroke="{theme.border}" stroke-dasharray="10 6" stroke-opacity=".8"/>'
        f'<ellipse class="kusu-shadow" cx="{cx:.1f}" cy="{shadow_y:.1f}" rx="86" ry="22" '
        f'fill="{theme.fg}" fill-opacity="{0.08 if theme.is_light else 0.18}" '
        f'style="transform-origin:{cx:.1f}px {shadow_y:.1f}px"/>'
    )

    css = (
        "@keyframes kusu-float{0%,100%{transform:translateY(0) rotate(-2.5deg)}50%{transform:translateY(-14px) rotate(2.5deg)}}\n"
        "@keyframes kusu-shadow{0%,100%{transform:scale(1);opacity:1}50%{transform:scale(.78);opacity:.45}}\n"
        "@keyframes kusu-ring{from{stroke-dashoffset:0}to{stroke-dashoffset:-32}}\n"
        "@keyframes hanko-pulse{0%{transform:scale(1);opacity:.9}100%{transform:scale(2.8);opacity:0}}\n"
        f".kusu-float{{transform-origin:{cx:.1f}px {cy:.1f}px;animation:kusu-float 4s ease-in-out infinite}}\n"
        ".kusu-shadow{animation:kusu-shadow 4s ease-in-out infinite}\n"
        ".kusu-ring{animation:kusu-ring 2.2s linear infinite}\n"
        ".hanko-ring{animation:hanko-pulse 2.4s ease-out infinite}"
    )

    rx_card = 626
    rw = (fr - 36) - rx_card
    busiest_val, busiest_sub = busiest_summary(busiest)
    cards = [
        ("TOTAL FOLDS", f"{total:,}", "last 365 days", theme.magenta),
        ("ACTIVE DAYS", f"{active_days}", f"of {len(calendar)} days", theme.cyan),
        ("PEAK CREST", busiest_val, busiest_sub, theme.amber),
    ]
    telemetry = telemetry_cards(cards, rx_card, rw, theme)

    sec_title = theme.section_label("centerpiece", "kusudama")
    body = (
        heading(44, sec_title, "// 03", theme)
        + f'''
<g class="ln" style="animation-delay:.15s"><text x="{x0}" y="96" class="dim"><tspan class="cy">›</tspan> 3d isometric kusudama · 20 folded spires · 52w</text></g>
<g>{shadow}<g class="kusu-float">{polyhedron}</g></g>
{telemetry}'''
    )
    return slice_svg(
        520,
        body,
        title="Origami Kusudama",
        desc=f"3D isometric Kusudama origami star polyhedron of the last 365 days: {total:,} contributions across {active_days} active days.",
        text=f"{sec_title}033d isometric kusudama20 folded spires52wTOTAL FOLDSACTIVE DAYSPEAK CREST{total}{active_days}{busiest_val}",
        theme=theme,
        css=css,
    )

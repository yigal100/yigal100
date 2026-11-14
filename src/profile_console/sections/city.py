"""Isometric contribution city skyline slice builder."""

from __future__ import annotations

import datetime
import hashlib
import math
from collections.abc import Iterator
from typing import TypedDict

from profile_console.svg import Theme, heading, slice_svg

CITY_TW, CITY_TH = 25, 12.5  # iso tile width / height
CITY_OX, CITY_OY = 152.5, 262  # grid origin inside the 880-wide slice
CITY_HMAX = 118  # tallest building, px


class _CityPalette(TypedDict):
    roofs: list[str]
    face_l: str
    face_r: str
    win_on: str
    win_side: str
    win_off: str
    lot_fill: str
    lot_stroke: str
    moon: str


_CITY_PALETTES: dict[str, _CityPalette] = {
    "dark": {
        "roofs": ["#0c2d6b", "#1554c0", "#2f81f7", "#1fd5ff"],
        "face_l": "#1a2440",
        "face_r": "#111831",
        "win_on": "#7df9ff",
        "win_side": "#4cc9f0",
        "win_off": "#111827",
        "lot_fill": "#161b22",
        "lot_stroke": "#0d1117",
        "moon": "#e6edf3",
    },
    "light": {
        "roofs": ["#bae6fd", "#7dd3fc", "#0284c7", "#0369a1"],
        "face_l": "#cbd5e1",
        "face_r": "#94a3b8",
        "win_on": "#fef08a",
        "win_side": "#fde047",
        "win_off": "#64748b",
        "lot_fill": "#e2e8f0",
        "lot_stroke": "#cbd5e1",
        "moon": "#f59e0b",
    },
}


def _p(x: float, y: float) -> str:
    return f"{x:.1f},{y:.1f}"


def _rng(seed: str) -> Iterator[float]:
    """Tiny deterministic PRNG so the same data always draws the same windows."""
    state = int(hashlib.sha256(seed.encode()).hexdigest()[:16], 16)
    while True:
        state = (state * 6364136223846793005 + 1442695040888963407) % 2**64
        yield (state >> 11) / 2**53


def _levels(counts: list[int]) -> list[int]:
    """GitHub-style quartile thresholds over the non-zero days."""
    nz = sorted(c for c in counts if c > 0)
    if not nz:
        return [1, 1, 1]

    def q(f: float) -> int:
        return nz[min(len(nz) - 1, int(len(nz) * f))]

    return [q(0.25), q(0.5), q(0.75)]


def build_city(calendar: list[list], updated: str, theme: Theme) -> str:
    """Render the ~/contribution-city isometric skyline slice."""
    x0, fl, fr = theme.text_x, theme.frame_left, theme.frame_right
    pal = _CITY_PALETTES[theme.variant]
    roofs = pal["roofs"]
    days = [(datetime.date.fromisoformat(d), n) for d, n in calendar]
    counts = [n for _, n in days]
    total, peak = sum(counts), max(counts) if counts else 0
    lv = _levels(counts)
    rnd = _rng(f"{updated}-{total}")
    start = days[0][0]

    cells = []
    for d, n in days:
        idx = (d - start).days
        cells.append((idx // 7, (d.weekday() + 1) % 7, n))  # week column, Sunday = 0
    cells.sort(key=lambda c: (c[0] + c[1], c[0]))  # back to front

    shapes, flick = [], 0
    for w, dow, n in cells:
        cx = CITY_OX + (w - dow) * CITY_TW / 2
        cy = CITY_OY + (w + dow) * CITY_TH / 2
        L, R = (cx - CITY_TW / 2, cy), (cx + CITY_TW / 2, cy)
        T, B = (cx, cy - CITY_TH / 2), (cx, cy + CITY_TH / 2)
        if n == 0:
            shapes.append(
                f'<path d="M{_p(*T)}L{_p(*R)}L{_p(*B)}L{_p(*L)}Z" fill="{pal["lot_fill"]}" stroke="{pal["lot_stroke"]}" stroke-width=".6"/>'
            )
            continue
        h = 8 + (CITY_HMAX - 8) * math.sqrt(n / peak)
        level = sum(n > t for t in lv)
        Tu, Ru, Bu, Lu = [(px, py - h) for px, py in (T, R, B, L)]
        shapes.append(
            f'<path d="M{_p(*L)}L{_p(*B)}L{_p(*Bu)}L{_p(*Lu)}Z" fill="{pal["face_l"]}"/>'
            f'<path d="M{_p(*B)}L{_p(*R)}L{_p(*Ru)}L{_p(*Bu)}Z" fill="{pal["face_r"]}"/>'
            f'<path d="M{_p(*Tu)}L{_p(*Ru)}L{_p(*Bu)}L{_p(*Lu)}Z" fill="{roofs[level]}"/>'
        )
        on, side, off, fl_wins = [], [], [], []
        for face, (a, b) in (("l", (L, B)), ("r", (B, R))):
            for r in range(int((h - 6) // 7)):
                v0 = 5 + r * 7
                for u0 in (0.18, 0.58):
                    lit = next(rnd) < 0.55
                    if not lit and next(rnd) < 0.5:
                        continue
                    pts = [
                        (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u - v)
                        for u, v in ((u0, v0), (u0 + 0.26, v0), (u0 + 0.26, v0 + 3.2), (u0, v0 + 3.2))
                    ]
                    seg = "M" + "L".join(_p(*q) for q in pts) + "Z"
                    if not lit:
                        off.append(seg)
                    elif next(rnd) < 0.03:
                        fl_wins.append((seg, face))
                    else:
                        (on if face == "l" else side).append(seg)
        if off:
            shapes.append(f'<path d="{"".join(off)}" fill="{pal["win_off"]}"/>')
        if on:
            shapes.append(f'<path d="{"".join(on)}" fill="{pal["win_on"]}"/>')
        if side:
            shapes.append(f'<path d="{"".join(side)}" fill="{pal["win_side"]}"/>')
        for seg, face in fl_wins:
            flick += 1
            shapes.append(f'<path class="f{flick % 3}" d="{seg}" fill="{pal["win_on"] if face == "l" else pal["win_side"]}"/>')

    # night sky in the empty top-right corner: stars, moon, a plane crossing
    stars = []
    for i in range(46):
        sx, sy = 470 + next(rnd) * 350, 118 + next(rnd) * 150
        if sx > 700 and sy < 215:  # keep the moon clear
            continue
        cls = f' class="s{i % 3}"' if i % 3 == 0 else ""
        stars.append(
            f'<circle{cls} cx="{sx:.1f}" cy="{sy:.1f}" r="{(0.6, 0.8, 1.1)[i % 3]}" '
            f'fill="#c9d1d9" opacity="{0.35 + next(rnd) * 0.5:.2f}"/>'
        )
    busiest_d, busiest_n = max(days, key=lambda t: t[1]) if days else (None, 0)
    busiest_str = (
        f'busiest day <tspan class="fg">{busiest_d:%b} {busiest_d.day}</tspan> · {busiest_n}'
        if busiest_d is not None and busiest_n
        else ""
    )
    info = [
        f'<tspan class="cy" font-weight="700">{total:,}</tspan> contributions · last 365 days',
        busiest_str,
        f"{sum(1 for n in counts if n)} active days",
    ]
    info_svg = "".join(
        f'<text x="{fr - 36}" y="{300 + i * 20}" text-anchor="end" class="dim" style="font-size:12px">{t}</text>'
        for i, t in enumerate(info)
        if t
    )
    legend = "".join(
        f'<rect x="{x0 + 52 + i * 16}" y="{642}" width="11" height="11" fill="{c}"/>'
        for i, c in enumerate([pal["lot_fill"]] + roofs)
    )
    sec_title = theme.section_label("centerpiece", "contribution-city")
    moon_cut = "" if theme.is_light else f'<circle cx="{fr - 74}" cy="{155}" r="12.5" fill="{theme.bg}"/>'
    body = (
        heading(44, sec_title, "// 03", theme)
        + f'''
<g class="ln" style="animation-delay:.15s"><text x="{x0}" y="96" class="dim"><tspan class="gr">$</tspan> render-city --last 365d <tspan fill="{theme.muted}"># one building per day</tspan></text></g>
<g>{"".join(stars)}</g>
<circle cx="{fr - 80}" cy="{160}" r="40" fill="url(#moonglow)"/>
<circle cx="{fr - 80}" cy="{160}" r="14" fill="{pal["moon"]}"/>
{moon_cut}
<g class="plane"><g transform="translate(0 132)"><rect x="0" y="0" width="14" height="2" rx="1" fill="{theme.muted}"/><circle class="bl" cx="0" cy="1" r="1.6" fill="#ff7b72"/><circle class="bl" cx="14" cy="1" r="1.6" fill="#f0f6fc" style="animation-delay:.7s"/></g></g>
{info_svg}
{"".join(shapes)}
<text x="{x0}" y="{652}" class="dim" style="font-size:11px">quiet</text>{legend}<text x="{x0 + 52 + 5 * 16 + 6}" y="{652}" class="dim" style="font-size:11px">skyscraper</text>'''
    )
    css = f"""@keyframes tw{{0%,100%{{opacity:.9}}50%{{opacity:.15}}}}
@keyframes fl{{0%,40%,100%{{opacity:1}}45%,60%{{opacity:.1}}}}
@keyframes blink{{0%,90%,100%{{opacity:0}}93%{{opacity:1}}}}
@keyframes fly{{from{{transform:translate({fl - 40}px,0)}}to{{transform:translate({fr + 40}px,-30px)}}}}
.s0{{animation:tw 3s infinite}}
.f0{{animation:fl 5s infinite}}.f1{{animation:fl 7s infinite 2s}}.f2{{animation:fl 9s infinite 4s}}
.plane{{animation:fly 26s linear infinite}}.bl{{animation:blink 1.4s infinite}}"""
    defs = '<radialGradient id="moonglow"><stop offset="0" stop-color="#f0f6fc" stop-opacity=".22"/><stop offset="1" stop-color="#f0f6fc" stop-opacity="0"/></radialGradient>'
    busiest_desc = (
        f", busiest day {busiest_d:%B} {busiest_d.day} with {busiest_n}" if busiest_d is not None and busiest_n else ""
    )
    desc = (
        f"Contribution city: an isometric night skyline with one building per day of the last year, "
        f"taller and brighter for busier days. {total:,} contributions{busiest_desc}."
    )
    return slice_svg(
        680,
        body,
        title="Contribution city",
        desc=desc,
        text="~/contribution-city// 03$ render-city --last 365d # one building per dayquietskyscraper",
        theme=theme,
        css=css,
        defs=defs,
    )

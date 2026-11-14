"""GitHub and DEV stats slice builder."""

from __future__ import annotations

import datetime
import html
import re

from profile_console.config import ProfileInfo
from profile_console.svg import Theme, esc, fmt_num, heading, slice_svg, up40


def _tile(
    x: float,
    y: float,
    w: float,
    h: float,
    label: str,
    value: str,
    sub: str,
    delay: float,
    theme: Theme,
    *,
    pending: bool = False,
    accent: str | None = None,
) -> str:
    cyan = accent or theme.cyan
    vc = theme.muted if pending else cyan
    if theme.is_modern:
        return f'''<g class="ln" style="animation-delay:{delay:.2f}s">
<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{theme.card_rx}" fill="{theme.surface}" stroke="{theme.border}" stroke-width="1"/>
<rect x="{x}" y="{y + 12}" width="4" height="{h - 24}" rx="2" fill="{cyan}"/>
<text x="{x + 16}" y="{y + 22}" letter-spacing="1.4" class="dim" style="font-size:10.5px">{esc(label)}</text>
<text x="{x + 16}" y="{y + 50}" font-weight="700" fill="{vc}" style="font-size:30px">{esc(value)}</text>
<text x="{x + 16}" y="{y + h - 12}" class="dim" style="font-size:11.5px">{esc(sub)}</text>
</g>'''
    glow = (
        ""
        if pending
        else f'<text x="{x + 16}" y="{y + 50}" font-weight="700" fill="{cyan}" '
        f'filter="url(#g)" opacity=".55" style="font-size:30px">{esc(value)}</text>'
    )
    return f'''<g class="ln" style="animation-delay:{delay:.2f}s">
<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{cyan}" fill-opacity=".035" stroke="{cyan}" stroke-opacity=".35"/>
<path d="M{x} {y + 12}V{y}H{x + 12}" fill="none" stroke="{cyan}" stroke-width="2"/>
<text x="{x + 16}" y="{y + 22}" letter-spacing="1.5" class="dim" style="font-size:10.5px">{esc(label)}</text>
{glow}<text x="{x + 16}" y="{y + 50}" font-weight="700" fill="{vc}" style="font-size:30px">{esc(value)}</text>
<text x="{x + 16}" y="{y + h - 12}" fill="#6e7681" style="font-size:12px">{esc(sub)}</text>
</g>'''


def build_stats(d: dict, profile: ProfileInfo, theme: Theme) -> str:
    """Render the ~/stats section from stats.json."""
    x, fr, cyan = theme.text_x, theme.frame_right, theme.cyan
    y = datetime.date.fromisoformat(d["updated"])
    since = datetime.date.fromisoformat(d["created_at"][:10])
    yrs = (y - since).days // 365
    if theme.is_modern:
        sec_title = theme.section_label("stats", "telemetry")
        sub_cmd = f"sensor array · {profile.handle}" if theme.scifi_labels else f"github telemetry · {profile.handle}"
        parts = [
            heading(44, sec_title, "// 02", theme),
            f'<g class="ln" style="animation-delay:.15s"><text x="{x}" y="96" class="dim">'
            f'<tspan class="cy">›</tspan> {esc(sub_cmd)}</text></g>',
        ]
    else:
        parts = [
            heading(44, "stats", "// 02", theme),
            f'<g class="ln" style="animation-delay:.15s"><text x="{x}" y="96" class="dim">'
            f'<tspan class="gr">$</tspan> gh stats --user {esc(profile.handle)}</text></g>',
        ]
    # row 1 — big tiles
    tw, gap, ty, th = 182, 16, 118, 92
    t1 = [
        (
            "TOTAL STARS",
            fmt_num(d["stars"]),
            f"across {d.get('repo_count', 'all')} repos" if d.get("repo_count") else "across all repos",
            theme.amber,
        ),
        (
            f"CONTRIBUTIONS {d['year']}",
            fmt_num(d["contributions_year"]),
            f"{fmt_num(d['contributions_all'])} all time",
            theme.cyan,
        )
        if "contributions_year" in d
        else (
            f"COMMITS {d['year']}",
            fmt_num(d["commits_year"]),
            f"{fmt_num(d['commits_all'])} all time",
            theme.cyan,
        ),
        ("PULL REQUESTS", fmt_num(d["prs"]), f"{fmt_num(d['prs_merged'])} merged", theme.violet),
        ("CURRENT STREAK", f"{d['streak_current']}d", f"longest: {d['streak_longest']} days", theme.green),
    ]
    for i, (lab, val, sub, acc) in enumerate(t1):
        parts.append(_tile(x + i * (tw + gap), ty, tw, th, lab, val, sub, 0.25 + i * 0.08, theme, accent=acc if theme.is_modern else None))

    # row 2 — neofetch list + languages
    ry, rh = ty + th + 16, 150
    lw = 300
    kv = [
        ("followers", fmt_num(d["followers"])),
        ("forks", fmt_num(d["forks"])),
        ("member since", f"{since:%b %Y} ({yrs}y)"),
    ]
    rows = "\n".join(
        f'<text x="{x + 16}" y="{ry + 44 + i * 32}" xml:space="preserve">'
        f'<tspan class="cy">{esc(k)}</tspan><tspan class="dim">{"." * (16 - len(k))}</tspan> '
        f'<tspan class="fg">{esc(v)}</tspan></text>'
        for i, (k, v) in enumerate(kv)
    )
    if theme.is_modern:
        parts.append(f'''<g class="ln" style="animation-delay:.6s">
<rect x="{x}" y="{ry}" width="{lw}" height="{rh}" rx="{theme.card_rx}" fill="{theme.surface}" stroke="{theme.border}" stroke-width="1"/>
<rect x="{x}" y="{ry + 14}" width="4" height="{rh - 28}" rx="2" fill="{theme.cyan}"/>
{rows}
</g>''')
    else:
        parts.append(f'''<g class="ln" style="animation-delay:.6s">
<rect x="{x}" y="{ry}" width="{lw}" height="{rh}" fill="{cyan}" fill-opacity=".035" stroke="{cyan}" stroke-opacity=".35"/>
<path d="M{x} {ry + 12}V{ry}H{x + 12}" fill="none" stroke="{cyan}" stroke-width="2"/>
{rows}
</g>''')
    lx = x + lw + gap
    lwid = (fr - 36) - lx
    langs = sorted(d["languages"].items(), key=lambda kv: -kv[1])
    total = sum(v for _, v in langs)
    top = langs[:5]
    other = total - sum(v for _, v in top)
    items = [(k, v / total) for k, v in top] + ([("Other", other / total)] if other else [])
    cols = [cyan, theme.magenta, theme.green, theme.amber, theme.violet, theme.muted]
    bx, by, bw = lx + 16, ry + 42, lwid - 32
    segs, cx = [], bx
    for (_, p), c in zip(items, cols):
        w = bw * p
        segs.append(f'<rect x="{cx:.1f}" y="{by}" width="{max(w - 2, 1):.1f}" height="8" rx="{"3" if theme.is_modern else "0"}" fill="{c}"/>')
        if not theme.is_modern:
            segs.append(
                f'<rect x="{cx:.1f}" y="{by}" width="{max(w - 2, 1):.1f}" height="8" fill="{c}" filter="url(#g)" opacity=".6"/>'
            )
        cx += w
    legend = []
    for i, ((k, p), c) in enumerate(zip(items, cols)):
        col, row = i % 2, i // 2
        lxx = bx + col * (bw / 2)
        lyy = by + 36 + row * 26
        legend.append(
            f'<rect x="{lxx}" y="{lyy - 9}" width="9" height="9" rx="{"2" if theme.is_modern else "0"}" fill="{c}"/>'
            f'<text x="{lxx + 18}" y="{lyy}" class="fg" style="font-size:13px">{esc(k)}</text>'
            f'<text x="{lxx + bw / 2 - 24}" y="{lyy}" text-anchor="end" class="dim" style="font-size:13px">{p * 100:.1f}%</text>'
        )
    if theme.is_modern:
        parts.append(f'''<g class="ln" style="animation-delay:.7s">
<rect x="{lx}" y="{ry}" width="{lwid}" height="{rh}" rx="{theme.card_rx}" fill="{theme.surface}" stroke="{theme.border}" stroke-width="1"/>
<rect x="{lx}" y="{ry + 14}" width="4" height="{rh - 28}" rx="2" fill="{theme.violet}"/>
<text x="{lx + 16}" y="{ry + 24}" letter-spacing="1.5" class="dim" style="font-size:10.5px">TOP LANGUAGES</text>
<rect x="{bx}" y="{by}" width="{bw}" height="8" rx="3" fill="{theme.surface_alt}"/>
{"".join(segs)}
{"".join(legend)}
</g>''')
    else:
        parts.append(f'''<g class="ln" style="animation-delay:.7s">
<rect x="{lx}" y="{ry}" width="{lwid}" height="{rh}" fill="{cyan}" fill-opacity=".035" stroke="{cyan}" stroke-opacity=".35"/>
<path d="M{lx} {ry + 12}V{ry}H{lx + 12}" fill="none" stroke="{cyan}" stroke-width="2"/>
<text x="{lx + 16}" y="{ry + 24}" letter-spacing="1.5" class="dim" style="font-size:10.5px">TOP LANGUAGES</text>
<rect x="{bx}" y="{by}" width="{bw}" height="8" fill="#11161d"/>
{"".join(segs)}
{"".join(legend)}
</g>''')

    # row 3 — DEV Community (tiles without data are left out; the row hides if all are missing)
    dv = d.get("dev") or {}
    t3 = [
        (lab, dv.get(k))
        for lab, k in (
            ("ARTICLES", "articles"),
            ("REACTIONS", "reactions"),
            ("COMMENTS", "comments"),
            ("VIEWS", "views"),
            ("DEV FOLLOWERS", "followers"),
        )
    ]
    t3 = [(lab, v) for lab, v in t3 if v is not None]
    fy = ry + rh + 30
    if t3:
        dy = ry + rh + 34
        parts.append(
            f'<g class="ln" style="animation-delay:.8s"><text x="{x}" y="{dy}" class="dim">'
            f'<tspan class="gr">$</tspan> dev stats --user {esc(profile.handle)}</text></g>'
        )
        n = len(t3)
        dw = (fr - 36 - x - (n - 1) * 12) / n
        for i, (lab, val) in enumerate(t3):
            parts.append(_tile(x + i * (dw + 12), dy + 16, dw, 76, lab, fmt_num(val), "", 0.9 + i * 0.06, theme))
        fy = dy + 16 + 76 + 30
    parts.append(
        f'<text x="{fr - 36}" y="{fy}" text-anchor="end" fill="{theme.muted}" style="font-size:11px">// last sync {d["updated"]}</text>'
    )
    h = up40(fy + 16)
    text = "".join(str(item) for item in [f"~/stats// 02$ gh stats --user {profile.handle} dev stats", "".join(parts)])
    text = re.sub(r"<[^>]+>", "", text) + "0123456789,—%.★()d"
    activity = (
        f"{d['contributions_year']} contributions in {d['year']}, {d['contributions_all']} all time"
        if "contributions_year" in d
        else f"{d['commits_year']} commits in {d['year']}, {d['commits_all']} all time"
    )
    desc = (
        f"GitHub stats: {d['stars']} total stars; {activity}; "
        f"{d['prs']} pull requests ({d['prs_merged']} merged); current streak {d['streak_current']} days, longest {d['streak_longest']}; "
        f"{d['followers']} followers; {d['forks']} forks; member since {since:%B %Y}. "
        "Top languages: "
        + ", ".join(f"{k} {p * 100:.1f}%" for k, p in items)
        + "."
        + ("" if not t3 else " DEV Community: " + ", ".join(f"{fmt_num(v)} {lab.lower()}" for lab, v in t3) + ".")
    )
    return slice_svg(h, "\n".join(parts), title="Stats", desc=desc, text=html.unescape(text), theme=theme)

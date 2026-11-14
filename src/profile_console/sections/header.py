"""Header and footer slice builders."""

from __future__ import annotations

from profile_console.config import ProfileInfo
from profile_console.svg import Theme, esc, slice_svg, stagger


def _build_modern_header(profile: ProfileInfo, theme: Theme) -> str:
    """Render header for modern adaptive themes (astrometrics, arcane-architect, studio)."""
    x, m, fl, fr = theme.text_x, theme.margin, theme.frame_left, theme.frame_right
    cyan, amber, green, violet = theme.cyan, theme.amber, theme.green, theme.violet
    bar_left = profile.node_label
    bar_right = profile.status_label
    name = profile.name
    lines = profile.bio
    h = 360

    dotx = fr - 20 - len(bar_right) * 8.2 - 16
    clean_rows: list[str] = []
    for idx, line in enumerate(lines):
        is_last = idx == len(lines) - 1
        dot_color = amber if is_last else cyan
        suffix = f'<tspan class="cy" font-weight="700">{esc(profile.tagline_handle)}</tspan>' if is_last else ""
        clean_rows.append(
            f'<circle cx="{x + 4}" cy="{{y_dot}}" r="2.8" fill="{dot_color}"/>'
            f'<text class="fg" x="{x + 16}" y="{{y}}">{esc(line)}{suffix}</text>'
        )
    desc_parts = []
    y_cur = 216
    for idx, r in enumerate(clean_rows):
        rendered = r.replace("{y}", str(y_cur)).replace("{y_dot}", str(y_cur - 5))
        desc_parts.append(f'<g class="ln" style="animation-delay:{0.45 + idx * 0.14:.2f}s">{rendered}</g>')
        y_cur += 26
    desc_lines = "\n".join(desc_parts)

    # Chaotic Good crest badge (top-right inside header body)
    bx, by, bw, bh = fr - 224, 78, 188, 64
    cx_em, cy_em = bx + 28, by + 32
    crest_accent = cyan if theme.is_studio else amber
    crest = f'''<g class="ln" style="animation-delay:.35s">
<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="{theme.card_rx}" fill="{theme.surface}" stroke="{crest_accent}" stroke-opacity=".6" stroke-width="1.2"/>
<circle cx="{cx_em}" cy="{cy_em}" r="16" fill="{crest_accent}" fill-opacity=".12" stroke="{crest_accent}" stroke-opacity=".6" stroke-width="1"/>
<path d="M{cx_em} {cy_em - 11}L{cx_em + 4} {cy_em - 3}L{cx_em + 11} {cy_em}L{cx_em + 4} {cy_em + 3}L{cx_em} {cy_em + 11}L{cx_em - 4} {cy_em + 3}L{cx_em - 11} {cy_em}L{cx_em - 4} {cy_em - 3}Z" fill="{crest_accent}"/>
<circle cx="{cx_em}" cy="{cy_em}" r="2.5" fill="{theme.surface}"/>
<text x="{bx + 54}" y="{by + 25}" letter-spacing="1.2" class="dim" style="font-size:9.5px">ALIGNMENT</text>
<text x="{bx + 54}" y="{by + 45}" font-weight="700" fill="{crest_accent}" letter-spacing=".8" style="font-size:13px">CHAOTIC GOOD</text>
</g>'''

    bg_motif = ""
    if theme.is_astrometrics:
        bg_motif = f'''<g opacity="{".25" if theme.is_light else ".32"}">
<ellipse cx="{fr - 110}" cy="195" rx="180" ry="62" transform="rotate(-14 {fr - 110} 195)" fill="none" stroke="{cyan}" stroke-width="1" stroke-dasharray="4 5"/>
<ellipse cx="{fr - 110}" cy="195" rx="125" ry="42" transform="rotate(-14 {fr - 110} 195)" fill="none" stroke="{violet}" stroke-width="1"/>
<circle cx="{fr - 265}" cy="222" r="3" fill="{cyan}"/>
<circle cx="{fr - 25}" cy="172" r="2.5" fill="{amber}"/>
</g>'''
        kicker = "OBSERVATORY // IDENTITY LOG" if theme.scifi_labels else "IDENTITY // PROFILE"
        footer_status = "ORBIT NOMINAL · CONTINUOUS EXPLORATION" if theme.scifi_labels else "SYSTEMS NOMINAL · READY"
    elif theme.is_arcane:
        bg_motif = f'''<g opacity="{".22" if theme.is_light else ".28"}">
<circle cx="{fr - 110}" cy="215" r="76" fill="none" stroke="{amber}" stroke-width="1" stroke-dasharray="3 4"/>
<polygon points="{fr - 110},148 {fr - 52},248 {fr - 168},248" fill="none" stroke="{cyan}" stroke-width="1"/>
</g>'''
        kicker = "CHARACTER SHEET // ARCHITECT"
        footer_status = "PROFICIENCY: SYSTEMS & CLOUD"
    else:
        bg_motif = (
            f'<rect x="{fr - 72}" y="170" width="36" height="6" fill="{cyan}"/>'
            f'<rect x="{fr - 72}" y="182" width="24" height="6" fill="{theme.magenta}"/>'
        )
        kicker = "00 // STUDIO SPEC SHEET"
        footer_status = "CHAOTIC GOOD · BUILD & SHIP"

    text = bar_left + bar_right + kicker + name + "ALIGNMENTCHAOTIC GOOD" + "".join(lines) + profile.tagline_handle + footer_status
    accent_bar = cyan if theme.is_studio else amber

    body = f'''<rect x="{fl}" y="{m}" width="{fr - fl}" height="34" fill="{theme.surface}"/>
<line x1="{fl}" y1="{m + 34}" x2="{fr}" y2="{m + 34}" stroke="{theme.border}" stroke-width="1"/>
<rect x="{fl}" y="{m}" width="6" height="34" fill="{accent_bar}"/>
<text x="{fl + 18}" y="{m + 22}" letter-spacing="1" class="cy" style="font-size:12px">{esc(bar_left)}</text>
<text x="{fr - 20}" y="{m + 22}" letter-spacing="1" class="dim" text-anchor="end" style="font-size:12px">{esc(bar_right)}</text>
<circle class="dot" cx="{dotx}" cy="{m + 18}" r="4" fill="{green}"/>
{bg_motif}
<text x="{x}" y="96" letter-spacing="1.8" class="cy" style="font-size:11px">{esc(kicker)}</text>
<text x="{x}" y="162" font-weight="800" letter-spacing="1.5" class="wh" style="font-size:48px">{esc(name)}</text>
<line x1="{x}" y1="180" x2="{x + 140}" y2="180" stroke="{accent_bar}" stroke-width="2.5" stroke-linecap="round"/>
{crest}
{desc_lines}
<g class="ln" style="animation-delay:.95s">
<rect x="{x}" y="302" width="8" height="8" rx="{"1" if theme.is_studio else "4"}" fill="{green}"/>
<text x="{x + 16}" y="310" letter-spacing="1.2" class="dim" style="font-size:11.5px">{esc(footer_status)}</text>
</g>'''
    return slice_svg(
        h,
        body,
        title=profile.header_title,
        desc=profile.header_desc,
        text=text,
        theme=theme,
        top=True,
        weights=(400, 700, 800),
    )


def build_header(profile: ProfileInfo, theme: Theme) -> str:
    """Render the top console header with glitch name and bio lines."""
    if theme.is_modern:
        return _build_modern_header(profile, theme)
    x, m, fl, fr = theme.text_x, theme.margin, theme.frame_left, theme.frame_right
    cyan, magenta, green = theme.cyan, theme.magenta, theme.green
    bar_left, bar_right = profile.node_label, profile.status_label
    name = profile.name
    lines = profile.bio
    text = bar_left + bar_right + name + "$ whoami>>" + "".join(lines) + profile.tagline_handle
    h = 360
    css = """@keyframes type{from{width:0}}
@keyframes flicker{0%{opacity:0}10%{opacity:1}14%{opacity:.2}22%{opacity:1}30%{opacity:.4}40%,100%{opacity:1}}
@keyframes gm{0%,92%,100%{transform:translate(0,0)}93%{transform:translate(5px,-1px)}95%{transform:translate(-3px,1px)}97%{transform:translate(2px,0)}}
@keyframes gc{0%,92%,100%{transform:translate(0,0)}93%{transform:translate(-5px,1px)}95%{transform:translate(4px,-1px)}97%{transform:translate(-2px,0)}}
.typing{animation:type .7s steps(8) .3s both}
.name{animation:flicker .9s linear 1.1s both}
.gm{animation:gm 6s linear 2s infinite}.gc{animation:gc 6s linear 2s infinite}"""
    defs = f"""<pattern id="scan" width="4" height="3" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#000" fill-opacity=".2"/></pattern>
<filter id="tglow" x="-5%" y="-40%" width="110%" height="180%"><feGaussianBlur stdDeviation="9"/></filter>
<filter id="sglow" x="-20%" y="-60%" width="140%" height="220%"><feGaussianBlur stdDeviation="3"/></filter>
<clipPath id="typeclip"><rect class="typing" x="{x}" y="80" width="140" height="30"/></clipPath>"""
    dotx = fr - 20 - len(bar_right) * 8.2 - 16
    rows: list[str | None] = [
        f'<text class="fg" x="{x}" y="{{y}}"><tspan class="cy">&gt;&gt;</tspan> {esc(line)}</text>'
        for line in lines[:-1]
    ]
    if lines:
        rows.append(
            f'<text class="fg" x="{x}" y="{{y}}"><tspan class="cy">&gt;&gt;</tspan> {esc(lines[-1])}'
            f'<tspan class="cy" font-weight="700">{esc(profile.tagline_handle)}</tspan></text>'
        )
    desc_lines, _ = stagger(rows, 218, 24, delay0=1.75, step=0.25)
    body = f'''<rect x="{fl}" y="{m}" width="{fr - fl}" height="34" fill="{cyan}" fill-opacity=".08"/>
<line x1="{fl}" y1="{m + 34}" x2="{fr}" y2="{m + 34}" stroke="{cyan}" stroke-opacity=".5"/>
<text x="{fl + 16}" y="{m + 22}" letter-spacing="1" class="cy" style="font-size:12px">{esc(bar_left)}</text>
<text x="{fr - 20}" y="{m + 22}" letter-spacing="1" class="dim" text-anchor="end" style="font-size:12px">{esc(bar_right)}</text>
<circle class="dot" cx="{dotx}" cy="{m + 18}" r="4" fill="{green}"/>
<circle class="dot" cx="{dotx}" cy="{m + 18}" r="4" fill="{green}" filter="url(#sglow)"/>
<g clip-path="url(#typeclip)"><text x="{x}" y="102" class="dim"><tspan class="gr">$</tspan> whoami</text></g>
<g class="name" font-weight="800" letter-spacing="2" style="font-size:56px">
<text x="{x}" y="172" fill="{cyan}" opacity=".55" filter="url(#tglow)" style="font-size:56px">{esc(name)}</text>
<g class="gm"><text x="{x + 3}" y="172" fill="{magenta}" opacity=".75" style="font-size:56px">{esc(name)}</text></g>
<g class="gc"><text x="{x - 3}" y="172" fill="{cyan}" opacity=".85" style="font-size:56px">{esc(name)}</text></g>
<text x="{x}" y="172" fill="#f0fbff" style="font-size:56px">{esc(name)}</text>
</g>
{desc_lines}
<g class="ln" style="animation-delay:2.8s">
<text x="{x}" y="304" class="gr">$</text>
<rect class="cursor" x="{x + 18}" y="291" width="10" height="17" fill="{cyan}"/>
<rect class="cursor" x="{x + 18}" y="291" width="10" height="17" fill="{cyan}" filter="url(#sglow)"/>
</g>
<rect x="{fl}" y="{m + 35}" width="{fr - fl}" height="{h - m - 35}" fill="url(#scan)"/>'''
    return slice_svg(
        h,
        body,
        title=profile.header_title,
        desc=profile.header_desc,
        text=text,
        theme=theme,
        top=True,
        css=css,
        defs=defs,
        weights=(400, 700, 800),
    )


def build_footer(profile: ProfileInfo, theme: Theme) -> str:
    """Render the bottom console footer slice."""
    x, fr, h = theme.text_x, theme.frame_right, 80
    handle = profile.handle
    if theme.is_modern:
        if theme.is_astrometrics:
            msg = (
                f"SECTOR // {handle.upper()} · END OF TRANSMISSION"
                if theme.scifi_labels
                else f"{handle} · end of transmission"
            )
            tag = "BOLDLY ARCHITECTING"
        elif theme.is_arcane:
            msg = f"{handle} · end of folio"
            tag = "CHAOTIC GOOD"
        else:
            msg = f"{handle} // EOF"
            tag = "CHAOTIC GOOD STUDIO"
        text = msg + tag
        body = (
            f'<circle cx="{x + 4}" cy="38" r="3" fill="{theme.cyan if theme.is_studio else theme.amber}"/>'
            f'<text x="{x + 16}" y="42" class="dim" style="font-size:12px">{esc(msg)}</text>'
            f'<text x="{fr - 36}" y="42" text-anchor="end" fill="{theme.muted}" style="font-size:11px">{esc(tag)}</text>'
        )
        return slice_svg(h, body, title="End of profile", desc="End of transmission.", text=text, theme=theme, bottom=True)
    text = f"$ exit connection to {handle} closed. // EOF"
    body = f'''<text x="{x}" y="30" class="dim"><tspan class="gr">$</tspan> exit</text>
<text x="{x}" y="52" class="dim">connection to <tspan class="cy">{esc(handle)}</tspan> closed. <tspan fill="#484f58">// EOF</tspan></text>'''
    return slice_svg(h, body, title="End of profile", desc="Connection closed.", text=text, theme=theme, bottom=True)

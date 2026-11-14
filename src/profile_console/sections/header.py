"""Header and footer slice builders."""

from __future__ import annotations

from profile_console.config import ProfileInfo
from profile_console.svg import Theme, esc, slice_svg, stagger


def build_header(profile: ProfileInfo, theme: Theme) -> str:
    """Render the top console header with glitch name and bio lines."""
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
    x, h = theme.text_x, 80
    handle = profile.handle
    text = f"$ exit connection to {handle} closed. // EOF"
    body = f'''<text x="{x}" y="30" class="dim"><tspan class="gr">$</tspan> exit</text>
<text x="{x}" y="52" class="dim">connection to <tspan class="cy">{esc(handle)}</tspan> closed. <tspan fill="#484f58">// EOF</tspan></text>'''
    return slice_svg(h, body, title="End of profile", desc="Connection closed.", text=text, theme=theme, bottom=True)

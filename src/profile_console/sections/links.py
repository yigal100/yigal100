"""Links section header and button slice builders."""

from __future__ import annotations

from profile_console.config import LinkItem, ProfileInfo
from profile_console.svg import Theme, esc, faces, heading, slice_svg, visible

BTN_GAP = 39.0


def link_slice_bounds(index: int, total_links: int, total_width: int) -> tuple[int, int]:
    """Return (x0, seg_width) for link slice `index` so all slices tile `total_width` exactly."""
    x0 = round(index * total_width / total_links)
    x1 = round((index + 1) * total_width / total_links)
    return x0, x1 - x0


def _icon_markup(key: str, x: float, y: int, icons: dict[str, str], cyan: str, bg: str = "#03040a", size: int = 18) -> str:
    if key == "linkedin":  # simple generic "in" glyph (LinkedIn isn't in Simple Icons)
        return (
            f'<rect x="{x:.1f}" y="{y}" width="{size}" height="{size}" rx="3" fill="{cyan}"/>'
            f'<text x="{x + size / 2:.1f}" y="{y + size - 4.5}" text-anchor="middle" '
            f'font-weight="700" fill="{bg}" style="font-size:12px">in</text>'
        )
    d = icons[key]
    return f'<path transform="translate({x:.1f} {y}) scale({size / 24})" d="{d}" fill="{cyan}"/>'


def build_links_head(profile: ProfileInfo, theme: Theme) -> str:
    """Render the ~/links section header."""
    x = theme.text_x
    if theme.is_astrometrics:
        sec_title = theme.section_label("links", "subspace-relays")
        sub = f"active relays · {profile.handle}" if theme.scifi_labels else f"channels · {profile.handle}"
        body = (
            heading(44, sec_title, "// 01", theme)
            + f'''
<g class="ln" style="animation-delay:.15s"><text x="{x}" y="96" class="dim"><tspan class="cy">›</tspan> {esc(sub)}</text></g>'''
        )
        return slice_svg(
            120,
            body,
            title="Links",
            desc="Where to find me",
            text=f"{sec_title}01{sub}",
            theme=theme,
        )
    body = (
        heading(44, "links", "// 01", theme)
        + f'''
<g class="ln" style="animation-delay:.15s"><text x="{x}" y="96" class="dim"><tspan class="gr">$</tspan> ping {esc(profile.handle)} --all-channels</text></g>'''
    )
    return slice_svg(
        120,
        body,
        title="Links",
        desc="Where to find me",
        text=f"~/links// 01$ ping {profile.handle} --all-channels",
        theme=theme,
    )


def build_link_button(
    index: int,
    link: LinkItem,
    total_links: int,
    icons: dict[str, str],
    theme: Theme,
) -> str:
    """Render a single clickable link button slice scaled to `total_links`."""
    h = 80
    x0, seg = link_slice_bounds(index, total_links, theme.width)
    content_w = (theme.frame_right - 36) - theme.text_x
    btn_w = (content_w - (total_links - 1) * BTN_GAP) / total_links
    lx = theme.text_x + index * (btn_w + BTN_GAP) - x0
    first, last = index == 0, index == total_links - 1
    fl, fr, cyan = theme.frame_left, theme.frame_right, theme.cyan
    bg0 = fl - x0 if first else 0
    bg1 = fr - x0 if last else seg
    rails = (f"M{fl - x0} 0V{h}" if first else "") + (f"M{fr - x0} 0V{h}" if last else "")
    glow = (f"M{fl - x0} -40V{h + 40}" if first else "") + (f"M{fr - x0} -40V{h + 40}" if last else "")
    by, bh, cut = 12, 56, 12
    text = link.label + link.handle + "in"
    icon_main = _icon_markup(link.icon, lx + 12, by + 11, icons, cyan, bg=theme.bg)

    if theme.is_astrometrics:
        conn_left = (
            f'<line x1="0" y1="{by + bh / 2}" x2="{lx:.1f}" y2="{by + bh / 2}" '
            f'stroke="{theme.border}" stroke-width="1.2" stroke-dasharray="3 3"/>'
            if not first
            else ""
        )
        conn_right = (
            f'<line x1="{lx + btn_w:.1f}" y1="{by + bh / 2}" x2="{seg}" y2="{by + bh / 2}" '
            f'stroke="{theme.border}" stroke-width="1.2" stroke-dasharray="3 3"/>'
            if not last
            else ""
        )
        body = f'''<g class="ln" style="animation-delay:{0.25 + index * 0.08:.2f}s">
{conn_left}{conn_right}
<rect x="{lx:.1f}" y="{by}" width="{btn_w:.1f}" height="{bh}" rx="10" fill="{theme.surface}" stroke="{theme.border}" stroke-width="1.2"/>
<circle cx="{lx:.1f}" cy="{by + bh / 2}" r="3.5" fill="{cyan}"/>
{icon_main}
<text x="{lx + 38:.1f}" y="{by + 25}" font-weight="700" class="wh" style="font-size:13px">{esc(link.label)}</text>
<text x="{lx + 12:.1f}" y="{by + 46}" class="dim" style="font-size:10px">{esc(link.handle)}</text>
</g>'''
        rail_color = theme.border if theme.is_light else cyan
        rail_op = "1" if theme.is_light else ".45"
        glow_markup = (
            ""
            if theme.is_light or not glow
            else f'<path d="{glow}" fill="none" stroke="{cyan}" stroke-width="2" opacity=".25" filter="url(#glow)"/>'
        )
        rail_markup = (
            f'<path d="{rails}" fill="none" stroke="{rail_color}" stroke-opacity="{rail_op}" stroke-width="1.2"/>'
            if rails
            else ""
        )
        dot_op = ".12" if theme.is_light else ".14"
        grid_op = ".06" if theme.is_light else ".045"
        grid_def = (
            f'<pattern id="grid" x="{(-x0) % 40}" width="40" height="40" patternUnits="userSpaceOnUse">'
            f'<path d="M40 0H0V40" fill="none" stroke="{cyan}" stroke-opacity="{grid_op}"/>'
            f'<circle cx="0" cy="0" r="1" fill="{cyan}" fill-opacity="{dot_op}"/></pattern>'
        )
    else:
        box = f"M{lx:.1f} {by}H{lx + btn_w - cut:.1f}L{lx + btn_w:.1f} {by + cut}V{by + bh}H{lx:.1f}Z"
        body = f'''<g class="ln" style="animation-delay:{0.25 + index * 0.08:.2f}s">
<path d="{box}" fill="{cyan}" fill-opacity=".05"/>
<path d="{box}" fill="none" stroke="{cyan}" stroke-opacity=".55"/>
<path d="M{lx + btn_w - cut:.1f} {by}L{lx + btn_w:.1f} {by + cut}" stroke="{cyan}" stroke-width="2"/>
<g filter="url(#g)" opacity=".5">{icon_main}</g>
{icon_main}
<text x="{lx + 38:.1f}" y="{by + 25}" font-weight="700" class="cy" style="font-size:13px">{esc(link.label)}</text>
<text x="{lx + 12:.1f}" y="{by + 46}" class="dim" style="font-size:10px">{esc(link.handle)}</text>
</g>'''
        glow_markup = (
            f'<path d="{glow}" fill="none" stroke="{cyan}" stroke-width="3" opacity=".55" filter="url(#glow)"/>'
            if glow
            else ""
        )
        rail_markup = f'<path d="{rails}" fill="none" stroke="{cyan}" stroke-width="1.2"/>' if rails else ""
        grid_def = f'<pattern id="grid" x="{(-x0) % 40}" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="{cyan}" stroke-opacity=".06"/></pattern>'

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{seg}" height="{h}" viewBox="0 0 {seg} {h}" role="img" aria-labelledby="t d">
<title id="t">{esc(link.label)}</title>
<desc id="d">{esc(link.label)}: {esc(link.url)}</desc>
<style>
{faces(text + visible(body), theme.fonts_dir)}
{theme.base_css}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
</style>
<defs>
{grid_def}
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="6"/></filter>
<filter id="g" x="-20%" y="-60%" width="140%" height="220%"><feGaussianBlur stdDeviation="4"/></filter>
</defs>
{glow_markup}
<rect x="{bg0}" y="0" width="{bg1 - bg0}" height="{h}" fill="{theme.bg}"/>
<rect x="{bg0}" y="0" width="{bg1 - bg0}" height="{h}" fill="url(#grid)"/>
{body}
{rail_markup}
</svg>
'''

"""Featured projects section header and card slice builders."""

from __future__ import annotations

import textwrap

from profile_console.config import ProjectItem
from profile_console.svg import Theme, esc, half_slice, heading, slice_svg

CARD_H = 200


def build_projects_head(theme: Theme) -> str:
    """Render the ~/projects section header."""
    if theme.is_astrometrics:
        sec_title = theme.section_label("projects", "missions")
        sub = "active mission dossiers" if theme.scifi_labels else "featured repositories"
        body = (
            heading(44, sec_title, "// 04", theme)
            + f'''
<g class="ln" style="animation-delay:.2s"><text x="{theme.text_x}" y="96" class="dim"><tspan class="cy">›</tspan> {esc(sub)}</text></g>'''
        )
        return slice_svg(120, body, title="Projects", desc="Projects", text=f"{sec_title}04{sub}", theme=theme)
    body = (
        heading(44, "projects", "// 04", theme)
        + f'''
<g class="ln" style="animation-delay:.2s"><text x="{theme.text_x}" y="96" class="dim"><tspan class="gr">$</tspan> ls -l ~/projects</text></g>'''
    )
    return slice_svg(120, body, title="Projects", desc="Projects", text="~/projects// 02$ ls -l", theme=theme)


def build_card(
    project: ProjectItem,
    side: str,
    delay: float,
    theme: Theme,
    stars: dict[str, int] | None = None,
) -> str:
    """Render a project card slice ('L', 'R', or 'F' for full-width odd final card)."""
    star_count = stars.get(project.slug, project.stars) if stars else project.stars
    tag_color = theme.resolve_color(project.tag_color)
    cyan = theme.cyan
    if side == "F":
        x0 = theme.text_x
        cw = (theme.frame_right - 36) - theme.text_x
        wrap_chars = 92
    else:
        x0 = 52 if side == "L" else 10  # card box, 378 wide, 20px gutter between the two cards
        cw = 378
        wrap_chars = 43
    y0, ch = 12, 176
    pad = 18
    tx = x0 + pad
    cut = 16
    lines = textwrap.wrap(project.desc, wrap_chars)
    assert len(lines) <= 3, lines
    tag_w = len(project.tag) * 7.6 + 16
    title_w = len(project.name) * 10.2
    desc = "\n".join(
        f'<text x="{tx}" y="{100 + i * 20}" class="fg" style="font-size:13px">{esc(line)}</text>'
        for i, line in enumerate(lines)
    )
    sx = x0 + cw - pad
    star = (
        f'<path transform="translate({sx - len(str(star_count)) * 7.2 - 20} 158) scale(.55)" '
        f'd="M10 0l2.9 6.6 7.1.6-5.4 4.7 1.6 7L10 15.2 3.8 18.9l1.6-7L0 7.2l7.1-.6z" fill="{theme.amber}"/>'
    )
    if theme.is_astrometrics:
        body = f'''<g class="ln" style="animation-delay:{delay:.2f}s">
<rect x="{x0}" y="{y0}" width="{cw}" height="{ch}" rx="10" fill="{theme.surface}" stroke="{theme.border}" stroke-width="1"/>
<rect x="{x0 + 14}" y="{y0}" width="56" height="3.5" rx="1.75" fill="{tag_color}"/>
<circle cx="{sx - 6}" cy="{y0 + 26}" r="5" fill="none" stroke="{cyan}" stroke-opacity=".45" stroke-width="1"/>
<circle cx="{sx - 6}" cy="{y0 + 26}" r="1.8" fill="{cyan}"/>
<text x="{tx}" y="{y0 + 34}" font-weight="700" class="wh" style="font-size:17px">{esc(project.name)}</text>
<path d="M{tx + title_w + 11} {y0 + 31}l8-8M{tx + title_w + 13} {y0 + 23}h6v6" fill="none" stroke="{cyan}" stroke-width="1.6"/>
<rect x="{tx}" y="{y0 + 46}" width="{tag_w}" height="18" rx="4" fill="{tag_color}" fill-opacity=".12" stroke="{tag_color}" stroke-opacity=".6"/>
<text x="{tx + 8}" y="{y0 + 59}" letter-spacing="1" fill="{tag_color}" font-weight="700" style="font-size:10.5px">{esc(project.tag)}</text>
{desc}
<text x="{tx}" y="{y0 + 158}" class="dim" style="font-size:12px">{esc(project.stack)}</text>
{star}
<text x="{sx}" y="{y0 + 158}" text-anchor="end" class="dim" style="font-size:12px">{star_count}</text>
</g>'''
    else:
        box = f"M{x0} {y0}H{x0 + cw - cut}L{x0 + cw} {y0 + cut}V{y0 + ch}H{x0 + cut}L{x0} {y0 + ch - cut}Z"
        body = f'''<g class="ln" style="animation-delay:{delay:.2f}s">
<path d="{box}" fill="{cyan}" fill-opacity=".035"/>
<path d="{box}" fill="none" stroke="{cyan}" stroke-opacity=".4"/>
<path d="M{x0 + cw - cut} {y0}L{x0 + cw} {y0 + cut}" stroke="{cyan}" stroke-width="2"/>
<text x="{tx}" y="{y0 + 34}" font-weight="700" fill="{cyan}" filter="url(#g)" opacity=".6" style="font-size:17px">{esc(project.name)}</text>
<text x="{tx}" y="{y0 + 34}" font-weight="700" class="cy" style="font-size:17px">{esc(project.name)}</text>
<path d="M{tx + title_w + 11} {y0 + 31}l8-8M{tx + title_w + 13} {y0 + 23}h6v6" fill="none" stroke="{cyan}" stroke-width="1.6"/>
<rect x="{tx}" y="{y0 + 46}" width="{tag_w}" height="18" fill="none" stroke="{tag_color}" stroke-opacity=".8"/>
<text x="{tx + 8}" y="{y0 + 59}" letter-spacing="1" fill="{tag_color}" style="font-size:11px">{esc(project.tag)}</text>
{desc}
<text x="{tx}" y="{y0 + 158}" class="dim" style="font-size:12px">{esc(project.stack)}</text>
{star}
<text x="{sx}" y="{y0 + 158}" text-anchor="end" class="dim" style="font-size:12px">{star_count}</text>
</g>'''
    text = project.name + project.tag + project.desc + project.stack + str(star_count)
    title = project.name
    card_desc = f"{project.name}: {project.desc} Built with {project.stack.replace(' · ', ', ')}. {star_count} stars."
    if side == "F":
        return slice_svg(CARD_H, body, title=title, desc=card_desc, text=text, theme=theme)
    return half_slice(CARD_H, side, body, title=title, desc=card_desc, text=text, theme=theme)

"""Recommended reading section header and row slice builders."""

from __future__ import annotations

from profile_console.config import ReadingItem
from profile_console.svg import Theme, esc, heading, slice_svg


def build_reading_head(theme: Theme, section_num: int = 6) -> str:
    """Render the ~/reading section header."""
    num = f"// {section_num:02d}"
    sec_title = theme.section_label("reading")
    if theme.is_modern:
        sub = "recommended reading & transmissions" if theme.scifi_labels else "recommended reading & references"
        body = (
            heading(44, sec_title, num, theme)
            + f'''
<g class="ln" style="animation-delay:.15s"><text x="{theme.text_x}" y="96" class="dim"><tspan class="cy">›</tspan> {esc(sub)}</text></g>'''
        )
        return slice_svg(
            120,
            body,
            title="Recommended Reading",
            desc="Recommended reading and references",
            text=f"{sec_title}{section_num:02d}{sub}",
            theme=theme,
        )
    body = (
        heading(44, sec_title, num, theme)
        + f'''
<g class="ln" style="animation-delay:.15s"><text x="{theme.text_x}" y="96" class="dim"><tspan class="gr">$</tspan> cat ~/reading/recommended.list <tspan fill="{theme.muted}"># curated</tspan></text></g>'''
    )
    return slice_svg(
        120,
        body,
        title="Recommended Reading",
        desc="Recommended reading and references",
        text=f"~/{sec_title}{num}$ cat ~/reading/recommended.list # curated",
        theme=theme,
    )


def build_reading_row(item: ReadingItem, index: int, theme: Theme) -> str:
    """Render a single recommended reading row slice."""
    x, fr, cyan = theme.text_x, theme.frame_right, theme.cyan
    rx = fr - 36
    ax = rx - 10
    tx = x + 22
    source = item.source.strip()
    source_x = ax - 18
    max_title = max(36, 72 - (len(source) + 3 if source else 0))
    shown = item.title if len(item.title) <= max_title else item.title[: max_title - 1].rstrip(" .,:;") + "…"

    if theme.is_modern:
        row_bg = (
            f'<rect x="{x - 10}" y="4" width="{rx - x + 20}" height="32" rx="{max(theme.card_rx - 2, 2)}" '
            f'fill="{theme.surface}" stroke="{theme.border}" stroke-width=".8"/>'
            if index % 2 == 0
            else ""
        )
        marker = f'<circle cx="{x + 6}" cy="20" r="2.5" fill="{cyan}"/>'
    else:
        row_bg = (
            f'<rect x="{x - 10}" y="4" width="{rx - x + 20}" height="32" '
            f'fill="{cyan}" fill-opacity="{".04" if index % 2 == 0 else "0"}"/>'
        )
        marker = f'<text x="{x + 4}" y="25" class="cy" style="font-size:13px">›</text>'

    source_el = (
        f'<text x="{source_x}" y="25" text-anchor="end" class="dim" style="font-size:12.5px">{esc(source)}</text>'
        if source
        else ""
    )

    body = f'''<g class="ln" style="animation-delay:{0.2 + index * 0.08:.2f}s">
{row_bg}
{marker}
<text x="{tx}" y="25" class="fg" style="font-size:14px">{esc(shown)}</text>
{source_el}
<path d="M{ax - 6} 25l8-8M{ax - 4} 17h6v6" fill="none" stroke="{cyan}" stroke-width="1.5"/>
</g>'''
    desc = f"{item.title} ({source})." if source else item.title
    return slice_svg(
        40,
        body,
        title=item.title,
        desc=desc,
        text=f"›{shown}{source}",
        theme=theme,
    )

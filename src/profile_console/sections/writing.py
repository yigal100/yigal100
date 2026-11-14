"""Writing and article row slice builders."""

from __future__ import annotations

from profile_console.svg import Theme, esc, heading, slice_svg

HEART = "M8 14.2 6.9 13.2C3 9.7.5 7.4.5 4.6.5 2.3 2.3.5 4.6.5c1.3 0 2.5.6 3.4 1.6C8.9 1.1 10.1.5 11.4.5c2.3 0 4.1 1.8 4.1 4.1 0 2.8-2.5 5.1-6.4 8.6z"
BUBBLE = "M1.5 1.5h13v9h-7l-3.5 3v-3h-2.5z"


def build_writing_head(theme: Theme) -> str:
    """Render the ~/writing section header."""
    if theme.is_astrometrics:
        sec_title = theme.section_label("writing", "subspace-log")
        sub = "recent transmissions & insights" if theme.scifi_labels else "recommended reading & insights"
        body = (
            heading(44, sec_title, "// 06", theme)
            + f'''
<g class="ln" style="animation-delay:.15s"><text x="{theme.text_x}" y="96" class="dim"><tspan class="cy">›</tspan> {esc(sub)}</text></g>'''
        )
        return slice_svg(
            120,
            body,
            title="Writing & Insights",
            desc="Articles and reading list",
            text=f"{sec_title}06{sub}",
            theme=theme,
        )
    body = (
        heading(44, "writing", "// 06", theme)
        + f'''
<g class="ln" style="animation-delay:.15s"><text x="{theme.text_x}" y="96" class="dim"><tspan class="gr">$</tspan> tail -n 5 ~/reading/insights.log <tspan fill="#484f58"># highlights</tspan></text></g>'''
    )
    return slice_svg(
        120,
        body,
        title="Writing & Insights",
        desc="Articles and reading list",
        text="~/writing// 06$ tail -n 5 ~/reading/insights.log # highlights",
        theme=theme,
    )


def build_article_row(article: dict, index: int, theme: Theme) -> str:
    """Render a single article highlight row slice."""
    x, fr, cyan, magenta = theme.text_x, theme.frame_right, theme.cyan, theme.magenta
    date = article["published_at"][:10]
    title = article["title"]
    maxc = 58
    shown = title if len(title) <= maxc else title[: maxc - 1].rstrip(" .,:;") + "…"
    tx = x + 112
    rx = fr - 36
    rc, cc = str(article["reactions"]), str(article["comments"])
    # right block:  ♥ 169   ▭ 218   ↗
    ax = rx - 10
    cx_num = ax - 18
    cx_icon = cx_num - 3 * 7.8 - 22  # fixed columns (room for 3 digits) so rows line up
    rx_num = cx_icon - 16
    rx_icon = rx_num - 3 * 7.8 - 22
    if theme.is_astrometrics:
        row_bg = (
            f'<rect x="{x - 10}" y="4" width="{rx - x + 20}" height="32" rx="6" fill="{theme.surface}" stroke="{theme.border}" stroke-width=".8"/>'
            if index % 2 == 0
            else ""
        )
        marker = f'<circle cx="{x + 95}" cy="20" r="2.5" fill="{cyan}"/>'
    else:
        row_bg = f'<rect x="{x - 10}" y="4" width="{rx - x + 20}" height="32" fill="{cyan}" fill-opacity="{".04" if index % 2 == 0 else "0"}"/>'
        marker = f'<text x="{x + 94}" y="25" class="cy" style="font-size:13px">›</text>'
    body = f'''<g class="ln" style="animation-delay:{0.2 + index * 0.08:.2f}s">
{row_bg}
<text x="{x}" y="25" class="dim" style="font-size:13px">{date}</text>
{marker}
<text x="{tx}" y="25" class="fg" style="font-size:14px">{esc(shown)}</text>
<path transform="translate({rx_icon:.1f} 13) scale(.8)" d="{HEART}" fill="{magenta}"/>
<text x="{rx_num:.1f}" y="25" text-anchor="end" class="dim" style="font-size:13px">{rc}</text>
<path transform="translate({cx_icon:.1f} 13) scale(.8)" d="{BUBBLE}" fill="none" stroke="{cyan}" stroke-width="1.5" stroke-linejoin="round"/>
<text x="{cx_num:.1f}" y="25" text-anchor="end" class="dim" style="font-size:13px">{cc}</text>
<path d="M{ax - 6} 25l8-8M{ax - 4} 17h6v6" fill="none" stroke="{cyan}" stroke-width="1.5"/>
</g>'''
    text = date + "›" + shown + rc + cc
    return slice_svg(
        40,
        body,
        title=title,
        desc=f"{title}. Published {date}. {rc} reactions, {cc} comments.",
        text=text,
        theme=theme,
    )


def build_writing_more(theme: Theme) -> str:
    """Render the 'read articles & insights' link slice."""
    x, cyan = theme.text_x, theme.cyan
    if theme.is_astrometrics:
        body = f'''<g class="ln" style="animation-delay:.7s">
<text x="{x}" y="26" style="font-size:13px"><tspan class="am">›</tspan><tspan class="cy"> read articles &amp; insights</tspan></text>
<path d="M{x + 224} 26l8-8M{x + 226} 18h6v6" fill="none" stroke="{cyan}" stroke-width="1.5"/>
</g>'''
        return slice_svg(
            40,
            body,
            title="All articles",
            desc="Read articles and insights",
            text="› read articles & insights",
            theme=theme,
        )
    body = f'''<g class="ln" style="animation-delay:.7s">
<text x="{x}" y="26" style="font-size:13px"><tspan class="gr">&gt;&gt;</tspan><tspan class="cy"> read articles &amp; insights</tspan></text>
<path d="M{x + 240} 26l8-8M{x + 242} 18h6v6" fill="none" stroke="{cyan}" stroke-width="1.5"/>
</g>'''
    return slice_svg(
        40,
        body,
        title="All articles",
        desc="Read articles and insights",
        text=">> read articles & insights",
        theme=theme,
    )

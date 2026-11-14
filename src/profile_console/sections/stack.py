"""Tech stack loadout slice builder."""

from __future__ import annotations

from profile_console.config import StackCategory
from profile_console.svg import Theme, esc, heading, slice_svg, up40


def build_stack(stack: tuple[StackCategory, ...], theme: Theme) -> str:
    """Render the ~/stack section with dynamic category column width and pill wrapping."""
    x0, cyan = theme.text_x, theme.cyan
    max_x = theme.frame_right - 36
    parts = [
        heading(44, "stack", "// 05", theme),
        f'<g class="ln" style="animation-delay:.15s"><text x="{x0}" y="96" class="dim">'
        '<tspan class="gr">$</tspan> scan --loadout --top-level</text></g>',
    ]
    y, rowh, wrap_h = 126, 44, 38
    cw = 0.6 * 13  # char advance at 13px
    max_cat_len = max((len(c.category) for c in stack), default=0)
    cat_col_w = max(104.0, max_cat_len * cw + 16)
    arrow_x = x0 + cat_col_w
    pills_x = arrow_x + 20

    for r, cat in enumerate(stack):
        parts.append(f'<g class="ln" style="animation-delay:{0.25 + r * 0.1:.2f}s">')
        parts.append(f'<text x="{x0}" y="{y + 20}" class="dim" style="font-size:13px">{esc(cat.category)}</text>')
        parts.append(f'<text x="{arrow_x:.1f}" y="{y + 20}" class="cy" style="font-size:13px">›</text>')
        x = pills_x
        for item in cat.items:
            w = len(item) * cw + 26
            if x > pills_x and x + w > max_x:
                x = pills_x
                y += wrap_h
            parts.append(
                f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="30" '
                f'fill="{cyan}" fill-opacity=".06" stroke="{cyan}" stroke-opacity=".55"/>'
            )
            parts.append(f'<path d="M{x:.1f} {y + 8}V{y}H{x + 8:.1f}" fill="none" stroke="{cyan}" stroke-width="2"/>')
            parts.append(
                f'<text x="{x + 13:.1f}" y="{y + 20}" font-weight="700" class="cy" '
                f'style="font-size:13px">{esc(item)}</text>'
            )
            x += w + 10
        parts.append("</g>")
        y += rowh
    h = up40(y + 10)
    text = "~/stack// 05$ scan --loadout --top-level›" + "".join(c.category + "".join(c.items) for c in stack)
    desc = "Tech stack. " + " ".join(f"{c.category}: {', '.join(c.items)}." for c in stack)
    return slice_svg(h, "\n".join(parts), title="Tech stack", desc=desc, text=text, theme=theme)

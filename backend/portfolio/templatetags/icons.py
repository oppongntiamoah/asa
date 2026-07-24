"""
A small hand-authored set of stroke icons for the nav — one place to edit
a glyph instead of hunting down every inline <svg> copy scattered across
base.html. Deliberately not an icon font/library pulled from a CDN, per
the no-heavy-JS/low-bandwidth constraint the rest of the app follows.

Usage: {% icon "home" class="w-5 h-5" %}
"""
from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()

# 24x24 viewBox, stroke-based outline paths.
_PATHS = {
    "home": '<path d="M3 10.5 12 3l9 7.5" /><path d="M5 9.5V20a1 1 0 0 0 1 1h4v-6h4v6h4a1 1 0 0 0 1-1V9.5" />',
    "holdings": '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2" />',
    "transactions": '<path d="M4 7h13l-3-3M20 17H7l3 3" />',
    "statements": '<path d="M7 3h7l5 5v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" /><path d="M14 3v5h5M9.5 16.5 12 14l2.5 2.5M12 14v7" />',
    "watchlist": '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z" /><circle cx="12" cy="12" r="3" />',
    "dividends": '<rect x="2" y="6" width="20" height="12" rx="2" /><circle cx="12" cy="12" r="3" /><path d="M6 6v.01M18 17.99V18" />',
    "analysis": '<path d="M3 3v16a2 2 0 0 0 2 2h16" /><path d="m7 14 4-4 3 3 5-6" />',
    "market": '<circle cx="12" cy="12" r="9" /><path d="M3 12h18M12 3a14 14 0 0 1 0 18 14 14 0 0 1 0-18Z" />',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2" /><path d="M8 3v4M16 3v4M3 10h18" />',
    "news": '<path d="M5 4h11a2 2 0 0 1 2 2v13a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V4Z" /><path d="M18 9h1a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H8" /><path d="M8 8h6M8 12h6M8 16h3" />',
    "pricing": '<rect x="2" y="5" width="20" height="14" rx="2" /><path d="M2 10h20M6 15h4" />',
    "settings": '<circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.7 1.7 0 0 0 .34 1.87l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.7 1.7 0 0 0-1.87-.34 1.7 1.7 0 0 0-1.04 1.56V21a2 2 0 0 1-4 0v-.09A1.7 1.7 0 0 0 8.96 19a1.7 1.7 0 0 0-1.87.34l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.7 1.7 0 0 0 4.6 15a1.7 1.7 0 0 0-1.56-1.04H3a2 2 0 0 1 0-4h.09A1.7 1.7 0 0 0 4.6 8.96a1.7 1.7 0 0 0-.34-1.87l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.7 1.7 0 0 0 8.96 4.6a1.7 1.7 0 0 0 1.04-1.56V3a2 2 0 0 1 4 0v.09A1.7 1.7 0 0 0 15 4.6a1.7 1.7 0 0 0 1.87-.34l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.7 1.7 0 0 0 19.4 8.96a1.7 1.7 0 0 0 1.56 1.04H21a2 2 0 0 1 0 4h-.09A1.7 1.7 0 0 0 19.4 15Z" />',
    "support": '<circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="3.5" /><path d="m5 5 3.5 3.5M19 5l-3.5 3.5M5 19l3.5-3.5M19 19l-3.5-3.5" />',
    "sun": '<circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />',
    "moon": '<path d="M20 14.5A8.5 8.5 0 1 1 9.5 4a7 7 0 0 0 10.5 10.5Z" />',
    "auto": '<rect x="3" y="4" width="18" height="12" rx="1.5" /><path d="M8 20h8M12 16v4" />',
    "eye": '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z" /><circle cx="12" cy="12" r="3" />',
    "eye-off": '<path d="M3 3l18 18" /><path d="M10.6 5.2A10.6 10.6 0 0 1 12 5c6.5 0 10 7 10 7a15.3 15.3 0 0 1-3.4 4.3M6.6 6.6C3.9 8.3 2 12 2 12s3.5 7 10 7a10.4 10.4 0 0 0 3.4-.6" /><path d="M9.5 9.9a3 3 0 0 0 4.2 4.2" />',
    "logout": '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><path d="M16 17l5-5-5-5M21 12H9" />',
    "chevron-down": '<path d="m6 9 6 6 6-6" />',
    "menu": '<path d="M4 6h16M4 12h16M4 18h16" />',
    "close": '<path d="M18 6 6 18M6 6l12 12" />',
    "plus": '<path d="M12 5v14M5 12h14" />',
}


# Tailwind's w-*/h-* utilities set the real rendered size, but SVGs have no
# intrinsic dimensions of their own — if the Play CDN hiccups (or is
# blocked), a class-only <svg> has nothing to fall back on and stretches to
# fill its container instead of just disappearing quietly. Explicit
# width/height attributes give it a sane pixel size independent of Tailwind
# ever loading; Tailwind's classes still take over normally once it does.
_SIZE_PX = {"w-4": 16, "w-5": 20}


@register.simple_tag
def icon(name, css_class="w-5 h-5"):
    d = _PATHS.get(name)
    if d is None:
        return ""
    px = next((v for k, v in _SIZE_PX.items() if k in css_class), 20)
    return format_html(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{}" height="{}" class="{}" '
        'fill="none" stroke="currentColor" stroke-width="1.75" '
        'stroke-linecap="round" stroke-linejoin="round">{}</svg>',
        px,
        px,
        css_class,
        mark_safe(d),
    )

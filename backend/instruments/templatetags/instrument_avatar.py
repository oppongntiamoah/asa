"""
GSE doesn't publish instrument logos anywhere scrapeable, and guessing at
company domains/brand marks for a financial app risks showing the wrong
mark next to real money figures — worse than showing none. So every
instrument gets a deterministic "initials badge" (same idea as GitHub/Slack
default avatars): a stable hue derived from the ticker so a given ticker
always renders the same color, with 1-2 letters on top. If an admin
uploads a confirmed-real logo (Instrument.logo), that's used instead.

Colors are inline styles, not Tailwind classes — classes built from a
runtime hash never appear literally in template source, so a
statically-scanned Tailwind build (unlike the Play CDN this app actually
loads) would never generate CSS for them.
"""
from django import template

from instruments.services import ticker_hue

register = template.Library()

_SIZE_CLASSES = {
    "xs": "w-6 h-6 text-[10px]",
    "sm": "w-8 h-8 text-xs",
    "md": "w-10 h-10 text-sm",
    "lg": "w-14 h-14 text-lg",
}


def _initials_for(ticker: str, name: str) -> str:
    ticker = (ticker or "").strip()
    if len(ticker) >= 2:
        return ticker[:2].upper()
    if name:
        words = name.split()
        return "".join(w[0] for w in words[:2]).upper()
    return "?"


@register.inclusion_tag("instruments/_avatar.html")
def instrument_avatar(instrument, size="sm"):
    ticker = getattr(instrument, "ticker", "") or ""
    hue = ticker_hue(ticker)
    return {
        "instrument": instrument,
        "size_classes": _SIZE_CLASSES.get(size, _SIZE_CLASSES["sm"]),
        "initials": _initials_for(ticker, getattr(instrument, "name", "")),
        "bg_color": f"hsl({hue}, 58%, 40%)",
    }

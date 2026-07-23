"""
Market-wide (not portfolio-scoped) instrument queries — used by the public
landing page and the per-ticker detail page. Contrast with
portfolio.services, which only ever looks at a single user's holdings.
"""
from .models import Instrument, PriceBar


def market_snapshot(limit=5):
    """
    Day-over-day movers across every actively-tracked instrument, plus the
    most recent trade date in the database. Used on the public landing
    page — deliberately has no notion of "live": it's the latest daily
    close GSE published, which is exactly what SikaTrack ever has.
    """
    latest_bar = PriceBar.objects.order_by("-trade_date").first()
    if latest_bar is None:
        return {"as_of": None, "instrument_count": 0, "gainers": [], "losers": []}

    rows = []
    instruments = Instrument.objects.filter(is_active=True).prefetch_related("price_bars")
    for instrument in instruments:
        bars = list(instrument.price_bars.all()[:2])
        if len(bars) < 2 or bars[0].close_price is None or bars[1].close_price in (None, 0):
            continue
        change_pct = (bars[0].close_price - bars[1].close_price) / bars[1].close_price * 100
        rows.append({
            "instrument": instrument,
            "close_price": bars[0].close_price,
            "change_pct": change_pct,
            "trade_date": bars[0].trade_date,
        })

    rows.sort(key=lambda r: r["change_pct"], reverse=True)
    gainers = [r for r in rows if r["change_pct"] > 0][:limit]
    losers = sorted([r for r in rows if r["change_pct"] < 0], key=lambda r: r["change_pct"])[:limit]

    return {
        "as_of": latest_bar.trade_date,
        "instrument_count": Instrument.objects.filter(is_active=True).count(),
        "gainers": gainers,
        "losers": losers,
    }


def price_history(instrument, days=None):
    """Chronological (oldest-first) close-price series for charting."""
    qs = instrument.price_bars.order_by("trade_date")
    if days:
        qs = qs.order_by("-trade_date")[:days]
        return list(reversed(list(qs)))
    return list(qs)

from datetime import date, timedelta

from .models import WatchlistItem


def watchlist_rows(user):
    items = WatchlistItem.objects.filter(user=user).select_related("instrument")
    one_year_ago = date.today() - timedelta(days=365)

    rows = []
    for item in items:
        bars = list(item.instrument.price_bars.all()[:2])
        latest = bars[0] if bars else None
        change_pct = None
        if len(bars) == 2 and bars[1].close_price:
            change_pct = (bars[0].close_price - bars[1].close_price) / bars[1].close_price * 100

        year_bars = item.instrument.price_bars.filter(trade_date__gte=one_year_ago)
        high_52w = max((b.close_price for b in year_bars), default=None)
        low_52w = min((b.close_price for b in year_bars), default=None)

        rows.append({
            "item": item,
            "instrument": item.instrument,
            "current_price": latest.close_price if latest else None,
            "price_date": latest.trade_date if latest else None,
            "change_pct": change_pct,
            "high_52w": high_52w,
            "low_52w": low_52w,
        })
    return rows

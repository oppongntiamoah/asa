"""
Market-wide (not portfolio-scoped) instrument queries — used by the public
landing page and the per-ticker detail page. Contrast with
portfolio.services, which only ever looks at a single user's holdings.
"""
from .models import Instrument, PriceBar


def ticker_hue(ticker: str) -> int:
    """Deterministic 0-359 hue from a ticker string — same ticker always
    gets the same color, used for both the instrument's avatar badge and
    matching chart segments so a ticker looks the same everywhere it
    appears."""
    h = 0
    for ch in ticker or "":
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    return h % 360


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


def top_movers(days=30, limit=10):
    """Active instruments ranked by close-price % change over the trailing
    `days` calendar days. Returns (gainers, losers), each sorted with the
    biggest mover first. Skips instruments without a bar that old."""
    from .analytics import period_return

    rows = []
    for instrument in Instrument.objects.filter(is_active=True):
        bars = list(instrument.price_bars.order_by("trade_date"))
        if len(bars) < 2:
            continue
        pct = period_return(bars, days)
        if pct is None:
            continue
        rows.append({
            "instrument": instrument,
            "change_pct": pct,
            "close_price": bars[-1].close_price,
            "trade_date": bars[-1].trade_date,
        })

    gainers = sorted((r for r in rows if r["change_pct"] > 0), key=lambda r: r["change_pct"], reverse=True)[:limit]
    losers = sorted((r for r in rows if r["change_pct"] < 0), key=lambda r: r["change_pct"])[:limit]
    return gainers, losers


def most_traded(days=30, limit=10):
    """Active instruments ranked by average daily shares traded over the
    trailing window, counting only bars that carry a volume figure."""
    rows = []
    for instrument in Instrument.objects.filter(is_active=True):
        bars = instrument.price_bars.order_by("-trade_date")[:days]
        volumes = [b.volume for b in bars if b.volume is not None]
        if not volumes:
            continue
        rows.append({"instrument": instrument, "avg_volume": sum(volumes) / len(volumes)})
    rows.sort(key=lambda r: r["avg_volume"], reverse=True)
    return rows[:limit]


def highest_turnover(days=30, limit=10):
    """Active instruments ranked by average daily GH¢ value traded over the
    trailing window, counting only bars that carry a turnover figure."""
    rows = []
    for instrument in Instrument.objects.filter(is_active=True):
        bars = instrument.price_bars.order_by("-trade_date")[:days]
        values = [float(b.turnover_value) for b in bars if b.turnover_value is not None]
        if not values:
            continue
        rows.append({"instrument": instrument, "avg_value": sum(values) / len(values)})
    rows.sort(key=lambda r: r["avg_value"], reverse=True)
    return rows[:limit]


def market_breadth():
    """Gainers/losers/unchanged among active instruments, each compared to
    its own immediately-prior close — not necessarily the same calendar
    date across instruments, since GSE tickers don't all trade every day."""
    gainers = losers = unchanged = 0
    latest_date = None
    for instrument in Instrument.objects.filter(is_active=True):
        bars = list(instrument.price_bars.all()[:2])
        if len(bars) < 2 or not bars[1].close_price or bars[0].close_price is None:
            continue
        if latest_date is None or bars[0].trade_date > latest_date:
            latest_date = bars[0].trade_date
        change = bars[0].close_price - bars[1].close_price
        if change > 0:
            gainers += 1
        elif change < 0:
            losers += 1
        else:
            unchanged += 1
    return {"gainers": gainers, "losers": losers, "unchanged": unchanged, "as_of": latest_date}

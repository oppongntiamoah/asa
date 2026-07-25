"""
Per-instrument analytics computed purely from PriceBar history — same
honesty rules as portfolio/analytics.py: a thin history gets None instead
of a fake-precision number, and nothing here invents data the source
doesn't have. Two notable absences, both because the field doesn't exist
in the data we actually ingest (see instruments/ingest/csv_ingest.py):

- No bid/offer spread — GSE's export has those columns but nothing parses
  them into PriceBar yet.
- No true intraday high/low — only open/close are in the daily export.

Reuses portfolio.analytics' generic (date, value) series functions
(max_drawdown, annualized_volatility) rather than re-deriving them, since
a price series and a portfolio-value series are the same shape.
"""
import bisect
from datetime import date, timedelta

from portfolio.analytics import annualized_volatility, max_drawdown


def _close_series(bars):
    """bars: chronological (oldest-first) PriceBar iterable."""
    return [(b.trade_date, float(b.close_price)) for b in bars if b.close_price is not None]


def period_return(bars, days):
    """% change from the close ~`days` calendar days before the latest bar,
    to the latest close. Uses the nearest bar on/before that target date.
    None if there's no bar that old."""
    series = _close_series(bars)
    if len(series) < 2:
        return None
    latest_date, latest_value = series[-1]
    target_date = latest_date - timedelta(days=days)
    dates = [d for d, _ in series]
    idx = bisect.bisect_right(dates, target_date) - 1
    if idx < 0:
        return None
    start_value = series[idx][1]
    if not start_value:
        return None
    return (latest_value - start_value) / start_value * 100


def ytd_return(bars):
    """% change since the first recorded close on/after 1 January of the
    latest bar's year."""
    series = _close_series(bars)
    if not series:
        return None
    latest_date, latest_value = series[-1]
    dates = [d for d, _ in series]
    idx = bisect.bisect_left(dates, date(latest_date.year, 1, 1))
    if idx >= len(series):
        return None
    start_value = series[idx][1]
    if not start_value:
        return None
    return (latest_value - start_value) / start_value * 100


def all_time_return(bars):
    series = _close_series(bars)
    if len(series) < 2 or not series[0][1]:
        return None
    return (series[-1][1] - series[0][1]) / series[0][1] * 100


def daily_change(bars):
    """(amount, pct) change from the prior close to the latest close —
    both None if there aren't two bars."""
    if len(bars) < 2 or bars[-1].close_price is None or not bars[-2].close_price:
        return None, None
    prev, latest = bars[-2].close_price, bars[-1].close_price
    return latest - prev, float((latest - prev) / prev * 100)


def moving_averages(bars, windows=(7, 20, 50, 100, 200)):
    """Latest simple moving average for each window, keyed by window size.
    A window is only included once there's enough history to fill it
    completely — no partial-window averages passed off as the real thing."""
    closes = [float(b.close_price) for b in bars if b.close_price is not None]
    return {w: sum(closes[-w:]) / w for w in windows if len(closes) >= w}


def fifty_two_week_range(bars):
    """High/low close over the trailing 365 days of *our own* ingested
    history, and where the latest close sits in that range. Not GSE's
    published Year High/Low (a separate figure csv_ingest doesn't store)
    — only as good as however much history has actually been loaded."""
    series = _close_series(bars)
    if not series:
        return None
    latest_date = series[-1][0]
    window = [v for d, v in series if d >= latest_date - timedelta(days=365)]
    if len(window) < 2:
        return None
    hi, lo, latest = max(window), min(window), window[-1]
    return {
        "high": hi,
        "low": lo,
        "position_pct": ((latest - lo) / (hi - lo) * 100) if hi > lo else 50.0,
    }


def liquidity_stats(bars, windows=(7, 30, 90)):
    """Average daily volume/turnover value over trailing windows — only
    counting bars that actually carry that field."""
    result = {}
    for w in windows:
        recent = bars[-w:]
        volumes = [b.volume for b in recent if b.volume is not None]
        values = [float(b.turnover_value) for b in recent if b.turnover_value is not None]
        result[w] = {
            "avg_volume": sum(volumes) / len(volumes) if volumes else None,
            "avg_value": sum(values) / len(values) if values else None,
        }
    return result


def trading_activity(bars):
    """Share of recorded days with zero reported volume, among bars that
    carry a volume figure at all. None with too few observations to mean
    anything."""
    with_volume = [b for b in bars if b.volume is not None]
    if len(with_volume) < 5:
        return None
    zero_days = sum(1 for b in with_volume if b.volume == 0)
    return {"zero_days": zero_days, "total_days": len(with_volume), "pct": zero_days / len(with_volume) * 100}


def best_worst_days(bars):
    """The single largest daily gain and loss (close-to-close %) in the
    loaded history, with their dates. None if fewer than 2 bars."""
    series = _close_series(bars)
    if len(series) < 2:
        return None
    changes = [
        (series[i][0], (series[i][1] - series[i - 1][1]) / series[i - 1][1] * 100)
        for i in range(1, len(series)) if series[i - 1][1]
    ]
    if not changes:
        return None
    return {
        "best": {"date": max(changes, key=lambda c: c[1])[0], "pct": max(c[1] for c in changes)},
        "worst": {"date": min(changes, key=lambda c: c[1])[0], "pct": min(c[1] for c in changes)},
    }


def volatility_90d(bars):
    series = _close_series(bars)
    return annualized_volatility(series[-91:]) if len(series) >= 11 else None


def drawdown_stats(bars):
    series = _close_series(bars)
    return max_drawdown(series) if series else None

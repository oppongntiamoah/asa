from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from portfolio.charts import svg_candle_chart, svg_line_chart, svg_volume_chart

from . import analytics
from .models import Instrument, PriceIngestBatch
from .services import highest_turnover, market_breadth, most_traded, price_history, top_movers

CHART_RANGES = {"1m": 30, "3m": 90, "6m": 180, "1y": 365, "max": None}
CHART_RANGE_LABELS = {"1m": "1M", "3m": "3M", "6m": "6M", "1y": "1Y", "max": "Max"}


@login_required
def market(request):
    """
    End-of-day quotes for every active GSE instrument — explicitly dated,
    never framed as live. GSE only publishes daily closing data; there's no
    real-time feed to show, and pretending otherwise would misrepresent
    what the app can actually promise.
    """
    query = request.GET.get("q", "").strip()
    instruments = Instrument.objects.filter(is_active=True).prefetch_related("price_bars")
    if query:
        instruments = instruments.filter(ticker__icontains=query)

    rows = []
    latest_date = None
    for instrument in instruments:
        bars = list(instrument.price_bars.all()[:2])
        latest = bars[0] if bars else None
        change_pct = None
        if len(bars) == 2 and bars[1].close_price:
            change_pct = (bars[0].close_price - bars[1].close_price) / bars[1].close_price * 100
        if latest and (latest_date is None or latest.trade_date > latest_date):
            latest_date = latest.trade_date
        rows.append({
            "instrument": instrument,
            "close_price": latest.close_price if latest else None,
            "trade_date": latest.trade_date if latest else None,
            "change_pct": change_pct,
        })

    rows.sort(key=lambda r: r["instrument"].ticker)
    return render(request, "instruments/market.html", {"rows": rows, "query": query, "latest_date": latest_date})


@login_required
def detail(request, ticker):
    """
    Price history and analytics for any actively-tracked instrument,
    whether or not the viewer holds it — the line/candle toggle and stats
    live here rather than only on the owned-position page, since browsing
    the market shouldn't require a position first. Shows a "Your position"
    panel when the viewer does hold it, linking through to the full
    owned-position view.
    """
    instrument = get_object_or_404(Instrument, ticker__iexact=ticker, is_active=True)

    chart_range = request.GET.get("range", "6m")
    if chart_range not in CHART_RANGES:
        chart_range = "6m"

    all_bars = price_history(instrument)  # full history — needed for 52wk/MA200/all-time stats regardless of chart range
    chart_bars = all_bars[-CHART_RANGES[chart_range]:] if CHART_RANGES[chart_range] else all_bars

    chart_series = [(b.trade_date, float(b.close_price)) for b in chart_bars if b.close_price is not None]
    candle_svg, has_intraday_range = svg_candle_chart(chart_bars)
    volume_svg = svg_volume_chart(chart_bars)

    change_amount, change_pct = analytics.daily_change(all_bars)

    returns_display = [
        ("1D", change_pct),
        ("7D", analytics.period_return(all_bars, 7)),
        ("30D", analytics.period_return(all_bars, 30)),
        ("3M", analytics.period_return(all_bars, 90)),
        ("6M", analytics.period_return(all_bars, 180)),
        ("YTD", analytics.ytd_return(all_bars)),
        ("1Y", analytics.period_return(all_bars, 365)),
        ("All-time", analytics.all_time_return(all_bars)),
    ]

    from portfolio.models import Holding

    holding = Holding.objects.filter(user=request.user, instrument=instrument).first()

    return render(
        request,
        "instruments/detail.html",
        {
            "instrument": instrument,
            "close_price": all_bars[-1].close_price if all_bars else None,
            "trade_date": all_bars[-1].trade_date if all_bars else None,
            "change_amount": change_amount,
            "change_pct": change_pct,
            "returns_display": returns_display,
            "chart_svg": svg_line_chart(chart_series),
            "candle_svg": candle_svg,
            "has_intraday_range": has_intraday_range,
            "volume_svg": volume_svg,
            "chart_range": chart_range,
            "chart_range_items": [(r, CHART_RANGE_LABELS[r]) for r in CHART_RANGES],
            "week_range": analytics.fifty_two_week_range(all_bars),
            "moving_averages": analytics.moving_averages(all_bars),
            "ma_windows": [7, 20, 50, 100, 200],
            "volatility": analytics.volatility_90d(all_bars),
            "drawdown": analytics.drawdown_stats(all_bars),
            "liquidity": analytics.liquidity_stats(all_bars),
            "liquidity_windows": [7, 30, 90],
            "trading_activity": analytics.trading_activity(all_bars),
            "best_worst": analytics.best_worst_days(all_bars),
            "holding": holding,
        },
    )


MOVER_PERIODS = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
MOVER_PERIOD_LABELS = {"7d": "7 days", "30d": "30 days", "90d": "90 days", "1y": "1 year"}


@login_required
def movers(request):
    """
    Market-wide rankings — gainers/losers, most traded, highest turnover,
    and today's breadth — across every actively-tracked instrument, not
    just what the viewer holds.
    """
    period = request.GET.get("period", "30d")
    if period not in MOVER_PERIODS:
        period = "30d"
    days = MOVER_PERIODS[period]

    gainers, losers = top_movers(days=days, limit=10)

    return render(
        request,
        "instruments/movers.html",
        {
            "period": period,
            "period_label": MOVER_PERIOD_LABELS[period],
            "periods": MOVER_PERIODS.keys(),
            "period_labels": MOVER_PERIOD_LABELS,
            "gainers": gainers,
            "losers": losers,
            "most_traded": most_traded(days=days, limit=10),
            "highest_turnover": highest_turnover(days=days, limit=10),
            "breadth": market_breadth(),
        },
    )

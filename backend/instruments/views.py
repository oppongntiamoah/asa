from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from portfolio.charts import svg_candle_chart, svg_line_chart

from .models import Instrument, PriceIngestBatch
from .services import price_history


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
    Price history for any actively-tracked instrument, whether or not the
    viewer holds it — the line/candle toggle lives here rather than only on
    the owned-position page, since browsing the market shouldn't require a
    position first. Shows a "Your position" panel when the viewer does hold
    it, linking through to the full owned-position view.
    """
    instrument = get_object_or_404(Instrument, ticker__iexact=ticker, is_active=True)

    bars = price_history(instrument, days=180)
    chart_series = [(b.trade_date, float(b.close_price)) for b in bars if b.close_price is not None]
    candle_svg, has_intraday_range = svg_candle_chart(bars)

    latest_bars = list(instrument.price_bars.all()[:2])
    latest = latest_bars[0] if latest_bars else None
    change_pct = None
    if len(latest_bars) == 2 and latest_bars[1].close_price:
        change_pct = (latest_bars[0].close_price - latest_bars[1].close_price) / latest_bars[1].close_price * 100

    from portfolio.models import Holding

    holding = Holding.objects.filter(user=request.user, instrument=instrument).first()

    return render(
        request,
        "instruments/detail.html",
        {
            "instrument": instrument,
            "close_price": latest.close_price if latest else None,
            "trade_date": latest.trade_date if latest else None,
            "change_pct": change_pct,
            "chart_svg": svg_line_chart(chart_series),
            "candle_svg": candle_svg,
            "has_intraday_range": has_intraday_range,
            "holding": holding,
        },
    )

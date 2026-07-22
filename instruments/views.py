from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Instrument, PriceIngestBatch


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

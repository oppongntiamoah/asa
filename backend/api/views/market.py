from instruments.models import Instrument
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..helpers import decimal_or_none, instrument_dict


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def market_list(request):
    """
    Full end-of-day quote list for every active GSE instrument — explicitly
    dated, never framed as live (see instruments.services.market_snapshot
    for the same convention on the public landing page).
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
            change_pct = float((bars[0].close_price - bars[1].close_price) / bars[1].close_price * 100)
        if latest and (latest_date is None or latest.trade_date > latest_date):
            latest_date = latest.trade_date
        rows.append({
            "instrument": instrument_dict(instrument),
            "close_price": decimal_or_none(latest.close_price) if latest else None,
            "trade_date": latest.trade_date.isoformat() if latest else None,
            "change_pct": change_pct,
        })

    rows.sort(key=lambda r: r["instrument"]["ticker"])
    return Response({"rows": rows, "latest_date": latest_date.isoformat() if latest_date else None})

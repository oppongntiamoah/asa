from django.shortcuts import get_object_or_404
from instruments.models import Instrument
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from watchlist.models import WatchlistItem
from watchlist.services import watchlist_rows

from ..helpers import decimal_or_none, instrument_dict


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def watchlist(request):
    if request.method == "GET":
        rows = watchlist_rows(request.user)
        return Response([
            {
                "id": r["item"].id,
                "instrument": instrument_dict(r["instrument"]),
                "current_price": decimal_or_none(r["current_price"]),
                "price_date": r["price_date"].isoformat() if r["price_date"] else None,
                "change_pct": decimal_or_none(r["change_pct"]),
                "high_52w": decimal_or_none(r["high_52w"]),
                "low_52w": decimal_or_none(r["low_52w"]),
            }
            for r in rows
        ])

    ticker = request.data.get("ticker", "").strip().upper()
    instrument = Instrument.objects.filter(ticker=ticker, is_active=True).first()
    if not instrument:
        return Response({"errors": {"ticker": f"No active instrument found for '{ticker}'."}}, status=400)

    item, created = WatchlistItem.objects.get_or_create(user=request.user, instrument=instrument)
    return Response({"id": item.id, "instrument": instrument_dict(instrument), "created": created}, status=201 if created else 200)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def watchlist_remove(request, pk):
    item = get_object_or_404(WatchlistItem, pk=pk, user=request.user)
    item.delete()
    return Response(status=204)

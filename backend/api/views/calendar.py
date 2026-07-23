from datetime import date

from corporate_actions.models import CorporateAction
from dividends.models import DividendRecord
from portfolio.models import Holding
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from watchlist.models import WatchlistItem

from ..helpers import instrument_dict


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def calendar_view(request):
    today = date.today()
    year = int(request.GET.get("year", today.year))
    month = int(request.GET.get("month", today.month))

    instrument_ids = set(Holding.objects.filter(user=request.user).values_list("instrument_id", flat=True))
    instrument_ids |= set(WatchlistItem.objects.filter(user=request.user).values_list("instrument_id", flat=True))

    actions = CorporateAction.objects.filter(
        instrument_id__in=instrument_ids, event_date__year=year, event_date__month=month
    ).select_related("instrument")
    dividends = DividendRecord.objects.filter(
        instrument_id__in=instrument_ids, ex_dividend_date__year=year, ex_dividend_date__month=month
    ).select_related("instrument")

    events = [
        {"date": a.event_date.isoformat(), "instrument": instrument_dict(a.instrument), "type": a.get_action_type_display(), "title": a.title}
        for a in actions
    ] + [
        {"date": d.ex_dividend_date.isoformat(), "instrument": instrument_dict(d.instrument), "type": "Ex-Dividend", "title": f"Ex-dividend — GHS {d.amount_per_share}/share"}
        for d in dividends
    ]
    events.sort(key=lambda e: e["date"])

    return Response({"year": year, "month": month, "events": events})

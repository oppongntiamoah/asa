from dividends.services import dividend_dashboard
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..helpers import decimal_or_none, instrument_dict


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dividend_history(request):
    data = dividend_dashboard(request.user)

    return Response({
        "total_received": float(data["total_received"]),
        "this_year": float(data["this_year"]),
        "portfolio_yield_pct": decimal_or_none(data["portfolio_yield_pct"]),
        "per_holding_yield": [
            {
                "instrument": instrument_dict(h["holding"].instrument),
                "trailing_12mo_received": float(h["trailing_12mo_received"]),
                "yield_pct": decimal_or_none(h["yield_pct"]),
            }
            for h in data["per_holding_yield"]
        ],
        "upcoming": [
            {
                "instrument": instrument_dict(d.instrument),
                "amount_per_share": float(d.amount_per_share),
                "ex_dividend_date": d.ex_dividend_date.isoformat(),
                "payment_date": d.payment_date.isoformat() if d.payment_date else None,
            }
            for d in data["upcoming"]
        ],
        "monthly_series": [{"month": m, "amount": float(a)} for m, a in data["monthly_series"]],
        "max_monthly_amount": float(data["max_monthly_amount"]),
        "annual_series": [
            {"year": r["year"], "amount": float(r["amount"]), "growth_pct": decimal_or_none(r["growth_pct"])}
            for r in data["annual_series"]
        ],
        "receipts": [
            {
                "instrument": instrument_dict(r.dividend_record.instrument),
                "amount_per_share": float(r.dividend_record.amount_per_share),
                "ex_dividend_date": r.dividend_record.ex_dividend_date.isoformat(),
                "payment_date": r.dividend_record.payment_date.isoformat() if r.dividend_record.payment_date else None,
                "quantity_held": float(r.quantity_held),
                "total_amount": float(r.total_amount),
            }
            for r in data["receipts"]
        ],
    })

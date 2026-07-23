"""
Purpose-built API for the Svelte PWA — not a general-purpose public REST
API, so views return the same dict shapes the existing Django template
views already use (via portfolio.services/analytics), transformed just
enough to be JSON-safe (model instances -> plain dicts). DRF's Response
already serializes Decimal/date correctly, so no ModelSerializer
boilerplate for data that was already stable and tested.
"""
from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from instruments.models import Instrument
from instruments.services import market_snapshot, price_history
from portfolio import analytics
from portfolio.charts import svg_line_chart
from portfolio.models import Holding, Transaction
from portfolio.services import (
    cost_basis_table,
    market_movers,
    portfolio_summary,
    sector_allocation,
)
from portfolio.views import _holdings_rows

from ..helpers import decimal_or_none as _decimal_or_none
from ..helpers import instrument_dict as _instrument_dict
from ..helpers import mover_dict as _mover_dict


@api_view(["GET"])
@permission_classes([AllowAny])
def csrf(request):
    """Sets the csrftoken cookie so the SPA can read it and send it back
    as X-CSRFToken on POST/PUT/DELETE requests."""
    return Response({"csrfToken": get_token(request)})


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get("username", "")
    password = request.data.get("password", "")
    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response({"detail": "Invalid username or password."}, status=400)
    login(request, user)
    return Response({"username": user.username, "first_name": user.first_name})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    logout(request)
    return Response({"detail": "Logged out."})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    return Response({"username": request.user.username, "first_name": request.user.first_name})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard(request):
    summary = portfolio_summary(request.user)
    value_series = analytics.portfolio_value_series(request.user)
    chart_series = [(d.isoformat(), float(v)) for d, v in value_series]

    allocations = [
        {
            "instrument": _instrument_dict(a["holding"].instrument),
            "value": _decimal_or_none(a["value"]),
            "pct": float(a["pct"]),
        }
        for a in summary["allocations"]
    ]
    asset_class_rows = [
        {"asset_class": r["asset_class"], "label": r["label"], "value": float(r["value"]), "pct": float(r["pct"])}
        for r in summary["asset_class_allocation"]["rows"]
    ]

    movers = market_movers(request.user)

    return Response({
        "total_value": float(summary["total_value"]),
        "cash_balance": float(summary["cash_balance"]),
        "total_cost_basis": float(summary["total_cost_basis"]),
        "total_unrealized_pnl": float(summary["total_unrealized_pnl"]),
        "total_unrealized_pct": _decimal_or_none(summary["total_unrealized_pct"]),
        "total_realized_pnl": float(summary["total_realized_pnl"]),
        "total_return_pct": _decimal_or_none(summary["total_return_pct"]),
        "num_holdings": summary["num_holdings"],
        "todays_change": {
            "amount": _decimal_or_none(summary["todays_change"]["amount"]),
            "pct": _decimal_or_none(summary["todays_change"]["pct"]),
        },
        "has_stale_price": summary["has_stale_price"],
        "has_any_transactions": request.user.transactions.exists(),
        "allocations": allocations,
        "asset_class_allocation": asset_class_rows,
        "sector_allocation": [
            {"sector": r["sector"], "value": float(r["value"]), "pct": float(r["pct"])}
            for r in sector_allocation(request.user)
        ],
        "movers": {
            "gainers": [_mover_dict(r) for r in movers["gainers"]],
            "losers": [_mover_dict(r) for r in movers["losers"]],
            "volume_leaders": [_mover_dict(r) for r in movers["volume_leaders"]],
            "value_leaders": [_mover_dict(r) for r in movers["value_leaders"]],
        },
        "chart_svg": svg_line_chart(chart_series),
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def holdings(request):
    query = request.GET.get("q", "").strip()
    sort_by = request.GET.get("sort", "market_value")
    direction = request.GET.get("dir", "desc")
    rows = _holdings_rows(request.user, query, sort_by, direction)

    return Response([
        {
            "instrument": _instrument_dict(r["instrument"]),
            "quantity": float(r["quantity"]),
            "avg_cost": float(r["avg_cost"]),
            "current_price": _decimal_or_none(r["current_price"]),
            "total_invested": float(r["total_invested"]),
            "market_value": _decimal_or_none(r["market_value"]),
            "gain_loss": _decimal_or_none(r["gain_loss"]),
            "pct_change": _decimal_or_none(r["pct_change"]),
        }
        for r in rows
    ])


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def cost_basis(request):
    rows = cost_basis_table(request.user)
    return Response([
        {
            "instrument": _instrument_dict(r["holding"].instrument),
            "average_cost": float(r["average_cost"]),
            "break_even_price": float(r["break_even_price"]),
            "current_price": _decimal_or_none(r["current_price"]),
            "gain_per_share": _decimal_or_none(r["gain_per_share"]),
            "gain_pct": _decimal_or_none(r["gain_pct"]),
        }
        for r in rows
    ])


@api_view(["GET"])
@permission_classes([AllowAny])
def market_summary(request):
    """
    Public, portfolio-agnostic snapshot for the landing page. Explicitly
    NOT "live" — as_of is the latest trade date SikaTrack has ingested,
    and the response says so rather than implying real-time data.
    """
    snap = market_snapshot(limit=5)
    return Response({
        "as_of": snap["as_of"].isoformat() if snap["as_of"] else None,
        "instrument_count": snap["instrument_count"],
        "gainers": [_mover_dict(r) for r in snap["gainers"]],
        "losers": [_mover_dict(r) for r in snap["losers"]],
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ticker_detail(request, ticker):
    instrument = get_object_or_404(Instrument, ticker__iexact=ticker)
    bars = price_history(instrument)

    latest = bars[-1] if bars else None
    previous = bars[-2] if len(bars) > 1 else None
    change_pct = None
    if latest and previous and previous.close_price:
        change_pct = float((latest.close_price - previous.close_price) / previous.close_price * 100)

    position = None
    holding = Holding.objects.filter(user=request.user, instrument=instrument).first()
    if holding:
        txns = Transaction.objects.filter(user=request.user, instrument=instrument).order_by("-trade_date")
        dividend_receipts = instrument.dividends.filter(receipts__user=request.user).prefetch_related("receipts")
        position = {
            "quantity": float(holding.quantity),
            "average_cost": float(holding.average_cost),
            "cost_basis": float(holding.cost_basis),
            "market_value": _decimal_or_none(holding.market_value()),
            "unrealized_pnl": _decimal_or_none(holding.unrealized_pnl()),
            "unrealized_pnl_pct": _decimal_or_none(holding.unrealized_pnl_percent()),
            "realized_pnl": float(holding.realized_pnl),
            "transactions": [
                {
                    "id": t.id,
                    "transaction_type": t.transaction_type,
                    "quantity": float(t.quantity),
                    "price_per_share": float(t.price_per_share),
                    "fees": float(t.fees),
                    "trade_date": t.trade_date.isoformat(),
                    "gross_amount": float(t.gross_amount),
                }
                for t in txns
            ],
            "dividend_receipts": [
                {
                    "amount_per_share": float(d.amount_per_share),
                    "ex_dividend_date": d.ex_dividend_date.isoformat(),
                    "total_amount": float(r.total_amount),
                }
                for d in dividend_receipts
                for r in d.receipts.filter(user=request.user)
            ],
        }

    return Response({
        "instrument": _instrument_dict(instrument),
        "latest_price": _decimal_or_none(latest.close_price) if latest else None,
        "latest_trade_date": latest.trade_date.isoformat() if latest else None,
        "change_pct": change_pct,
        "history": [
            {
                "trade_date": bar.trade_date.isoformat(),
                "close_price": float(bar.close_price),
                "volume": bar.volume,
            }
            for bar in bars
        ],
        "position": position,
    })

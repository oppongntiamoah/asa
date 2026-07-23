"""Read-only analysis endpoints — each mirrors one classic
portfolio/*.html page, reusing portfolio.services/analytics/insights
directly rather than recomputing anything here."""
from portfolio import analytics, insights
from portfolio.charts import svg_line_chart
from portfolio.services import sector_performance, transaction_analysis
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..helpers import decimal_or_none, instrument_dict


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def transaction_analysis_view(request):
    data = transaction_analysis(request.user)
    return Response({
        "total_buys": data["total_buys"],
        "total_sells": data["total_sells"],
        "avg_purchase_price": decimal_or_none(data["avg_purchase_price"]),
        "largest_purchase": _txn_summary(data["largest_purchase"]),
        "largest_sale": _txn_summary(data["largest_sale"]),
        "avg_holding_period_days": data["avg_holding_period_days"],
        "monthly": [
            {"month": m["month"], "buys": float(m["buys"]), "sells": float(m["sells"]), "count": m["count"]}
            for m in data["monthly"]
        ],
        "trading_frequency_per_month": data["trading_frequency_per_month"],
    })


def _txn_summary(t):
    if t is None:
        return None
    return {
        "instrument": instrument_dict(t.instrument),
        "quantity": float(t.quantity),
        "price_per_share": float(t.price_per_share),
        "trade_date": t.trade_date.isoformat(),
        "gross_amount": float(t.gross_amount),
    }


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def sector_analysis_view(request):
    rows = sector_performance(request.user)
    return Response([
        {
            "sector": r["sector"],
            "invested": float(r["invested"]),
            "invested_pct": float(r["invested_pct"]),
            "value": decimal_or_none(r["value"]),
            "return_pct": decimal_or_none(r["return_pct"]),
        }
        for r in rows
    ])


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def performance_view(request):
    series = analytics.portfolio_value_series(request.user)
    history_days = (series[-1][0] - series[0][0]).days if len(series) >= 2 else 0
    chart_series = [(d.isoformat(), float(v)) for d, v in series]

    correlation = analytics.holdings_correlation(request.user)
    correlation_grid = None
    if correlation.get("tickers"):
        tickers = correlation["tickers"]
        correlation_grid = [
            {
                "ticker": row_t,
                "cells": [
                    1.0 if row_t == col_t else correlation["matrix"].get((row_t, col_t))
                    for col_t in tickers
                ],
            }
            for row_t in tickers
        ]

    max_dd = analytics.max_drawdown(series)

    return Response({
        "has_series": len(series) >= 2,
        "history_days": history_days,
        "chart_svg": svg_line_chart(chart_series),
        "cagr": analytics.cagr(series),
        "max_drawdown": None if max_dd is None else {
            "max_drawdown_pct": max_dd["max_drawdown_pct"],
            "peak_date": max_dd["peak_date"].isoformat(),
            "trough_date": max_dd["trough_date"].isoformat(),
        },
        "volatility": analytics.annualized_volatility(series),
        "var_95": analytics.historical_var(series),
        "xirr": analytics.portfolio_xirr(request.user),
        "rolling_30d": [{"date": d.isoformat(), "return_pct": v} for d, v in analytics.rolling_returns(series, window_days=30)[-6:]],
        "correlation_tickers": correlation.get("tickers"),
        "correlation_grid": correlation_grid,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def risk_health_view(request):
    data = insights.concentration_and_health(request.user)
    return Response({
        "largest_position": None if data["largest_position"] is None else {
            "instrument": instrument_dict(data["largest_position"]["holding"].instrument),
            "pct": data["largest_position"]["pct"],
        },
        "largest_sector": data["largest_sector"],
        "diversification_score": data["diversification_score"],
        "health_score": data["health_score"],
        "warnings": data["warnings"],
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def insights_view(request):
    return Response({"insights": insights.rule_based_insights(request.user)})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def cash_flow_view(request):
    rows = insights.cash_flow_analysis(request.user)
    return Response([
        {"month": r["month"], "invested": float(r["invested"]), "divested": float(r["divested"]), "net": float(r["net"])}
        for r in rows
    ])


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def tax_summary_view(request):
    rows = insights.realized_gains_by_year(request.user)
    return Response([{"year": r["year"], "realized_gain": float(r["realized_gain"])} for r in rows])


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def timeline_view(request):
    events = insights.portfolio_timeline(request.user)
    return Response([
        {"date": e["date"].isoformat(), "kind": e["kind"], "description": e["description"], "amount": float(e["amount"])}
        for e in events
    ])

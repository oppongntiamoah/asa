import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from corporate_actions.models import CorporateAction
from instruments.models import Instrument

from . import analytics, insights
from .charts import svg_line_chart
from .forms import TransactionForm
from .models import Holding, Transaction
from .services import (
    InsufficientHoldingError,
    cost_basis_table,
    create_transaction,
    current_holding_quantity,
    delete_transaction,
    portfolio_summary,
    sector_allocation,
    sector_performance,
    top_movers,
    transaction_analysis,
    winners_losers,
)

HOLDINGS_SORT_KEYS = {
    "ticker": lambda r: r["instrument"].ticker,
    "quantity": lambda r: r["quantity"],
    "avg_cost": lambda r: r["avg_cost"],
    "current_price": lambda r: (r["current_price"] is not None, r["current_price"] or 0),
    "total_invested": lambda r: r["total_invested"],
    "market_value": lambda r: (r["market_value"] is not None, r["market_value"] or 0),
    "gain_loss": lambda r: (r["gain_loss"] is not None, r["gain_loss"] or 0),
    "pct_change": lambda r: (r["pct_change"] is not None, r["pct_change"] or 0),
}


def _holdings_rows(user, query="", sort_by="market_value", direction="desc"):
    holdings = Holding.objects.filter(user=user).select_related("instrument")
    if query:
        holdings = holdings.filter(instrument__ticker__icontains=query)

    rows = []
    for holding in holdings:
        current_price = holding.latest_price()
        market_value = holding.market_value()
        gain_loss = holding.unrealized_pnl()
        rows.append({
            "instrument": holding.instrument,
            "quantity": holding.quantity,
            "avg_cost": holding.average_cost,
            "current_price": current_price,
            "total_invested": holding.cost_basis,
            "market_value": market_value,
            "gain_loss": gain_loss,
            "pct_change": holding.unrealized_pnl_percent(),
        })

    key_fn = HOLDINGS_SORT_KEYS.get(sort_by, HOLDINGS_SORT_KEYS["market_value"])
    rows.sort(key=key_fn, reverse=(direction == "desc"))
    return rows


@login_required
def dashboard(request):
    summary = portfolio_summary(request.user)
    has_any_transactions = Transaction.objects.filter(user=request.user).exists()

    context = {
        **summary,
        "has_any_transactions": has_any_transactions,
        "top_movers": top_movers(request.user),
        "sector_allocation": sector_allocation(request.user),
        "winners_losers": winners_losers(request.user, limit=3),
        "upcoming_actions": CorporateAction.objects.filter(
            instrument__holdings__user=request.user
        ).distinct().order_by("event_date")[:5],
    }
    return render(request, "portfolio/dashboard.html", context)


@login_required
def holdings_list(request):
    query = request.GET.get("q", "").strip()
    sort_by = request.GET.get("sort", "market_value")
    direction = request.GET.get("dir", "desc")

    rows = _holdings_rows(request.user, query, sort_by, direction)
    sort_columns = [
        ("ticker", "Symbol"), ("quantity", "Quantity"), ("avg_cost", "Avg. Buy Price"),
        ("current_price", "Current Price"), ("total_invested", "Total Invested"),
        ("market_value", "Market Value"), ("gain_loss", "Gain/Loss"), ("pct_change", "% Change"),
    ]
    return render(request, "portfolio/holdings_list.html", {
        "rows": rows, "query": query, "sort_by": sort_by, "direction": direction,
        "sort_columns": sort_columns,
    })


@login_required
def holdings_csv_export(request):
    query = request.GET.get("q", "").strip()
    sort_by = request.GET.get("sort", "market_value")
    direction = request.GET.get("dir", "desc")
    rows = _holdings_rows(request.user, query, sort_by, direction)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="holdings.csv"'
    writer = csv.writer(response)
    writer.writerow(["Symbol", "Quantity", "Avg Buy Price", "Current Price", "Total Invested", "Market Value", "Gain/Loss", "% Change"])
    for r in rows:
        writer.writerow([
            r["instrument"].ticker, r["quantity"], r["avg_cost"],
            r["current_price"] if r["current_price"] is not None else "",
            r["total_invested"], r["market_value"] if r["market_value"] is not None else "",
            r["gain_loss"] if r["gain_loss"] is not None else "",
            f'{r["pct_change"]:.2f}' if r["pct_change"] is not None else "",
        ])
    return response


@login_required
def stock_breakdown(request):
    summary = portfolio_summary(request.user)
    return render(request, "portfolio/stock_breakdown.html", {
        "allocations": summary["allocations"],
        "sector_allocation": sector_allocation(request.user),
        "total_value": summary["total_value"],
    })


@login_required
def transaction_analysis_view(request):
    return render(request, "portfolio/transaction_analysis.html", transaction_analysis(request.user))


@login_required
def cost_basis_view(request):
    return render(request, "portfolio/cost_basis.html", {"rows": cost_basis_table(request.user)})


@login_required
def sector_analysis_view(request):
    return render(request, "portfolio/sector_analysis.html", {"sectors": sector_performance(request.user)})


@login_required
def performance_view(request):
    series = analytics.portfolio_value_series(request.user)
    history_days = (series[-1][0] - series[0][0]).days if len(series) >= 2 else 0

    chart_series = [(d.isoformat(), float(v)) for d, v in series]
    correlation = analytics.holdings_correlation(request.user)
    correlation_grid = None
    if correlation.get("tickers"):
        tickers = correlation["tickers"]
        correlation_grid = [
            {"ticker": row_t, "cells": [
                1.0 if row_t == col_t else correlation["matrix"].get((row_t, col_t))
                for col_t in tickers
            ]}
            for row_t in tickers
        ]

    context = {
        "history_days": history_days,
        "chart_svg": svg_line_chart(chart_series),
        "cagr": analytics.cagr(series),
        "max_drawdown": analytics.max_drawdown(series),
        "volatility": analytics.annualized_volatility(series),
        "var_95": analytics.historical_var(series),
        "xirr": analytics.portfolio_xirr(request.user),
        "rolling_30d": analytics.rolling_returns(series, window_days=30)[-6:],
        "correlation_tickers": correlation.get("tickers"),
        "correlation_grid": correlation_grid,
        "has_series": len(series) >= 2,
    }
    return render(request, "portfolio/performance.html", context)


@login_required
def risk_health_view(request):
    return render(request, "portfolio/risk_health.html", insights.concentration_and_health(request.user))


@login_required
def insights_view(request):
    return render(request, "portfolio/insights.html", {"insights": insights.rule_based_insights(request.user)})


@login_required
def cash_flow_view(request):
    return render(request, "portfolio/cash_flow.html", {"rows": insights.cash_flow_analysis(request.user)})


@login_required
def tax_summary_view(request):
    return render(request, "portfolio/tax_summary.html", {"rows": insights.realized_gains_by_year(request.user)})


@login_required
def timeline_view(request):
    return render(request, "portfolio/timeline.html", {"events": insights.portfolio_timeline(request.user)})


@login_required
def holding_detail(request, instrument_id):
    holding = get_object_or_404(Holding, user=request.user, instrument_id=instrument_id)
    transactions = Transaction.objects.filter(user=request.user, instrument=holding.instrument)
    dividend_receipts = holding.instrument.dividends.filter(receipts__user=request.user).prefetch_related("receipts")
    return render(
        request,
        "portfolio/holding_detail.html",
        {"holding": holding, "transactions": transactions, "dividend_receipts": dividend_receipts},
    )


@login_required
def transaction_list(request):
    transactions = Transaction.objects.filter(user=request.user).select_related("instrument")
    return render(request, "portfolio/transaction_list.html", {"transactions": transactions})


@login_required
def transaction_add(request):
    if request.method == "POST":
        form = TransactionForm(request.POST)
        if form.is_valid():
            try:
                create_transaction(
                    user=request.user,
                    instrument=form.cleaned_data["instrument"],
                    transaction_type=form.cleaned_data["transaction_type"],
                    quantity=form.cleaned_data["quantity"],
                    price_per_share=form.cleaned_data["price_per_share"],
                    fees=form.cleaned_data["fees"],
                    trade_date=form.cleaned_data["trade_date"],
                    broker=form.cleaned_data["broker"],
                    notes=form.cleaned_data["notes"],
                )
            except InsufficientHoldingError as exc:
                form.add_error("quantity", str(exc))
            else:
                messages.success(request, "Transaction added.")
                return redirect("portfolio:dashboard")
    else:
        form = TransactionForm()
    return render(request, "portfolio/transaction_form.html", {"form": form})


@login_required
def transaction_delete(request, pk):
    txn = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == "POST":
        delete_transaction(txn)
        messages.success(request, "Transaction removed.")
        return redirect("portfolio:transaction_list")
    return render(request, "portfolio/transaction_confirm_delete.html", {"transaction": txn})


@login_required
def check_sell_quantity(request):
    """HTMX endpoint: live-validates a sell quantity against current holding on blur."""
    instrument_id = request.GET.get("instrument")
    transaction_type = request.GET.get("transaction_type")
    quantity = request.GET.get("quantity")

    if transaction_type != Transaction.SELL or not instrument_id or not quantity:
        return HttpResponse("")

    try:
        instrument = Instrument.objects.get(pk=instrument_id)
        quantity_decimal = float(quantity)
    except (Instrument.DoesNotExist, ValueError):
        return HttpResponse("")

    held = current_holding_quantity(request.user, instrument)
    if quantity_decimal > held:
        return HttpResponse(
            f'<p class="text-xs text-red-600 mt-1">You only hold {held} shares of {instrument.ticker}.</p>'
        )
    return HttpResponse("")

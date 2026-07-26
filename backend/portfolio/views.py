import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from corporate_actions.models import CorporateAction
from instruments.models import Instrument

from . import analytics, insights
from .charts import svg_candle_chart, svg_line_chart
from .context import get_active_portfolio, set_active_portfolio
from .forms import CashBalanceForm, PortfolioForm, TransactionForm
from .models import CashBalance, Holding, Portfolio, Transaction
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


def _holdings_rows(portfolio, query="", sort_by="market_value", direction="desc"):
    holdings = Holding.objects.filter(portfolio=portfolio).select_related("instrument")
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


def home(request):
    """
    Root URL: a marketing landing page for anonymous visitors, the real
    dashboard for signed-in users — so "/" works for both without a
    redirect-to-login detour losing the pitch for people who aren't
    signed up yet.
    """
    if request.user.is_authenticated:
        return dashboard(request)

    from instruments.services import market_snapshot
    from news.models import NewsArticle

    return render(request, "portfolio/landing.html", {
        "latest_news": NewsArticle.objects.filter(is_published=True)[:3],
        "snapshot": market_snapshot(limit=5),
    })


@login_required
def dashboard(request):
    active_portfolio = get_active_portfolio(request)
    summary = portfolio_summary(active_portfolio)
    has_any_transactions = Transaction.objects.filter(portfolio=active_portfolio).exists()

    value_series = analytics.portfolio_value_series(active_portfolio)
    chart_series = [(d.isoformat(), float(v)) for d, v in value_series]

    risk = insights.concentration_and_health(active_portfolio)
    smart_insights = insights.rule_based_insights(active_portfolio)[:3]

    context = {
        **summary,
        "has_any_transactions": has_any_transactions,
        "top_movers": top_movers(active_portfolio),
        "sector_allocation": sector_allocation(active_portfolio),
        "winners_losers": winners_losers(active_portfolio, limit=3),
        "chart_svg": svg_line_chart(chart_series),
        "upcoming_actions": CorporateAction.objects.filter(
            instrument__holdings__portfolio=active_portfolio
        ).distinct().order_by("event_date")[:5],
        "health_score": risk["health_score"],
        "smart_insights": smart_insights,
    }
    return render(request, "portfolio/dashboard.html", context)


@login_required
def holdings_list(request):
    query = request.GET.get("q", "").strip()
    sort_by = request.GET.get("sort", "market_value")
    direction = request.GET.get("dir", "desc")

    rows = _holdings_rows(get_active_portfolio(request), query, sort_by, direction)
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
    rows = _holdings_rows(get_active_portfolio(request), query, sort_by, direction)

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
    active_portfolio = get_active_portfolio(request)
    summary = portfolio_summary(active_portfolio)
    return render(request, "portfolio/stock_breakdown.html", {
        "allocations": summary["allocations"],
        "sector_allocation": sector_allocation(active_portfolio),
        "total_value": summary["total_value"],
    })


@login_required
def transaction_analysis_view(request):
    return render(request, "portfolio/transaction_analysis.html", transaction_analysis(get_active_portfolio(request)))


@login_required
def cost_basis_view(request):
    return render(request, "portfolio/cost_basis.html", {"rows": cost_basis_table(get_active_portfolio(request))})


@login_required
def sector_analysis_view(request):
    return render(request, "portfolio/sector_analysis.html", {"sectors": sector_performance(get_active_portfolio(request))})


@login_required
def performance_view(request):
    active_portfolio = get_active_portfolio(request)
    series = analytics.portfolio_value_series(active_portfolio)
    history_days = (series[-1][0] - series[0][0]).days if len(series) >= 2 else 0

    chart_series = [(d.isoformat(), float(v)) for d, v in series]
    correlation = analytics.holdings_correlation(active_portfolio)
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
        "xirr": analytics.portfolio_xirr(active_portfolio),
        "rolling_30d": analytics.rolling_returns(series, window_days=30)[-6:],
        "correlation_tickers": correlation.get("tickers"),
        "correlation_grid": correlation_grid,
        "has_series": len(series) >= 2,
    }
    return render(request, "portfolio/performance.html", context)


@login_required
def risk_health_view(request):
    return render(request, "portfolio/risk_health.html", insights.concentration_and_health(get_active_portfolio(request)))


@login_required
def insights_view(request):
    return render(request, "portfolio/insights.html", {"insights": insights.rule_based_insights(get_active_portfolio(request))})


@login_required
def cash_flow_view(request):
    return render(request, "portfolio/cash_flow.html", {"rows": insights.cash_flow_analysis(get_active_portfolio(request))})


@login_required
def tax_summary_view(request):
    return render(request, "portfolio/tax_summary.html", {"rows": insights.realized_gains_by_year(get_active_portfolio(request))})


@login_required
def timeline_view(request):
    return render(request, "portfolio/timeline.html", {"events": insights.portfolio_timeline(get_active_portfolio(request))})


@login_required
def update_cash_balance(request):
    active_portfolio = get_active_portfolio(request)
    balance, _ = CashBalance.objects.get_or_create(portfolio=active_portfolio)
    if request.method == "POST":
        form = CashBalanceForm(request.POST, instance=balance)
        if form.is_valid():
            form.save()
            messages.success(request, "Cash balance updated.")
    return redirect("accounts:settings")


@login_required
def holding_detail(request, instrument_id):
    active_portfolio = get_active_portfolio(request)
    holding = get_object_or_404(Holding, portfolio=active_portfolio, instrument_id=instrument_id)
    transactions = Transaction.objects.filter(portfolio=active_portfolio, instrument=holding.instrument)
    dividend_receipts = holding.instrument.dividends.filter(receipts__portfolio=active_portfolio).prefetch_related("receipts")

    from instruments.services import price_history

    from .charts import lightweight_chart_data

    bars = price_history(holding.instrument, days=180)
    chart_series = [(b.trade_date, float(b.close_price)) for b in bars if b.close_price is not None]
    candle_svg, has_intraday_range = svg_candle_chart(bars)

    return render(
        request,
        "portfolio/holding_detail.html",
        {
            "holding": holding,
            "transactions": transactions,
            "dividend_receipts": dividend_receipts,
            "chart_svg": svg_line_chart(chart_series),
            "candle_svg": candle_svg,
            "has_intraday_range": has_intraday_range,
            "lw_chart_data": lightweight_chart_data(bars),
        },
    )


@login_required
def transaction_list(request):
    transactions = Transaction.objects.filter(portfolio=get_active_portfolio(request)).select_related("instrument")
    return render(request, "portfolio/transaction_list.html", {"transactions": transactions})


@login_required
def transaction_add(request):
    if request.method == "POST":
        form = TransactionForm(request.POST)
        if form.is_valid():
            try:
                create_transaction(
                    portfolio=get_active_portfolio(request),
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
    txn = get_object_or_404(Transaction, pk=pk, portfolio=get_active_portfolio(request))
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

    held = current_holding_quantity(get_active_portfolio(request), instrument)
    if quantity_decimal > held:
        return HttpResponse(
            f'<p class="text-xs text-red-600 mt-1">You only hold {held} shares of {instrument.ticker}.</p>'
        )
    return HttpResponse("")


@login_required
def portfolios_view(request):
    from billing.services import is_billing_enabled, max_portfolios_for_user

    portfolios = Portfolio.objects.filter(user=request.user)
    limit = max_portfolios_for_user(request.user)
    return render(request, "portfolio/portfolios.html", {
        "portfolios": portfolios,
        "active_portfolio": get_active_portfolio(request),
        "limit": limit,
        "unlimited": not is_billing_enabled(),
        "can_create": portfolios.count() < limit,
    })


@login_required
def portfolio_switch(request, portfolio_id):
    if request.method == "POST":
        portfolio = get_object_or_404(Portfolio, id=portfolio_id, user=request.user)
        set_active_portfolio(request, portfolio)
        messages.success(request, f'Switched to "{portfolio.name}".')
    return redirect("portfolio:dashboard")


@login_required
def portfolio_create(request):
    from billing.services import max_portfolios_for_user

    limit = max_portfolios_for_user(request.user)
    current_count = Portfolio.objects.filter(user=request.user).count()
    if current_count >= limit:
        messages.error(
            request,
            f"You've reached your plan's limit of {limit} portfolio{'s' if limit != 1 else ''}. "
            f"Upgrade to add more.",
        )
        return redirect("portfolio:portfolios")

    if request.method == "POST":
        form = PortfolioForm(request.POST)
        if form.is_valid():
            portfolio = form.save(commit=False)
            portfolio.user = request.user
            portfolio.save()
            set_active_portfolio(request, portfolio)
            messages.success(request, f'Created "{portfolio.name}" and switched to it.')
            return redirect("portfolio:portfolios")
    else:
        form = PortfolioForm()
    return render(request, "portfolio/portfolio_form.html", {"form": form, "mode": "create"})


@login_required
def portfolio_rename(request, portfolio_id):
    portfolio = get_object_or_404(Portfolio, id=portfolio_id, user=request.user)
    if request.method == "POST":
        form = PortfolioForm(request.POST, instance=portfolio)
        if form.is_valid():
            form.save()
            messages.success(request, "Portfolio renamed.")
            return redirect("portfolio:portfolios")
    else:
        form = PortfolioForm(instance=portfolio)
    return render(request, "portfolio/portfolio_form.html", {"form": form, "mode": "rename", "portfolio": portfolio})


@login_required
def portfolio_delete(request, portfolio_id):
    portfolio = get_object_or_404(Portfolio, id=portfolio_id, user=request.user)
    remaining_count = Portfolio.objects.filter(user=request.user).count()
    can_delete = remaining_count > 1

    if request.method == "POST":
        if not can_delete:
            messages.error(request, "You need at least one portfolio — this is your only one.")
            return redirect("portfolio:portfolios")

        was_default = portfolio.is_default
        was_active = get_active_portfolio(request).id == portfolio.id
        portfolio.delete()

        replacement = Portfolio.objects.filter(user=request.user).order_by("created_at").first()
        if replacement:
            if was_default:
                replacement.is_default = True
                replacement.save(update_fields=["is_default"])
            if was_active:
                set_active_portfolio(request, replacement)

        messages.success(request, "Portfolio deleted.")
        return redirect("portfolio:portfolios")

    return render(
        request, "portfolio/portfolio_confirm_delete.html", {"portfolio": portfolio, "can_delete": can_delete}
    )

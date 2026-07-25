"""Generates per-portfolio DividendReceipt rows from an admin-entered
DividendRecord, and dashboard aggregates over those receipts."""
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from portfolio.models import Holding, Portfolio, Transaction

from .models import DividendReceipt, DividendRecord


def _quantity_held_as_of(portfolio, instrument, as_of_date) -> Decimal:
    """Replays transactions up to and including as_of_date to find the
    quantity held on the dividend's record date — Holding only tracks the
    *current* quantity, which isn't necessarily what was held historically."""
    quantity = Decimal("0")
    txns = Transaction.objects.filter(
        portfolio=portfolio, instrument=instrument, trade_date__lte=as_of_date
    ).order_by("trade_date", "created_at", "id")
    for txn in txns:
        quantity += txn.quantity if txn.transaction_type == Transaction.BUY else -txn.quantity
    return quantity


def generate_receipts_for_dividend(dividend_record):
    """Idempotent: safe to call again if the DividendRecord is edited."""
    instrument = dividend_record.instrument
    portfolio_ids = Transaction.objects.filter(instrument=instrument).values_list("portfolio_id", flat=True).distinct()

    created_or_updated = []
    for portfolio in Portfolio.objects.filter(id__in=portfolio_ids):
        quantity_held = _quantity_held_as_of(portfolio, instrument, dividend_record.record_date)
        if quantity_held <= 0:
            DividendReceipt.objects.filter(portfolio=portfolio, dividend_record=dividend_record).delete()
            continue

        total_amount = quantity_held * dividend_record.amount_per_share
        receipt, _ = DividendReceipt.objects.update_or_create(
            portfolio=portfolio,
            dividend_record=dividend_record,
            defaults={"quantity_held": quantity_held, "total_amount": total_amount},
        )
        created_or_updated.append(receipt)
    return created_or_updated


def dividend_dashboard(portfolio):
    """Aggregate dividend figures for the dividend dashboard page."""
    receipts = DividendReceipt.objects.filter(portfolio=portfolio).select_related(
        "dividend_record", "dividend_record__instrument"
    )
    today = date.today()
    year_start = date(today.year, 1, 1)

    total_received = Decimal("0")
    this_year = Decimal("0")
    trailing_12mo_by_instrument = defaultdict(Decimal)
    monthly_income = defaultdict(Decimal)  # {"YYYY-MM": amount}
    annual_income = defaultdict(Decimal)  # {year: amount}

    twelve_months_ago = today - timedelta(days=365)

    for r in receipts:
        effective_date = r.dividend_record.payment_date or r.dividend_record.ex_dividend_date
        total_received += r.total_amount
        annual_income[effective_date.year] += r.total_amount
        monthly_income[effective_date.strftime("%Y-%m")] += r.total_amount
        if effective_date >= year_start:
            this_year += r.total_amount
        if effective_date >= twelve_months_ago:
            trailing_12mo_by_instrument[r.dividend_record.instrument_id] += r.total_amount

    # Portfolio dividend yield: trailing-12-month dividend income / current cost basis.
    holdings = Holding.objects.filter(portfolio=portfolio).select_related("instrument")
    total_cost_basis = sum((h.cost_basis for h in holdings), Decimal("0"))
    trailing_12mo_total = sum(trailing_12mo_by_instrument.values(), Decimal("0"))
    portfolio_yield_pct = (trailing_12mo_total / total_cost_basis * 100) if total_cost_basis else None

    per_holding_yield = []
    for h in holdings:
        received = trailing_12mo_by_instrument.get(h.instrument_id, Decimal("0"))
        yield_pct = (received / h.cost_basis * 100) if h.cost_basis else None
        per_holding_yield.append({"holding": h, "trailing_12mo_received": received, "yield_pct": yield_pct})
    per_holding_yield.sort(key=lambda x: x["trailing_12mo_received"], reverse=True)

    upcoming = DividendRecord.objects.filter(
        instrument__holdings__portfolio=portfolio, ex_dividend_date__gte=today
    ).distinct().order_by("ex_dividend_date")[:10]

    sorted_months = sorted(monthly_income.keys())[-12:]
    monthly_series = [(m, monthly_income[m]) for m in sorted_months]
    max_monthly_amount = max((amount for _, amount in monthly_series), default=Decimal("1"))

    sorted_years = sorted(annual_income.keys())
    annual_series = []
    prev_amount = None
    for y in sorted_years:
        amount = annual_income[y]
        growth_pct = ((amount - prev_amount) / prev_amount * 100) if prev_amount else None
        annual_series.append({"year": y, "amount": amount, "growth_pct": growth_pct})
        prev_amount = amount

    return {
        "total_received": total_received,
        "this_year": this_year,
        "portfolio_yield_pct": portfolio_yield_pct,
        "per_holding_yield": per_holding_yield,
        "upcoming": upcoming,
        "monthly_series": monthly_series,
        "max_monthly_amount": max_monthly_amount,
        "annual_series": annual_series,
        "receipts": receipts,
    }

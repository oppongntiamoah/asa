"""
Cost-basis + P&L calculation — average cost method (MVP scope; FIFO is
post-MVP). Pure-ish functions over a queryset so the math is trivially
unit-testable without needing a full request/response cycle.
"""
from decimal import Decimal

from django.db import transaction as db_transaction

from .models import Holding, Transaction


class InsufficientHoldingError(ValueError):
    """Raised when a sell would take a holding negative — no short positions in MVP."""


def recalculate_holding(user, instrument):
    """
    Replays all transactions for (user, instrument) in trade_date order and
    rebuilds the Holding row. Called synchronously after any transaction
    create/update/delete — volumes are low enough (dozens to low hundreds of
    transactions per user) that this is cheap; no need to make it async.
    """
    txns = Transaction.objects.filter(user=user, instrument=instrument).order_by("trade_date", "created_at", "id")

    quantity = Decimal("0")
    total_cost = Decimal("0")
    realized_pnl = Decimal("0")

    for txn in txns:
        if txn.transaction_type == Transaction.BUY:
            total_cost += txn.gross_amount + txn.fees
            quantity += txn.quantity
        else:  # SELL
            avg_cost = (total_cost / quantity) if quantity else Decimal("0")
            realized_pnl += (txn.price_per_share - avg_cost) * txn.quantity - txn.fees
            total_cost -= avg_cost * txn.quantity
            quantity -= txn.quantity

    average_cost = (total_cost / quantity) if quantity else Decimal("0")

    if quantity <= 0:
        Holding.objects.filter(user=user, instrument=instrument).delete()
        return None

    holding, _ = Holding.objects.update_or_create(
        user=user,
        instrument=instrument,
        defaults={
            "quantity": quantity,
            "average_cost": average_cost,
            "realized_pnl": realized_pnl,
        },
    )
    return holding


def current_holding_quantity(user, instrument, exclude_transaction_id=None) -> Decimal:
    txns = Transaction.objects.filter(user=user, instrument=instrument)
    if exclude_transaction_id:
        txns = txns.exclude(id=exclude_transaction_id)

    quantity = Decimal("0")
    for txn in txns.order_by("trade_date", "created_at", "id"):
        quantity += txn.quantity if txn.transaction_type == Transaction.BUY else -txn.quantity
    return quantity


@db_transaction.atomic
def create_transaction(*, user, instrument, transaction_type, quantity, price_per_share, fees, trade_date, broker="", notes="", source_statement=None):
    if transaction_type == Transaction.SELL:
        held = current_holding_quantity(user, instrument)
        if quantity > held:
            raise InsufficientHoldingError(
                f"Cannot sell {quantity} shares of {instrument.ticker} — you hold {held}."
            )

    txn = Transaction.objects.create(
        user=user,
        instrument=instrument,
        transaction_type=transaction_type,
        quantity=quantity,
        price_per_share=price_per_share,
        fees=fees,
        trade_date=trade_date,
        broker=broker,
        notes=notes,
        source_statement=source_statement,
    )
    recalculate_holding(user, instrument)
    return txn


@db_transaction.atomic
def delete_transaction(transaction: Transaction):
    user, instrument = transaction.user, transaction.instrument
    transaction.delete()
    recalculate_holding(user, instrument)


def total_invested_ever(user) -> Decimal:
    """Sum of every BUY's cost (gross + fees) across all time — the
    denominator for a whole-account total-return %, distinct from
    total_cost_basis which only reflects currently-open positions."""
    total = Decimal("0")
    for txn in Transaction.objects.filter(user=user, transaction_type=Transaction.BUY):
        total += txn.gross_amount + txn.fees
    return total


def todays_change(user):
    """Dollar and % change in portfolio value from the prior close to the
    latest close, across currently-held instruments. None values (rather
    than 0) when there isn't a second price point yet to compare against."""
    holdings = Holding.objects.filter(user=user).select_related("instrument")
    change_amount = Decimal("0")
    prior_total = Decimal("0")
    have_comparison = False

    for holding in holdings:
        bars = list(holding.instrument.price_bars.all()[:2])
        if len(bars) < 2:
            continue
        have_comparison = True
        latest, previous = bars
        change_amount += (latest.close_price - previous.close_price) * holding.quantity
        prior_total += previous.close_price * holding.quantity

    if not have_comparison:
        return {"amount": None, "pct": None}
    pct = (change_amount / prior_total * 100) if prior_total else None
    return {"amount": change_amount, "pct": pct}


def portfolio_summary(user):
    """Aggregate figures for the dashboard header."""
    holdings = Holding.objects.filter(user=user).select_related("instrument")

    total_value = Decimal("0")
    total_cost_basis = Decimal("0")
    has_stale_price = False

    for holding in holdings:
        value = holding.market_value()
        total_cost_basis += holding.cost_basis
        if value is not None:
            total_value += value
        else:
            has_stale_price = True

    total_unrealized_pnl = total_value - total_cost_basis
    total_unrealized_pct = (
        (total_unrealized_pnl / total_cost_basis) * 100 if total_cost_basis else None
    )
    total_realized_pnl = sum((h.realized_pnl for h in holdings), Decimal("0"))

    invested_ever = total_invested_ever(user)
    total_return_pct = (
        ((total_unrealized_pnl + total_realized_pnl) / invested_ever) * 100 if invested_ever else None
    )

    allocations = []
    for holding in holdings:
        value = holding.market_value()
        pct = (value / total_value * 100) if value is not None and total_value else Decimal("0")
        allocations.append({"holding": holding, "value": value, "pct": pct})
    allocations.sort(key=lambda a: a["pct"], reverse=True)

    return {
        "holdings": holdings,
        "allocations": allocations,
        "total_value": total_value,
        "total_cost_basis": total_cost_basis,
        "total_unrealized_pnl": total_unrealized_pnl,
        "total_unrealized_pct": total_unrealized_pct,
        "total_realized_pnl": total_realized_pnl,
        "total_return_pct": total_return_pct,
        "num_holdings": holdings.count(),
        "todays_change": todays_change(user),
        "has_stale_price": has_stale_price,
    }


def sector_allocation(user):
    """Current holdings grouped by Instrument.sector, by market value."""
    holdings = Holding.objects.filter(user=user).select_related("instrument")
    by_sector = {}
    total_value = Decimal("0")

    for holding in holdings:
        value = holding.market_value()
        if value is None:
            continue
        sector = holding.instrument.sector or "Unclassified"
        by_sector[sector] = by_sector.get(sector, Decimal("0")) + value
        total_value += value

    result = [
        {"sector": sector, "value": value, "pct": (value / total_value * 100) if total_value else Decimal("0")}
        for sector, value in by_sector.items()
    ]
    result.sort(key=lambda r: r["pct"], reverse=True)
    return result


def transaction_analysis(user):
    """Buy/sell activity statistics for the Transaction Analysis page."""
    from collections import defaultdict

    from .analytics import average_holding_period_days

    txns = list(Transaction.objects.filter(user=user).select_related("instrument"))
    buys = [t for t in txns if t.transaction_type == Transaction.BUY]
    sells = [t for t in txns if t.transaction_type == Transaction.SELL]

    avg_purchase_price = (
        sum(t.price_per_share * t.quantity for t in buys) / sum(t.quantity for t in buys)
        if buys else None
    )
    largest_purchase = max(buys, key=lambda t: t.gross_amount, default=None)
    largest_sale = max(sells, key=lambda t: t.gross_amount, default=None)

    by_month = defaultdict(lambda: {"buys": Decimal("0"), "sells": Decimal("0"), "count": 0})
    for t in txns:
        key = t.trade_date.strftime("%Y-%m")
        if t.transaction_type == Transaction.BUY:
            by_month[key]["buys"] += t.gross_amount
        else:
            by_month[key]["sells"] += t.gross_amount
        by_month[key]["count"] += 1

    monthly = [{"month": m, **v} for m, v in sorted(by_month.items())]
    span_months = len(by_month) or 1
    trading_frequency = len(txns) / span_months

    return {
        "total_buys": len(buys),
        "total_sells": len(sells),
        "avg_purchase_price": avg_purchase_price,
        "largest_purchase": largest_purchase,
        "largest_sale": largest_sale,
        "avg_holding_period_days": average_holding_period_days(user),
        "monthly": monthly,
        "trading_frequency_per_month": trading_frequency,
    }


def cost_basis_table(user):
    """Per-holding cost basis breakdown for the Cost Basis Analysis page."""
    holdings = Holding.objects.filter(user=user).select_related("instrument")
    rows = []
    for h in holdings:
        current_price = h.latest_price()
        gain_per_share = (current_price - h.average_cost) if current_price is not None else None
        rows.append({
            "holding": h,
            "average_cost": h.average_cost,
            "break_even_price": h.average_cost,  # fees are already folded into average_cost
            "current_price": current_price,
            "gain_per_share": gain_per_share,
            "gain_pct": h.unrealized_pnl_percent(),
        })
    rows.sort(key=lambda r: r["gain_pct"] or 0, reverse=True)
    return rows


def sector_performance(user):
    """Weighted return per sector, for the Sector Analysis page."""
    holdings = Holding.objects.filter(user=user).select_related("instrument")
    by_sector = {}

    for h in holdings:
        sector = h.instrument.sector or "Unclassified"
        value = h.market_value()
        cost = h.cost_basis
        bucket = by_sector.setdefault(sector, {"sector": sector, "invested": Decimal("0"), "value": Decimal("0"), "has_price": True})
        bucket["invested"] += cost
        if value is not None:
            bucket["value"] += value
        else:
            bucket["has_price"] = False

    total_invested = sum((b["invested"] for b in by_sector.values()), Decimal("0"))
    result = []
    for bucket in by_sector.values():
        invested_pct = (bucket["invested"] / total_invested * 100) if total_invested else Decimal("0")
        return_pct = ((bucket["value"] - bucket["invested"]) / bucket["invested"] * 100) if bucket["invested"] else None
        result.append({
            "sector": bucket["sector"],
            "invested": bucket["invested"],
            "invested_pct": invested_pct,
            "value": bucket["value"] if bucket["has_price"] else None,
            "return_pct": return_pct if bucket["has_price"] else None,
        })
    result.sort(key=lambda r: r["invested_pct"], reverse=True)
    return result


def winners_losers(user, limit=10):
    """Splits top_movers into gainers (best first) and losers (worst first)
    among currently-held instruments."""
    movers = top_movers(user, limit=None)
    gainers = sorted((m for m in movers if m["change_pct"] > 0), key=lambda m: m["change_pct"], reverse=True)
    losers = sorted((m for m in movers if m["change_pct"] < 0), key=lambda m: m["change_pct"])
    return {"gainers": gainers[:limit], "losers": losers[:limit]}


def top_movers(user, limit=5):
    """Stocks among the user's holdings with the largest daily % move."""
    from instruments.models import PriceBar

    movers = []
    for holding in Holding.objects.filter(user=user).select_related("instrument"):
        bars = list(holding.instrument.price_bars.all()[:2])
        if len(bars) < 2 or bars[1].close_price == 0:
            continue
        latest, previous = bars
        change_pct = ((latest.close_price - previous.close_price) / previous.close_price) * 100
        movers.append({
            "instrument": holding.instrument,
            "close_price": latest.close_price,
            "change_pct": change_pct,
            "trade_date": latest.trade_date,
        })
    movers.sort(key=lambda m: abs(m["change_pct"]), reverse=True)
    return movers[:limit]

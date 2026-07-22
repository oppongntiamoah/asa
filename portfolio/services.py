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
        "has_stale_price": has_stale_price,
    }


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

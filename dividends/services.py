"""Generates per-user DividendReceipt rows from an admin-entered DividendRecord."""
from decimal import Decimal

from django.contrib.auth import get_user_model

from portfolio.models import Transaction

from .models import DividendReceipt

User = get_user_model()


def _quantity_held_as_of(user, instrument, as_of_date) -> Decimal:
    """Replays transactions up to and including as_of_date to find the
    quantity held on the dividend's record date — Holding only tracks the
    *current* quantity, which isn't necessarily what was held historically."""
    quantity = Decimal("0")
    txns = Transaction.objects.filter(
        user=user, instrument=instrument, trade_date__lte=as_of_date
    ).order_by("trade_date", "created_at", "id")
    for txn in txns:
        quantity += txn.quantity if txn.transaction_type == Transaction.BUY else -txn.quantity
    return quantity


def generate_receipts_for_dividend(dividend_record):
    """Idempotent: safe to call again if the DividendRecord is edited."""
    instrument = dividend_record.instrument
    user_ids = Transaction.objects.filter(instrument=instrument).values_list("user_id", flat=True).distinct()

    created_or_updated = []
    for user in User.objects.filter(id__in=user_ids):
        quantity_held = _quantity_held_as_of(user, instrument, dividend_record.record_date)
        if quantity_held <= 0:
            DividendReceipt.objects.filter(user=user, dividend_record=dividend_record).delete()
            continue

        total_amount = quantity_held * dividend_record.amount_per_share
        receipt, _ = DividendReceipt.objects.update_or_create(
            user=user,
            dividend_record=dividend_record,
            defaults={"quantity_held": quantity_held, "total_amount": total_amount},
        )
        created_or_updated.append(receipt)
    return created_or_updated

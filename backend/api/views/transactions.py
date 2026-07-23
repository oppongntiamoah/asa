"""
Transaction CRUD + cash balance + single-holding detail — the "editable
data" surface the PWA needed beyond the original read-only dashboard/
holdings endpoints. Reuses portfolio.services for all the actual
create/update/delete logic (average-cost recalculation, sell-quantity
guarding) rather than duplicating it here.
"""
from datetime import date
from decimal import Decimal, InvalidOperation

from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from instruments.models import Instrument
from portfolio.forms import CashBalanceForm
from portfolio.models import CashBalance, Transaction
from portfolio.services import (
    InsufficientHoldingError,
    create_transaction,
    current_holding_quantity,
    delete_transaction,
    get_cash_balance,
    recalculate_holding,
)

from ..helpers import decimal_or_none, instrument_dict


def _txn_dict(t):
    return {
        "id": t.id,
        "instrument": instrument_dict(t.instrument),
        "transaction_type": t.transaction_type,
        "quantity": float(t.quantity),
        "price_per_share": float(t.price_per_share),
        "fees": float(t.fees),
        "trade_date": t.trade_date.isoformat(),
        "broker": t.broker,
        "notes": t.notes,
        "gross_amount": float(t.gross_amount),
    }


def _parse_decimal(value, field_errors, field_name, required=True):
    if value in (None, ""):
        if required:
            field_errors[field_name] = "This field is required."
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation:
        field_errors[field_name] = "Enter a valid number."
        return None


def _parse_date(value, field_errors, field_name):
    # DRF/Django cast a DateField from a "YYYY-MM-DD" string fine once
    # persisted, but the in-memory model instance keeps whatever Python
    # type was assigned until it's reloaded from the DB — so a freshly
    # created/updated object's .trade_date is still a str here, and
    # .isoformat() on it blows up when the response gets serialized.
    if not value:
        field_errors[field_name] = "This field is required."
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(value)
    except ValueError:
        field_errors[field_name] = "Enter a valid date (YYYY-MM-DD)."
        return None


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def transactions(request):
    if request.method == "GET":
        txns = Transaction.objects.filter(user=request.user).select_related("instrument").order_by("-trade_date", "-id")
        return Response([_txn_dict(t) for t in txns])

    data = request.data
    errors = {}

    instrument = None
    instrument_id = data.get("instrument_id")
    if not instrument_id:
        errors["instrument_id"] = "Select an instrument."
    else:
        instrument = Instrument.objects.filter(pk=instrument_id, is_active=True).first()
        if instrument is None:
            errors["instrument_id"] = "Unknown or inactive instrument."

    transaction_type = data.get("transaction_type")
    if transaction_type not in (Transaction.BUY, Transaction.SELL):
        errors["transaction_type"] = "Must be BUY or SELL."

    quantity = _parse_decimal(data.get("quantity"), errors, "quantity")
    price_per_share = _parse_decimal(data.get("price_per_share"), errors, "price_per_share")
    fees = _parse_decimal(data.get("fees", "0"), errors, "fees", required=False) or Decimal("0")
    trade_date = _parse_date(data.get("trade_date"), errors, "trade_date")

    if errors:
        return Response({"errors": errors}, status=400)

    try:
        txn = create_transaction(
            user=request.user,
            instrument=instrument,
            transaction_type=transaction_type,
            quantity=quantity,
            price_per_share=price_per_share,
            fees=fees,
            trade_date=trade_date,
            broker=data.get("broker", ""),
            notes=data.get("notes", ""),
        )
    except InsufficientHoldingError as exc:
        return Response({"errors": {"quantity": str(exc)}}, status=400)

    return Response(_txn_dict(txn), status=201)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def transaction_detail(request, pk):
    txn = get_object_or_404(Transaction, pk=pk, user=request.user)

    if request.method == "DELETE":
        delete_transaction(txn)
        return Response(status=204)

    data = request.data
    errors = {}

    instrument = txn.instrument
    if "instrument_id" in data:
        instrument = Instrument.objects.filter(pk=data["instrument_id"], is_active=True).first()
        if instrument is None:
            errors["instrument_id"] = "Unknown or inactive instrument."

    transaction_type = data.get("transaction_type", txn.transaction_type)
    if transaction_type not in (Transaction.BUY, Transaction.SELL):
        errors["transaction_type"] = "Must be BUY or SELL."

    quantity = _parse_decimal(data.get("quantity", txn.quantity), errors, "quantity")
    price_per_share = _parse_decimal(data.get("price_per_share", txn.price_per_share), errors, "price_per_share")
    fees = _parse_decimal(data.get("fees", txn.fees), errors, "fees", required=False)
    trade_date = _parse_date(data.get("trade_date", txn.trade_date), errors, "trade_date")

    if errors:
        return Response({"errors": errors}, status=400)

    old_instrument = txn.instrument
    txn.instrument = instrument
    txn.transaction_type = transaction_type
    txn.quantity = quantity
    txn.price_per_share = price_per_share
    txn.fees = fees if fees is not None else txn.fees
    txn.trade_date = trade_date
    txn.broker = data.get("broker", txn.broker)
    txn.notes = data.get("notes", txn.notes)

    if transaction_type == Transaction.SELL:
        held = current_holding_quantity(request.user, instrument, exclude_transaction_id=txn.id)
        if quantity > held:
            return Response(
                {"errors": {"quantity": f"Cannot sell {quantity} shares of {instrument.ticker} — you hold {held}."}},
                status=400,
            )

    txn.save()
    recalculate_holding(request.user, old_instrument)
    if instrument.id != old_instrument.id:
        recalculate_holding(request.user, instrument)

    return Response(_txn_dict(txn))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def check_sell_quantity(request):
    instrument_id = request.GET.get("instrument")
    quantity = request.GET.get("quantity")
    exclude_id = request.GET.get("exclude")

    if not instrument_id or not quantity:
        return Response({"ok": True})

    try:
        instrument = Instrument.objects.get(pk=instrument_id)
        quantity_decimal = Decimal(quantity)
    except (Instrument.DoesNotExist, InvalidOperation):
        return Response({"ok": True})

    held = current_holding_quantity(request.user, instrument, exclude_transaction_id=exclude_id)
    if quantity_decimal > held:
        return Response({"ok": False, "message": f"You only hold {held} shares of {instrument.ticker}."})
    return Response({"ok": True})


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def cash_balance(request):
    balance, _ = CashBalance.objects.get_or_create(user=request.user)

    if request.method == "GET":
        return Response({"amount_ghs": float(balance.amount_ghs)})

    form = CashBalanceForm(request.data, instance=balance)
    if not form.is_valid():
        return Response({"errors": form.errors}, status=400)
    form.save()
    return Response({"amount_ghs": float(balance.amount_ghs)})



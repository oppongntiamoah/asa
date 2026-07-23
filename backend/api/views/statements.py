"""
Statement upload -> parse -> review -> confirm, as a JSON API. Mirrors
statements/views.py exactly (same credit gating, same async parse task,
same commit logic) — this is the "editable, re-uploadable" data flow:
users can fix a misparsed row here rather than being stuck with whatever
the PDF parser guessed, and re-uploading a fresh statement is just
uploading again (each upload is its own StatementUpload, nothing is
overwritten).
"""
from datetime import date
from decimal import Decimal, InvalidOperation

from billing.services import consume_credit, get_or_create_balance, has_credit, is_billing_enabled
from django.db import transaction as db_transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_q.tasks import async_task
from instruments.models import Instrument
from portfolio.services import InsufficientHoldingError, create_transaction
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..helpers import decimal_or_none, instrument_dict
from statements.models import ExtractedTransaction, StatementUpload


def _statement_dict(s):
    return {
        "id": s.id,
        "broker": s.broker,
        "broker_display": s.get_broker_display(),
        "status": s.status,
        "parse_error": s.parse_error,
        "uploaded_at": s.uploaded_at.isoformat(),
        "confirmed_at": s.confirmed_at.isoformat() if s.confirmed_at else None,
    }


def _row_dict(row):
    return {
        "id": row.id,
        "raw_ticker_text": row.raw_ticker_text,
        "matched_instrument": instrument_dict(row.matched_instrument) if row.matched_instrument else None,
        "transaction_type": row.transaction_type,
        "quantity": decimal_or_none(row.quantity),
        "price_per_share": decimal_or_none(row.price_per_share),
        "fees": float(row.fees),
        "trade_date": row.trade_date.isoformat() if row.trade_date else None,
        "confidence": row.confidence,
        "parse_notes": row.parse_notes,
        "is_confirmed": row.is_confirmed,
        "is_excluded": row.is_excluded,
    }


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def statements(request):
    if request.method == "GET":
        qs = StatementUpload.objects.filter(user=request.user)
        return Response([_statement_dict(s) for s in qs])

    if not has_credit(request.user, "pdf_processing"):
        return Response({"errors": {"file": "You're out of PDF processing credits."}}, status=402)

    broker = request.data.get("broker")
    file = request.data.get("file")
    if broker not in dict(StatementUpload.BROKER_CHOICES):
        return Response({"errors": {"broker": "Select a broker."}}, status=400)
    if not file:
        return Response({"errors": {"file": "Choose a PDF file."}}, status=400)

    statement = StatementUpload.objects.create(user=request.user, broker=broker, file=file)
    consume_credit(request.user, "pdf_processing")
    async_task("statements.tasks.parse_statement", statement.id)

    return Response(_statement_dict(statement), status=201)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def statement_detail(request, pk):
    statement = get_object_or_404(StatementUpload, pk=pk, user=request.user)
    return Response(_statement_dict(statement))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def statement_rows(request, pk):
    statement = get_object_or_404(StatementUpload, pk=pk, user=request.user)
    rows = ExtractedTransaction.objects.filter(statement=statement).select_related("matched_instrument")
    return Response({"statement": _statement_dict(statement), "rows": [_row_dict(r) for r in rows]})


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def statement_row_detail(request, pk, row_id):
    statement = get_object_or_404(StatementUpload, pk=pk, user=request.user, status=StatementUpload.NEEDS_REVIEW)
    row = get_object_or_404(ExtractedTransaction, pk=row_id, statement=statement)

    data = request.data
    if "matched_instrument_id" in data:
        row.matched_instrument = (
            Instrument.objects.filter(pk=data["matched_instrument_id"], is_active=True).first()
            if data["matched_instrument_id"] else None
        )
    if "transaction_type" in data:
        row.transaction_type = data["transaction_type"]
    if "quantity" in data:
        try:
            row.quantity = Decimal(str(data["quantity"])) if data["quantity"] not in (None, "") else None
        except InvalidOperation:
            return Response({"errors": {"quantity": "Enter a valid number."}}, status=400)
    if "price_per_share" in data:
        try:
            row.price_per_share = Decimal(str(data["price_per_share"])) if data["price_per_share"] not in (None, "") else None
        except InvalidOperation:
            return Response({"errors": {"price_per_share": "Enter a valid number."}}, status=400)
    if "trade_date" in data:
        raw_date = data["trade_date"]
        if not raw_date:
            row.trade_date = None
        else:
            try:
                row.trade_date = date.fromisoformat(raw_date)
            except ValueError:
                return Response({"errors": {"trade_date": "Enter a valid date (YYYY-MM-DD)."}}, status=400)
    if "is_excluded" in data:
        row.is_excluded = bool(data["is_excluded"])

    row.save()
    return Response(_row_dict(row))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def statement_confirm(request, pk):
    statement = get_object_or_404(StatementUpload, pk=pk, user=request.user, status=StatementUpload.NEEDS_REVIEW)
    rows = list(ExtractedTransaction.objects.filter(statement=statement).select_related("matched_instrument"))

    to_commit = []
    row_errors = {}
    for row in rows:
        if row.is_excluded:
            continue
        if not (row.matched_instrument and row.quantity and row.price_per_share and row.trade_date and row.transaction_type):
            row_errors[row.id] = "Fill in every field or exclude this row before confirming."
        else:
            to_commit.append(row)

    if row_errors:
        return Response({"errors": {"rows": row_errors}}, status=400)

    to_commit.sort(key=lambda r: r.trade_date)
    try:
        with db_transaction.atomic():
            for row in to_commit:
                row.is_confirmed = True
                row.save()
                create_transaction(
                    user=request.user,
                    instrument=row.matched_instrument,
                    transaction_type=row.transaction_type,
                    quantity=row.quantity,
                    price_per_share=row.price_per_share,
                    fees=row.fees,
                    trade_date=row.trade_date,
                    broker=statement.get_broker_display(),
                    source_statement=statement,
                )
            statement.status = StatementUpload.CONFIRMED
            statement.confirmed_at = timezone.now()
            statement.save(update_fields=["status", "confirmed_at"])
    except InsufficientHoldingError as exc:
        return Response({"errors": {"non_field": (
            f"Couldn't commit: {exc} This can happen if an earlier purchase of this stock — e.g. "
            f"an IPO allocation row above that's excluded by default — needs to be completed first. "
            f"Complete that row, or exclude/adjust this sell, and try again."
        )}}, status=400)

    return Response({"committed": len(to_commit), "statement": _statement_dict(statement)})

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from corporate_actions.models import CorporateAction
from instruments.models import Instrument

from .forms import TransactionForm
from .models import Holding, Transaction
from .services import (
    InsufficientHoldingError,
    create_transaction,
    current_holding_quantity,
    delete_transaction,
    portfolio_summary,
    top_movers,
)


@login_required
def dashboard(request):
    summary = portfolio_summary(request.user)
    has_any_transactions = Transaction.objects.filter(user=request.user).exists()

    context = {
        **summary,
        "has_any_transactions": has_any_transactions,
        "top_movers": top_movers(request.user),
        "upcoming_actions": CorporateAction.objects.filter(
            instrument__holdings__user=request.user
        ).distinct().order_by("event_date")[:5],
    }
    return render(request, "portfolio/dashboard.html", context)


@login_required
def holdings_list(request):
    holdings = Holding.objects.filter(user=request.user).select_related("instrument")
    return render(request, "portfolio/holdings_list.html", {"holdings": holdings})


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

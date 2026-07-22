from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction as db_transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django_q.tasks import async_task

from billing.services import consume_credit, get_or_create_balance, has_credit, is_billing_enabled
from portfolio.services import InsufficientHoldingError, create_transaction

from .forms import ExtractedTransactionFormSet, StatementUploadForm
from .models import ExtractedTransaction, StatementUpload


@login_required
def upload(request):
    if request.method == "POST":
        if not has_credit(request.user, "pdf_processing"):
            messages.error(request, "You're out of PDF processing credits.")
            return redirect("billing:pricing")

        form = StatementUploadForm(request.POST, request.FILES)
        if form.is_valid():
            statement = form.save(commit=False)
            statement.user = request.user
            statement.save()
            consume_credit(request.user, "pdf_processing")
            async_task("statements.tasks.parse_statement", statement.id)
            return redirect("statements:status", pk=statement.pk)
    else:
        form = StatementUploadForm()

    context = {"form": form, "billing_enabled": is_billing_enabled()}
    if context["billing_enabled"]:
        context["credits_remaining"] = get_or_create_balance(request.user).pdf_processing_credits
    return render(request, "statements/upload.html", context)


@login_required
def status(request, pk):
    """Polled via HTMX while the async parse task runs."""
    statement = get_object_or_404(StatementUpload, pk=pk, user=request.user)
    is_htmx = request.headers.get("HX-Request") == "true"

    if statement.status == StatementUpload.NEEDS_REVIEW:
        target_url = reverse("statements:review", kwargs={"pk": statement.pk})
        return HttpResponse(headers={"HX-Redirect": target_url}) if is_htmx else redirect(target_url)
    if statement.status == StatementUpload.FAILED:
        if is_htmx:
            target_url = reverse("statements:status", kwargs={"pk": statement.pk})
            return HttpResponse(headers={"HX-Redirect": target_url})
        return render(request, "statements/failed.html", {"statement": statement})

    template = "statements/_status_poll.html" if is_htmx else "statements/status.html"
    return render(request, template, {"statement": statement})


@login_required
def review(request, pk):
    statement = get_object_or_404(StatementUpload, pk=pk, user=request.user, status=StatementUpload.NEEDS_REVIEW)
    queryset = ExtractedTransaction.objects.filter(statement=statement)

    if request.method == "POST":
        formset = ExtractedTransactionFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            to_commit = []
            has_row_errors = False

            for form in formset:
                row = form.save(commit=False)
                if row.is_excluded:
                    continue
                if not (row.matched_instrument and row.quantity and row.price_per_share and row.trade_date and row.transaction_type):
                    form.add_error(None, "Fill in every field or exclude this row before confirming.")
                    has_row_errors = True
                else:
                    to_commit.append(row)

            if not has_row_errors:
                # Sort by trade_date so sells within the same statement never
                # land before the buy that funded them purely due to PDF row order.
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
                        for form in formset:
                            excluded_row = form.instance
                            if excluded_row.is_excluded:
                                excluded_row.save()

                        statement.status = StatementUpload.CONFIRMED
                        statement.confirmed_at = timezone.now()
                        statement.save(update_fields=["status", "confirmed_at"])
                except InsufficientHoldingError as exc:
                    messages.error(
                        request,
                        f"Couldn't commit: {exc} This can happen if an earlier purchase of this stock — e.g. "
                        f"an IPO allocation row above that's excluded by default — needs to be completed first. "
                        f"Complete that row, or exclude/adjust this sell, and try again.",
                    )
                else:
                    messages.success(request, f"{len(to_commit)} transactions added to your portfolio.")
                    return redirect("statements:confirmed", pk=statement.pk)
    else:
        formset = ExtractedTransactionFormSet(queryset=queryset)

    rows_and_forms = list(zip(queryset, formset.forms))
    included_count = sum(1 for row, _ in rows_and_forms if not row.is_excluded)
    return render(
        request, "statements/review.html",
        {"statement": statement, "formset": formset, "rows_and_forms": rows_and_forms, "included_count": included_count},
    )


@login_required
def confirmed(request, pk):
    statement = get_object_or_404(StatementUpload, pk=pk, user=request.user, status=StatementUpload.CONFIRMED)
    count = statement.committed_transactions.count()
    return render(request, "statements/confirmed.html", {"statement": statement, "count": count})

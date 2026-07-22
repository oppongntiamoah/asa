import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from . import paystack
from .models import BillingSettings, Plan, Purchase
from .services import confirm_purchase, get_or_create_balance, is_billing_enabled

logger = logging.getLogger(__name__)


def pricing(request):
    plans = Plan.objects.filter(is_active=True)
    return render(request, "billing/pricing.html", {"plans": plans, "billing_enabled": is_billing_enabled()})


@login_required
def my_credits(request):
    balance = get_or_create_balance(request.user)
    purchases = Purchase.objects.filter(user=request.user)
    return render(
        request, "billing/my_credits.html",
        {"balance": balance, "purchases": purchases, "billing_enabled": is_billing_enabled()},
    )


@login_required
@require_POST
def start_purchase(request, plan_code):
    plan = get_object_or_404(Plan, code=plan_code, is_active=True)
    reference = paystack.generate_reference()

    purchase = Purchase.objects.create(
        user=request.user,
        plan=plan,
        amount_ghs=plan.price_ghs,
        provider_reference=reference,
    )

    if not settings_configured():
        # No live Paystack keys in this environment — fail loudly rather than
        # pretending checkout works, so this is never silently broken in prod.
        messages.error(request, "Payments aren't configured yet. Please try again later.")
        return redirect("billing:pricing")

    try:
        data = paystack.initialize_transaction(
            email=request.user.email or f"{request.user.username}@sikatrack.local",
            amount_ghs=plan.price_ghs,
            reference=reference,
            callback_url=request.build_absolute_uri(reverse("billing:callback")),
        )
    except paystack.PaystackError as exc:
        logger.exception("Paystack initialize failed for purchase %s", purchase.id)
        purchase.status = Purchase.FAILED
        purchase.save(update_fields=["status"])
        messages.error(request, f"Couldn't start checkout: {exc}")
        return redirect("billing:pricing")

    return redirect(data["authorization_url"])


def settings_configured() -> bool:
    from django.conf import settings
    return bool(settings.PAYSTACK_SECRET_KEY)


@login_required
def callback(request):
    """Paystack redirects the user's browser here after checkout. This is a
    UX convenience only — the webhook is the authoritative success signal
    (see paystack.py docstring) — but verifying directly here lets us show
    an immediate result instead of making the user wait on webhook latency.
    confirm_purchase() is idempotent, so it's safe if the webhook also fires."""
    reference = request.GET.get("reference") or request.GET.get("trxref")
    purchase = get_object_or_404(Purchase, provider_reference=reference, user=request.user)

    if purchase.status != Purchase.SUCCESS and settings_configured():
        try:
            data = paystack.verify_transaction(reference)
            purchase.momo_network = (data.get("authorization") or {}).get("channel", "")
            if data.get("status") == "success":
                confirm_purchase(purchase)
            elif data.get("status") in ("failed", "abandoned"):
                purchase.status = Purchase.FAILED
                purchase.save(update_fields=["status", "momo_network"])
        except paystack.PaystackError:
            logger.exception("Paystack verify failed for purchase %s", purchase.id)

    return render(request, "billing/callback.html", {"purchase": purchase})


@csrf_exempt
@require_POST
def webhook(request):
    signature = request.headers.get("x-paystack-signature", "")
    if not paystack.verify_webhook_signature(request.body, signature):
        return HttpResponseBadRequest("invalid signature")

    try:
        event = json.loads(request.body)
    except ValueError:
        return HttpResponseBadRequest("invalid json")

    if event.get("event") == "charge.success":
        reference = event.get("data", {}).get("reference")
        try:
            purchase = Purchase.objects.get(provider_reference=reference)
        except Purchase.DoesNotExist:
            logger.warning("Webhook for unknown purchase reference %s", reference)
            return HttpResponse(status=200)  # ack anyway — nothing to retry

        purchase.raw_webhook_payload = event
        purchase.momo_network = event.get("data", {}).get("channel", "")
        purchase.save(update_fields=["raw_webhook_payload", "momo_network"])
        confirm_purchase(purchase)

    return HttpResponse(status=200)

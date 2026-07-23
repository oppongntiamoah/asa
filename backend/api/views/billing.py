import logging

from billing import paystack
from billing.models import Plan, Purchase
from billing.services import get_or_create_balance, is_billing_enabled
from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

logger = logging.getLogger(__name__)


def _plan_dict(p):
    return {
        "code": p.code,
        "name": p.name,
        "price_ghs": float(p.price_ghs),
        "pdf_processing_credits": p.pdf_processing_credits,
        "stock_alert_credits": p.stock_alert_credits,
        "dividend_alert_credits": p.dividend_alert_credits,
        "data_export_credits": p.data_export_credits,
        "max_devices": p.max_devices,
        "feature_bullets": p.feature_bullets,
    }


@api_view(["GET"])
@permission_classes([AllowAny])
def plans(request):
    return Response({
        "billing_enabled": is_billing_enabled(),
        "plans": [_plan_dict(p) for p in Plan.objects.filter(is_active=True)],
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def credits(request):
    balance = get_or_create_balance(request.user)
    purchases = Purchase.objects.filter(user=request.user)
    return Response({
        "billing_enabled": is_billing_enabled(),
        "balance": {
            "pdf_processing_credits": balance.pdf_processing_credits,
            "stock_alert_credits": balance.stock_alert_credits,
            "dividend_alert_credits": balance.dividend_alert_credits,
            "data_export_credits": balance.data_export_credits,
        },
        "purchases": [
            {
                "id": p.id,
                "plan_code": p.plan.code,
                "plan_name": p.plan.name,
                "amount_ghs": float(p.amount_ghs),
                "status": p.status,
                "created_at": p.created_at.isoformat(),
                "confirmed_at": p.confirmed_at.isoformat() if p.confirmed_at else None,
            }
            for p in purchases
        ],
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def start_purchase(request, plan_code):
    from django.conf import settings

    plan = get_object_or_404(Plan, code=plan_code, is_active=True)
    reference = paystack.generate_reference()

    purchase = Purchase.objects.create(
        user=request.user, plan=plan, amount_ghs=plan.price_ghs, provider_reference=reference,
    )

    if not settings.PAYSTACK_SECRET_KEY:
        purchase.status = Purchase.FAILED
        purchase.save(update_fields=["status"])
        return Response({"errors": {"non_field": "Payments aren't configured yet. Please try again later."}}, status=503)

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
        return Response({"errors": {"non_field": f"Couldn't start checkout: {exc}"}}, status=502)

    return Response({"authorization_url": data["authorization_url"]})

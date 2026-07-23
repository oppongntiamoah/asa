"""
Thin Paystack client for one-time mobile money checkout. See
PRODUCT_DESIGN.md §6.3 for the flow rationale (hosted checkout so
SikaTrack never touches a MoMo PIN; webhook is the source of truth for
payment success, never the redirect alone).

Requires PAYSTACK_SECRET_KEY in the environment. Untestable without live
Paystack credentials — the surrounding views/signature verification are
unit-testable independently of the actual HTTP calls here.
"""
import hashlib
import hmac
import uuid

import requests
from django.conf import settings

PAYSTACK_BASE_URL = "https://api.paystack.co"


class PaystackError(Exception):
    pass


def _headers():
    return {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }


def generate_reference() -> str:
    return f"sikatrack_{uuid.uuid4().hex[:20]}"


def initialize_transaction(*, email: str, amount_ghs, reference: str, callback_url: str) -> dict:
    """Amount is converted to pesewas (Paystack's base unit, like cents)."""
    amount_pesewas = int(amount_ghs * 100)
    response = requests.post(
        f"{PAYSTACK_BASE_URL}/transaction/initialize",
        headers=_headers(),
        json={
            "email": email,
            "amount": amount_pesewas,
            "reference": reference,
            "callback_url": callback_url,
            "currency": "GHS",
            "channels": ["mobile_money", "card"],
        },
        timeout=15,
    )
    data = response.json()
    if not data.get("status"):
        raise PaystackError(data.get("message", "Paystack initialize failed"))
    return data["data"]  # includes authorization_url to redirect the user to


def verify_transaction(reference: str) -> dict:
    response = requests.get(
        f"{PAYSTACK_BASE_URL}/transaction/verify/{reference}", headers=_headers(), timeout=15
    )
    data = response.json()
    if not data.get("status"):
        raise PaystackError(data.get("message", "Paystack verify failed"))
    return data["data"]


def verify_webhook_signature(request_body: bytes, signature_header: str) -> bool:
    """
    Paystack signs webhook payloads with HMAC-SHA512 of the raw request body
    using the secret key. Never trust a webhook without this check — it's
    the only thing standing between "a payment happened" and "someone POSTed
    to our webhook URL claiming a payment happened."
    """
    if not signature_header or not settings.PAYSTACK_SECRET_KEY:
        return False
    computed = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode("utf-8"), request_body, hashlib.sha512
    ).hexdigest()
    return hmac.compare_digest(computed, signature_header)

"""
Credit gating for paid features. The single entry point every feature
should call is has_credit()/consume_credit() — never check CreditBalance
directly — so the free/paid toggle in BillingSettings has exactly one
place to intercept.
"""
from .models import BillingSettings, CreditBalance, Plan, Purchase

CREDIT_FIELDS = {
    "pdf_processing": "pdf_processing_credits",
    "stock_alert": "stock_alert_credits",
    "dividend_alert": "dividend_alert_credits",
    "data_export": "data_export_credits",
}


class InsufficientCreditsError(Exception):
    def __init__(self, credit_type):
        self.credit_type = credit_type
        super().__init__(f"Not enough {credit_type} credits.")


def is_billing_enabled() -> bool:
    return BillingSettings.load().billing_enabled


def get_or_create_balance(user) -> CreditBalance:
    balance, _ = CreditBalance.objects.get_or_create(user=user)
    return balance


def has_credit(user, credit_type: str) -> bool:
    """True if the user can use this feature right now — always True while
    billing is switched off, regardless of their actual balance."""
    if not is_billing_enabled():
        return True
    field = CREDIT_FIELDS[credit_type]
    balance = get_or_create_balance(user)
    return getattr(balance, field) > 0


def consume_credit(user, credit_type: str) -> None:
    """Deducts one credit. No-op while billing is off. Raises
    InsufficientCreditsError if billing is on and the balance is exhausted —
    callers should check has_credit() first to avoid hitting this in the
    normal path, but this guards against a race between check and use."""
    if not is_billing_enabled():
        return
    field = CREDIT_FIELDS[credit_type]
    balance = get_or_create_balance(user)
    if getattr(balance, field) <= 0:
        raise InsufficientCreditsError(credit_type)
    setattr(balance, field, getattr(balance, field) - 1)
    balance.save(update_fields=[field, "updated_at"])


def grant_plan_credits(user, plan: Plan) -> CreditBalance:
    """Adds a purchased plan's credit allotment on top of whatever the user
    already has — one-time purchases stack rather than reset a balance.
    max_portfolios is a cap, not a spendable credit, so it's raised to the
    plan's level rather than added — buying BASIC after PRO shouldn't push
    it back down, and buying PRO twice shouldn't double it."""
    balance = get_or_create_balance(user)
    for credit_type, field in CREDIT_FIELDS.items():
        plan_amount = getattr(plan, field)
        setattr(balance, field, getattr(balance, field) + plan_amount)
    balance.max_portfolios = max(balance.max_portfolios, plan.max_portfolios)
    balance.save()
    return balance


def max_portfolios_for_user(user) -> int:
    """How many portfolios this user may create. Uncapped while billing is
    off, mirroring has_credit()'s free-for-everyone behavior — once billing
    is on, it's the free-tier default (1) unless raised by a purchased
    plan."""
    if not is_billing_enabled():
        return 10_000
    return get_or_create_balance(user).max_portfolios


def confirm_purchase(purchase: Purchase) -> None:
    """Marks a Purchase successful and grants its plan's credits. Idempotent
    — safe to call twice for the same purchase (e.g. a retried webhook)."""
    from django.utils import timezone

    if purchase.status == Purchase.SUCCESS:
        return
    purchase.status = Purchase.SUCCESS
    purchase.confirmed_at = timezone.now()
    purchase.save(update_fields=["status", "confirmed_at"])
    grant_plan_credits(purchase.user, purchase.plan)

from django.conf import settings
from django.db import models


class BillingSettings(models.Model):
    """
    Singleton switch: while billing_enabled is False, every credit check in
    services.py passes automatically regardless of actual balance — the
    whole app is free. Flip it on later from Django admin, no deploy needed.
    Enforced as a singleton via pk=1 in save()/load(), the common lightweight
    pattern for one global toggle that doesn't warrant a separate settings
    library dependency.
    """

    billing_enabled = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # singleton — never actually delete the row

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return f"Billing is {'ON (paid)' if self.billing_enabled else 'OFF (everything free)'}"


class Plan(models.Model):
    """
    One-time-purchase plan (not a recurring subscription — see Purchase).
    Numeric credit fields are the ones actually enforced by services.py
    today (currently just pdf_processing_credits, since statement upload is
    the one credit-consuming feature that exists). The others are modeled
    now so Plan matches the real pricing tiers, but aren't checked anywhere
    yet — there's no alert delivery or CSV export built to spend them on.
    feature_bullets holds pure marketing checklist lines (priority support,
    AI assistant, etc.) that don't correspond to an enforceable limit at all.
    """

    code = models.CharField(max_length=20, unique=True)  # "BASIC", "PRO", "ULTRA"
    name = models.CharField(max_length=50)
    price_ghs = models.DecimalField(max_digits=8, decimal_places=2)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    pdf_processing_credits = models.PositiveIntegerField(default=0)
    stock_alert_credits = models.PositiveIntegerField(default=0)
    dividend_alert_credits = models.PositiveIntegerField(default=0)
    data_export_credits = models.PositiveIntegerField(default=0)
    max_devices = models.PositiveIntegerField(default=1)

    feature_bullets = models.JSONField(
        default=list, blank=True,
        help_text="Extra marketing checklist lines shown on the pricing card, e.g. "
                   "'Priority processing and support', 'AI-powered financial assistant'.",
    )

    class Meta:
        ordering = ["sort_order"]

    def __str__(self):
        return f"{self.name} — GHS {self.price_ghs}"


class Purchase(models.Model):
    INITIATED = "INITIATED"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    STATUS_CHOICES = [(INITIATED, "Initiated"), (SUCCESS, "Success"), (FAILED, "Failed")]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="purchases")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="purchases")
    amount_ghs = models.DecimalField(max_digits=8, decimal_places=2)
    provider = models.CharField(max_length=20, default="PAYSTACK")
    provider_reference = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=INITIATED)
    momo_network = models.CharField(max_length=20, blank=True)
    raw_webhook_payload = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} — {self.plan.code} ({self.status})"


class CreditBalance(models.Model):
    """Running per-user credit balances. Purchases add to these; features spend them."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="credit_balance")
    pdf_processing_credits = models.IntegerField(default=0)
    stock_alert_credits = models.IntegerField(default=0)
    dividend_alert_credits = models.IntegerField(default=0)
    data_export_credits = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} credits"

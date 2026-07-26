from django.conf import settings
from django.db import models


class StatementUpload(models.Model):
    PENDING = "PENDING"
    PARSING = "PARSING"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"
    STATUS_CHOICES = [
        (PENDING, "Pending"), (PARSING, "Parsing"), (NEEDS_REVIEW, "Needs review"),
        (CONFIRMED, "Confirmed"), (FAILED, "Failed"),
    ]

    BROKER_CHOICES = [
        ("IC_SECURITIES", "IC Securities"),
        ("BLACKSTAR", "Black Star Advisors"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="statement_uploads")
    broker = models.CharField(max_length=30, choices=BROKER_CHOICES)
    file = models.FileField(upload_to="statements/%Y/%m/")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    parse_error = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.user} — {self.get_broker_display()} ({self.status})"


class ExtractedTransaction(models.Model):
    """
    One row per transaction the parser found. Exists independently of
    portfolio.Transaction so the review/edit step never touches committed
    data — only on confirm do rows become real Transaction objects.
    """

    statement = models.ForeignKey(StatementUpload, on_delete=models.CASCADE, related_name="extracted_rows")
    raw_ticker_text = models.CharField(max_length=100, blank=True)
    matched_instrument = models.ForeignKey(
        "instruments.Instrument", null=True, blank=True, on_delete=models.SET_NULL
    )
    transaction_type = models.CharField(max_length=4, choices=[("BUY", "Buy"), ("SELL", "Sell")], blank=True)
    quantity = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    price_per_share = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    trade_date = models.DateField(null=True, blank=True)
    confidence = models.CharField(
        max_length=10, choices=[("HIGH", "High"), ("LOW", "Low — needs review")], default="HIGH"
    )
    parse_notes = models.TextField(blank=True)
    is_confirmed = models.BooleanField(default=False)
    is_excluded = models.BooleanField(default=False)
    row_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["row_order"]

    def __str__(self):
        return f"{self.raw_ticker_text} {self.transaction_type} {self.quantity}"

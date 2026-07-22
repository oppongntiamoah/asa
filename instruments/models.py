from django.conf import settings
from django.db import models


class Instrument(models.Model):
    """A GSE-listed security."""

    ticker = models.CharField(max_length=12, unique=True)  # e.g. "MTNGH", "GCB", "EGL"
    name = models.CharField(max_length=255)
    sector = models.CharField(max_length=100, blank=True)
    isin = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)  # False if delisted/suspended
    listed_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["ticker"]

    def __str__(self):
        return self.ticker

    def latest_price(self):
        return self.price_bars.first()


class PriceBar(models.Model):
    """One daily closing observation. Deliberately NOT a live quote model."""

    SOURCE_CHOICES = [("csv_upload", "Manual CSV upload"), ("scrape", "Automated scrape")]

    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE, related_name="price_bars")
    trade_date = models.DateField()
    close_price = models.DecimalField(max_digits=12, decimal_places=4)
    open_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    high_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    low_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="csv_upload")
    ingested_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["instrument", "trade_date"], name="uniq_price_per_day")
        ]
        indexes = [models.Index(fields=["instrument", "-trade_date"])]
        ordering = ["-trade_date"]

    def __str__(self):
        return f"{self.instrument.ticker} {self.trade_date} @ {self.close_price}"


class PriceIngestBatch(models.Model):
    """Audit trail for each CSV upload/scrape run — critical for debugging bad data."""

    source = models.CharField(max_length=20, default="csv_upload")
    trade_date = models.DateField()
    row_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    raw_file = models.FileField(upload_to="price_ingest/", null=True, blank=True)
    error_log = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.trade_date} ({self.row_count} rows, {self.error_count} errors)"

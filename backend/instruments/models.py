from django.conf import settings
from django.db import models


class Instrument(models.Model):
    """
    A tradeable holding. Despite the app's original GSE-equities-only scope,
    this also covers money market/liquidity funds and fixed income —
    anything a broker statement lists as a position — because they fit the
    exact same shape (a ticker/name, a periodic unit price, buy/sell
    transactions against it) as an equity. Reusing Instrument/PriceBar/
    Transaction/Holding for these means no new data model or UI was needed
    to support them; only asset_class distinguishes them, mainly for
    portfolio-breakdown reporting. Real bonds have coupon/maturity
    structure this doesn't model — acceptable for now since the only real
    fixed-income case seen so far (the founder's own IC statement) has a
    zero balance; revisit with dedicated fields if that becomes untrue.
    """

    EQUITY = "EQUITY"
    FUND = "FUND"
    FIXED_INCOME = "FIXED_INCOME"
    ASSET_CLASS_CHOICES = [
        (EQUITY, "Equity"),
        (FUND, "Fund"),
        (FIXED_INCOME, "Fixed Income"),
    ]

    ticker = models.CharField(max_length=12, unique=True)  # e.g. "MTNGH", "GCB", "EGL"
    name = models.CharField(max_length=255)
    asset_class = models.CharField(max_length=20, choices=ASSET_CLASS_CHOICES, default=EQUITY)
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
    turnover_value = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True,
        help_text="GSE's 'Total Value Traded (GH¢)' — stored directly from the "
                   "source rather than derived (volume × close), since it's VWAP-based.",
    )
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

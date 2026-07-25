from django.conf import settings
from django.db import models


class Portfolio(models.Model):
    """
    A fully separate ledger — its own transactions, holdings, and cash
    balance — so a user can track e.g. a personal account and a retirement
    account side by side without their positions mixing. Every user has at
    least one (auto-created on signup); how many more they can add is
    capped by their billing.Plan.max_portfolios.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="portfolios")
    name = models.CharField(max_length=100)
    is_default = models.BooleanField(
        default=False,
        help_text="The portfolio a user lands on when no other is selected. Exactly one per user.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.name} ({self.user})"


class Transaction(models.Model):
    BUY = "BUY"
    SELL = "SELL"
    TYPE_CHOICES = [(BUY, "Buy"), (SELL, "Sell")]

    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="transactions")
    instrument = models.ForeignKey("instruments.Instrument", on_delete=models.PROTECT, related_name="transactions")
    transaction_type = models.CharField(max_length=4, choices=TYPE_CHOICES)
    quantity = models.DecimalField(max_digits=14, decimal_places=4)
    price_per_share = models.DecimalField(max_digits=12, decimal_places=4)
    fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    trade_date = models.DateField()
    broker = models.CharField(max_length=50, blank=True)
    source_statement = models.ForeignKey(
        "statements.StatementUpload", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="committed_transactions",
    )
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["portfolio", "instrument", "trade_date"], name="portfolio_t_portf_trd_idx")]
        ordering = ["-trade_date", "-created_at"]

    def __str__(self):
        return f"{self.transaction_type} {self.quantity} {self.instrument.ticker} @ {self.price_per_share}"

    @property
    def gross_amount(self):
        return self.quantity * self.price_per_share


class Holding(models.Model):
    """
    Cached/computed snapshot, one row per (portfolio, instrument), rebuilt
    whenever that portfolio's transactions for that instrument change. Not
    the source of truth (Transaction is) — exists so dashboard reads don't
    recompute from full transaction history on every page load.
    """

    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="holdings")
    instrument = models.ForeignKey("instruments.Instrument", on_delete=models.CASCADE, related_name="holdings")
    quantity = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    average_cost = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    realized_pnl = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    last_recalculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["portfolio", "instrument"], name="uniq_holding_per_portfolio_instrument")
        ]
        ordering = ["instrument__ticker"]

    def __str__(self):
        return f"{self.portfolio} — {self.instrument.ticker}: {self.quantity}"

    @property
    def cost_basis(self):
        return self.quantity * self.average_cost

    def latest_price(self):
        bar = self.instrument.price_bars.first()
        return bar.close_price if bar else None

    def market_value(self):
        price = self.latest_price()
        return (price * self.quantity) if price is not None else None

    def unrealized_pnl(self):
        value = self.market_value()
        return (value - self.cost_basis) if value is not None else None

    def unrealized_pnl_percent(self):
        pnl = self.unrealized_pnl()
        if pnl is None or self.cost_basis == 0:
            return None
        return (pnl / self.cost_basis) * 100


class CashBalance(models.Model):
    """
    A single manually-set number, not a transaction ledger — deliberately
    simple. Deposits/withdrawals aren't tracked here; the user just updates
    this figure to match their brokerage account's cash balance when it
    changes. Counts toward total portfolio value and the asset-class
    breakdown alongside equities/funds/fixed income.
    """

    portfolio = models.OneToOneField(Portfolio, on_delete=models.CASCADE, related_name="cash_balance")
    amount_ghs = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.portfolio} — GHS {self.amount_ghs}"

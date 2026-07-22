from django.conf import settings
from django.db import models


class WatchlistItem(models.Model):
    """Tracks a stock without owning it. No alert delivery here — Telegram/
    alert notifications were dropped from scope; this is tracking only."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="watchlist_items")
    instrument = models.ForeignKey("instruments.Instrument", on_delete=models.CASCADE, related_name="watchers")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "instrument"], name="uniq_watchlist_item")
        ]
        ordering = ["instrument__ticker"]

    def __str__(self):
        return f"{self.user} watching {self.instrument.ticker}"

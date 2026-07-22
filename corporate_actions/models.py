from django.conf import settings
from django.db import models


class CorporateAction(models.Model):
    AGM = "AGM"
    RIGHTS_ISSUE = "RIGHTS_ISSUE"
    EARNINGS = "EARNINGS"
    EX_DIVIDEND = "EX_DIVIDEND"
    OTHER = "OTHER"
    ACTION_TYPES = [
        (AGM, "Annual General Meeting"),
        (RIGHTS_ISSUE, "Rights Issue"),
        (EARNINGS, "Earnings Release"),
        (EX_DIVIDEND, "Ex-Dividend Date"),
        (OTHER, "Other"),
    ]

    instrument = models.ForeignKey("instruments.Instrument", on_delete=models.CASCADE, related_name="corporate_actions")
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    event_date = models.DateField(help_text="The date the action occurs/takes effect.")
    source_url = models.URLField(blank=True)
    entered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["instrument", "event_date"])]
        ordering = ["event_date"]

    def __str__(self):
        return f"{self.instrument.ticker} — {self.title} ({self.event_date})"

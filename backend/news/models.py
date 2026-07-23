from django.conf import settings
from django.db import models
from django.utils.text import slugify


class NewsArticle(models.Model):
    """
    Founder-authored market news/commentary shown on the public landing
    page and a dedicated News section — deliberately editorial content,
    not scraped or AI-generated, consistent with the rest of the app's
    "never fabricate data" rule. Unpublished articles are saved but never
    served by the public API, so a draft can be prepared ahead of time.
    """

    MARKET = "MARKET"
    COMPANY = "COMPANY"
    REGULATORY = "REGULATORY"
    ECONOMY = "ECONOMY"
    GSE = "GSE"
    OTHER = "OTHER"
    CATEGORY_CHOICES = [
        (MARKET, "Market"),
        (COMPANY, "Company"),
        (REGULATORY, "Regulatory"),
        (ECONOMY, "Economy"),
        (GSE, "GSE Announcements"),
        (OTHER, "Other"),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default=MARKET)
    image = models.ImageField(upload_to="news/%Y/%m/", blank=True)
    summary = models.CharField(
        max_length=300, blank=True,
        help_text="Short teaser shown on the News list card. Falls back to the start of the body if left blank.",
    )
    body = models.TextField()
    source_url = models.URLField(blank=True, help_text="Link to the original source, if this summarizes one.")
    published_at = models.DateTimeField()
    is_published = models.BooleanField(default=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-published_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)[:260]
            slug = base_slug
            n = 1
            while NewsArticle.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                n += 1
                slug = f"{base_slug}-{n}"
            self.slug = slug
        super().save(*args, **kwargs)

    def display_summary(self):
        if self.summary:
            return self.summary
        return (self.body[:240] + "…") if len(self.body) > 240 else self.body

from django.conf import settings
from django.db import models
from django.utils.html import strip_tags
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field


class SiteSettings(models.Model):
    """
    Singleton row (always pk=1) for the handful of site-wide values that
    used to be hardcoded in templates — contact details, default SEO tags,
    and third-party script IDs (Analytics/AdSense). Editing this in Django
    admin reflects immediately everywhere it's used, instead of needing a
    code change + redeploy for a phone number or a meta description.
    """

    # Contact — see templates/news/contact.html
    support_email = models.EmailField(blank=True)
    support_phone = models.CharField(max_length=30, blank=True)
    office_address = models.CharField(max_length=255, blank=True)
    twitter_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)

    # SEO defaults — individual pages/articles can still override these.
    default_meta_title = models.CharField(max_length=70, blank=True, default="SikaTrack — GSE Portfolio Tracker")
    default_meta_description = models.CharField(
        max_length=160, blank=True,
        help_text="Shown in search results and social link previews when a page doesn't set its own.",
    )
    og_image = models.ImageField(upload_to="site/", blank=True, null=True)

    # Third-party scripts — left blank means the script simply isn't
    # loaded, rather than shipping a broken/placeholder tag.
    google_analytics_id = models.CharField(max_length=30, blank=True, help_text="e.g. G-XXXXXXXXXX")
    adsense_client_id = models.CharField(
        max_length=30, blank=True, help_text="e.g. ca-pub-1234567890123456 — leave blank to show no ads."
    )
    adsense_sidebar_slot_id = models.CharField(max_length=30, blank=True, help_text="Ad unit slot ID for the news sidebar placement.")

    class Meta:
        verbose_name = "Site settings"
        verbose_name_plural = "Site settings"

    def __str__(self):
        return "Site settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # singleton — deleting from admin would just leave every page without defaults

    @classmethod
    def load(cls) -> "SiteSettings":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


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
    body = CKEditor5Field(config_name="default")
    source_url = models.URLField(blank=True, help_text="Link to the original source, if this summarizes one.")
    meta_title = models.CharField(
        max_length=70, blank=True, help_text="Overrides the page <title>/SEO title. Falls back to the article title."
    )
    meta_description = models.CharField(
        max_length=160, blank=True, help_text="Overrides the SEO/social description. Falls back to the summary."
    )
    published_at = models.DateTimeField()
    is_published = models.BooleanField(default=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)
    view_count = models.PositiveIntegerField(default=0)

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
        plain = strip_tags(self.body).strip()
        return (plain[:240] + "…") if len(plain) > 240 else plain

    def seo_title(self):
        return self.meta_title or self.title

    def seo_description(self):
        return self.meta_description or self.display_summary()

    def related_articles(self, limit=4):
        return (
            NewsArticle.objects.filter(category=self.category, is_published=True)
            .exclude(pk=self.pk)
            .order_by("-published_at")[:limit]
        )

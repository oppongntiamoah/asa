from django.contrib import admin

from .models import NewsArticle, SiteSettings


@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "published_at", "is_published", "author"]
    list_filter = ["category", "is_published"]
    search_fields = ["title", "body"]
    prepopulated_fields = {"slug": ["title"]}
    date_hierarchy = "published_at"
    fieldsets = (
        (None, {"fields": ("title", "slug", "category", "image", "summary", "body", "source_url")}),
        ("SEO (optional overrides)", {"fields": ("meta_title", "meta_description"), "classes": ("collapse",)}),
        ("Publishing", {"fields": ("published_at", "is_published", "author")}),
    )

    def save_model(self, request, obj, form, change):
        if not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Contact details", {"fields": ("support_email", "support_phone", "office_address")}),
        ("Social links", {"fields": ("twitter_url", "linkedin_url", "facebook_url")}),
        ("SEO defaults", {"fields": ("default_meta_title", "default_meta_description", "og_image")}),
        ("Analytics & ads", {"fields": ("google_analytics_id", "adsense_client_id", "adsense_sidebar_slot_id")}),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        # Singleton — skip the list page and go straight to the one row.
        obj = SiteSettings.load()
        from django.shortcuts import redirect
        return redirect("admin:news_sitesettings_change", obj.pk)

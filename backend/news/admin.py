from django.contrib import admin

from .models import NewsArticle


@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "published_at", "is_published", "author"]
    list_filter = ["category", "is_published"]
    search_fields = ["title", "body"]
    prepopulated_fields = {"slug": ["title"]}
    date_hierarchy = "published_at"

    def save_model(self, request, obj, form, change):
        if not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)

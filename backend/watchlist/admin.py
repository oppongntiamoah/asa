from django.contrib import admin

from .models import WatchlistItem


@admin.register(WatchlistItem)
class WatchlistItemAdmin(admin.ModelAdmin):
    list_display = ("user", "instrument", "created_at")
    search_fields = ("user__username", "instrument__ticker")
    autocomplete_fields = ("user", "instrument")

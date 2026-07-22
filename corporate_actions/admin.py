from django.contrib import admin

from .models import CorporateAction


@admin.register(CorporateAction)
class CorporateActionAdmin(admin.ModelAdmin):
    list_display = ("instrument", "action_type", "title", "event_date")
    list_filter = ("action_type",)
    search_fields = ("instrument__ticker", "title")
    autocomplete_fields = ("instrument",)

    def save_model(self, request, obj, form, change):
        if not obj.entered_by_id:
            obj.entered_by = request.user
        super().save_model(request, obj, form, change)

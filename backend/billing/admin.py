from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path

from .models import BillingSettings, CreditBalance, Plan, Purchase


@admin.register(BillingSettings)
class BillingSettingsAdmin(admin.ModelAdmin):
    """
    Singleton — the change_list redirects straight to the (only) change
    form so flipping the free/paid switch is one click from the admin
    index, not a detour through an empty list page.
    """

    list_display = ("billing_enabled", "updated_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = BillingSettings.load()
        return redirect("admin:billing_billingsettings_change", obj.pk)


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "price_ghs", "pdf_processing_credits", "is_active", "sort_order")
    list_editable = ("is_active", "sort_order")
    search_fields = ("code", "name")


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "amount_ghs", "status", "provider_reference", "created_at")
    list_filter = ("status", "plan")
    search_fields = ("user__username", "provider_reference")
    autocomplete_fields = ("user",)
    readonly_fields = ("raw_webhook_payload",)


@admin.register(CreditBalance)
class CreditBalanceAdmin(admin.ModelAdmin):
    list_display = ("user", "pdf_processing_credits", "stock_alert_credits", "dividend_alert_credits", "data_export_credits")
    search_fields = ("user__username",)
    autocomplete_fields = ("user",)

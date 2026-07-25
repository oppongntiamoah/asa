from django.contrib import admin

from .models import DividendRecord, DividendReceipt
from .services import generate_receipts_for_dividend


@admin.register(DividendRecord)
class DividendRecordAdmin(admin.ModelAdmin):
    list_display = ("instrument", "amount_per_share", "record_date", "ex_dividend_date", "payment_date")
    list_filter = ("instrument",)
    search_fields = ("instrument__ticker",)
    autocomplete_fields = ("instrument",)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        generate_receipts_for_dividend(obj)


@admin.register(DividendReceipt)
class DividendReceiptAdmin(admin.ModelAdmin):
    list_display = ("portfolio", "dividend_record", "quantity_held", "total_amount")
    search_fields = ("portfolio__name", "portfolio__user__username")
    autocomplete_fields = ("portfolio", "dividend_record")

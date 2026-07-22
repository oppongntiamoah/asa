from django.contrib import admin

from .models import Holding, Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("user", "instrument", "transaction_type", "quantity", "price_per_share", "trade_date")
    list_filter = ("transaction_type", "broker")
    search_fields = ("user__username", "instrument__ticker")
    autocomplete_fields = ("user", "instrument")


@admin.register(Holding)
class HoldingAdmin(admin.ModelAdmin):
    list_display = ("user", "instrument", "quantity", "average_cost", "realized_pnl")
    search_fields = ("user__username", "instrument__ticker")
    autocomplete_fields = ("user", "instrument")

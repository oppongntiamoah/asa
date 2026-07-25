from django.contrib import admin

from .models import CashBalance, Holding, Portfolio, Transaction


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "is_default", "created_at")
    list_filter = ("is_default",)
    search_fields = ("name", "user__username")
    autocomplete_fields = ("user",)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("portfolio", "instrument", "transaction_type", "quantity", "price_per_share", "trade_date")
    list_filter = ("transaction_type", "broker")
    search_fields = ("portfolio__name", "portfolio__user__username", "instrument__ticker")
    autocomplete_fields = ("portfolio", "instrument")


@admin.register(Holding)
class HoldingAdmin(admin.ModelAdmin):
    list_display = ("portfolio", "instrument", "quantity", "average_cost", "realized_pnl")
    search_fields = ("portfolio__name", "portfolio__user__username", "instrument__ticker")
    autocomplete_fields = ("portfolio", "instrument")


@admin.register(CashBalance)
class CashBalanceAdmin(admin.ModelAdmin):
    list_display = ("portfolio", "amount_ghs", "updated_at")
    search_fields = ("portfolio__name", "portfolio__user__username")
    autocomplete_fields = ("portfolio",)

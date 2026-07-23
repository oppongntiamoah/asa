from django.urls import path

from . import views

app_name = "portfolio"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("holdings/", views.holdings_list, name="holdings"),
    path("holdings/export/", views.holdings_csv_export, name="holdings_csv_export"),
    path("holdings/breakdown/", views.stock_breakdown, name="stock_breakdown"),
    path("holdings/<int:instrument_id>/", views.holding_detail, name="holding_detail"),
    path("transactions/", views.transaction_list, name="transaction_list"),
    path("transactions/add/", views.transaction_add, name="transaction_add"),
    path("transactions/<int:pk>/delete/", views.transaction_delete, name="transaction_delete"),
    path("transactions/check-sell-quantity/", views.check_sell_quantity, name="check_sell_quantity"),
    path("analysis/transactions/", views.transaction_analysis_view, name="transaction_analysis"),
    path("analysis/cost-basis/", views.cost_basis_view, name="cost_basis"),
    path("analysis/sectors/", views.sector_analysis_view, name="sector_analysis"),
    path("analysis/performance/", views.performance_view, name="performance"),
    path("analysis/risk/", views.risk_health_view, name="risk_health"),
    path("analysis/insights/", views.insights_view, name="insights"),
    path("analysis/cash-flow/", views.cash_flow_view, name="cash_flow"),
    path("analysis/tax/", views.tax_summary_view, name="tax_summary"),
    path("analysis/timeline/", views.timeline_view, name="timeline"),
    path("cash-balance/update/", views.update_cash_balance, name="update_cash_balance"),
]

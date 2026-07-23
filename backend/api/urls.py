from django.urls import path

from .views import account, analysis, billing, calendar, core, dividends, market, statements, transactions, watchlist

app_name = "api"

urlpatterns = [
    # Auth
    path("csrf/", core.csrf, name="csrf"),
    path("auth/login/", core.login_view, name="login"),
    path("auth/logout/", core.logout_view, name="logout"),
    path("auth/me/", core.me, name="me"),
    # Dashboard / holdings / market
    path("dashboard/", core.dashboard, name="dashboard"),
    path("holdings/", core.holdings, name="holdings"),
    path("cost-basis/", core.cost_basis, name="cost_basis"),
    path("market/summary/", core.market_summary, name="market_summary"),
    path("market/ticker/<str:ticker>/", core.ticker_detail, name="ticker_detail"),
    path("market/list/", market.market_list, name="market_list"),
    # Transactions / cash / holding detail
    path("transactions/", transactions.transactions, name="transactions"),
    path("transactions/<int:pk>/", transactions.transaction_detail, name="transaction_detail"),
    path("transactions/check-sell/", transactions.check_sell_quantity, name="check_sell_quantity"),
    path("cash-balance/", transactions.cash_balance, name="cash_balance"),
    # Analysis suite
    path("analysis/transactions/", analysis.transaction_analysis_view, name="analysis_transactions"),
    path("analysis/sectors/", analysis.sector_analysis_view, name="analysis_sectors"),
    path("analysis/performance/", analysis.performance_view, name="analysis_performance"),
    path("analysis/risk/", analysis.risk_health_view, name="analysis_risk"),
    path("analysis/insights/", analysis.insights_view, name="analysis_insights"),
    path("analysis/cash-flow/", analysis.cash_flow_view, name="analysis_cash_flow"),
    path("analysis/tax/", analysis.tax_summary_view, name="analysis_tax"),
    path("analysis/timeline/", analysis.timeline_view, name="analysis_timeline"),
    # Dividends / calendar / watchlist
    path("dividends/", dividends.dividend_history, name="dividends"),
    path("calendar/", calendar.calendar_view, name="calendar"),
    path("watchlist/", watchlist.watchlist, name="watchlist"),
    path("watchlist/<int:pk>/", watchlist.watchlist_remove, name="watchlist_remove"),
    # Statements
    path("statements/", statements.statements, name="statements"),
    path("statements/<int:pk>/", statements.statement_detail, name="statement_detail"),
    path("statements/<int:pk>/rows/", statements.statement_rows, name="statement_rows"),
    path("statements/<int:pk>/rows/<int:row_id>/", statements.statement_row_detail, name="statement_row_detail"),
    path("statements/<int:pk>/confirm/", statements.statement_confirm, name="statement_confirm"),
    # Billing
    path("billing/plans/", billing.plans, name="billing_plans"),
    path("billing/credits/", billing.credits, name="billing_credits"),
    path("billing/purchase/<str:plan_code>/", billing.start_purchase, name="billing_purchase"),
    # Account
    path("account/profile/", account.profile, name="account_profile"),
]

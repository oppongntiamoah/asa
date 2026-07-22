from django.urls import path

from . import views

app_name = "portfolio"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("holdings/", views.holdings_list, name="holdings"),
    path("holdings/<int:instrument_id>/", views.holding_detail, name="holding_detail"),
    path("transactions/", views.transaction_list, name="transaction_list"),
    path("transactions/add/", views.transaction_add, name="transaction_add"),
    path("transactions/<int:pk>/delete/", views.transaction_delete, name="transaction_delete"),
    path("transactions/check-sell-quantity/", views.check_sell_quantity, name="check_sell_quantity"),
]

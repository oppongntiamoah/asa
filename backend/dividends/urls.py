from django.urls import path

from . import views

app_name = "dividends"

urlpatterns = [
    path("", views.dividend_history, name="history"),
]

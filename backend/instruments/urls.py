from django.urls import path

from . import views

app_name = "instruments"

urlpatterns = [
    path("", views.market, name="market"),
    path("movers/", views.movers, name="movers"),
    path("<str:ticker>/", views.detail, name="detail"),
]

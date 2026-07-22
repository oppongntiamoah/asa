from django.urls import path

from . import views

app_name = "billing"

urlpatterns = [
    path("", views.pricing, name="pricing"),
    path("my-credits/", views.my_credits, name="my_credits"),
    path("purchase/<str:plan_code>/", views.start_purchase, name="start_purchase"),
    path("callback/", views.callback, name="callback"),
    path("webhook/", views.webhook, name="webhook"),
]

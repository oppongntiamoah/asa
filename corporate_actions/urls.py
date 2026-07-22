from django.urls import path

from . import views

app_name = "corporate_actions"

urlpatterns = [
    path("", views.calendar_view, name="calendar"),
]

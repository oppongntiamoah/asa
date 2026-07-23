from django.urls import path

from . import views

app_name = "api"

urlpatterns = [
    path("csrf/", views.csrf, name="csrf"),
    path("auth/login/", views.login_view, name="login"),
    path("auth/logout/", views.logout_view, name="logout"),
    path("auth/me/", views.me, name="me"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("holdings/", views.holdings, name="holdings"),
    path("cost-basis/", views.cost_basis, name="cost_basis"),
]

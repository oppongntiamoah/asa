from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import StyledPasswordChangeForm

app_name = "accounts"

urlpatterns = [
    path("signup/", views.SignUpView.as_view(), name="signup"),
    path("login/", views.TwoFactorLoginView.as_view(), name="login"),
    path("login/verify/", views.two_factor_verify_view, name="two_factor_verify"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(template_name="accounts/password_reset.html"),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(template_name="accounts/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(template_name="accounts/password_reset_confirm.html"),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(template_name="accounts/password_reset_complete.html"),
        name="password_reset_complete",
    ),
    path(
        "password-change/",
        auth_views.PasswordChangeView.as_view(
            template_name="accounts/password_change.html",
            form_class=StyledPasswordChangeForm,
            success_url="/accounts/password-change/done/",
        ),
        name="password_change",
    ),
    path(
        "password-change/done/",
        auth_views.PasswordChangeDoneView.as_view(template_name="accounts/password_change_done.html"),
        name="password_change_done",
    ),
    path("settings/", views.settings_view, name="settings"),
    path("settings/export/", views.export_data, name="export_data"),
    path("settings/delete/", views.request_deletion, name="request_deletion"),
    path("settings/devices/", views.devices_view, name="devices"),
    path("settings/devices/<int:pk>/revoke/", views.revoke_device, name="revoke_device"),
    path("settings/devices/revoke-all/", views.revoke_all_other_devices, name="revoke_all_other_devices"),
    path("settings/2fa/", views.two_factor_status_view, name="two_factor_status"),
    path("settings/2fa/setup/", views.two_factor_setup_view, name="two_factor_setup"),
    path("settings/2fa/disable/", views.two_factor_disable_view, name="two_factor_disable"),
    path("settings/2fa/recovery-codes/", views.two_factor_recovery_codes_view, name="two_factor_recovery_codes"),
    path("support/", views.support, name="support"),
]

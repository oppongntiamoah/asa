import csv

import pyotp
from django.conf import settings as django_settings
from django.contrib import messages
from django.contrib.auth import login, logout, views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.sessions.models import Session
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import CreateView
from django_ratelimit.decorators import ratelimit

from .forms import (
    DisableTOTPForm, ProfileForm, SignUpForm, StyledAuthenticationForm, TOTPConfirmForm, TOTPVerifyForm,
)
from .models import TOTPDevice, TOTPRecoveryCode, User, UserSession
from .user_agent import describe_user_agent, is_mobile_user_agent


@method_decorator(ratelimit(key="ip", rate="10/h", method="POST", block=True), name="post")
class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = "accounts/signup.html"
    success_url = reverse_lazy("portfolio:dashboard")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("portfolio:dashboard")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)

        from portfolio.models import Portfolio

        Portfolio.objects.create(user=self.object, name="Default", is_default=True)
        # Baseline so the "new news" popup only fires for articles published
        # after this account existed, not every article ever written.
        self.object.last_seen_news_at = timezone.now()
        self.object.save(update_fields=["last_seen_news_at"])
        return response


@method_decorator(ratelimit(key="ip", rate="15/m", method="POST", block=True), name="post")
class TwoFactorLoginView(auth_views.LoginView):
    """
    Same as Django's stock LoginView, except a user with a confirmed
    TOTPDevice doesn't get logged in on a correct password alone — the
    session is held pending until they also pass the code-verify step.
    """

    template_name = "accounts/login.html"
    authentication_form = StyledAuthenticationForm

    def form_valid(self, form):
        user = form.get_user()
        device = getattr(user, "totp_device", None)
        if device and device.confirmed:
            self.request.session["pending_2fa_user_id"] = user.pk
            next_url = self.get_redirect_url()
            if next_url:
                self.request.session["pending_2fa_next"] = next_url
            return redirect("accounts:two_factor_verify")
        return super().form_valid(form)


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
def two_factor_verify_view(request):
    user_id = request.session.get("pending_2fa_user_id")
    if not user_id:
        return redirect("accounts:login")
    user = get_object_or_404(User, pk=user_id)
    device = getattr(user, "totp_device", None)

    if request.method == "POST":
        form = TOTPVerifyForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data["code"]
            if device and (device.verify(code) or TOTPRecoveryCode.try_consume(user, code)):
                del request.session["pending_2fa_user_id"]
                next_url = request.session.pop("pending_2fa_next", None)
                login(request, user, backend=django_settings.AUTHENTICATION_BACKENDS[0])
                return redirect(next_url or "portfolio:dashboard")
            form.add_error("code", "That code didn't work. Check your app's time is in sync, or use a recovery code.")
    else:
        form = TOTPVerifyForm()
    return render(request, "accounts/two_factor_verify.html", {"form": form})


@login_required
def settings_view(request):
    from portfolio.context import get_active_portfolio
    from portfolio.forms import CashBalanceForm
    from portfolio.models import CashBalance

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("accounts:settings")
    else:
        form = ProfileForm(instance=request.user)

    cash_balance, _ = CashBalance.objects.get_or_create(portfolio=get_active_portfolio(request))
    cash_form = CashBalanceForm(instance=cash_balance)
    return render(request, "accounts/settings.html", {"form": form, "cash_form": cash_form})


@login_required
def export_data(request):
    """Data export (CSV of transactions) — also doubles as part of the
    Ghana Data Protection Act 'right to access' story: a user can pull
    their own data any time, not just via a manual request to the founder.
    Covers every portfolio the user has, not just the active one — this is
    an export of everything SikaTrack holds about them, not a portfolio
    report."""
    from portfolio.models import Transaction

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="sikatrack_transactions.csv"'
    writer = csv.writer(response)
    writer.writerow(["Portfolio", "Date", "Type", "Symbol", "Quantity", "Price", "Fees", "Broker", "Notes"])
    txns = Transaction.objects.filter(portfolio__user=request.user).select_related(
        "instrument", "portfolio"
    ).order_by("portfolio__name", "trade_date")
    for t in txns:
        writer.writerow([t.portfolio.name, t.trade_date, t.transaction_type, t.instrument.ticker, t.quantity, t.price_per_share, t.fees, t.broker, t.notes])
    return response


@login_required
def request_deletion(request):
    """
    MVP-scope deletion handling per PRODUCT_DESIGN.md §8.3: doesn't need to
    be fully self-service on day one, but must be honored promptly. This
    immediately revokes access (deactivate + log out) rather than queuing
    silently, and tells the user what happens next; full data erasure is
    still a manual step for the founder until a self-service deletion
    pipeline is built.
    """
    if request.method == "POST":
        user = request.user
        user.is_active = False
        user.save(update_fields=["is_active"])
        logout(request)
        messages.success(
            request,
            "Your account has been deactivated and you've been logged out. "
            "Email the address in Support to request full data deletion.",
        )
        return redirect("accounts:login")
    return render(request, "accounts/request_deletion.html")


def support(request):
    return render(request, "accounts/support.html")


@login_required
def devices_view(request):
    """
    Lists this account's active logins ("Devices" under Settings) — one
    UserSession row per session_key, but only ever shown while the
    matching django.contrib.sessions.Session row still exists (hasn't
    expired or been cleared), so a stale UserSession left behind by a
    session that just timed out doesn't linger on the page.
    """
    sessions = list(UserSession.objects.filter(user=request.user))
    live_keys = set(
        Session.objects.filter(
            session_key__in=[s.session_key for s in sessions], expire_date__gt=timezone.now()
        ).values_list("session_key", flat=True)
    )
    current_key = request.session.session_key
    rows = [
        {
            "session": s,
            "description": describe_user_agent(s.user_agent),
            "is_mobile": is_mobile_user_agent(s.user_agent),
            "is_current": s.session_key == current_key,
        }
        for s in sessions
        if s.session_key in live_keys
    ]
    rows.sort(key=lambda r: (not r["is_current"], -r["session"].last_seen.timestamp()))
    return render(request, "accounts/devices.html", {"rows": rows})


@login_required
@require_POST
def revoke_device(request, pk):
    user_session = get_object_or_404(UserSession, pk=pk, user=request.user)
    if user_session.session_key == request.session.session_key:
        messages.error(request, "That's your current session — use Log out instead.")
    else:
        Session.objects.filter(session_key=user_session.session_key).delete()
        user_session.delete()
        messages.success(request, "That device has been logged out.")
    return redirect("accounts:devices")


@login_required
@require_POST
def revoke_all_other_devices(request):
    current_key = request.session.session_key
    other_sessions = UserSession.objects.filter(user=request.user).exclude(session_key=current_key)
    keys = list(other_sessions.values_list("session_key", flat=True))
    Session.objects.filter(session_key__in=keys).delete()
    count = other_sessions.count()
    other_sessions.delete()
    if count:
        messages.success(request, f"Logged out {count} other device{'s' if count != 1 else ''}.")
    else:
        messages.info(request, "No other devices were logged in.")
    return redirect("accounts:devices")


@login_required
def two_factor_status_view(request):
    device = getattr(request.user, "totp_device", None)
    return render(request, "accounts/two_factor_status.html", {
        "device": device,
        "recovery_codes_remaining": request.user.recovery_codes.filter(used_at__isnull=True).count() if device and device.confirmed else 0,
    })


@login_required
def two_factor_setup_view(request):
    device = getattr(request.user, "totp_device", None)
    if device and device.confirmed:
        return redirect("accounts:two_factor_status")

    if not device:
        device = TOTPDevice.objects.create(user=request.user, secret=pyotp.random_base32())

    if request.method == "POST":
        form = TOTPConfirmForm(request.POST)
        if form.is_valid() and device.verify(form.cleaned_data["code"]):
            device.confirmed = True
            device.save(update_fields=["confirmed"])
            codes = TOTPRecoveryCode.generate_set(request.user)
            request.session["fresh_recovery_codes"] = codes
            messages.success(request, "Two-factor authentication is on.")
            return redirect("accounts:two_factor_recovery_codes")
        if form.is_valid():
            form.add_error("code", "That code didn't match — check your app and try again.")
    else:
        form = TOTPConfirmForm()

    import qrcode
    import qrcode.image.svg

    qr = qrcode.make(device.provisioning_uri(), image_factory=qrcode.image.svg.SvgImage)
    import io
    buf = io.BytesIO()
    qr.save(buf)
    qr_svg = buf.getvalue().decode("utf-8")

    return render(request, "accounts/two_factor_setup.html", {
        "form": form, "secret": device.secret, "qr_svg": qr_svg,
    })


@login_required
def two_factor_disable_view(request):
    device = getattr(request.user, "totp_device", None)
    if not device:
        return redirect("accounts:two_factor_status")

    if request.method == "POST":
        form = DisableTOTPForm(request.POST)
        if form.is_valid():
            if request.user.check_password(form.cleaned_data["password"]):
                device.delete()
                TOTPRecoveryCode.objects.filter(user=request.user).delete()
                messages.success(request, "Two-factor authentication is off.")
                return redirect("accounts:two_factor_status")
            form.add_error("password", "Incorrect password.")
    else:
        form = DisableTOTPForm()
    return render(request, "accounts/two_factor_disable.html", {"form": form})


@login_required
def two_factor_recovery_codes_view(request):
    """
    GET only shows freshly-generated codes handed off via the session right
    after setup (or a regeneration) — codes are hashed at rest and can't be
    displayed again later, so this view has nothing to show once that
    session key is gone.
    """
    device = getattr(request.user, "totp_device", None)
    if not device or not device.confirmed:
        return redirect("accounts:two_factor_status")

    if request.method == "POST":
        codes = TOTPRecoveryCode.generate_set(request.user)
        request.session["fresh_recovery_codes"] = codes
        messages.success(request, "New recovery codes generated — your old ones no longer work.")
        return redirect("accounts:two_factor_recovery_codes")

    codes = request.session.pop("fresh_recovery_codes", None)
    return render(request, "accounts/two_factor_recovery_codes.html", {"codes": codes})

import csv

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import ProfileForm, SignUpForm


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
        return response


@login_required
def settings_view(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("accounts:settings")
    else:
        form = ProfileForm(instance=request.user)
    return render(request, "accounts/settings.html", {"form": form})


@login_required
def export_data(request):
    """Data export (CSV of transactions) — also doubles as part of the
    Ghana Data Protection Act 'right to access' story: a user can pull
    their own data any time, not just via a manual request to the founder."""
    from portfolio.models import Transaction

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="sikatrack_transactions.csv"'
    writer = csv.writer(response)
    writer.writerow(["Date", "Type", "Symbol", "Quantity", "Price", "Fees", "Broker", "Notes"])
    for t in Transaction.objects.filter(user=request.user).select_related("instrument").order_by("trade_date"):
        writer.writerow([t.trade_date, t.transaction_type, t.instrument.ticker, t.quantity, t.price_per_share, t.fees, t.broker, t.notes])
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

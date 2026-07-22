from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from instruments.models import Instrument

from .models import WatchlistItem
from .services import watchlist_rows


@login_required
def watchlist(request):
    if request.method == "POST":
        ticker = request.POST.get("ticker", "").strip().upper()
        instrument = Instrument.objects.filter(ticker=ticker, is_active=True).first()
        if not instrument:
            messages.error(request, f"No active instrument found for '{ticker}'.")
        else:
            _, created = WatchlistItem.objects.get_or_create(user=request.user, instrument=instrument)
            if created:
                messages.success(request, f"Added {instrument.ticker} to your watchlist.")
            else:
                messages.info(request, f"You're already watching {instrument.ticker}.")
        return redirect("watchlist:watchlist")

    return render(request, "watchlist/watchlist.html", {
        "rows": watchlist_rows(request.user),
        "instruments": Instrument.objects.filter(is_active=True),
    })


@login_required
def remove(request, pk):
    item = get_object_or_404(WatchlistItem, pk=pk, user=request.user)
    if request.method == "POST":
        item.delete()
        messages.success(request, "Removed from watchlist.")
    return redirect("watchlist:watchlist")

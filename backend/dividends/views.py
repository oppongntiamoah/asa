from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from portfolio.context import get_active_portfolio

from .services import dividend_dashboard


@login_required
def dividend_history(request):
    context = dividend_dashboard(get_active_portfolio(request))
    return render(request, "dividends/history.html", context)

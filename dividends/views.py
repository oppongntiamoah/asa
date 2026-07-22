from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .services import dividend_dashboard


@login_required
def dividend_history(request):
    context = dividend_dashboard(request.user)
    return render(request, "dividends/history.html", context)

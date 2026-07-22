from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import DividendReceipt


@login_required
def dividend_history(request):
    receipts = DividendReceipt.objects.filter(user=request.user).select_related(
        "dividend_record", "dividend_record__instrument"
    )
    total_received = sum((r.total_amount for r in receipts), Decimal("0"))
    return render(request, "dividends/history.html", {"receipts": receipts, "total_received": total_received})

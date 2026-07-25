import calendar as calendar_module
from datetime import date

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from dividends.models import DividendRecord
from portfolio.context import get_active_portfolio
from portfolio.models import Holding
from watchlist.models import WatchlistItem

from .models import CorporateAction


@login_required
def calendar_view(request):
    today = date.today()
    year = int(request.GET.get("year", today.year))
    month = int(request.GET.get("month", today.month))

    instrument_ids = set(Holding.objects.filter(portfolio=get_active_portfolio(request)).values_list("instrument_id", flat=True))
    instrument_ids |= set(WatchlistItem.objects.filter(user=request.user).values_list("instrument_id", flat=True))

    actions = CorporateAction.objects.filter(
        instrument_id__in=instrument_ids, event_date__year=year, event_date__month=month
    ).select_related("instrument")
    dividends = DividendRecord.objects.filter(
        instrument_id__in=instrument_ids, ex_dividend_date__year=year, ex_dividend_date__month=month
    ).select_related("instrument")

    events_by_day = {}
    for a in actions:
        events_by_day.setdefault(a.event_date.day, []).append(f"{a.instrument.ticker}: {a.get_action_type_display()}")
    for d in dividends:
        events_by_day.setdefault(d.ex_dividend_date.day, []).append(f"{d.instrument.ticker}: Ex-dividend")

    _, days_in_month = calendar_module.monthrange(year, month)
    first_weekday = date(year, month, 1).weekday()  # Monday=0

    weeks = []
    week = [None] * first_weekday
    for day in range(1, days_in_month + 1):
        week.append(day)
        if len(week) == 7:
            weeks.append(week)
            week = []
    if week:
        week += [None] * (7 - len(week))
        weeks.append(week)

    prev_month = month - 1 or 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    return render(request, "corporate_actions/calendar.html", {
        "year": year, "month": month, "month_name": calendar_module.month_name[month],
        "weeks": weeks, "events_by_day": events_by_day,
        "prev_year": prev_year, "prev_month": prev_month,
        "next_year": next_year, "next_month": next_month,
        "upcoming": sorted(
            [*[{"date": a.event_date, "text": f"{a.instrument.ticker} — {a.title}"} for a in actions],
             *[{"date": d.ex_dividend_date, "text": f"{d.instrument.ticker} — Ex-dividend"} for d in dividends]],
            key=lambda e: e["date"],
        ),
    })

"""
Risk/health scoring, rule-based "insights" text, cash flow, realized-gains
tax summary, and a merged activity timeline — all derived purely from data
already in the app (no external benchmark, no LLM). Formulas are kept
simple and documented inline so they're auditable, not a black box.
"""
from collections import defaultdict
from decimal import Decimal

from django.contrib.auth import get_user_model

from dividends.services import dividend_dashboard
from portfolio.models import Holding, Transaction

User = get_user_model()

CONCENTRATION_POSITION_WARNING_PCT = 25
CONCENTRATION_SECTOR_WARNING_PCT = 40


def concentration_and_health(user):
    """
    Diversification score: 100 * (1 - HHI), where HHI (Herfindahl-Hirschman
    Index) is the sum of each holding's portfolio-weight-squared. A single
    100%-weighted holding scores 0; N equally-weighted holdings score
    ~100*(1 - 1/N) — approaches 100 as holdings grow and even out.

    Health score: a transparent weighted average of three 0-100
    components — diversification (40%), sector balance (30%, 100 minus the
    largest sector's weight), and returns (30%, total return % clipped to
    [-50, +50] and rescaled to 0-100). There is no cash-allocation
    component — SikaTrack doesn't track cash balances, so it's honestly
    left out rather than assumed at some default.
    """
    from portfolio.services import portfolio_summary, sector_allocation

    summary = portfolio_summary(user)
    holdings = summary["holdings"]
    total_value = summary["total_value"]

    warnings = []
    largest_position = None
    diversification_score = None

    if holdings and total_value:
        weights = []
        for h in holdings:
            value = h.market_value()
            if value is None:
                continue
            weight = float(value / total_value)
            weights.append((h, weight))

        if weights:
            weights.sort(key=lambda w: w[1], reverse=True)
            largest_position = {"holding": weights[0][0], "pct": weights[0][1] * 100}
            hhi = sum(w ** 2 for _, w in weights)
            diversification_score = (1 - hhi) * 100

            if largest_position["pct"] >= CONCENTRATION_POSITION_WARNING_PCT:
                warnings.append(
                    f"{largest_position['holding'].instrument.ticker} represents "
                    f"{largest_position['pct']:.0f}% of your portfolio."
                )
            if len(weights) >= 3:
                top3_pct = sum(w for _, w in weights[:3]) * 100
                if top3_pct >= 60:
                    warnings.append(f"Your top 3 positions account for {top3_pct:.0f}% of your portfolio.")

    sectors = sector_allocation(user)
    largest_sector = sectors[0] if sectors else None
    if largest_sector and largest_sector["pct"] >= CONCENTRATION_SECTOR_WARNING_PCT:
        warnings.append(
            f"{largest_sector['pct']:.0f}% of your portfolio is in {largest_sector['sector']}, "
            f"increasing sector-specific risk."
        )

    health_score = None
    if diversification_score is not None:
        sector_balance_score = (100 - float(largest_sector["pct"])) if largest_sector else 100
        return_component = summary["total_return_pct"]
        return_score = 50.0 if return_component is None else max(0.0, min(100.0, (float(return_component) + 50) / 100 * 100))
        health_score = round(
            diversification_score * 0.4 + sector_balance_score * 0.3 + return_score * 0.3
        )

    return {
        "largest_position": largest_position,
        "largest_sector": largest_sector,
        "diversification_score": diversification_score,
        "health_score": health_score,
        "warnings": warnings,
    }


def rule_based_insights(user):
    """
    Plain-Python generated observations from existing data — explicitly
    NOT an LLM call. Kept as a separate function so swapping in real AI
    generation later (a deliberate cost/latency decision, not a default)
    only means replacing this function's body.
    """
    from portfolio.services import portfolio_summary

    summary = portfolio_summary(user)
    holdings = summary["holdings"]
    insights = []

    risk = concentration_and_health(user)
    insights.extend(risk["warnings"])

    priced_holdings = [(h, h.unrealized_pnl_percent()) for h in holdings]
    priced_holdings = [(h, pct) for h, pct in priced_holdings if pct is not None]
    if priced_holdings:
        best = max(priced_holdings, key=lambda x: x[1])
        insights.append(f"{best[0].instrument.ticker} is your best-performing holding, returning {best[1]:.1f}%.")
        worst = min(priced_holdings, key=lambda x: x[1])
        if worst[0] != best[0] and worst[1] < 0:
            insights.append(f"{worst[0].instrument.ticker} is your worst-performing holding, down {abs(worst[1]):.1f}%.")

    if summary["total_realized_pnl"] > 0:
        insights.append(f"You've realized GHS {summary['total_realized_pnl']:.2f} in profits so far.")

    dividends = dividend_dashboard(user)
    annual = dividends["annual_series"]
    if len(annual) >= 2 and annual[-1]["growth_pct"] is not None:
        direction = "up" if annual[-1]["growth_pct"] >= 0 else "down"
        insights.append(f"Dividend income is {direction} {abs(annual[-1]['growth_pct']):.0f}% compared with the prior year.")

    return insights


def cash_flow_analysis(user):
    """
    Investment activity (buys/sells) by month — NOT a full cash-flow
    statement. SikaTrack doesn't have a cash ledger (deposits/withdrawals
    aren't logged anywhere), so "money in/out of the brokerage account" is
    out of scope here; this only covers money moving between cash and
    equity positions within the tracked portfolio.
    """
    by_month = defaultdict(lambda: {"invested": Decimal("0"), "divested": Decimal("0")})
    for t in Transaction.objects.filter(user=user):
        key = t.trade_date.strftime("%Y-%m")
        if t.transaction_type == Transaction.BUY:
            by_month[key]["invested"] += t.gross_amount + t.fees
        else:
            by_month[key]["divested"] += t.gross_amount - t.fees

    rows = []
    for month in sorted(by_month.keys()):
        v = by_month[month]
        rows.append({"month": month, "invested": v["invested"], "divested": v["divested"], "net": v["divested"] - v["invested"]})
    return rows


def realized_gains_by_year(user):
    """
    Realized gains bucketed by calendar year of the sell transaction,
    replaying each instrument's transaction history to get the average
    cost at the time of each sale (mirrors portfolio.services.recalculate_holding's
    average-cost logic, but records each sale's gain individually instead
    of only the final aggregate).
    """
    by_instrument = defaultdict(list)
    for t in Transaction.objects.filter(user=user).order_by("trade_date", "created_at", "id"):
        by_instrument[t.instrument_id].append(t)

    by_year = defaultdict(Decimal)
    for txns in by_instrument.values():
        quantity = Decimal("0")
        total_cost = Decimal("0")
        for t in txns:
            if t.transaction_type == Transaction.BUY:
                total_cost += t.gross_amount + t.fees
                quantity += t.quantity
            else:
                avg_cost = (total_cost / quantity) if quantity else Decimal("0")
                gain = (t.price_per_share - avg_cost) * t.quantity - t.fees
                by_year[t.trade_date.year] += gain
                total_cost -= avg_cost * t.quantity
                quantity -= t.quantity

    return [{"year": y, "realized_gain": by_year[y]} for y in sorted(by_year.keys())]


def portfolio_timeline(user):
    """Chronological feed of buy/sell transactions and dividend receipts.
    Stock splits and cash deposits/withdrawals aren't included — neither is
    modeled in SikaTrack yet."""
    from dividends.models import DividendReceipt

    events = []
    for t in Transaction.objects.filter(user=user).select_related("instrument"):
        events.append({
            "date": t.trade_date,
            "kind": t.transaction_type,
            "description": f"{t.transaction_type.title()} {t.quantity} {t.instrument.ticker} @ GHS {t.price_per_share}",
            "amount": t.gross_amount,
        })
    for r in DividendReceipt.objects.filter(user=user).select_related("dividend_record", "dividend_record__instrument"):
        effective_date = r.dividend_record.payment_date or r.dividend_record.ex_dividend_date
        events.append({
            "date": effective_date,
            "kind": "DIVIDEND",
            "description": f"Dividend — {r.dividend_record.instrument.ticker}",
            "amount": r.total_amount,
        })

    events.sort(key=lambda e: e["date"], reverse=True)
    return events

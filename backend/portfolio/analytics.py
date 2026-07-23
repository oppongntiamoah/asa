"""
Portfolio-level analytics computed purely from data we actually have
(Transaction + PriceBar + DividendReceipt) — no external index/benchmark
feed, no risk-free rate, no numpy/pandas dependency (kept out deliberately
to stay light for low-bandwidth users and avoid a heavy new dependency for
a handful of stats functions).

Every function here is honest about its limits: a new account with a few
weeks of price history will get thin/None results rather than a
fake-precision number. Callers are responsible for showing "not enough
history yet" copy when a function returns None or an empty list.
"""
import bisect
from collections import defaultdict
from datetime import date
from decimal import Decimal

from instruments.models import PriceBar
from portfolio.models import Transaction


def _price_on_or_before(sorted_bars, target_date):
    """sorted_bars: ascending list of (date, Decimal price). Returns the
    latest price at or before target_date, or None if there isn't one."""
    dates = [d for d, _ in sorted_bars]
    idx = bisect.bisect_right(dates, target_date) - 1
    return sorted_bars[idx][1] if idx >= 0 else None


def portfolio_value_series(user):
    """
    Reconstructs total portfolio value at each distinct price date, by
    replaying transaction history against price history. One point per
    distinct PriceBar trade_date across ever-held instruments, from the
    user's first transaction onward.

    An instrument with no price bar on/before a given date is excluded
    from that day's total rather than assumed worthless — the same
    "unpriced" convention used on the dashboard.

    Returns [] if the user has no transactions.
    """
    transactions = list(Transaction.objects.filter(user=user).order_by("trade_date", "created_at", "id"))
    if not transactions:
        return []

    instrument_ids = {t.instrument_id for t in transactions}
    bars_by_instrument = defaultdict(list)
    for bar in PriceBar.objects.filter(instrument_id__in=instrument_ids).order_by("instrument_id", "trade_date"):
        bars_by_instrument[bar.instrument_id].append((bar.trade_date, bar.close_price))

    all_dates = sorted({d for bars in bars_by_instrument.values() for d, _ in bars})
    first_txn_date = transactions[0].trade_date
    all_dates = [d for d in all_dates if d >= first_txn_date]
    if not all_dates:
        return []

    txns_by_date = defaultdict(list)
    for t in transactions:
        txns_by_date[t.trade_date].append(t)
    sorted_txn_dates = sorted(txns_by_date.keys())

    quantities = defaultdict(Decimal)
    txn_idx = 0
    series = []

    for d in all_dates:
        while txn_idx < len(sorted_txn_dates) and sorted_txn_dates[txn_idx] <= d:
            for t in txns_by_date[sorted_txn_dates[txn_idx]]:
                delta = t.quantity if t.transaction_type == Transaction.BUY else -t.quantity
                quantities[t.instrument_id] += delta
            txn_idx += 1

        total = Decimal("0")
        for instrument_id, qty in quantities.items():
            if qty <= 0:
                continue
            price = _price_on_or_before(bars_by_instrument[instrument_id], d)
            if price is not None:
                total += qty * price
        series.append((d, total))

    return series


def daily_returns(series):
    """[(date, value), ...] -> [float pct return, ...] skipping zero-value days."""
    returns = []
    for i in range(1, len(series)):
        prev = series[i - 1][1]
        curr = series[i][1]
        if prev and prev > 0:
            returns.append(float((curr - prev) / prev))
    return returns


def cagr(series):
    """Compound annual growth rate, as a percentage. None with less than 60
    days of history — annualizing anything shorter (e.g. a 2-month, +30%
    run extrapolated to +500%/year) is technically correct arithmetic but
    practically misleading, so it's withheld rather than shown. Even above
    that threshold, callers should show the underlying day count alongside
    the number so a still-fairly-short window doesn't read as precise."""
    if len(series) < 2:
        return None
    start_date, start_value = series[0]
    end_date, end_value = series[-1]
    days = (end_date - start_date).days
    if days < 60 or start_value <= 0:
        return None
    years = days / 365.25
    return (float(end_value / start_value) ** (1 / years) - 1) * 100


def max_drawdown(series):
    """Largest peak-to-trough decline in the value series, as a percentage
    (returned as a negative number). None if series is empty."""
    if not series:
        return None
    peak = series[0][1]
    peak_date = series[0][0]
    worst = Decimal("0")
    worst_peak_date = peak_date
    worst_trough_date = peak_date

    for d, value in series:
        if value > peak:
            peak = value
            peak_date = d
        if peak > 0:
            dd = (value - peak) / peak
            if dd < worst:
                worst = dd
                worst_peak_date = peak_date
                worst_trough_date = d

    return {
        "max_drawdown_pct": float(worst) * 100,
        "peak_date": worst_peak_date,
        "trough_date": worst_trough_date,
    }


def annualized_volatility(series, trading_days=252):
    """Annualized standard deviation of daily returns, as a percentage.
    None with fewer than 10 return observations — too noisy to report."""
    returns = daily_returns(series)
    if len(returns) < 10:
        return None
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    return (variance ** 0.5) * (trading_days ** 0.5) * 100


def historical_var(series, confidence=0.95):
    """Historical Value at Risk: the daily loss (as a positive percentage)
    not expected to be exceeded more than (1-confidence) of days, based on
    the account's own observed return history. None with <20 observations
    — a VaR estimate off fewer data points isn't worth showing."""
    returns = sorted(daily_returns(series))
    if len(returns) < 20:
        return None
    idx = max(0, int((1 - confidence) * len(returns)) - 1)
    worst_return = returns[idx]
    return max(0.0, -worst_return * 100)


def rolling_returns(series, window_days=30):
    """[(date, pct_return_over_prior_window), ...] — only points with a
    full window available are included."""
    if len(series) < 2:
        return []
    result = []
    dates = [d for d, _ in series]
    for i, (d, value) in enumerate(series):
        window_start_date = d - __import__("datetime").timedelta(days=window_days)
        j = bisect.bisect_left(dates, window_start_date)
        if j >= i or j >= len(series):
            continue
        start_value = series[j][1]
        if start_value and start_value > 0:
            result.append((d, float((value - start_value) / start_value) * 100))
    return result


def xirr(cash_flows, guess=0.1):
    """
    Money-weighted (dollar-weighted) annualized return. cash_flows is a
    list of (date, amount) — negative for money going into the portfolio
    (buys), positive for money coming out (sells, dividends, and a final
    synthetic flow of the current market value). Solved via Newton's
    method; returns None if it doesn't converge within 100 iterations or
    there are fewer than 2 cash flows.
    """
    if len(cash_flows) < 2:
        return None
    cash_flows = [(d, float(amount)) for d, amount in cash_flows]
    t0 = min(cf[0] for cf in cash_flows)

    def year_frac(d):
        return (d - t0).days / 365.0

    def npv(rate):
        return sum(amount / ((1 + rate) ** year_frac(d)) for d, amount in cash_flows)

    def npv_derivative(rate):
        return sum(
            -year_frac(d) * amount / ((1 + rate) ** (year_frac(d) + 1))
            for d, amount in cash_flows
            if year_frac(d) != 0
        )

    rate = guess
    for _ in range(100):
        try:
            f = npv(rate)
            df = npv_derivative(rate)
        except (OverflowError, ZeroDivisionError):
            return None
        if df == 0:
            return None
        new_rate = rate - f / df
        if new_rate <= -0.999:
            new_rate = -0.999  # clamp — a >100% annualized loss isn't a meaningful rate to keep iterating on
        if abs(new_rate - rate) < 1e-6:
            return new_rate * 100
        rate = new_rate
    return None


def portfolio_xirr(user):
    """Builds the cash-flow series (buys negative, sells/dividends positive,
    plus a final flow of today's market value) and solves XIRR on it."""
    from dividends.models import DividendReceipt
    from portfolio.services import portfolio_summary

    flows = []
    for t in Transaction.objects.filter(user=user):
        amount = t.gross_amount + t.fees if t.transaction_type == Transaction.BUY else t.gross_amount - t.fees
        flows.append((t.trade_date, -amount if t.transaction_type == Transaction.BUY else amount))

    for receipt in DividendReceipt.objects.filter(user=user).select_related("dividend_record"):
        pay_date = receipt.dividend_record.payment_date or receipt.dividend_record.ex_dividend_date
        flows.append((pay_date, receipt.total_amount))

    summary = portfolio_summary(user)
    if summary["total_value"] > 0:
        flows.append((date.today(), summary["total_value"]))

    return xirr(flows)


def holdings_correlation(user):
    """
    Pairwise Pearson correlation of daily returns between the user's
    currently-held instruments, using their price history. Thin/sparse
    trading on GSE means these numbers are noisy for low-volume stocks —
    callers should caveat this in the UI rather than present it as precise.
    Returns {} if fewer than 2 holdings have enough overlapping history.
    """
    from portfolio.models import Holding

    holdings = list(Holding.objects.filter(user=user).select_related("instrument"))
    if len(holdings) < 2:
        return {}

    return_series = {}
    for holding in holdings:
        bars = list(holding.instrument.price_bars.order_by("trade_date"))
        if len(bars) < 11:
            continue
        returns = {}
        for i in range(1, len(bars)):
            prev, curr = bars[i - 1].close_price, bars[i].close_price
            if prev:
                returns[bars[i].trade_date] = float((curr - prev) / prev)
        return_series[holding.instrument.ticker] = returns

    tickers = sorted(return_series.keys())
    matrix = {}
    for i, a in enumerate(tickers):
        for b in tickers[i:]:
            shared_dates = set(return_series[a]) & set(return_series[b])
            if len(shared_dates) < 10:
                continue
            xs = [return_series[a][d] for d in shared_dates]
            ys = [return_series[b][d] for d in shared_dates]
            corr = _pearson(xs, ys)
            if corr is not None:
                matrix[(a, b)] = corr
                matrix[(b, a)] = corr
    return {"tickers": tickers, "matrix": matrix}


def _pearson(xs, ys):
    n = len(xs)
    if n < 2:
        return None
    mean_x, mean_y = sum(xs) / n, sum(ys) / n
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    var_x = sum((x - mean_x) ** 2 for x in xs)
    var_y = sum((y - mean_y) ** 2 for y in ys)
    if var_x == 0 or var_y == 0:
        return None
    return cov / ((var_x ** 0.5) * (var_y ** 0.5))


def average_holding_period_days(user):
    """
    Approximation, not exact lot-level FIFO tracking: per instrument, the
    buy-quantity-weighted average acquisition date vs. either the last sell
    date (if the position is now fully closed) or today (if still open).
    Returns the simple average across instruments in days, or None if the
    user has no buy transactions.
    """
    by_instrument = defaultdict(list)
    for t in Transaction.objects.filter(user=user).order_by("trade_date"):
        by_instrument[t.instrument_id].append(t)

    holding_periods = []
    for instrument_id, txns in by_instrument.items():
        buys = [t for t in txns if t.transaction_type == Transaction.BUY]
        sells = [t for t in txns if t.transaction_type == Transaction.SELL]
        if not buys:
            continue

        total_qty = sum(t.quantity for t in buys)
        if total_qty <= 0:
            continue
        weighted_days_from_epoch = sum(t.quantity * t.trade_date.toordinal() for t in buys)
        avg_acquisition_ordinal = float(weighted_days_from_epoch / total_qty)
        avg_acquisition_date = date.fromordinal(round(avg_acquisition_ordinal))

        net_qty = sum(t.quantity for t in buys) - sum(t.quantity for t in sells)
        end_date = sells[-1].trade_date if net_qty <= 0 and sells else date.today()

        holding_periods.append((end_date - avg_acquisition_date).days)

    if not holding_periods:
        return None
    return sum(holding_periods) / len(holding_periods)

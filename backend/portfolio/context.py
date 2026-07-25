"""
Active-portfolio resolution — every page a signed-in user visits operates
on exactly one of their portfolios at a time, chosen via the sidebar
switcher and remembered in the session. This is the one place that logic
lives, so views and the context processor below can't drift out of sync.
"""
from .models import Portfolio


def get_active_portfolio(request):
    """
    Resolves which Portfolio the current request should operate on: the
    one named in the session if it still belongs to this user, otherwise
    their default (or first) portfolio. Every user always has at least
    one (created on signup, or by the data migration for accounts that
    predate portfolios), so this only ever falls through to creating one
    as a last-resort safety net, not the normal path.

    Memoized on the request object — the context processor and the view
    itself would otherwise each hit the DB for the same answer.
    """
    if hasattr(request, "_active_portfolio"):
        return request._active_portfolio

    portfolio = None
    portfolio_id = request.session.get("active_portfolio_id")
    if portfolio_id:
        portfolio = Portfolio.objects.filter(id=portfolio_id, user=request.user).first()

    if portfolio is None:
        portfolio = Portfolio.objects.filter(user=request.user, is_default=True).first()
    if portfolio is None:
        portfolio = Portfolio.objects.filter(user=request.user).order_by("created_at").first()
    if portfolio is None:
        portfolio = Portfolio.objects.create(user=request.user, name="Default", is_default=True)

    if request.session.get("active_portfolio_id") != portfolio.id:
        request.session["active_portfolio_id"] = portfolio.id

    request._active_portfolio = portfolio
    return portfolio


def set_active_portfolio(request, portfolio):
    request.session["active_portfolio_id"] = portfolio.id
    request._active_portfolio = portfolio


def portfolio_context(request):
    """Context processor — exposes active_portfolio/user_portfolios to
    every template so the sidebar switcher doesn't need each view to pass
    them explicitly."""
    if not request.user.is_authenticated:
        return {}
    return {
        "active_portfolio": get_active_portfolio(request),
        "user_portfolios": Portfolio.objects.filter(user=request.user),
    }

"""
Sidebar group active-state — computed from the request path/namespace so
the same rule can't drift between the desktop sidebar and the mobile
drawer. Django's {% with %} tag only accepts a single filter expression
(no `or`/`in`), so this lives in a tiny context-aware tag instead of being
awkwardly inlined at every call site.
"""
from django import template

register = template.Library()

_GROUP_CHECKS = {
    "portfolio": lambda path, ns: (
        path.startswith("/holdings/") or path.startswith("/transactions/")
        or "statements" in ns or "watchlist" in ns or "dividends" in ns
    ),
    "analysis": lambda path, ns: path.startswith("/analysis/"),
    "market": lambda path, ns: "instruments" in ns or "corporate_actions" in ns or "news" in ns,
}


@register.simple_tag(takes_context=True)
def nav_group_active(context, group):
    request = context.get("request")
    if request is None or request.resolver_match is None:
        return False
    check = _GROUP_CHECKS.get(group)
    if check is None:
        return False
    return check(request.path, request.resolver_match.namespaces)

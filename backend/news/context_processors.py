from .models import NewsArticle, SiteSettings


def site_settings(request):
    return {"site_settings": SiteSettings.load()}


def news_notification(request):
    """Powers the "new article" toast in base.html. last_seen_news_at is
    set at signup, so this only ever flags articles published after the
    account existed — never floods a new user with every past article."""
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {}
    qs = NewsArticle.objects.filter(is_published=True)
    if user.last_seen_news_at:
        qs = qs.filter(published_at__gt=user.last_seen_news_at)
    latest = qs.order_by("-published_at").first()
    return {"unseen_news_article": latest}

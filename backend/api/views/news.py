from django.shortcuts import get_object_or_404
from news.models import NewsArticle
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


def _article_summary_dict(request, article):
    return {
        "slug": article.slug,
        "title": article.title,
        "category": article.category,
        "category_display": article.get_category_display(),
        "image": request.build_absolute_uri(article.image.url) if article.image else None,
        "summary": article.display_summary(),
        "published_at": article.published_at.isoformat(),
    }


@api_view(["GET"])
@permission_classes([AllowAny])
def news_list(request):
    category = request.GET.get("category", "").strip()
    articles = NewsArticle.objects.filter(is_published=True)
    if category:
        articles = articles.filter(category=category)
    limit = min(int(request.GET.get("limit", 50)), 100)

    return Response({
        "articles": [_article_summary_dict(request, a) for a in articles[:limit]],
        "categories": [{"value": v, "label": l} for v, l in NewsArticle.CATEGORY_CHOICES],
    })


@api_view(["GET"])
@permission_classes([AllowAny])
def news_detail(request, slug):
    article = get_object_or_404(NewsArticle, slug=slug, is_published=True)
    return Response({
        "slug": article.slug,
        "title": article.title,
        "category": article.category,
        "category_display": article.get_category_display(),
        "image": request.build_absolute_uri(article.image.url) if article.image else None,
        "body": article.body,
        "source_url": article.source_url,
        "published_at": article.published_at.isoformat(),
    })

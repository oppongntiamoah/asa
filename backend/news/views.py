from django.shortcuts import get_object_or_404, render

from .models import NewsArticle


def news_list(request):
    category = request.GET.get("category", "").strip()
    articles = NewsArticle.objects.filter(is_published=True)
    if category:
        articles = articles.filter(category=category)

    context = {
        "articles": articles,
        "categories": NewsArticle.CATEGORY_CHOICES,
        "active_category": category,
    }
    # HTMX category-filter clicks only need the pills+grid re-rendered
    # (so the active pill highlight updates too), not a full page
    # (including the sidebar/header) round-trip.
    template = "news/_content.html" if request.headers.get("HX-Request") == "true" else "news/list.html"
    return render(request, template, context)


def news_detail(request, slug):
    article = get_object_or_404(NewsArticle, slug=slug, is_published=True)
    return render(request, "news/detail.html", {"article": article})


def faq(request):
    faqs = [
        ("Are the prices live?", "No. GSE publishes closing prices once a day — every price in SikaTrack is labeled with the date it's from."),
        ("Is this investment advice?", "No. SikaTrack is an informational portfolio tracker, not a licensed investment adviser or broker under Ghanaian securities law."),
        ("Which brokers can I upload statements from?", "IC Securities and Black Star Advisors today. More brokers are being added over time — you can always add transactions manually in the meantime."),
        ("How much does it cost?", "SikaTrack is free to use right now. If paid plans launch later, your existing data and free-tier features won't disappear."),
        ("How do I delete my account?", "Once you're signed in, go to Settings → Danger zone → Request account deletion."),
        ("Is my data private?", "Yes. Your portfolio is visible only to you."),
    ]
    return render(request, "news/faq.html", {"faqs": faqs})


def contact(request):
    return render(request, "news/contact.html")

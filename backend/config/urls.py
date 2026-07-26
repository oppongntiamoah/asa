from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def manifest(request):
    return JsonResponse({
        "name": "SikaTrack",
        "short_name": "SikaTrack",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#f9fafb",
        "theme_color": "#059669",
        "icons": [],
    })


urlpatterns = [
    path("admin/", admin.site.urls),
    path("manifest.json", manifest, name="manifest"),
    path("accounts/", include("accounts.urls")),
    path("dividends/", include("dividends.urls")),
    path("statements/", include("statements.urls")),
    path("billing/", include("billing.urls")),
    path("watchlist/", include("watchlist.urls")),
    path("calendar/", include("corporate_actions.urls")),
    path("market/", include("instruments.urls")),
    path("news/", include("news.urls")),
    path("ckeditor5/", include("django_ckeditor_5.urls")),
    path("", include("portfolio.urls")),
]

# Not the most efficient way to serve uploaded media at scale, but for a
# single-server deployment without a separate object store/CDN configured,
# this is what actually makes uploaded images (news, instrument logos,
# OG images) reachable at all in production — the DEBUG-only static()
# helper Django ships with would otherwise leave /media/ completely
# unserved once DEBUG=False. Swap for S3/CDN-backed storage if traffic
# ever justifies it.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

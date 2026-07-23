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
    path("api/", include("api.urls")),
    path("", include("portfolio.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

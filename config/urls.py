from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import FileResponse, HttpResponse, JsonResponse
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


def spa_shell(request):
    """
    Serves the built Svelte SPA's index.html (see frontend/). The SPA does
    its own client-side (hash-based) routing from there, so this one view
    is all Django needs — no wildcard path capture required.
    """
    index_path = settings.BASE_DIR / "static" / "app" / "index.html"
    if not index_path.exists():
        return HttpResponse(
            "The SikaTrack app isn't built yet. Run `npm run build` in frontend/.",
            status=501,
        )
    return FileResponse(open(index_path, "rb"), content_type="text/html")


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
    path("app/", spa_shell, name="spa_shell"),
    path("", include("portfolio.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

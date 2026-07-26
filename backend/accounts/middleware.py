from datetime import timedelta

from django.utils import timezone

from .models import UserSession

_STALE_AFTER = timedelta(minutes=5)


class UpdateSessionActivityMiddleware:
    """Keeps UserSession.last_seen roughly current for the Devices page,
    without writing to the database on every single request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        user = getattr(request, "user", None)
        session_key = getattr(request.session, "session_key", None)
        if user is not None and user.is_authenticated and session_key:
            UserSession.objects.filter(
                session_key=session_key, last_seen__lt=timezone.now() - _STALE_AFTER
            ).update(last_seen=timezone.now())
        return response

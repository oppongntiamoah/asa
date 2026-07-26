from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from .models import UserSession
from .user_agent import get_client_ip


@receiver(user_logged_in)
def record_login_session(sender, request, user, **kwargs):
    session_key = request.session.session_key
    if not session_key:
        request.session.save()
        session_key = request.session.session_key
    UserSession.objects.update_or_create(
        session_key=session_key,
        defaults={
            "user": user,
            "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            "ip_address": get_client_ip(request),
        },
    )


@receiver(user_logged_out)
def remove_logout_session(sender, request, user, **kwargs):
    session_key = getattr(request.session, "session_key", None)
    if session_key:
        UserSession.objects.filter(session_key=session_key).delete()

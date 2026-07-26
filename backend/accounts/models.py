import secrets

import pyotp
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model from day one — cheap now, painful to retrofit later."""

    phone_number = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen_news_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Set to signup time and updated whenever the user views/dismisses News — anything published after this counts as 'new'.",
    )

    def __str__(self):
        return self.get_full_name() or self.username


class UserSession(models.Model):
    """
    One row per active login, so a user can see (and revoke) exactly what's
    logged into their account — "Devices" under Settings. Mirrors Django's
    own session table (keyed on the same session_key) rather than
    replacing it: revoking here deletes the real Session row too, which is
    what actually invalidates it server-side.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions")
    session_key = models.CharField(max_length=40, unique=True)
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-last_seen"]

    def __str__(self):
        return f"{self.user} — {self.session_key[:8]}"


class TOTPDevice(models.Model):
    """
    One authenticator-app secret per user (Google/Microsoft Authenticator,
    1Password, etc. — anything that speaks standard TOTP). `confirmed`
    stays False until the user proves they actually scanned the code and
    can produce a valid one-time code, so an abandoned setup never
    silently gates login.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="totp_device")
    secret = models.CharField(max_length=32)
    confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def verify(self, code: str) -> bool:
        return pyotp.TOTP(self.secret).verify((code or "").strip().replace(" ", ""), valid_window=1)

    def provisioning_uri(self) -> str:
        label = self.user.email or self.user.username
        return pyotp.TOTP(self.secret).provisioning_uri(name=label, issuer_name="SikaTrack")


class TOTPRecoveryCode(models.Model):
    """
    One-time backup codes generated alongside a confirmed TOTPDevice, for
    the "I lost my phone" case. Stored hashed (same hasher as passwords) —
    the plaintext is shown to the user exactly once, at generation time.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recovery_codes")
    code_hash = models.CharField(max_length=128)
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def generate_plaintext_code() -> str:
        return f"{secrets.token_hex(4)}-{secrets.token_hex(4)}"

    @classmethod
    def generate_set(cls, user, count=8) -> list:
        """Replaces any existing codes and returns the new plaintext codes
        (only ever available at generation time — not recoverable after)."""
        cls.objects.filter(user=user).delete()
        plaintext_codes = [cls.generate_plaintext_code() for _ in range(count)]
        cls.objects.bulk_create([cls(user=user, code_hash=make_password(code)) for code in plaintext_codes])
        return plaintext_codes

    @classmethod
    def try_consume(cls, user, code: str) -> bool:
        code = (code or "").strip()
        if not code:
            return False
        for recovery_code in cls.objects.filter(user=user, used_at__isnull=True):
            if check_password(code, recovery_code.code_hash):
                from django.utils import timezone

                recovery_code.used_at = timezone.now()
                recovery_code.save(update_fields=["used_at"])
                return True
        return False

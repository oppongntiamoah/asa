"""
Base settings shared by dev and prod. Never point DJANGO_SETTINGS_MODULE
here directly — use config.settings.dev or config.settings.prod.
"""
from pathlib import Path

from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("SECRET_KEY", default="django-insecure-change-me-in-prod")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_q",
    "import_export",
    "rest_framework",
    "accounts",
    "instruments",
    "portfolio",
    "dividends",
    "corporate_actions",
    "statements",
    "billing",
    "watchlist",
    "news",
    "api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME", default="sikatrack"),
        "USER": config("DB_USER", default="sikatrack"),
        "PASSWORD": config("DB_PASSWORD", default="sikatrack_dev"),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
    }
}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Accra"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "portfolio:dashboard"
LOGOUT_REDIRECT_URL = "accounts:login"

# Django-Q2 — ORM broker, no Redis/RabbitMQ needed. See PRODUCT_DESIGN.md §2.4.
Q_CLUSTER = {
    "name": "sikatrack",
    "workers": 2,
    "timeout": 90,
    "retry": 120,
    "queue_limit": 50,
    "bulk": 10,
    "orm": "default",
}

# Statement uploads: private storage served only through authenticated views,
# never a public MEDIA_URL path. See PRODUCT_DESIGN.md §8.1.
PRIVATE_MEDIA_ROOT = BASE_DIR / "private_media"

# Paystack — one-time mobile money checkout for billing. Empty by default;
# billing.services.is_billing_enabled() is False by default too, so a
# missing key only matters once the founder actually switches billing on.
PAYSTACK_SECRET_KEY = config("PAYSTACK_SECRET_KEY", default="")
PAYSTACK_PUBLIC_KEY = config("PAYSTACK_PUBLIC_KEY", default="")

# The Svelte PWA (see frontend/) talks to this API using session auth +
# CSRF, not tokens — it's served from the same origin (Vite's dev proxy in
# development, Django's own static files in production), so there's no
# cross-origin cookie problem to solve and no need for a JWT/DRF-token
# dependency on top of the session auth the rest of the app already uses.
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
}

import os

import dj_database_url

from .base import *

DEBUG = False

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-scorpionhq-2026-random-key-xyz",
)

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(
        "DJANGO_ALLOWED_HOSTS",
        "rayyan20n.pythonanywhere.com",
    ).split(",")
    if host.strip()
]

# Database
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=60,
        )
    }

# WhiteNoise
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
] + [m for m in MIDDLEWARE if m != "django.middleware.security.SecurityMiddleware"]

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# SSL
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Security headers
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"

CSRF_TRUSTED_ORIGINS = [
    "https://rayyan20n.pythonanywhere.com",
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Local secrets (API keys etc.) — NEVER committed to git.
# Create config/settings/local_settings.py on the server with:
#   GEMINI_API_KEY = "your-actual-key-here"
# This file is in .gitignore and survives git pull/reset.
# ---------------------------------------------------------------------------
try:
    from .local_settings import *  # noqa: F401, F403
except ImportError:
    pass

# Fallback: env var if local_settings.py doesn't set the key
if not GEMINI_API_KEY:
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

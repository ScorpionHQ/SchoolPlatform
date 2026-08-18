import os

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

from .base import *

DEBUG = False

if os.environ.get("DJANGO_SECRET_KEY") in (
    None,
    "",
    "dev-only-insecure-secret-key-change-me",
):

    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY must be set in the production "
        "environment."
    )

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(
        "DJANGO_ALLOWED_HOSTS",
        "",
    ).split(",")
    if host.strip()
]

if not ALLOWED_HOSTS:

    ALLOWED_HOSTS = [
        "localhost",
        "127.0.0.1",
    ]

# Render provides DATABASE_URL automatically
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=60,
        )
    }
elif all(
    os.environ.get(name)
    for name in (
        "DJANGO_DB_NAME",
        "DJANGO_DB_USER",
        "DJANGO_DB_PASSWORD",
        "DJANGO_DB_HOST",
    )
):

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ["DJANGO_DB_NAME"],
            "USER": os.environ["DJANGO_DB_USER"],
            "PASSWORD": os.environ["DJANGO_DB_PASSWORD"],
            "HOST": os.environ["DJANGO_DB_HOST"],
            "PORT": os.environ.get("DJANGO_DB_PORT", "5432"),
            "CONN_MAX_AGE": 60,
        }
    }

# WhiteNoise - serve static files
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

SECURE_SSL_REDIRECT = os.environ.get(
    "DJANGO_SECURE_SSL_REDIRECT",
    "True",
) == "True"

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SESSION_COOKIE_SECURE = os.environ.get(
    "DJANGO_SESSION_COOKIE_SECURE",
    "True",
) == "True"

CSRF_COOKIE_SECURE = os.environ.get(
    "DJANGO_CSRF_COOKIE_SECURE",
    "True",
) == "True"

SECURE_HSTS_SECONDS = int(
    os.environ.get(
        "DJANGO_SECURE_HSTS_SECONDS",
        "31536000",
    )
)

SECURE_HSTS_INCLUDE_SUBDOMAINS = True

SECURE_HSTS_PRELOAD = True

SECURE_CONTENT_TYPE_NOSNIFF = True

SECURE_BROWSER_XSS_FILTER = True

X_FRAME_OPTIONS = "DENY"

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "DJANGO_CSRF_TRUSTED_ORIGINS",
        "",
    ).split(",")
    if origin.strip()
]

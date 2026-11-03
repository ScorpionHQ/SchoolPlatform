"""Production settings.

Target stack: Render (free web service) + Neon Postgres + Neon Object Storage.

Every value comes from environment variables; no secret is committed to git.
"""

import os

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401,F403


def env_list(name, default=""):
    return [
        item.strip()
        for item in os.environ.get(name, default).split(",")
        if item.strip()
    ]


DEBUG = False

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

SECRET_KEY = (
    os.environ.get("DJANGO_SECRET_KEY")
    or os.environ.get("SECRET_KEY")
    or ""
).strip()

if not SECRET_KEY or SECRET_KEY.startswith(("django-insecure-", "dev-only")):
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY must be set to a strong random value in production."
    )

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS")

RENDER_EXTERNAL_HOSTNAME = os.environ.get(
    "RENDER_EXTERNAL_HOSTNAME",
    "",
).strip()

if RENDER_EXTERNAL_HOSTNAME and RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

if not ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        "DJANGO_ALLOWED_HOSTS must list at least one host."
    )

# ---------------------------------------------------------------------------
# Database (Neon Postgres)
# ---------------------------------------------------------------------------

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

if not DATABASE_URL:
    raise ImproperlyConfigured(
        "DATABASE_URL must point to the Neon Postgres database."
    )

DATABASES = {
    "default": dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=60,
        conn_health_checks=True,
    )
}

# Neon's pooled endpoint (PgBouncer, transaction mode) needs server-side
# cursors disabled.
if "pooler" in DATABASE_URL:
    DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True

# ---------------------------------------------------------------------------
# Static files (WhiteNoise) and media files (Neon Object Storage)
# ---------------------------------------------------------------------------

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

AWS_STORAGE_BUCKET_NAME = os.environ.get(
    "AWS_STORAGE_BUCKET_NAME",
    "",
).strip()

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "").strip()

AWS_SECRET_ACCESS_KEY = os.environ.get(
    "AWS_SECRET_ACCESS_KEY",
    "",
).strip()

AWS_S3_ENDPOINT_URL = (
    os.environ.get("AWS_S3_ENDPOINT_URL")
    or os.environ.get("AWS_ENDPOINT_URL_S3")
    or ""
).strip()

AWS_S3_REGION_NAME = (
    os.environ.get("AWS_S3_REGION_NAME")
    or os.environ.get("AWS_REGION")
    or ""
).strip()

USE_REMOTE_MEDIA = all(
    [
        AWS_STORAGE_BUCKET_NAME,
        AWS_ACCESS_KEY_ID,
        AWS_SECRET_ACCESS_KEY,
        AWS_S3_ENDPOINT_URL,
    ]
)

if USE_REMOTE_MEDIA:

    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": AWS_STORAGE_BUCKET_NAME,
            "access_key": AWS_ACCESS_KEY_ID,
            "secret_key": AWS_SECRET_ACCESS_KEY,
            "endpoint_url": AWS_S3_ENDPOINT_URL,
            "region_name": AWS_S3_REGION_NAME or None,
            # Neon Object Storage requires path-style requests.
            "addressing_style": "path",
            "signature_version": "s3v4",
            # Private bucket: files are served through signed URLs.
            "querystring_auth": True,
            "querystring_expire": 3600,
            "file_overwrite": False,
            "default_acl": None,
            "object_parameters": {
                "CacheControl": "max-age=86400",
            },
        },
    }

# Without S3, keep uploads in Postgres so they survive a redeploy on hosts
# with an ephemeral disk.
elif os.environ.get("MEDIA_IN_DATABASE", "1") == "1":

    STORAGES["default"] = {
        "BACKEND": "core.storage.DatabaseStorage",
    }

# ---------------------------------------------------------------------------
# HTTPS / proxy (Render terminates TLS in front of the app)
# ---------------------------------------------------------------------------

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SECURE_SSL_REDIRECT = (
    os.environ.get("DJANGO_SECURE_SSL_REDIRECT", "1") == "1"
)

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# Enable only after the final domain is live, otherwise browsers pin HSTS.
SECURE_HSTS_SECONDS = int(
    os.environ.get("DJANGO_SECURE_HSTS_SECONDS", "0")
)
SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_HSTS_SECONDS > 0
SECURE_HSTS_PRELOAD = False

CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

if RENDER_EXTERNAL_HOSTNAME:

    render_origin = f"https://{RENDER_EXTERNAL_HOSTNAME}"

    if render_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(render_origin)

# ---------------------------------------------------------------------------
# Email (password reset)
# ---------------------------------------------------------------------------

EMAIL_HOST = os.environ.get("EMAIL_HOST", "").strip()

EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))

EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "").strip()

EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")

EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "1") == "1"

DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL",
    "SchoolPlatform <no-reply@localhost>",
)

# Without an SMTP host, print reset emails to the Render logs instead of
# failing the request.
EMAIL_BACKEND = os.environ.get(
    "DJANGO_EMAIL_BACKEND",
    (
        "django.core.mail.backends.smtp.EmailBackend"
        if EMAIL_HOST
        else "django.core.mail.backends.console.EmailBackend"
    ),
)

# ---------------------------------------------------------------------------
# Logging (Render reads stdout)
# ---------------------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

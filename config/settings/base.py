from pathlib import Path
import os
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent.parent

try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass


SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "dev-only-insecure-secret-key-change-me",
)

ADMIN_URL = os.environ.get(
    "DJANGO_ADMIN_URL",
    "admin/",
)

DEBUG = False

ALLOWED_HOSTS = []


INSTALLED_APPS = [
    
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    
    "core",
    "accounts",
    "institutions",
    "students",
    "parents",
    "teachers",
    "administration",
    "classes",
    "subjects",
    "attendance",
    "grades",
    "notifications",
    "assistant",
    "billing",
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',

    'django.middleware.locale.LocaleMiddleware',

    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'accounts.middleware.ForcePasswordChangeMiddleware',
    'accounts.middleware.ForceProfilePhotoMiddleware',

    'institutions.middleware.TenantMiddleware',
]


ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.i18n",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "institutions.context_processors.tenant_context",
                "notifications.context_processors.notifications_context",
                "assistant.context_processors.assistant_context",
            ],
        },
    },
]


WSGI_APPLICATION = "config.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]
LANGUAGE_CODE = "ar"

LANGUAGES = [
    ("ar", _("Arabic")),
    ("en", _("English")),
]

TIME_ZONE = "Asia/Baghdad"

USE_I18N = True

USE_TZ = True

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

STATIC_URL = "static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"


MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"


# ---------------------------------------------------------------------------
# AI Assistant (local agent only — no external LLM API)
# ---------------------------------------------------------------------------

ASSISTANT_ENABLED = True

# Default persona (used for every non-student user).
ASSISTANT_NAME = "Huda"
ASSISTANT_AVATAR = "assistant/avatar.png"
ASSISTANT_DESCRIPTION = ""

# Student personas by gender.
ASSISTANT_NAME_MALE = "Rayyan"
ASSISTANT_AVATAR_MALE = "assistant/avatar_male.png"

ASSISTANT_NAME_FEMALE = "Huda"
ASSISTANT_AVATAR_FEMALE = "assistant/avatar_female.png"

# Assistant file uploads (document reader).
ASSISTANT_MAX_FILES = int(os.environ.get("ASSISTANT_MAX_FILES", "10"))
ASSISTANT_MAX_FILE_SIZE_MB = int(
    os.environ.get("ASSISTANT_MAX_FILE_SIZE_MB", "20")
)
ASSISTANT_MAX_FILE_TEXT_CHARS = int(
    os.environ.get("ASSISTANT_MAX_FILE_TEXT_CHARS", "300000")
)
ASSISTANT_REPORT_EXCERPT_CHARS = int(
    os.environ.get("ASSISTANT_REPORT_EXCERPT_CHARS", "3000")
)
ASSISTANT_FILE_PROMPT_CHARS = int(
    os.environ.get("ASSISTANT_FILE_PROMPT_CHARS", "120000")
)
ASSISTANT_ALLOWED_EXTENSIONS = (
    "pdf",
    "docx",
    "xlsx",
    "txt",
    "md",
    "csv",
    "png",
    "jpg",
    "jpeg",
    "webp",
)

# OpenRouter (free models — OpenAI-compatible).
# Get a free key from https://openrouter.ai/keys (no credit card).
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.environ.get(
    "OPENROUTER_MODEL",
    "google/gemma-4-26b-a4b-it:free",
)
OPENROUTER_BACKUP_MODELS = [
    m.strip()
    for m in os.environ.get(
        "OPENROUTER_BACKUP_MODELS",
        "nvidia/nemotron-3-super-120b-a12b:free,nvidia/nemotron-3-nano-30b-a3b:free",
    ).split(",")
    if m.strip()
]
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_TIMEOUT = int(os.environ.get("OPENROUTER_TIMEOUT", "30"))
OPENROUTER_MAX_TOKENS = int(
    os.environ.get("OPENROUTER_MAX_TOKENS", "4096")
)


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"

# ---------------------------------------------------------------------------
# Local secrets (API keys etc.) — NEVER committed to git.
# Create config/settings/local_settings.py with your actual keys.
# This file is in .gitignore and survives git pull/reset.
# ---------------------------------------------------------------------------
try:
    from .local_settings import *  # noqa: F401, F403
except ImportError:
    pass

from django.contrib.messages import constants as message_constants

MESSAGE_TAGS = {
    message_constants.DEBUG: "secondary",
    message_constants.INFO: "info",
    message_constants.SUCCESS: "success",
    message_constants.WARNING: "warning",
    message_constants.ERROR: "danger",
}
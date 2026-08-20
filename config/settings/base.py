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
# AI Assistant
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

# External LLM API (optional). Leave blank to use the built-in agent.
ASSISTANT_API_URL = os.environ.get("ASSISTANT_API_URL", "")
ASSISTANT_API_KEY = os.environ.get("ASSISTANT_API_KEY", "")
ASSISTANT_API_MODEL = os.environ.get(
    "ASSISTANT_API_MODEL",
    "gpt-4o-mini",
)
ASSISTANT_API_TIMEOUT = 12

# Google Gemini (free tier). The recommended engine for the assistant:
# free of charge, very powerful, and supports Google Search grounding
# with real sources. Get a free API key from Google AI Studio
# (https://aistudio.google.com/apikey) and put it in the .env file.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")
GEMINI_BACKUP_MODELS = ["gemini-3.6-flash"]
GEMINI_TIMEOUT = int(os.environ.get("GEMINI_TIMEOUT", "30"))
GEMINI_ENABLE_SEARCH = os.environ.get(
    "GEMINI_ENABLE_SEARCH",
    "1",
) == "1"
GEMINI_MAX_OUTPUT_TOKENS = int(
    os.environ.get("GEMINI_MAX_OUTPUT_TOKENS", "8192")
)

# Assistant file uploads (AI document reader).
# Users can attach PDF/DOCX/XLSX/TXT/CSV/images and ask the assistant to
# summarize, analyze or answer questions about them, then export a PDF report.
ASSISTANT_MAX_FILES = int(os.environ.get("ASSISTANT_MAX_FILES", "10"))
ASSISTANT_MAX_FILE_SIZE_MB = int(
    os.environ.get("ASSISTANT_MAX_FILE_SIZE_MB", "20")
)
# Max characters of extracted text kept per file (protects the LLM prompt).
ASSISTANT_MAX_FILE_TEXT_CHARS = int(
    os.environ.get("ASSISTANT_MAX_FILE_TEXT_CHARS", "300000")
)
# Per-file excerpt included inside generated PDF reports.
ASSISTANT_REPORT_EXCERPT_CHARS = int(
    os.environ.get("ASSISTANT_REPORT_EXCERPT_CHARS", "3000")
)
# Extracted text included in each Gemini prompt, capped per file.
ASSISTANT_FILE_PROMPT_CHARS = int(
    os.environ.get("ASSISTANT_FILE_PROMPT_CHARS", "120000")
)
# Allowed upload extensions.
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


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"

from django.contrib.messages import constants as message_constants

MESSAGE_TAGS = {
    message_constants.DEBUG: "secondary",
    message_constants.INFO: "info",
    message_constants.SUCCESS: "success",
    message_constants.WARNING: "warning",
    message_constants.ERROR: "danger",
}
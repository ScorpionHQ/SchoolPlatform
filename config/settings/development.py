import os

from .base import *

DEBUG = True

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "0.0.0.0",
    "desktop-du12on1.tailab0205.ts.net",
]

if os.environ.get("DJANGO_DEBUG_HOSTS"):

    ALLOWED_HOSTS.extend(
        host.strip()
        for host in os.environ["DJANGO_DEBUG_HOSTS"].split(",")
        if host.strip()
    )

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

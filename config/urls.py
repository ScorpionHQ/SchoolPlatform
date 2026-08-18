from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("", include("core.urls")),
    path("i18n/", include("django.conf.urls.i18n")),
    path(
     "accounts/",
     include("accounts.urls"),
    ),
    path(
     "notifications/",
     include("notifications.urls"),
    ),
    path(
     "assistant/",
     include("assistant.urls"),
    ),
    path(
     "administration/",
     include("administration.urls"),
    ),
    path(
     "billing/",
     include("billing.urls"),
    ),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )

handler400 = "core.views.error_400"
handler403 = "core.views.error_403"
handler404 = "core.views.error_404"
handler500 = "core.views.error_500"
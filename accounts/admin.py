from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    list_display = (
        "username",
        "first_name",
        "last_name",
        "role",
        "login_code",
        "is_staff",
    )

    fieldsets = UserAdmin.fieldsets + (
        (
            _("School Platform"),
            {
                "fields": (
                    "role",
                    "login_code",
                    "phone_number",
                    "profile_image",
                )
            },
        ),
    )

    readonly_fields = (
        "login_code",
    )
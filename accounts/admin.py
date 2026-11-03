from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import AuditLog, User


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


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):

    list_display = (
        "created_at",
        "user",
        "action",
        "model_name",
        "object_id",
        "ip_address",
    )

    list_filter = (
        "action",
        "model_name",
    )

    search_fields = (
        "user__username",
        "description",
    )

    readonly_fields = (
        "user",
        "action",
        "model_name",
        "object_id",
        "description",
        "ip_address",
        "created_at",
    )

    def has_add_permission(self, request):

        return False

    def has_change_permission(self, request, obj=None):

        return False
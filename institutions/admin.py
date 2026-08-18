from django.contrib import admin

from .models import Institution


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "short_name",
        "manager_code",
        "phone_number",
        "is_active",
    )

    search_fields = (
        "name",
        "short_name",
        "phone_number",
    )

    list_filter = (
        "is_active",
    )

    ordering = (
        "name",
    )
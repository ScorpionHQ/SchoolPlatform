from django.contrib import admin

from .models import Parent


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "relationship",
        "created_at",
    )

    list_filter = (
        "created_at",
    )

    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__login_code",
    )

    filter_horizontal = (
        "students",
    )

    raw_id_fields = (
        "user",
    )

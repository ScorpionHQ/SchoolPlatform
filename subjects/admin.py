from django.contrib import admin

from .models import Subject


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "name",
        "code",
        "institution",
        "classroom",
        "teacher",
        "created_at",
    )

    list_filter = (
        "institution",
        "classroom",
    )

    search_fields = (
        "name",
        "code",
    )

    autocomplete_fields = (
        "teacher",
    )

    list_select_related = (
        "institution",
        "classroom",
        "teacher",
    )

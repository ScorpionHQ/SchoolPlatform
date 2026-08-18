from django.contrib import admin

from .models import ClassRoom


@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "level",
        "academic_year",
        "institution",
    )

    search_fields = (
        "name",
        "level",
        "academic_year",
    )

    list_filter = (
        "institution",
        "academic_year",
    )
from django.contrib import admin

from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "student_code",
        "user",
        "institution",
        "classroom",
        "parent_phone",
        "created_at",
    )

    list_filter = (
        "institution",
        "classroom",
        "created_at",
    )

    search_fields = (
        "student_code",
        "user__first_name",
        "user__last_name",
        "user__username",
    )

    ordering = (
        "student_code",
    )
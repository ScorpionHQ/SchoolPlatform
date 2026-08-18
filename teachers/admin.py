from django.contrib import admin

from .models import Teacher


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = (
        "employee_code",
        "user",
        "institution",
        "specialization",
    )

    search_fields = (
        "employee_code",
        "user__username",
        "user__first_name",
        "user__last_name",
    )

    list_filter = (
        "institution",
        "specialization",
    )
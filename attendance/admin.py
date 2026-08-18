from django.contrib import admin

from .models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "date",
        "status",
        "teacher",
    )

    search_fields = (
        "student__student_code",
        "student__user__first_name",
        "student__user__last_name",
    )

    list_filter = (
        "status",
        "date",
    )

    date_hierarchy = "date"

    ordering = (
        "-date",
    )
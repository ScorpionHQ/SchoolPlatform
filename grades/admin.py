from django.contrib import admin

from .models import Grade


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "subject",
        "exam_name",
        "score",
        "max_score",
        "exam_date",
    )

    search_fields = (
        "student__student_code",
        "student__user__first_name",
        "student__user__last_name",
        "subject__name",
        "exam_name",
    )

    list_filter = (
        "subject",
        "exam_date",
    )

    date_hierarchy = "exam_date"

    ordering = (
        "-exam_date",
    )
from django.conf import settings
from django.db import models


class Grade(models.Model):
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="grades",
    )

    subject = models.ForeignKey(
        "subjects.Subject",
        on_delete=models.CASCADE,
        related_name="grades",
    )

    teacher = models.ForeignKey(
     "teachers.Teacher",
     on_delete=models.SET_NULL,
     null=True,
     blank=True,
     related_name="recorded_grades",
    )

    exam_name = models.CharField(
        max_length=100,
    )

    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    max_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=100,
    )

    note = models.TextField(
        blank=True,
    )

    exam_date = models.DateField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-exam_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "subject", "exam_name"],
                name="unique_grade_per_student_subject_exam",
            ),
        ]

    def __str__(self):
        return (
            f"{self.student} - "
            f"{self.subject} - "
            f"{self.exam_name}"
        )
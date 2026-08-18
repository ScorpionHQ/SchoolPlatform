from django.db import models
from django.utils.translation import gettext_lazy as _


class Attendance(models.Model):

    class Status(models.TextChoices):
        PRESENT = "present", _("Present")
        ABSENT = "absent", _("Absent")
        LATE = "late", _("Late")
        EXCUSED = "excused", _("Excused")

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )

    teacher = models.ForeignKey(
        "teachers.Teacher",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attendance_records",
    )

    subject = models.ForeignKey(
      "subjects.Subject",
       on_delete=models.CASCADE,
       related_name="attendance_records",
       null=True,
       blank=True,
    )

    classroom = models.ForeignKey(
      "classes.ClassRoom",
      on_delete=models.CASCADE,
      related_name="attendance_records",
      null=True,
      blank=True,
    )
    date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PRESENT,
    )

    note = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-date"]
        unique_together = (
            "student",
            "subject",
            "date",
        )

    def __str__(self):
        return (
            f"{self.student} - "
            f"{self.subject} - "
            f"{self.date}"
        )
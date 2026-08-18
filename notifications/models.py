from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Notification(models.Model):

    class Type(models.TextChoices):
        STUDENT = "student", _("Student")
        TEACHER = "teacher", _("Teacher")
        PARENT = "parent", _("Parent")
        CLASS = "class", _("Class")
        SUBJECT = "subject", _("Subject")
        GRADE = "grade", _("Grade")
        ATTENDANCE = "attendance", _("Attendance")
        FINANCE = "finance", _("Finance")
        ANNOUNCEMENT = "announcement", _("Announcement")
        INSTITUTION = "institution", _("Institution")
        SYSTEM = "system", _("System")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.SYSTEM,
    )

    title = models.CharField(
        max_length=255,
    )

    message = models.TextField(
        blank=True,
    )

    link = models.CharField(
        max_length=255,
        blank=True,
    )

    is_read = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")

    def __str__(self):
        return self.title

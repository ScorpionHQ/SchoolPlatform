from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from classes.models import ClassRoom


class Student(models.Model):

    class Gender(models.TextChoices):
        MALE = "male", _("Male")
        FEMALE = "female", _("Female")

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile",
    )

    institution = models.ForeignKey(
        "institutions.Institution",
        on_delete=models.CASCADE,
        related_name="students",
    )

    classroom = models.ForeignKey(
        "classes.ClassRoom",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
    )

    gender = models.CharField(
        max_length=10,
        choices=Gender.choices,
        blank=True,
        default="",
    )


    student_code = models.CharField(
        max_length=30,
        unique=True,
    )

    date_of_birth = models.DateField(
        null=True,
        blank=True,
    )

    address = models.TextField(
        blank=True,
    )

    parent_phone = models.CharField(
        max_length=20,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["student_code"]

    def __str__(self):
        return self.user.get_full_name() or self.student_code
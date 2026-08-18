from django.conf import settings
from django.db import models


class Parent(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="parent_profile",
    )

    students = models.ManyToManyField(
        "students.Student",
        related_name="parents",
        blank=True,
    )

    relationship = models.CharField(
        max_length=50,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["user__username"]

    def __str__(self):
        return self.user.get_full_name() or self.user.username
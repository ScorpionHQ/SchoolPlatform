from django.db import models


class Subject(models.Model):
    institution = models.ForeignKey(
        "institutions.Institution",
        on_delete=models.CASCADE,
        related_name="subjects",
    )

    name = models.CharField(
        max_length=100,
    )

    code = models.CharField(
        max_length=30,
        blank=True,
    )

    description = models.TextField(
        blank=True,
    )

    teacher = models.ForeignKey(
     "teachers.Teacher",
     on_delete=models.SET_NULL,
     null=True,
     blank=True,
     related_name="subjects",
    )
    classroom = models.ForeignKey(
     "classes.ClassRoom",
     on_delete=models.CASCADE,
     related_name="subjects",
     null=True,
     blank=True,
    )
    created_at = models.DateTimeField(
     auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
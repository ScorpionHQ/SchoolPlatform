from django.db import models
from django.utils.translation import gettext_lazy as _

class ClassRoom(models.Model):

    class Stage(models.TextChoices):

     PRIMARY = "primary", _("Primary School")

     MIDDLE = "middle", _("Middle School")

     PREPARATORY = "preparatory", _("Preparatory School")
     
    institution = models.ForeignKey(
        "institutions.Institution",
        on_delete=models.CASCADE,
        related_name="classrooms",
    )

    stage = models.CharField(
        max_length=20,
        choices=Stage.choices,
        default=Stage.PRIMARY,
    )

    name = models.CharField(
        max_length=100,
    )

    level = models.CharField(
        max_length=50,
    )

    academic_year = models.CharField(
        max_length=20,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["stage", "level", "name"]
        verbose_name = _("Class Room")
        verbose_name_plural = _("Class Rooms")
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "name", "level", "academic_year"],
                name="unique_classroom_per_institution",
            ),
        ]

    def __str__(self):
        return f"{self.name} - {self.level}"
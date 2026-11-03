from django.db import models


class StoredFile(models.Model):
    """A small file kept in the database (see ``core.storage``)."""

    name = models.CharField(
        max_length=255,
        unique=True,
    )

    content = models.BinaryField(
        editable=False,
    )

    content_type = models.CharField(
        max_length=100,
        blank=True,
    )

    size = models.PositiveBigIntegerField(
        default=0,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name



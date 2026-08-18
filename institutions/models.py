from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class Institution(models.Model):
    name = models.CharField(
        max_length=200,
    )
    users = models.ManyToManyField(
    settings.AUTH_USER_MODEL,
    related_name="institutions",
    blank=True,
)

    manager_code = models.CharField(
        max_length=30,
        unique=True,
        blank=True,
        help_text=_(
            "A dedicated login code for this school's manager. "
            "Auto-generated if left empty."
        ),
    )

    short_name = models.CharField(
        max_length=50,
    )

    logo = models.ImageField(
        upload_to="institutions/logos/",
        blank=True,
        null=True,
    )

    address = models.TextField(
        blank=True,
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True,
    )

    email = models.EmailField(
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["name"]
        verbose_name = _("Institution")
        verbose_name_plural = _("Institutions")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.manager_code:
            self.manager_code = self.generate_manager_code()
        super().save(*args, **kwargs)

    def generate_manager_code(self):
        """Generate a unique manager login code for this school."""

        base = "MGR"

        if self.short_name:
            cleaned = "".join(
                ch
                for ch in self.short_name.strip().upper()
                if ch.isalnum() or ch in "-_"
            )
            if cleaned:
                base = f"MGR-{cleaned}"

        candidate = base
        counter = 1

        while (
            Institution.objects.filter(
                manager_code=candidate,
            ).exclude(pk=self.pk).exists()
        ):
            counter += 1
            candidate = f"{base}-{counter}"

        return candidate
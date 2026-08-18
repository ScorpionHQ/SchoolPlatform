from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Conversation(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assistant_conversations",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-updated_at", "-created_at"]
        verbose_name = _("Assistant conversation")
        verbose_name_plural = _("Assistant conversations")

    def __str__(self):
        return f"#{self.pk} - {self.user}"


class Message(models.Model):

    class Role(models.TextChoices):
        USER = "user", _("User")
        ASSISTANT = "assistant", _("Assistant")
        SYSTEM = "system", _("System")

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
    )

    content = models.TextField()

    sources = models.JSONField(
        default=list,
        blank=True,
        help_text=_("Sources cited by the assistant, as a list of "
                    "{title, url} objects."),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["created_at", "id"]
        verbose_name = _("Assistant message")
        verbose_name_plural = _("Assistant messages")

    def __str__(self):
        return f"{self.get_role_display()}: {self.content[:50]}"


class Attachment(models.Model):

    class Kind(models.TextChoices):
        PDF = "pdf", _("PDF document")
        DOCX = "docx", _("Word document")
        XLSX = "xlsx", _("Excel spreadsheet")
        TEXT = "text", _("Text file")
        IMAGE = "image", _("Image")
        OTHER = "other", _("File")

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="attachments",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assistant_attachments",
    )

    name = models.CharField(
        max_length=255,
    )

    file = models.FileField(
        upload_to="assistant/%Y/%m/%d/",
        help_text=_("The uploaded document or image."),
    )

    kind = models.CharField(
        max_length=10,
        choices=Kind.choices,
        default=Kind.OTHER,
    )

    size = models.PositiveIntegerField(
        default=0,
        help_text=_("File size in bytes."),
    )

    text = models.TextField(
        default="",
        blank=True,
        help_text=_("Extracted text used for summarization and Q&A."),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = _("Assistant attachment")
        verbose_name_plural = _("Assistant attachments")

    def __str__(self):
        return self.name

    @property
    def display_size(self):
        from .fileutils import human_size
        return human_size(self.size)

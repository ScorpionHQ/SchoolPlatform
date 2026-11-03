from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from .managers import UserManager


class User(AbstractUser):

    class Role(models.TextChoices):
        STUDENT = "student", _("Student")
        PARENT = "parent", _("Parent")
        TEACHER = "teacher", _("Teacher")
        ASSISTANT_MANAGER = "assistant_manager", _("Assistant Manager")
        MANAGER = "manager", _("Manager")
        SYSTEM_ADMIN = "system_admin", _("System Administrator")

    class Gender(models.TextChoices):
        MALE = "male", _("Male")
        FEMALE = "female", _("Female")

    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        default=Role.STUDENT,
    )

    gender = models.CharField(
        max_length=10,
        choices=Gender.choices,
        blank=True,
        default="",
        help_text=_("Used to pick the assistant character (boy/girl)."),
    )

    login_code = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        editable=False,
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True,
    )

    profile_image = models.ImageField(
        upload_to="profiles/",
        blank=True,
        null=True,
    )

    must_change_password = models.BooleanField(
        default=False,
        help_text=_("Forces the user to change their password on next login."),
    )

    objects = UserManager()

    def save(self, *args, **kwargs):

        old_role = None

        if self.pk:

            try:
                old_role = User.objects.get(pk=self.pk).role
            except User.DoesNotExist:
                pass

        if not self.login_code:
            self.login_code = self.generate_login_code()

        elif old_role and old_role != self.role:
            self.login_code = self.generate_login_code()

        super().save(*args, **kwargs)

    def generate_login_code(self):

        prefixes = {
            self.Role.STUDENT: "STU",
            self.Role.PARENT: "PAR",
            self.Role.TEACHER: "TCH",
            self.Role.ASSISTANT_MANAGER: "ASM",
            self.Role.MANAGER: "ADM",
            self.Role.SYSTEM_ADMIN: "SYS",
        }

        prefix = prefixes.get(
            self.role,
            "USR",
        )

        users = User.objects.filter(
            login_code__startswith=prefix,
        )

        max_number = 0

        for user in users:

            try:
                number = int(
                    user.login_code[len(prefix):]
                )

                if number > max_number:
                    max_number = number

            except Exception:
                pass

        return f"{prefix}{max_number + 1:06d}"

    def __str__(self):
        return self.get_full_name() or self.username


class AuditLog(models.Model):
    """A simple, append-only record of security-relevant actions."""

    class Action(models.TextChoices):
        LOGIN = "login", _("Login")
        LOGOUT = "logout", _("Logout")
        CREATE = "create", _("Create")
        UPDATE = "update", _("Update")
        DELETE = "delete", _("Delete")
        PASSWORD = "password", _("Password change")

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )

    action = models.CharField(
        max_length=20,
        choices=Action.choices,
    )

    model_name = models.CharField(
        max_length=100,
        blank=True,
    )

    object_id = models.CharField(
        max_length=50,
        blank=True,
    )

    description = models.TextField(
        blank=True,
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = _("Audit log")
        verbose_name_plural = _("Audit logs")

    def __str__(self):
        return f"{self.user} - {self.action} - {self.created_at:%Y-%m-%d %H:%M}"
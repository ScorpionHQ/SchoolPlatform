from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class FeeType(models.Model):
    """A kind of fee charged to students (registration, books, transport...)."""

    institution = models.ForeignKey(
        "institutions.Institution",
        on_delete=models.CASCADE,
        related_name="fee_types",
    )

    name = models.CharField(
        max_length=100,
        verbose_name=_("Fee name"),
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Amount (IQD)"),
    )

    is_required = models.BooleanField(
        default=True,
        verbose_name=_("Required"),
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
    )

    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Sort order"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = _("Fee Type")
        verbose_name_plural = _("Fee Types")
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "name"],
                name="unique_fee_type_per_institution",
            ),
        ]

    def __str__(self):
        return self.name


class StudentFee(models.Model):
    """A fee charged to a specific student for a specific fee type/year."""

    institution = models.ForeignKey(
        "institutions.Institution",
        on_delete=models.CASCADE,
        related_name="student_fees",
    )

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="fees",
    )

    fee_type = models.ForeignKey(
        FeeType,
        on_delete=models.CASCADE,
        related_name="student_fees",
    )

    academic_year = models.CharField(
        max_length=20,
        blank=True,
        default="",
        verbose_name=_("Academic year"),
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Amount (IQD)"),
    )

    paid_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Paid"),
    )

    note = models.TextField(
        blank=True,
        verbose_name=_("Note"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = _("Student Fee")
        verbose_name_plural = _("Student Fees")
        constraints = [
            models.UniqueConstraint(
                fields=["student", "fee_type", "academic_year"],
                name="unique_student_fee_per_year",
            ),
        ]

    @property
    def remaining(self):
        return max(self.amount - self.paid_amount, 0)

    @property
    def is_fully_paid(self):
        return self.paid_amount >= self.amount

    def __str__(self):
        return f"{self.student} - {self.fee_type}"


class Payment(models.Model):

    class Method(models.TextChoices):
        CASH = "cash", _("Cash")
        CARD = "card", _("Card")
        BANK_TRANSFER = "bank_transfer", _("Bank Transfer")

    institution = models.ForeignKey(
        "institutions.Institution",
        on_delete=models.CASCADE,
        related_name="payments",
    )

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="payments",
    )

    student_fee = models.ForeignKey(
        StudentFee,
        on_delete=models.CASCADE,
        related_name="payments",
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Amount (IQD)"),
    )

    method = models.CharField(
        max_length=20,
        choices=Method.choices,
        default=Method.CASH,
        verbose_name=_("Method"),
    )

    note = models.TextField(
        blank=True,
        verbose_name=_("Note"),
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_payments",
        verbose_name=_("Recorded by"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = _("Payment")
        verbose_name_plural = _("Payments")

    def __str__(self):
        return f"{self.student} - {self.amount}"

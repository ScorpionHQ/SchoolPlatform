from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils.translation import gettext as _

from notifications.services import NotificationService

from .models import FeeType, Payment, StudentFee


class BillingError(Exception):
    pass


class BillingService:
    """Business logic for fees, charges and payments."""

    @staticmethod
    def create_fee_type(form):
        return form.save()

    @staticmethod
    def update_fee_type(form):
        return form.save()

    @staticmethod
    def delete_fee_type(fee_type):
        """Hard-delete fee types that have no charges; otherwise deactivate."""

        if fee_type.student_fees.exists():
            fee_type.is_active = False
            fee_type.save(update_fields=["is_active"])
            return False

        fee_type.delete()
        return True

    @staticmethod
    def charge_classroom(classroom, fee_type, academic_year=""):
        """Create a fee charge for every student in a classroom."""

        created = 0
        skipped = 0

        with transaction.atomic():

            for student in classroom.students.select_related(
                "user",
            ).all():

                _, was_created = StudentFee.objects.get_or_create(
                    student=student,
                    fee_type=fee_type,
                    academic_year=academic_year,
                    defaults={
                        "institution": classroom.institution,
                        "amount": fee_type.amount,
                    },
                )

                if was_created:
                    created += 1
                else:
                    skipped += 1

        return created, skipped

    @staticmethod
    def record_payment(
        student_fee,
        amount,
        *,
        method=Payment.Method.CASH,
        note="",
        user=None,
        notify=True,
    ):
        """Register a payment towards a student fee."""

        try:
            amount = Decimal(str(amount))
        except (InvalidOperation, ValueError):
            raise BillingError(_("Invalid payment amount."))

        remaining = student_fee.remaining

        if amount <= 0:
            raise BillingError(_("Payment amount must be greater than zero."))

        if amount > remaining:
            raise BillingError(
                _("Payment amount cannot exceed the remaining balance.")
            )

        with transaction.atomic():

            student_fee.paid_amount += amount
            student_fee.save(
                update_fields=["paid_amount", "updated_at"]
            )

            payment = Payment.objects.create(
                institution=student_fee.institution,
                student=student_fee.student,
                student_fee=student_fee,
                amount=amount,
                method=method,
                note=note or "",
                created_by=user,
            )

        if notify:

            student = student_fee.student

            message = _(
                "A payment of {amount} IQD was recorded for "
                "{fee_type} (remaining: {remaining})."
            ).format(
                amount=amount,
                fee_type=student_fee.fee_type.name,
                remaining=student_fee.remaining,
            )

            NotificationService.student_and_parents(
                student,
                ntype=NotificationService.Type.FINANCE,
                title=_("Payment recorded"),
                message=message,
                student_link="/billing/my-fees/",
                parent_link="/billing/my-fees/",
                email=True,
            )

        return payment

    @staticmethod
    def delete_payment(payment):
        """Reverse a payment and restore the student fee balance."""

        with transaction.atomic():

            fee = payment.student_fee

            fee.paid_amount = max(
                fee.paid_amount - payment.amount,
                0,
            )

            fee.save(
                update_fields=["paid_amount", "updated_at"]
            )

            payment.delete()

        return fee

    @staticmethod
    def delete_student_fee(student_fee):
        """Remove a charge. Refuses when payments were already recorded."""

        if student_fee.payments.exists():
            raise BillingError(
                _("Cannot delete a fee that already has payments.")
            )

        student_fee.delete()

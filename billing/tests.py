from decimal import Decimal
from io import BytesIO

import pypdf
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from classes.models import ClassRoom
from institutions.models import Institution
from institutions.tenant import SESSION_KEY
from notifications.models import Notification
from students.models import Student

from .forms import ChargeClassForm, FeeTypeForm, PaymentForm
from .models import FeeType, Payment, StudentFee
from .services import BillingError, BillingService


def _manager(username="manager", institutions=None):
    user = User.objects.create_user(
        username=username,
        password="pass12345",
        role=User.Role.MANAGER,
    )
    if institutions:
        user.institutions.add(*institutions)
    return user


def _teacher(username="teacher"):
    return User.objects.create_user(
        username=username,
        password="pass12345",
        role=User.Role.TEACHER,
    )


def _student(institution, classroom, username="student", code="S100001"):
    user = User.objects.create_user(
        username=username,
        password="pass12345",
        role=User.Role.STUDENT,
        first_name="Sami",
        last_name="Ali",
    )
    return Student.objects.create(
        user=user,
        institution=institution,
        classroom=classroom,
        student_code=code,
    )


class BillingModelTests(TestCase):

    def setUp(self):

        self.institution = Institution.objects.create(
            name="Billing School",
            short_name="BS",
        )

        self.other = Institution.objects.create(
            name="Other School",
            short_name="OS",
        )

        self.fee = FeeType.objects.create(
            institution=self.institution,
            name="Tuition",
            amount=Decimal("50000.00"),
        )

    def test_fee_type_str(self):
        self.assertEqual(str(self.fee), "Tuition")

    def test_fee_type_unique_per_institution(self):

        duplicate = FeeType(
            institution=self.institution,
            name="Tuition",
            amount=Decimal("100.00"),
        )

        with self.assertRaises(ValidationError):
            duplicate.full_clean()

        FeeType.objects.create(
            institution=self.other,
            name="Tuition",
            amount=Decimal("100.00"),
        )

        self.assertEqual(
            FeeType.objects.filter(name="Tuition").count(),
            2,
        )

    def test_student_fee_remaining_and_fully_paid(self):

        classroom = ClassRoom.objects.create(
            name="Class 1",
            institution=self.institution,
        )

        student = _student(self.institution, classroom)

        student_fee = StudentFee.objects.create(
            institution=self.institution,
            student=student,
            fee_type=self.fee,
            amount=Decimal("100.00"),
            paid_amount=Decimal("40.00"),
        )

        self.assertEqual(student_fee.remaining, Decimal("60.00"))
        self.assertFalse(student_fee.is_fully_paid)

        student_fee.paid_amount = Decimal("100.00")
        student_fee.save(update_fields=["paid_amount"])

        self.assertEqual(student_fee.remaining, Decimal("0.00"))
        self.assertTrue(student_fee.is_fully_paid)

    def test_remaining_never_negative(self):

        classroom = ClassRoom.objects.create(
            name="Class 1",
            institution=self.institution,
        )

        student = _student(self.institution, classroom)

        student_fee = StudentFee.objects.create(
            institution=self.institution,
            student=student,
            fee_type=self.fee,
            amount=Decimal("100.00"),
            paid_amount=Decimal("150.00"),
        )

        self.assertEqual(student_fee.remaining, Decimal("0.00"))

    def test_payment_str(self):

        classroom = ClassRoom.objects.create(
            name="Class 1",
            institution=self.institution,
        )

        student = _student(self.institution, classroom)

        student_fee = StudentFee.objects.create(
            institution=self.institution,
            student=student,
            fee_type=self.fee,
            amount=Decimal("100.00"),
        )

        payment = Payment.objects.create(
            institution=self.institution,
            student=student,
            student_fee=student_fee,
            amount=Decimal("50.00"),
        )

        self.assertIn("Sami", str(payment))

    def test_student_fee_unique_per_year(self):

        classroom = ClassRoom.objects.create(
            name="Class 1",
            institution=self.institution,
        )

        student = _student(self.institution, classroom)

        StudentFee.objects.create(
            institution=self.institution,
            student=student,
            fee_type=self.fee,
            amount=Decimal("100.00"),
            academic_year="2025-2026",
        )

        duplicate = StudentFee(
            institution=self.institution,
            student=student,
            fee_type=self.fee,
            amount=Decimal("100.00"),
            academic_year="2025-2026",
        )

        with self.assertRaises(ValidationError):
            duplicate.full_clean()

        StudentFee.objects.create(
            institution=self.institution,
            student=student,
            fee_type=self.fee,
            amount=Decimal("100.00"),
            academic_year="2026-2027",
        )

        self.assertEqual(student.fees.count(), 2)


class BillingServiceTests(TestCase):

    def setUp(self):

        self.institution = Institution.objects.create(
            name="Billing School",
            short_name="BS",
        )

        self.manager = _manager(
            "manager",
            institutions=[self.institution],
        )

        self.classroom = ClassRoom.objects.create(
            name="Class 1",
            institution=self.institution,
        )

        self.student = _student(
            self.institution,
            self.classroom,
            username="student1",
            code="S100001",
        )

        self.fee = FeeType.objects.create(
            institution=self.institution,
            name="Tuition",
            amount=Decimal("50000.00"),
        )

    def test_delete_fee_type_hard_delete_when_unused(self):

        deleted = BillingService.delete_fee_type(self.fee)

        self.assertTrue(deleted)
        self.assertFalse(
            FeeType.objects.filter(pk=self.fee.pk).exists()
        )

    def test_delete_fee_type_deactivates_when_used(self):

        StudentFee.objects.create(
            institution=self.institution,
            student=self.student,
            fee_type=self.fee,
            amount=self.fee.amount,
        )

        deleted = BillingService.delete_fee_type(self.fee)

        self.assertFalse(deleted)
        self.assertTrue(
            FeeType.objects.get(pk=self.fee.pk).is_active is False
        )

    def test_charge_classroom_charges_every_student(self):

        second = _student(
            self.institution,
            self.classroom,
            username="student2",
            code="S100002",
        )

        created, skipped = BillingService.charge_classroom(
            self.classroom,
            self.fee,
            "2025-2026",
        )

        self.assertEqual(created, 2)
        self.assertEqual(skipped, 0)

        self.assertEqual(
            StudentFee.objects.filter(
                student__in=[self.student, second],
            ).count(),
            2,
        )

    def test_charge_classroom_skips_existing(self):

        BillingService.charge_classroom(
            self.classroom,
            self.fee,
            "2025-2026",
        )

        created, skipped = BillingService.charge_classroom(
            self.classroom,
            self.fee,
            "2025-2026",
        )

        self.assertEqual(created, 0)
        self.assertEqual(skipped, 1)

    def test_record_payment_updates_balance_and_creates_payment(self):

        student_fee = StudentFee.objects.create(
            institution=self.institution,
            student=self.student,
            fee_type=self.fee,
            amount=self.fee.amount,
        )

        payment = BillingService.record_payment(
            student_fee,
            "10000.00",
            method=Payment.Method.CASH,
            note="first installment",
            user=self.manager,
        )

        student_fee.refresh_from_db()

        self.assertEqual(
            student_fee.paid_amount,
            Decimal("10000.00"),
        )

        self.assertEqual(payment.amount, Decimal("10000.00"))
        self.assertEqual(payment.created_by, self.manager)

        self.assertEqual(
            Notification.objects.filter(
                user=self.student.user,
                type=Notification.Type.FINANCE,
            ).count(),
            1,
        )

    def test_record_payment_rejects_zero_or_negative(self):

        student_fee = StudentFee.objects.create(
            institution=self.institution,
            student=self.student,
            fee_type=self.fee,
            amount=self.fee.amount,
        )

        with self.assertRaises(BillingError):
            BillingService.record_payment(
                student_fee,
                "0",
                user=self.manager,
            )

        with self.assertRaises(BillingError):
            BillingService.record_payment(
                student_fee,
                "-50",
                user=self.manager,
            )

        student_fee.refresh_from_db()
        self.assertEqual(student_fee.paid_amount, Decimal("0.00"))

    def test_record_payment_rejects_overpayment(self):

        student_fee = StudentFee.objects.create(
            institution=self.institution,
            student=self.student,
            fee_type=self.fee,
            amount=Decimal("100.00"),
        )

        with self.assertRaises(BillingError):

            BillingService.record_payment(
                student_fee,
                "150.00",
                user=self.manager,
            )

    def test_record_payment_rejects_invalid_amount(self):

        student_fee = StudentFee.objects.create(
            institution=self.institution,
            student=self.student,
            fee_type=self.fee,
            amount=Decimal("100.00"),
        )

        with self.assertRaises(BillingError):

            BillingService.record_payment(
                student_fee,
                "not-a-number",
                user=self.manager,
            )

    def test_delete_payment_restores_balance(self):

        student_fee = StudentFee.objects.create(
            institution=self.institution,
            student=self.student,
            fee_type=self.fee,
            amount=Decimal("100.00"),
        )

        payment = BillingService.record_payment(
            student_fee,
            "40.00",
            user=self.manager,
        )

        BillingService.delete_payment(payment)

        student_fee.refresh_from_db()

        self.assertEqual(student_fee.paid_amount, Decimal("0.00"))
        self.assertEqual(
            Payment.objects.filter(pk=payment.pk).count(),
            0,
        )

    def test_delete_student_fee_refuses_with_payments(self):

        student_fee = StudentFee.objects.create(
            institution=self.institution,
            student=self.student,
            fee_type=self.fee,
            amount=Decimal("100.00"),
        )

        BillingService.record_payment(
            student_fee,
            "10.00",
            user=self.manager,
        )

        with self.assertRaises(BillingError):
            BillingService.delete_student_fee(student_fee)

        self.assertTrue(
            StudentFee.objects.filter(pk=student_fee.pk).exists()
        )

    def test_delete_student_fee_works_without_payments(self):

        student_fee = StudentFee.objects.create(
            institution=self.institution,
            student=self.student,
            fee_type=self.fee,
            amount=Decimal("100.00"),
        )

        BillingService.delete_student_fee(student_fee)

        self.assertFalse(
            StudentFee.objects.filter(pk=student_fee.pk).exists()
        )


class BillingFormTests(TestCase):

    def setUp(self):

        self.institution = Institution.objects.create(
            name="Billing School",
            short_name="BS",
        )

        self.manager = _manager(
            "manager",
            institutions=[self.institution],
        )

        self.classroom = ClassRoom.objects.create(
            name="Class 1",
            institution=self.institution,
        )

        self.student = _student(
            self.institution,
            self.classroom,
        )

        self.fee = FeeType.objects.create(
            institution=self.institution,
            name="Tuition",
            amount=Decimal("50000.00"),
        )

    def test_fee_type_form_rejects_non_positive_amount(self):

        form = FeeTypeForm(
            {
                "name": "Books",
                "amount": "0",
                "is_required": True,
                "is_active": True,
            },
            institution=self.institution,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("amount", form.errors)

    def test_fee_type_form_assigns_institution(self):

        form = FeeTypeForm(
            {
                "name": "Books",
                "amount": "25000.00",
                "is_required": False,
                "is_active": True,
            },
            institution=self.institution,
        )

        self.assertTrue(form.is_valid())

        fee_type = form.save()

        self.assertEqual(fee_type.institution, self.institution)

    def test_charge_class_form_restricts_querysets(self):

        form = ChargeClassForm(institution=self.institution)

        self.assertIn(self.fee, form.fields["fee_type"].queryset)
        self.assertIn(
            self.classroom,
            form.fields["classroom"].queryset,
        )

    def test_charge_class_form_excludes_inactive_fees(self):

        inactive = FeeType.objects.create(
            institution=self.institution,
            name="Old Fee",
            amount=Decimal("100.00"),
            is_active=False,
        )

        form = ChargeClassForm(institution=self.institution)

        self.assertNotIn(
            inactive,
            form.fields["fee_type"].queryset,
        )

    def test_payment_form_valid(self):

        form = PaymentForm(
            {
                "amount": "5000.00",
                "method": Payment.Method.CASH,
                "note": "",
            }
        )

        self.assertTrue(form.is_valid())

    def test_payment_form_rejects_non_numeric_amount(self):

        form = PaymentForm(
            {
                "amount": "abc",
                "method": Payment.Method.CASH,
                "note": "",
            }
        )

        self.assertFalse(form.is_valid())


class BillingPermissionTests(TestCase):

    def setUp(self):

        self.institution = Institution.objects.create(
            name="Billing School",
            short_name="BS",
        )

        self.manager = _manager(
            "manager",
            institutions=[self.institution],
        )

        self.teacher = _teacher("teacher")

    def _login(self, user):

        self.client.force_login(user)

        session = self.client.session

        session[SESSION_KEY] = self.institution.pk

        session.save()

    def test_anonymous_redirected_to_login(self):

        response = self.client.get(reverse("billing:charges"))

        self.assertEqual(response.status_code, 302)

        self.assertIn(
            reverse("login"),
            response.url,
        )

    def test_teacher_forbidden_from_charges(self):

        self._login(self.teacher)

        for name in (
            "billing:charges",
            "billing:fees",
            "billing:charge_class",
            "billing:balances",
        ):

            response = self.client.get(reverse(name))

            self.assertEqual(
                response.status_code,
                403,
                msg=f"{name} should be forbidden for teachers",
            )

    def test_manager_can_access_charges(self):

        self._login(self.manager)

        response = self.client.get(reverse("billing:charges"))

        self.assertEqual(response.status_code, 200)


class BillingViewTests(TestCase):

    def setUp(self):

        self.institution = Institution.objects.create(
            name="Billing School",
            short_name="BS",
        )

        self.manager = _manager(
            "manager",
            institutions=[self.institution],
        )

        self.classroom = ClassRoom.objects.create(
            name="Class 1",
            institution=self.institution,
        )

        self.student = _student(
            self.institution,
            self.classroom,
            username="student1",
            code="S100001",
        )

        self.second_student = _student(
            self.institution,
            self.classroom,
            username="student2",
            code="S100002",
        )

        self.fee = FeeType.objects.create(
            institution=self.institution,
            name="Tuition",
            amount=Decimal("50000.00"),
        )

        self.student_fee = StudentFee.objects.create(
            institution=self.institution,
            student=self.student,
            fee_type=self.fee,
            amount=self.fee.amount,
            academic_year="2025-2026",
        )

    def _login(self):

        self.client.force_login(self.manager)

        session = self.client.session

        session[SESSION_KEY] = self.institution.pk

        session.save()

    def test_fee_type_list_shows_fee_types(self):

        self._login()

        response = self.client.get(reverse("billing:fees"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tuition")
        self.assertContains(response, "50000")

    def test_fee_type_list_create(self):

        self._login()

        response = self.client.post(
            reverse("billing:fees"),
            {
                "name": "Books",
                "amount": "25000.00",
                "is_required": False,
                "is_active": True,
            },
        )

        self.assertRedirects(
            response,
            reverse("billing:fees"),
        )

        self.assertTrue(
            FeeType.objects.filter(
                name="Books",
                institution=self.institution,
            ).exists()
        )

    def test_fee_type_toggle(self):

        self._login()

        self.assertTrue(
            FeeType.objects.get(pk=self.fee.pk).is_active
        )

        response = self.client.post(
            reverse(
                "billing:fee_toggle",
                args=[self.fee.pk],
            )
        )

        self.assertRedirects(
            response,
            reverse("billing:fees"),
        )

        self.assertFalse(
            FeeType.objects.get(pk=self.fee.pk).is_active
        )

    def test_fee_type_delete_deactivates_when_charged(self):

        self._login()

        response = self.client.post(
            reverse(
                "billing:fee_delete",
                args=[self.fee.pk],
            )
        )

        self.assertRedirects(
            response,
            reverse("billing:fees"),
        )

        self.assertTrue(
            FeeType.objects.filter(pk=self.fee.pk).exists()
        )

        self.assertFalse(
            FeeType.objects.get(pk=self.fee.pk).is_active
        )

    def test_charge_class_charges_all_students(self):

        self._login()

        response = self.client.post(
            reverse("billing:charge_class"),
            {
                "classroom": self.classroom.pk,
                "fee_type": self.fee.pk,
                "academic_year": "2026-2027",
            },
        )

        self.assertRedirects(
            response,
            reverse("billing:charges"),
        )

        self.assertEqual(
            StudentFee.objects.filter(
                student__in=[
                    self.student,
                    self.second_student,
                ],
                academic_year="2026-2027",
            ).count(),
            2,
        )

    def test_charges_list_shows_fees(self):

        self._login()

        response = self.client.get(reverse("billing:charges"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tuition")

    def test_charges_filter_by_classroom(self):

        self._login()

        other_classroom = ClassRoom.objects.create(
            name="Class 2",
            institution=self.institution,
        )

        other_student = _student(
            self.institution,
            other_classroom,
            username="student3",
            code="S100003",
        )

        StudentFee.objects.create(
            institution=self.institution,
            student=other_student,
            fee_type=self.fee,
            amount=self.fee.amount,
        )

        response = self.client.get(
            reverse("billing:charges"),
            {
                "classroom": self.classroom.pk,
            },
        )

        self.assertContains(response, "Sami Ali")
        self.assertNotContains(response, "S100003")

    def test_payment_create_success(self):

        self._login()

        response = self.client.post(
            reverse("billing:payment_create"),
            {
                "student_fee": self.student_fee.pk,
                "amount": "10000.00",
                "method": Payment.Method.CASH,
                "note": "installment",
            },
        )

        self.assertRedirects(
            response,
            reverse("billing:charges"),
        )

        self.student_fee.refresh_from_db()

        self.assertEqual(
            self.student_fee.paid_amount,
            Decimal("10000.00"),
        )

        self.assertEqual(Payment.objects.count(), 1)

    def test_payment_create_rejects_overpayment_without_500(self):

        self._login()

        response = self.client.post(
            reverse("billing:payment_create"),
            {
                "student_fee": self.student_fee.pk,
                "amount": "999999.00",
                "method": Payment.Method.CASH,
                "note": "",
            },
        )

        self.assertRedirects(
            response,
            reverse("billing:charges"),
        )

        self.student_fee.refresh_from_db()
        self.assertEqual(self.student_fee.paid_amount, Decimal("0.00"))

    def test_payment_create_missing_student_fee_does_not_crash(self):

        self._login()

        response = self.client.post(
            reverse("billing:payment_create"),
            {
                "student_fee": "",
                "amount": "100.00",
                "method": Payment.Method.CASH,
                "note": "",
            },
        )

        self.assertRedirects(
            response,
            reverse("billing:charges"),
        )

        self.assertEqual(Payment.objects.count(), 0)

    def test_payment_delete_restores_balance(self):

        self._login()

        BillingService.record_payment(
            self.student_fee,
            "5000.00",
            user=self.manager,
        )

        payment = Payment.objects.get()

        response = self.client.post(
            reverse(
                "billing:payment_delete",
                args=[payment.pk],
            )
        )

        self.assertRedirects(
            response,
            reverse("billing:charges"),
        )

        self.student_fee.refresh_from_db()
        self.assertEqual(self.student_fee.paid_amount, Decimal("0.00"))

    def test_student_fee_delete(self):

        self._login()

        response = self.client.post(
            reverse(
                "billing:student_fee_delete",
                args=[self.student_fee.pk],
            )
        )

        self.assertRedirects(
            response,
            reverse("billing:charges"),
        )

        self.assertFalse(
            StudentFee.objects.filter(pk=self.student_fee.pk).exists()
        )

    def test_student_fee_delete_refused_with_payments(self):

        self._login()

        BillingService.record_payment(
            self.student_fee,
            "100.00",
            user=self.manager,
        )

        response = self.client.post(
            reverse(
                "billing:student_fee_delete",
                args=[self.student_fee.pk],
            )
        )

        self.assertRedirects(
            response,
            reverse("billing:charges"),
        )

        self.assertTrue(
            StudentFee.objects.filter(pk=self.student_fee.pk).exists()
        )

    def test_balances_shows_totals(self):

        self._login()

        self.student_fee.paid_amount = Decimal("20000.00")
        self.student_fee.save(update_fields=["paid_amount"])

        response = self.client.get(reverse("billing:balances"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sami Ali")

    def test_receipt_renders(self):

        self._login()

        payment = BillingService.record_payment(
            self.student_fee,
            "5000.00",
            user=self.manager,
        )

        response = self.client.get(
            reverse(
                "billing:receipt",
                args=[payment.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tuition")
        self.assertContains(response, "5000")

    def test_receipt_scoped_to_institution(self):

        self._login()

        other = Institution.objects.create(
            name="Other",
            short_name="OT",
        )

        other_manager = _manager(
            "other_manager",
            institutions=[other],
        )

        payment = BillingService.record_payment(
            self.student_fee,
            "5000.00",
            user=self.manager,
        )

        self.client.force_login(other_manager)

        self.client.session[SESSION_KEY] = other.pk
        self.client.session.save()

        response = self.client.get(
            reverse(
                "billing:receipt",
                args=[payment.pk],
            )
        )

        self.assertEqual(response.status_code, 404)


class BillingMyFeesTests(TestCase):

    def setUp(self):

        self.institution = Institution.objects.create(
            name="Billing School",
            short_name="BS",
        )

        self.manager = _manager(
            "manager",
            institutions=[self.institution],
        )

        self.classroom = ClassRoom.objects.create(
            name="Class 1",
            institution=self.institution,
        )

        self.fee = FeeType.objects.create(
            institution=self.institution,
            name="Tuition",
            amount=Decimal("50000.00"),
        )

        self.student_user = User.objects.create_user(
            username="student",
            password="pass12345",
            role=User.Role.STUDENT,
            first_name="Sami",
            last_name="Ali",
        )

        self.student = Student.objects.create(
            user=self.student_user,
            institution=self.institution,
            classroom=self.classroom,
            student_code="S100001",
        )

        StudentFee.objects.create(
            institution=self.institution,
            student=self.student,
            fee_type=self.fee,
            amount=self.fee.amount,
            paid_amount=Decimal("10000.00"),
        )

    def _login(self, user, session_institution=None):

        self.client.force_login(user)

        if session_institution:

            session = self.client.session

            session[SESSION_KEY] = session_institution.pk

            session.save()

    def test_student_sees_own_fees(self):

        self._login(self.student_user)

        response = self.client.get(reverse("billing:my_fees"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tuition")
        self.assertContains(response, "10000")

    def test_manager_sees_institution_fees(self):

        self._login(self.manager, session_institution=self.institution)

        response = self.client.get(reverse("billing:my_fees"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tuition")

    def test_system_admin_gets_empty_list(self):

        admin = User.objects.create_user(
            username="sysadmin",
            password="pass12345",
            role=User.Role.SYSTEM_ADMIN,
        )

        self._login(admin)

        response = self.client.get(reverse("billing:my_fees"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Tuition")


class BillingTenantIsolationTests(TestCase):

    def setUp(self):

        self.first = Institution.objects.create(
            name="First School",
            short_name="F1",
        )

        self.second = Institution.objects.create(
            name="Second School",
            short_name="S2",
        )

        self.fee = FeeType.objects.create(
            institution=self.first,
            name="First Fee",
            amount=Decimal("100.00"),
        )

        self.other_fee = FeeType.objects.create(
            institution=self.second,
            name="Second Fee",
            amount=Decimal("200.00"),
        )

        self.manager = _manager(
            "manager",
            institutions=[self.first, self.second],
        )

    def _login_as(self, institution):

        self.client.force_login(self.manager)

        session = self.client.session

        session[SESSION_KEY] = institution.pk

        session.save()

    def test_fees_scoped_to_current_institution(self):

        self._login_as(self.first)

        response = self.client.get(reverse("billing:fees"))

        self.assertContains(response, "First Fee")
        self.assertNotContains(response, "Second Fee")

    def test_charges_scoped_to_current_institution(self):

        classroom = ClassRoom.objects.create(
            name="Class 1",
            institution=self.first,
        )

        student = _student(
            self.first,
            classroom,
            username="student1",
            code="S100001",
        )

        StudentFee.objects.create(
            institution=self.first,
            student=student,
            fee_type=self.fee,
            amount=Decimal("100.00"),
        )

        self._login_as(self.first)

        response = self.client.get(reverse("billing:charges"))

        self.assertContains(response, "First Fee")

        session = self.client.session

        session[SESSION_KEY] = self.second.pk

        session.save()

        response = self.client.get(reverse("billing:charges"))

        self.assertNotContains(response, "First Fee")


class FeePricesPdfTests(TestCase):

    def setUp(self):

        self.institution = Institution.objects.create(
            name="PDF School",
            short_name="PS",
        )

        self.manager = _manager(
            "pdfmanager",
            institutions=[self.institution],
        )

        self.teacher = _teacher("pdftch")

        self.active_fee = FeeType.objects.create(
            institution=self.institution,
            name="Registration",
            amount=Decimal("25000.00"),
            is_required=True,
        )

        FeeType.objects.create(
            institution=self.institution,
            name="Transport",
            amount=Decimal("15000.00"),
            is_required=False,
            is_active=False,
        )

    def _login(self, user):

        self.client.force_login(user)

        session = self.client.session

        session[SESSION_KEY] = self.institution.pk

        session.save()

    def test_requires_manager(self):

        self._login(self.teacher)

        response = self.client.get(reverse("billing:prices_pdf"))

        self.assertEqual(response.status_code, 403)

    def test_returns_pdf_attachment(self):

        self._login(self.manager)

        response = self.client.get(reverse("billing:prices_pdf"))

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response["Content-Type"],
            "application/pdf",
        )

        self.assertIn(
            "attachment",
            response["Content-Disposition"],
        )

        self.assertIn(
            "fee_prices_{}.pdf".format(self.institution.pk),
            response["Content-Disposition"],
        )

        content = response.content

        self.assertTrue(
            content.startswith(b"%PDF-"),
        )

    def test_pdf_includes_only_active_fees(self):

        self._login(self.manager)

        content = self.client.get(
            reverse("billing:prices_pdf")
        ).content

        reader = pypdf.PdfReader(BytesIO(content))

        text = "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )

        self.assertIn("Registration", text)

        self.assertNotIn("Transport", text)

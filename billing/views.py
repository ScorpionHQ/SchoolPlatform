from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import F, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _

from accounts.decorators import login_required, manager_required
from classes.models import ClassRoom
from students.models import Student

from .forms import ChargeClassForm, FeeTypeForm, PaymentForm
from .models import FeeType, Payment, StudentFee
from .pdf import build_fee_prices_pdf
from .services import BillingError, BillingService


def _get_institution(request):
    return getattr(request, "current_institution", None)


@manager_required
def fee_type_list(request):

    institution = _get_institution(request)

    if institution is None:
        messages.warning(request, _("Please select an institution first."))
        return redirect("institutions:select")

    if request.method == "POST":

        form = FeeTypeForm(
            request.POST,
            institution=institution,
        )

        if form.is_valid():

            BillingService.create_fee_type(form)

            messages.success(request, _("Fee type added successfully."))

            return redirect("billing:fees")

    else:

        form = FeeTypeForm(institution=institution)

    fee_types = FeeType.objects.filter(
        institution=institution,
    )

    return render(
        request,
        "billing/fee_types.html",
        {
            "form": form,
            "fee_types": fee_types,
        },
    )


@manager_required
def fee_type_toggle(request, pk):

    institution = _get_institution(request)

    fee_type = get_object_or_404(
        FeeType,
        pk=pk,
        institution=institution,
    )

    if request.method == "POST":

        fee_type.is_active = not fee_type.is_active

        fee_type.save(update_fields=["is_active"])

        messages.success(request, _("Fee type updated."))

    return redirect("billing:fees")


@manager_required
def fee_type_delete(request, pk):

    institution = _get_institution(request)

    fee_type = get_object_or_404(
        FeeType,
        pk=pk,
        institution=institution,
    )

    if request.method == "POST":

        deleted = BillingService.delete_fee_type(fee_type)

        if deleted:
            messages.success(request, _("Fee type deleted."))
        else:
            messages.warning(
                request,
                _("Fee type has charges and was deactivated instead."),
            )

    return redirect("billing:fees")


@manager_required
def fee_prices_pdf(request):

    institution = _get_institution(request)

    if institution is None:

        messages.warning(
            request,
            _("Please select an institution first."),
        )

        return redirect("institutions:select")

    fee_types = FeeType.objects.filter(
        institution=institution,
        is_active=True,
    ).order_by(
        "sort_order",
        "name",
    )

    buffer = build_fee_prices_pdf(institution, fee_types)

    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/pdf",
    )

    response["Content-Disposition"] = (
        'attachment; filename="fee_prices_{}.pdf"'.format(
            institution.pk,
        )
    )

    return response


@manager_required
def charge_class(request):

    institution = _get_institution(request)

    if institution is None:
        messages.warning(request, _("Please select an institution first."))
        return redirect("institutions:select")

    if request.method == "POST":

        form = ChargeClassForm(
            request.POST,
            institution=institution,
        )

        if form.is_valid():

            created, skipped = BillingService.charge_classroom(
                form.cleaned_data["classroom"],
                form.cleaned_data["fee_type"],
                form.cleaned_data["academic_year"],
            )

            messages.success(
                request,
                _("{created} charge(s) created, {skipped} already existed.").format(
                    created=created,
                    skipped=skipped,
                ),
            )

            return redirect("billing:charges")

    else:

        form = ChargeClassForm(institution=institution)

    return render(
        request,
        "billing/charge_form.html",
        {
            "form": form,
        },
    )


@manager_required
def charges(request):

    institution = _get_institution(request)

    fees = StudentFee.objects.none()

    if institution:

        fees = (
            StudentFee.objects.filter(
                institution=institution,
            )
            .select_related(
                "student__user",
                "fee_type",
                "student__classroom",
            )
        )

    classroom_id = request.GET.get("classroom")
    q = request.GET.get("q")

    if classroom_id:
        fees = fees.filter(student__classroom_id=classroom_id)

    if q:
        fees = fees.filter(
            student__user__first_name__icontains=q,
        )

    paginator = Paginator(fees, 15)

    fees = paginator.get_page(request.GET.get("page"))

    classrooms = (
        ClassRoom.objects.filter(institution=institution)
        if institution
        else ClassRoom.objects.none()
    )

    return render(
        request,
        "billing/charges.html",
        {
            "fees": fees,
            "classrooms": classrooms,
            "payment_form": PaymentForm(),
            "requested_classroom": classroom_id,
        },
    )


@manager_required
def student_fee_delete(request, pk):

    institution = _get_institution(request)

    fee = get_object_or_404(
        StudentFee,
        pk=pk,
        institution=institution,
    )

    if request.method == "POST":

        try:
            BillingService.delete_student_fee(fee)
            messages.success(request, _("Charge removed."))
        except BillingError as exc:
            messages.error(request, str(exc))

    return redirect("billing:charges")


@manager_required
def payment_create(request):

    institution = _get_institution(request)

    if request.method == "POST":

        fee = None

        fee_id = request.POST.get("student_fee")

        if fee_id:

            fee = StudentFee.objects.filter(
                pk=fee_id,
                institution=institution,
            ).first()

        if fee is None:

            messages.error(
                request,
                _("Please choose a valid charge to pay."),
            )

            return redirect("billing:charges")

        form = PaymentForm(request.POST)

        if form.is_valid():

            try:

                BillingService.record_payment(
                    fee,
                    form.cleaned_data["amount"],
                    method=form.cleaned_data["method"],
                    note=form.cleaned_data["note"],
                    user=request.user,
                )

                messages.success(
                    request,
                    _("Payment recorded successfully."),
                )

            except BillingError as exc:
                messages.error(request, str(exc))

        else:

            messages.error(request, _("Please check the payment details."))

    return redirect("billing:charges")


@manager_required
def payment_delete(request, pk):

    institution = _get_institution(request)

    payment = get_object_or_404(
        Payment,
        pk=pk,
        institution=institution,
    )

    if request.method == "POST":

        BillingService.delete_payment(payment)

        messages.success(request, _("Payment removed."))

    return redirect("billing:charges")


@manager_required
def balances(request):

    institution = _get_institution(request)

    students = Student.objects.none()

    if institution:

        students = (
            Student.objects.filter(
                institution=institution,
            )
            .select_related("user", "classroom")
            .annotate(
                total_due=Sum("fees__amount"),
                total_paid=Sum("fees__paid_amount"),
            )
            .annotate(
                total_remaining=F("total_due") - F("total_paid"),
            )
            .order_by("student_code")
        )

    q = request.GET.get("q")

    if q:
        students = students.filter(user__first_name__icontains=q)

    paginator = Paginator(students, 15)

    students = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "billing/balances.html",
        {
            "students": students,
        },
    )


@login_required
def my_fees(request):
    """Fees of the current student, or of the children of a parent."""

    user = request.user

    students = []

    if user.role == user.Role.STUDENT:

        profile = getattr(user, "student_profile", None)

        if profile:
            students = [profile]

    elif user.role == user.Role.PARENT:

        profile = getattr(user, "parent_profile", None)

        if profile:
            students = list(profile.students.select_related("classroom"))

    elif user.role in (user.Role.MANAGER, user.Role.ASSISTANT_MANAGER):

        institution = _get_institution(request)

        if institution:
            students = list(
                Student.objects.filter(institution=institution)
            )

    return render(
        request,
        "billing/my_fees.html",
        {
            "students": students,
        },
    )


@manager_required
def receipt(request, pk):

    institution = _get_institution(request)

    payment = get_object_or_404(
        Payment,
        pk=pk,
        institution=institution,
    )

    return render(
        request,
        "billing/receipt.html",
        {
            "payment": payment,
        },
    )

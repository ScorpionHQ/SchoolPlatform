from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _

from accounts.decorators import manager_required

from .forms import GradeForm
from .models import Grade
from .services import GradeService


def _get_institution(request):
    """Return the current institution for the request, or None."""

    return getattr(request, "current_institution", None)


@manager_required
def grade_list(request):

    institution = _get_institution(request)

    grades = Grade.objects.none()

    if institution:

        grades = Grade.objects.filter(
            student__institution=institution,
        ).select_related(
            "student",
            "subject",
            "teacher",
        )

    q = request.GET.get("q")

    if q:

        grades = grades.filter(
            student__user__first_name__icontains=q,
        )

    paginator = Paginator(
        grades,
        10,
    )

    page = request.GET.get("page")

    grades = paginator.get_page(page)

    return render(
        request,
        "grades/list.html",
        {
            "grades": grades,
        },
    )


@manager_required
def grade_create(request):

    institution = _get_institution(request)

    if institution is None:

        messages.warning(
            request,
            _("Please select an institution first."),
        )

        return redirect("institutions:select")

    if request.method == "POST":

        form = GradeForm(
            request.POST,
            institution=institution,
        )

        if form.is_valid():

            GradeService.create_grade(form)

            messages.success(
                request,
                _("Grade added successfully."),
            )

            return redirect("grades:list")

    else:

        form = GradeForm(
            institution=institution,
        )

    return render(
        request,
        "grades/grade_form.html",
        {
            "form": form,
        },
    )


@manager_required
def grade_update(request, pk):

    institution = _get_institution(request)

    grade = get_object_or_404(
        Grade,
        pk=pk,
        student__institution=institution,
    )

    if request.method == "POST":

        form = GradeForm(
            request.POST,
            instance=grade,
            institution=institution,
        )

        if form.is_valid():

            GradeService.update_grade(form)

            messages.success(
                request,
                _("Grade updated successfully."),
            )

            return redirect("grades:list")

    else:

        form = GradeForm(
            instance=grade,
            institution=institution,
        )

    return render(
        request,
        "grades/grade_form.html",
        {
            "form": form,
        },
    )


@manager_required
def grade_delete(request, pk):

    institution = _get_institution(request)

    grade = get_object_or_404(
        Grade,
        pk=pk,
        student__institution=institution,
    )

    if request.method == "POST":

        GradeService.delete_grade(
            grade,
        )

        messages.success(
            request,
            _("Grade deleted successfully."),
        )

        return redirect("grades:list")

    return render(
        request,
        "grades/grade_confirm_delete.html",
        {
            "grade": grade,
        },
    )
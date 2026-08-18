from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _

from accounts.decorators import manager_required
from classes.models import ClassRoom

from .forms import SubjectForm
from .models import Subject
from .services import SubjectService


def _get_institution(request):
    """Return the current institution for the request, or None."""

    return getattr(request, "current_institution", None)


@manager_required
def subject_list(request):

    institution = _get_institution(request)

    subjects = Subject.objects.none()
    classrooms = []

    if institution:

        classrooms = list(
            ClassRoom.objects.filter(
                institution=institution,
            ).values("id", "name", "level").order_by("name")
        )

        subjects = Subject.objects.filter(
            institution=institution,
        ).select_related(
            "institution",
            "teacher",
            "classroom",
        )

    q = request.GET.get("q", "").strip()
    classroom_id = request.GET.get("classroom")

    if q:
        subjects = subjects.filter(
            Q(name__icontains=q) | Q(code__icontains=q),
        )

    if classroom_id:
        subjects = subjects.filter(classroom__id=classroom_id)

    paginator = Paginator(subjects, 10)

    page = request.GET.get("page")

    subjects = paginator.get_page(page)

    return render(
        request,
        "subjects/list.html",
        {
            "subjects": subjects,
            "classrooms": classrooms,
            "q": q,
            "selected_classroom": classroom_id,
        },
    )


@manager_required
def subject_create(request):

    institution = _get_institution(request)

    if institution is None:

        messages.warning(
            request,
            _("Please select an institution first."),
        )

        return redirect("institutions:select")

    if request.method == "POST":

        form = SubjectForm(
            request.POST,
            institution=institution,
        )

        if form.is_valid():

            SubjectService.create_subject(form)

            messages.success(
                request,
                _("Subject created successfully."),
            )

            return redirect("subjects:list")

    else:

        form = SubjectForm(
            institution=institution,
        )

    return render(
        request,
        "subjects/subject_form.html",
        {
            "form": form,
        },
    )


@manager_required
def subject_update(request, pk):

    institution = _get_institution(request)

    subject = get_object_or_404(
        Subject,
        pk=pk,
        institution=institution,
    )

    if request.method == "POST":

        form = SubjectForm(
            request.POST,
            instance=subject,
            institution=institution,
        )

        if form.is_valid():

            SubjectService.update_subject(form)

            messages.success(
                request,
                _("Subject updated successfully."),
            )

            return redirect("subjects:list")

    else:

        form = SubjectForm(
            instance=subject,
            institution=institution,
        )

    return render(
        request,
        "subjects/subject_form.html",
        {
            "form": form,
        },
    )


@manager_required
def subject_delete(request, pk):

    institution = _get_institution(request)

    subject = get_object_or_404(
        Subject,
        pk=pk,
        institution=institution,
    )

    if request.method == "POST":

        SubjectService.delete_subject(subject)

        messages.success(
            request,
            _("Subject deleted successfully."),
        )

        return redirect("subjects:list")

    return render(
        request,
        "subjects/subject_confirm_delete.html",
        {
            "subject": subject,
        },
    )
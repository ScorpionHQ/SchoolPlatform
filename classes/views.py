from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _

from accounts.decorators import manager_required

from .forms import ClassRoomForm
from .models import ClassRoom
from .services import ClassRoomService


def _get_institution(request):
    """Return the current institution for the request, or None."""

    return getattr(request, "current_institution", None)


@manager_required
def classroom_list(request):

    institution = _get_institution(request)

    classrooms = ClassRoom.objects.none()

    if institution:

        classrooms = ClassRoom.objects.filter(
            institution=institution,
        ).select_related(
            "institution",
        )

    q = request.GET.get("q")

    if q:

        classrooms = classrooms.filter(
            name__icontains=q,
        )

    paginator = Paginator(classrooms, 10)

    page = request.GET.get("page")

    classrooms = paginator.get_page(page)

    return render(
        request,
        "classes/list.html",
        {
            "classrooms": classrooms,
        },
    )


@manager_required
def classroom_create(request):

    institution = _get_institution(request)

    if institution is None:

        messages.warning(
            request,
            _("Please select an institution first."),
        )

        return redirect("institutions:select")

    if request.method == "POST":

        form = ClassRoomForm(
            request.POST,
            institution=institution,
        )

        if form.is_valid():

            ClassRoomService.create_classroom(form)

            messages.success(
                request,
                _("Class created successfully."),
            )

            return redirect("classes:list")

    else:

        form = ClassRoomForm(
            institution=institution,
        )

    return render(
        request,
        "classes/classroom_form.html",
        {
            "form": form,
        },
    )


@manager_required
def classroom_update(request, pk):

    institution = _get_institution(request)

    classroom = get_object_or_404(
        ClassRoom,
        pk=pk,
        institution=institution,
    )

    if request.method == "POST":

        form = ClassRoomForm(
            request.POST,
            instance=classroom,
            institution=institution,
        )

        if form.is_valid():

            ClassRoomService.update_classroom(form)

            messages.success(
                request,
                _("Class updated successfully."),
            )

            return redirect("classes:list")

    else:

        form = ClassRoomForm(
            instance=classroom,
            institution=institution,
        )

    return render(
        request,
        "classes/classroom_form.html",
        {
            "form": form,
        },
    )


@manager_required
def classroom_delete(request, pk):

    institution = _get_institution(request)

    classroom = get_object_or_404(
        ClassRoom,
        pk=pk,
        institution=institution,
    )

    if request.method == "POST":

        ClassRoomService.delete_classroom(
            classroom,
        )

        messages.success(
            request,
            _("Class deleted successfully."),
        )

        return redirect("classes:list")

    return render(
        request,
        "classes/classroom_confirm_delete.html",
        {
            "classroom": classroom,
        },
    )
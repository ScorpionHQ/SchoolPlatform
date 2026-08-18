from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _

from accounts.decorators import manager_required
from classes.models import ClassRoom

from .forms import ParentForm
from .models import Parent
from .services import ParentService


def _get_institution(request):
    """Return the current institution for the request, or None."""

    return getattr(request, "current_institution", None)


@manager_required
def parent_list(request):

    institution = _get_institution(request)

    parents = Parent.objects.none()
    classrooms = []

    if institution:

        classrooms = list(
            ClassRoom.objects.filter(
                institution=institution,
            ).values("id", "name", "level").order_by("name")
        )

        parents = Parent.objects.filter(
            students__institution=institution,
        ).distinct().select_related(
            "user",
        ).prefetch_related(
            "students",
        )

    q = request.GET.get("q", "").strip()
    classroom_id = request.GET.get("classroom")

    if q:
        parents = parents.filter(
            Q(user__first_name__icontains=q)
            | Q(user__last_name__icontains=q),
        )

    if classroom_id:
        parents = parents.filter(
            students__classroom__id=classroom_id,
        ).distinct()

    paginator = Paginator(
        parents,
        10,
    )

    page = request.GET.get("page")

    parents = paginator.get_page(page)

    return render(
        request,
        "parents/list.html",
        {
            "parents": parents,
            "classrooms": classrooms,
            "q": q,
            "selected_classroom": classroom_id,
        },
    )


@manager_required
def parent_create(request):

    institution = _get_institution(request)

    if institution is None:

        messages.warning(
            request,
            _("Please select an institution first."),
        )

        return redirect("institutions:select")

    if request.method == "POST":

        form = ParentForm(
            request.POST,
            institution=institution,
        )

        if form.is_valid():

            try:

                ParentService.create_parent(
                    username=form.cleaned_data["username"],
                    password=form.cleaned_data["password"],
                    first_name=form.cleaned_data["first_name"],
                    last_name=form.cleaned_data["last_name"],
                    relationship=form.cleaned_data["relationship"],
                    students=form.cleaned_data["students"],
                )

                messages.success(
                    request,
                    _("Parent created successfully."),
                )

                return redirect("parents:list")

            except ValidationError as e:

                form.add_error(
                    None,
                    e,
                )

    else:

        form = ParentForm(
            institution=institution,
        )

    return render(
        request,
        "parents/parent_form.html",
        {
            "form": form,
        },
    )


@manager_required
def parent_update(request, pk):

    institution = _get_institution(request)

    parent = get_object_or_404(
        Parent.objects.select_related("user"),
        pk=pk,
        students__institution=institution,
    )

    if request.method == "POST":

        form = ParentForm(
            request.POST,
            is_update=True,
            institution=institution,
        )

        if form.is_valid():

            try:

                ParentService.update_parent(
                    parent=parent,
                    username=form.cleaned_data["username"],
                    password=form.cleaned_data["password"],
                    first_name=form.cleaned_data["first_name"],
                    last_name=form.cleaned_data["last_name"],
                    relationship=form.cleaned_data["relationship"],
                    students=form.cleaned_data["students"],
                )

                messages.success(
                    request,
                    _("Parent updated successfully."),
                )

                return redirect("parents:list")

            except ValidationError as e:

                form.add_error(
                    None,
                    e,
                )

    else:

        form = ParentForm(
            initial={
                "parent_id": parent.id,
                "username": parent.user.username,
                "first_name": parent.user.first_name,
                "last_name": parent.user.last_name,
                "relationship": parent.relationship,
                "students": parent.students.all(),
            },
            is_update=True,
            institution=institution,
        )

    return render(
        request,
        "parents/parent_form.html",
        {
            "form": form,
        },
    )


@manager_required
def parent_delete(request, pk):

    institution = _get_institution(request)

    parent = get_object_or_404(
        Parent.objects.select_related("user"),
        pk=pk,
        students__institution=institution,
    )

    if request.method == "POST":

        ParentService.delete_parent(
            parent,
        )

        messages.success(
            request,
            _("Parent deleted successfully."),
        )

        return redirect(
            "parents:list",
        )

    return render(
        request,
        "parents/parent_confirm_delete.html",
        {
            "parent": parent,
        },
    )

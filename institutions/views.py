from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from accounts.decorators import role_required
from accounts.models import User

from .forms import InstitutionForm
from .models import Institution
from .services import InstitutionService
from .tenant import SESSION_KEY, institutions_for_user


@role_required(User.Role.SYSTEM_ADMIN)
def institution_list(request):

    institutions = Institution.objects.all()

    q = request.GET.get("q")
    status = request.GET.get("status")

    if q:
        institutions = institutions.filter(name__icontains=q)

    if status == "active":
        institutions = institutions.filter(is_active=True)

    elif status == "inactive":
        institutions = institutions.filter(is_active=False)

    total_institutions = Institution.objects.count()
    active_institutions = Institution.objects.filter(is_active=True).count()
    inactive_institutions = Institution.objects.filter(is_active=False).count()

    paginator = Paginator(institutions, 10)

    page_number = request.GET.get("page")

    institutions = paginator.get_page(page_number)

    context = {
        "institutions": institutions,
        "total_institutions": total_institutions,
        "active_institutions": active_institutions,
        "inactive_institutions": inactive_institutions,
    }

    return render(
        request,
        "institutions/list.html",
        context,
    )


@role_required(User.Role.SYSTEM_ADMIN)
def institution_create(request):

    if request.method == "POST":

        form = InstitutionForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():

            InstitutionService.create_institution(form)

            messages.success(
                request,
                _("Institution created successfully."),
            )

            return redirect("institutions:list")

    else:

        form = InstitutionForm()

    return render(
        request,
        "institutions/institution_form.html",
        {
            "form": form,
        },
    )


@role_required(User.Role.SYSTEM_ADMIN)
def institution_update(request, pk):

    institution = get_object_or_404(
        Institution,
        pk=pk,
    )

    if request.method == "POST":

        form = InstitutionForm(
            request.POST,
            request.FILES,
            instance=institution,
        )

        if form.is_valid():

            InstitutionService.update_institution(form)

            messages.success(
                request,
                _("Institution updated successfully."),
            )

            return redirect("institutions:list")

    else:

        form = InstitutionForm(
            instance=institution,
        )

    return render(
        request,
        "institutions/institution_form.html",
        {
            "form": form,
        },
    )


@role_required(User.Role.SYSTEM_ADMIN)
def institution_delete(request, pk):

    institution = get_object_or_404(
        Institution,
        pk=pk,
    )

    if request.method == "POST":

        institution.delete()

        messages.success(
            request,
            _("Institution deleted successfully."),
        )

        return redirect("institutions:list")

    return render(
        request,
        "institutions/confirm_delete.html",
        {
            "institution": institution,
        },
    )


@role_required(
    User.Role.SYSTEM_ADMIN,
    User.Role.MANAGER,
    User.Role.ASSISTANT_MANAGER,
)
def institution_select(request):

    institutions = institutions_for_user(request.user)

    return render(
        request,
        "institutions/select.html",
        {
            "institutions": institutions,
        },
    )


@role_required(
    User.Role.SYSTEM_ADMIN,
    User.Role.MANAGER,
    User.Role.ASSISTANT_MANAGER,
)
def institution_switch(request):

    if request.method == "POST":

        institution_id = request.POST.get(
            "institution_id",
        )

        available = institutions_for_user(request.user)

        institution = None

        if institution_id:

            institution = available.filter(
                pk=institution_id,
            ).first()

        if institution:

            request.session[SESSION_KEY] = institution.pk

            messages.success(
                request,
                _("Switched to {name}.").format(
                    name=institution.name,
                ),
            )

        else:

            messages.error(
                request,
                _("Invalid institution."),
            )

        next_url = request.POST.get(
            "next",
        ) or reverse("dashboard")

        if next_url.startswith(("//", "http://", "https://")):
            next_url = reverse("dashboard")

        return redirect(next_url)

    return redirect("dashboard")

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from accounts.decorators import role_required
from accounts.models import User
from institutions.models import Institution
from parents.models import Parent
from students.models import Student

try:
    from teachers.models import Teacher
except ImportError:
    Teacher = None

from .forms import UserAdminForm


@role_required(User.Role.SYSTEM_ADMIN)
def dashboard(request):

    users = User.objects.all()

    students = Student.objects
    parents = Parent.objects
    teachers = Teacher.objects if Teacher else Student.objects.none()

    role_data = [
        {
            "value": role.value,
            "label": role.label,
            "count": users.filter(role=role).count(),
        }
        for role in User.Role
    ]

    context = {
        "total_users": users.count(),
        "active_users": users.filter(is_active=True).count(),
        "inactive_users": users.filter(is_active=False).count(),
        "institution_count": Institution.objects.count(),
        "active_institutions": Institution.objects.filter(
            is_active=True,
        ).count(),
        "inactive_institutions": Institution.objects.filter(
            is_active=False,
        ).count(),
        "student_count": students.count(),
        "teacher_count": teachers.count(),
        "parent_count": parents.count(),
        "role_data": role_data,
        "recent_users": users.order_by("-date_joined")[:8],
        "recent_institutions": (
            Institution.objects.order_by("-created_at")[:5]
        ),
    }

    return render(
        request,
        "administration/dashboard.html",
        context,
    )


@role_required(User.Role.SYSTEM_ADMIN)
def user_list(request):

    users = User.objects.all().order_by("-date_joined")

    q = request.GET.get("q")
    role = request.GET.get("role")
    status = request.GET.get("status")

    if q:

        users = users.filter(
            Q(username__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(login_code__icontains=q)
        )

    if role and role in User.Role.values:
        users = users.filter(role=role)

    if status == "active":
        users = users.filter(is_active=True)

    elif status == "inactive":
        users = users.filter(is_active=False)

    total_users = User.objects.count()

    role_counts = {
        role.value: User.objects.filter(role=role).count()
        for role in User.Role
    }

    paginator = Paginator(users, 20)

    page_number = request.GET.get("page")

    users = paginator.get_page(page_number)

    context = {
        "users": users,
        "total_users": total_users,
        "role_counts": role_counts,
        "roles": User.Role.choices,
        "active_filter": status,
        "role_filter": role,
        "q": q,
    }

    return render(
        request,
        "administration/user_list.html",
        context,
    )


@role_required(User.Role.SYSTEM_ADMIN)
def user_create(request):

    if request.method == "POST":

        form = UserAdminForm(request.POST)

        if form.is_valid():

            user = form.save()

            messages.success(
                request,
                _("User {name} created successfully.").format(
                    name=user.get_full_name() or user.username,
                ),
            )

            return redirect(
                reverse(
                    "administration:user_update",
                    kwargs={"pk": user.pk},
                )
            )

    else:

        form = UserAdminForm()

    return render(
        request,
        "administration/user_form.html",
        {
            "form": form,
            "title": _("Create User"),
        },
    )


@role_required(User.Role.SYSTEM_ADMIN)
def user_update(request, pk):

    user = get_object_or_404(
        User,
        pk=pk,
    )

    if request.method == "POST":

        form = UserAdminForm(
            request.POST,
            instance=user,
        )

        if form.is_valid():

            user = form.save()

            messages.success(
                request,
                _("User {name} updated successfully.").format(
                    name=user.get_full_name() or user.username,
                ),
            )

            return redirect(
                reverse(
                    "administration:user_update",
                    kwargs={"pk": user.pk},
                )
            )

    else:

        form = UserAdminForm(instance=user)

    return render(
        request,
        "administration/user_form.html",
        {
            "form": form,
            "user": user,
            "title": _("Edit User"),
        },
    )


@role_required(User.Role.SYSTEM_ADMIN)
def user_delete(request, pk):

    user = get_object_or_404(
        User,
        pk=pk,
    )

    if request.method == "POST":

        display_name = user.get_full_name() or user.username

        user.delete()

        messages.success(
            request,
            _("User {name} deleted successfully.").format(
                name=display_name,
            ),
        )

        return redirect("administration:user_list")

    return render(
        request,
        "administration/confirm_delete.html",
        {
            "user": user,
            "cancel_url": reverse(
                "administration:user_update",
                kwargs={"pk": user.pk},
            ),
        },
    )

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from parents.models import Parent
from students.models import Student
from teachers.models import Teacher

from institutions.tenant import institutions_for_user

from .forms import PasswordChangeForm
from .models import User


def login_view(request):

    if request.method == "POST":

        login_code = request.POST.get(
            "login_code",
            "",
        ).strip()

        password = request.POST.get(
            "password",
            "",
        )

        try:

            user = User.objects.get(
                login_code=login_code,
            )

        except User.DoesNotExist:

            messages.error(
                request,
                _("Invalid login code or password."),
            )

            return render(
                request,
                "accounts/login.html",
            )

        authenticated_user = authenticate(
            request,
            username=user.username,
            password=password,
        )

        if authenticated_user is None:

            messages.error(
                request,
                _("Invalid login code or password."),
            )

            return render(
                request,
                "accounts/login.html",
            )

        login(
            request,
            authenticated_user,
        )

        if authenticated_user.must_change_password:

            messages.warning(
                request,
                _("You must change your password before continuing."),
            )

            return redirect("change_password")

        if authenticated_user.role == User.Role.SYSTEM_ADMIN:
            return redirect("dashboard")

        if authenticated_user.role in [
            User.Role.MANAGER,
            User.Role.ASSISTANT_MANAGER,
        ]:

            institution_count = institutions_for_user(
                authenticated_user,
            ).count()

            if institution_count > 1:
                return redirect("institutions:select")

            if institution_count == 0:

                messages.warning(
                    request,
                    _(
                        "No institution is assigned to your account yet. "
                        "Please contact the system administrator."
                    ),
                )

            return redirect("dashboard")

        elif authenticated_user.role == User.Role.TEACHER:
            return redirect("teachers:dashboard")

        elif authenticated_user.role == User.Role.STUDENT:
            return redirect("student_dashboard")

        elif authenticated_user.role == User.Role.PARENT:
            return redirect("parent_dashboard")

        return redirect("dashboard")

    return render(
        request,
        "accounts/login.html",
    )


@login_required
def profile_view(request):

    profile = None

    if request.user.role == User.Role.STUDENT:

        profile = Student.objects.select_related(
            "classroom",
            "institution",
        ).filter(
            user=request.user,
        ).first()

    elif request.user.role == User.Role.PARENT:

        profile = Parent.objects.filter(
            user=request.user,
        ).first()

    elif request.user.role == User.Role.TEACHER:

        profile = Teacher.objects.select_related(
            "institution",
        ).filter(
            user=request.user,
        ).first()

    return render(
        request,
        "accounts/profile.html",
        {
            "profile": profile,
        },
    )


@login_required
def change_password_view(request):

    form = PasswordChangeForm(
        user=request.user,
        data=request.POST or None,
    )

    if request.method == "POST":

        if form.is_valid():

            request.user.set_password(
                form.cleaned_data["new_password"],
            )

            request.user.must_change_password = False

            request.user.save()

            login(
                request,
                request.user,
            )

            messages.success(
                request,
                _("Your password has been changed successfully."),
            )

            return redirect("dashboard")

    return render(
        request,
        "accounts/change_password.html",
        {
            "form": form,
        },
    )


@login_required
@require_POST
def logout_view(request):

    logout(request)

    return redirect("login")


@login_required
def upload_profile_photo(request):

    if request.method == "POST" and request.FILES.get("profile_image"):

        image = request.FILES["profile_image"]

        if image.size > 5 * 1024 * 1024:

            messages.error(
                request,
                _("Image must be less than 5 MB."),
            )

            return render(request, "accounts/upload_photo.html")

        request.user.profile_image = image
        request.user.save(update_fields=["profile_image"])

        messages.success(
            request,
            _("Profile photo uploaded successfully."),
        )

        next_url = request.GET.get("next")

        if next_url:

            return redirect(next_url)

        if request.user.role == User.Role.TEACHER:

            return redirect("teachers:dashboard")

        if request.user.role == User.Role.PARENT:

            return redirect("parent_dashboard")

        return redirect("student_dashboard")

    return render(request, "accounts/upload_photo.html")

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import resolve
from django.utils.translation import gettext_lazy as _


class ForcePasswordChangeMiddleware:

    ALLOWED_URL_NAMES = {
        "change_password",
        "logout",
        "login",
    }

    ALLOWED_PATH_PREFIXES = (
        "/static/",
        "/media/",
        "/i18n/",
        "/admin/",
    )

    def __init__(self, get_response):

        self.get_response = get_response

    def __call__(self, request):

        user = request.user

        if user.is_authenticated and user.must_change_password:

            resolved = None

            try:
                resolved = resolve(request.path)
            except Exception:
                pass

            url_name = resolved.url_name if resolved else None

            is_allowed = (
                url_name in self.ALLOWED_URL_NAMES
                or request.path.startswith(self.ALLOWED_PATH_PREFIXES)
            )

            if not is_allowed:

                return redirect("change_password")

        return self.get_response(request)


class RequireRoleProfileMiddleware:
    """Send users whose role profile is missing to a helpful page.

    Creating a user from the administration panel creates only the login
    account. A student/teacher account also needs its ``Student``/``Teacher``
    record, and a parent needs a ``Parent`` record. Without this check those
    users hit a 500/404 on their dashboard with no explanation.
    """

    ALLOWED_URL_NAMES = {
        "profile",
        "change_password",
        "logout",
        "login",
    }

    ALLOWED_PATH_PREFIXES = (
        "/static/",
        "/media/",
        "/i18n/",
        "/admin/",
    )

    def __init__(self, get_response):

        self.get_response = get_response

    def __call__(self, request):

        user = request.user

        if (
            user.is_authenticated
            and self._wants_html(request)
            and self._profile_is_missing(user)
        ):

            resolved = None

            try:
                resolved = resolve(request.path)
            except Exception:
                pass

            url_name = resolved.url_name if resolved else None

            is_allowed = (
                url_name in self.ALLOWED_URL_NAMES
                or request.path.startswith(self.ALLOWED_PATH_PREFIXES)
            )

            if not is_allowed:

                messages.warning(
                    request,
                    _(
                        "Your account is not linked to a school profile yet. "
                        "Please contact the administration."
                    ),
                )

                return redirect("profile")

        return self.get_response(request)

    @staticmethod
    def _profile_is_missing(user):
        """True only for the roles that require a school profile."""

        from parents.models import Parent
        from students.models import Student
        from teachers.models import Teacher

        if user.role == "student":
            return not Student.objects.filter(user=user).exists()

        if user.role == "teacher":
            return not Teacher.objects.filter(user=user).exists()

        if user.role == "parent":
            return not Parent.objects.filter(user=user).exists()

        return False

    @staticmethod
    def _wants_html(request):
        """Do not intercept JSON, AJAX or API clients."""

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return False

        accept = request.headers.get("accept", "")

        return "text/html" in accept


class ForceProfilePhotoMiddleware:
    """Gently remind students and teachers to add a profile photo.

    The photo is optional: this middleware never blocks a request. Blocking
    used to redirect JSON/API responses and every page, and uploads may live
    on storage that is reset when the server restarts.
    """

    REMINDER_SESSION_KEY = "profile_photo_reminder_shown"

    REMINDER_ROLES = ("student", "teacher")

    def __init__(self, get_response):

        self.get_response = get_response

    def __call__(self, request):

        user = request.user

        if (
            request.method == "GET"
            and user.is_authenticated
            and user.role in self.REMINDER_ROLES
            and not user.profile_image
            and not request.session.get(self.REMINDER_SESSION_KEY)
            and self._wants_html(request)
        ):

            messages.info(
                request,
                _(
                    "Add a profile photo so teachers and classmates "
                    "can recognize you."
                ),
            )

            request.session[self.REMINDER_SESSION_KEY] = True

        return self.get_response(request)

    @staticmethod
    def _wants_html(request):
        """Do not touch JSON, AJAX or API clients."""

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return False

        accept = request.headers.get("accept", "")

        return "text/html" in accept

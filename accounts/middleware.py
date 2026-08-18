from django.shortcuts import redirect
from django.urls import resolve, reverse


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


class ForceProfilePhotoMiddleware:

    ALLOWED_URL_NAMES = {
        "upload_photo",
        "logout",
        "login",
        "change_password",
    }

    ALLOWED_PATH_PREFIXES = (
        "/static/",
        "/media/",
        "/i18n/",
        "/admin/",
    )

    FORCED_ROLES = ("student", "teacher")

    def __init__(self, get_response):

        self.get_response = get_response

    def __call__(self, request):

        user = request.user

        if (
            user.is_authenticated
            and user.role in self.FORCED_ROLES
            and not user.profile_image
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

                response = self.get_response(request)

                if response.status_code == 200:

                    return redirect(
                        f"{reverse('upload_photo')}?next={request.path}"
                    )

                return response

        return self.get_response(request)

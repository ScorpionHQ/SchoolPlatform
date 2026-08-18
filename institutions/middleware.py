from institutions.models import Institution

from .tenant import resolve_institution


class TenantMiddleware:
    """Attach the current institution to every authenticated request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        user = request.user

        if user.is_authenticated:

            available, institution = resolve_institution(
                user,
                request.session,
            )

            request.user_institutions = available
            request.current_institution = institution

        else:

            request.user_institutions = Institution.objects.none()
            request.current_institution = None

        return self.get_response(request)

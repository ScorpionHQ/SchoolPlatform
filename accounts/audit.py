"""Helpers for writing audit-log entries from views."""

from .models import AuditLog


def client_ip(request):
    """Return the real client IP, taking Render's proxy header into account."""

    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")

    if forwarded:
        return forwarded.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR", "")


def log_action(
    request,
    action,
    *,
    obj=None,
    model_name="",
    object_id="",
    description="",
    user=None,
):
    """Record one audit entry.

    ``request`` is used to find the acting user and IP. Pass ``user``
    explicitly for actions where the subject is not the logged-in user
    (for example a password reset link).
    """

    if user is None:

        candidate = getattr(request, "user", None)

        if candidate is not None and getattr(
            candidate,
            "is_authenticated",
            False,
        ):
            user = candidate

    if obj is not None and not model_name:
        model_name = obj.__class__.__name__

    object_id = object_id or (
        "" if obj is None else str(getattr(obj, "pk", "") or "")
    )

    return AuditLog.objects.create(
        user=user,
        action=action,
        model_name=model_name[:100],
        object_id=object_id[:50],
        description=(description or "")[:2000],
        ip_address=client_ip(request) or None,
    )

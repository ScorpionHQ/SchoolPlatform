def notifications_context(request):
    """Provide the unread notifications count for the navbar badge."""

    user = getattr(request, "user", None)

    unread_count = 0

    if user is not None and user.is_authenticated:

        unread_count = user.notifications.filter(
            is_read=False,
        ).count()

    return {
        "unread_notifications_count": unread_count,
    }

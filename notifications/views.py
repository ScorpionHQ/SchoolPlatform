from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _

from .models import Notification


@login_required
def notification_list(request):

    notifications = request.user.notifications.all()

    paginator = Paginator(notifications, 20)

    page_number = request.GET.get("page")

    notifications = paginator.get_page(page_number)

    return render(
        request,
        "notifications/list.html",
        {
            "notifications": notifications,
        },
    )


@login_required
def notification_mark_read(request, pk):

    notification = get_object_or_404(
        Notification,
        pk=pk,
        user=request.user,
    )

    if request.method == "POST":

        notification.is_read = True

        notification.save(update_fields=["is_read"])

        if notification.link:

            return redirect(notification.link)

    return redirect("notifications:list")


@login_required
def notification_mark_all_read(request):

    if request.method == "POST":

        request.user.notifications.filter(
            is_read=False,
        ).update(is_read=True)

        messages.success(
            request,
            _("All notifications marked as read."),
        )

    return redirect("notifications:list")


@login_required
def notification_unread_count(request):

    count = request.user.notifications.filter(
        is_read=False,
    ).count()

    return JsonResponse(
        {
            "count": count,
        }
    )

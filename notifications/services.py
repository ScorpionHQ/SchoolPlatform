from django.conf import settings

from accounts.models import User

from .models import Notification

MANAGER_ROLES = (
    User.Role.MANAGER,
    User.Role.ASSISTANT_MANAGER,
)


class NotificationService:
    """Create in-app notifications for platform users."""

    Type = Notification.Type

    @staticmethod
    def send_email_delivery(user, title, message):
        """Deliver an optional email copy of a notification.

        Controlled by the ``NOTIFICATIONS_EMAIL_ENABLED`` setting so that
        deployments without SMTP are never broken by this call.
        """

        if not getattr(settings, "NOTIFICATIONS_EMAIL_ENABLED", False):
            return

        email = (getattr(user, "email", "") or "").strip()

        if not email:
            return

        try:

            from django.core.mail import send_mail

            send_mail(
                subject=title,
                message=message,
                from_email=None,
                recipient_list=[email],
                fail_silently=True,
            )

        except Exception:
            pass

    @staticmethod
    def notify_users(
        users,
        *,
        ntype,
        title,
        message="",
        link="",
        email=False,
    ):
        """Create one notification for every given user.

        ``users`` may be a queryset, list or any iterable of users.
        """

        created = []

        for user in users:

            if user is None:
                continue

            created.append(
                Notification.objects.create(
                    user=user,
                    type=ntype,
                    title=title,
                    message=message or "",
                    link=link or "",
                )
            )

            if email:
                NotificationService.send_email_delivery(
                    user,
                    title,
                    message or title,
                )

        return created

    @staticmethod
    def notify_user(
        user,
        *,
        ntype,
        title,
        message="",
        link="",
        email=False,
    ):

        return NotificationService.notify_users(
            [user],
            ntype=ntype,
            title=title,
            message=message,
            link=link,
            email=email,
        )

    @staticmethod
    def institution_managers(institution):
        """Managers and assistant managers linked to an institution."""

        return User.objects.filter(
            institutions=institution,
            role__in=MANAGER_ROLES,
        )

    @staticmethod
    def system_admins():

        return User.objects.filter(
            role=User.Role.SYSTEM_ADMIN,
        )

    @staticmethod
    def notify_institution_managers(
        institution,
        *,
        ntype,
        title,
        message="",
        link="",
    ):

        return NotificationService.notify_users(
            NotificationService.institution_managers(institution),
            ntype=ntype,
            title=title,
            message=message,
            link=link,
        )

    @staticmethod
    def notify_system_admins(
        *,
        ntype,
        title,
        message="",
        link="",
    ):

        return NotificationService.notify_users(
            NotificationService.system_admins(),
            ntype=ntype,
            title=title,
            message=message,
            link=link,
        )

    @staticmethod
    def student_and_parents(
        student,
        *,
        ntype,
        title,
        message="",
        student_link="",
        parent_link="",
        email=False,
    ):
        """Notify a student and all their linked parents.

        The student and each parent may receive a different link.
        """

        created = []

        if student is None:
            return created

        if student.user_id:

            created += NotificationService.notify_users(
                [student.user],
                ntype=ntype,
                title=title,
                message=message,
                link=student_link or parent_link,
                email=email,
            )

        for parent in student.parents.select_related("user"):

            created += NotificationService.notify_users(
                [parent.user],
                ntype=ntype,
                title=title,
                message=message,
                link=parent_link or student_link,
                email=email,
            )

        return created

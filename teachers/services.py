from django.db import transaction
from django.utils.translation import gettext as _

from notifications.services import NotificationService

from .models import Teacher


class TeacherService:

    @staticmethod
    @transaction.atomic
    def create_teacher(form):

        teacher = form.save()

        NotificationService.notify_institution_managers(
            teacher.institution,
            ntype=NotificationService.Type.TEACHER,
            title=_("New teacher added"),
            message=_(
                "Teacher {name} has been added to {institution}."
            ).format(
                name=teacher.user.get_full_name() or teacher.user.username,
                institution=teacher.institution.name,
            ),
            link=f"/teachers/{teacher.pk}/edit/",
        )

        NotificationService.notify_user(
            teacher.user,
            ntype=NotificationService.Type.TEACHER,
            title=_("Welcome!"),
            message=_(
                "Your teacher account has been created at {institution}."
            ).format(
                institution=teacher.institution.name,
            ),
            link="/teachers/dashboard/",
        )

        return teacher

    @staticmethod
    @transaction.atomic
    def update_teacher(form):

        teacher = form.save()

        NotificationService.notify_institution_managers(
            teacher.institution,
            ntype=NotificationService.Type.TEACHER,
            title=_("Teacher updated"),
            message=_(
                "The data of teacher {name} has been updated."
            ).format(
                name=teacher.user.get_full_name() or teacher.user.username,
            ),
            link=f"/teachers/{teacher.pk}/edit/",
        )

        NotificationService.notify_user(
            teacher.user,
            ntype=NotificationService.Type.TEACHER,
            title=_("Profile updated"),
            message=_("Your teacher data has been updated."),
            link="/teachers/dashboard/",
        )

        return teacher

    @staticmethod
    @transaction.atomic
    def delete_teacher(teacher):

        institution = teacher.institution

        teacher_name = (
            teacher.user.get_full_name()
            or teacher.user.username
        )

        teacher.delete()

        NotificationService.notify_institution_managers(
            institution,
            ntype=NotificationService.Type.TEACHER,
            title=_("Teacher deleted"),
            message=_(
                "Teacher {name} has been removed."
            ).format(
                name=teacher_name,
            ),
            link="/teachers/",
        )
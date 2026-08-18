from django.db import transaction
from django.utils.translation import gettext as _

from notifications.services import NotificationService

from .models import ClassRoom


class ClassRoomService:

    @staticmethod
    @transaction.atomic
    def create_classroom(form):

        classroom = form.save()

        NotificationService.notify_institution_managers(
            classroom.institution,
            ntype=NotificationService.Type.CLASS,
            title=_("New class added"),
            message=_(
                "Class {name} has been added to {institution}."
            ).format(
                name=classroom.name,
                institution=classroom.institution.name,
            ),
            link=f"/classes/{classroom.pk}/edit/",
        )

        return classroom

    @staticmethod
    @transaction.atomic
    def update_classroom(form):

        classroom = form.save()

        NotificationService.notify_institution_managers(
            classroom.institution,
            ntype=NotificationService.Type.CLASS,
            title=_("Class updated"),
            message=_(
                "The data of class {name} has been updated."
            ).format(
                name=classroom.name,
            ),
            link=f"/classes/{classroom.pk}/edit/",
        )

        return classroom

    @staticmethod
    @transaction.atomic
    def delete_classroom(classroom):

        institution = classroom.institution

        classroom_name = classroom.name

        classroom.delete()

        NotificationService.notify_institution_managers(
            institution,
            ntype=NotificationService.Type.CLASS,
            title=_("Class deleted"),
            message=_(
                "Class {name} has been removed."
            ).format(
                name=classroom_name,
            ),
            link="/classes/",
        )
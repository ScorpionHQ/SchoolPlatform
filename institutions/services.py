from django.db import transaction
from django.utils.translation import gettext as _

from notifications.services import NotificationService

from .models import Institution


class InstitutionService:

    @staticmethod
    @transaction.atomic
    def create_institution(form):

        institution = form.save()

        NotificationService.notify_system_admins(
            ntype=NotificationService.Type.INSTITUTION,
            title=_("New institution added"),
            message=_(
                "Institution {name} has been created."
            ).format(
                name=institution.name,
            ),
            link=f"/institutions/{institution.pk}/edit/",
        )

        NotificationService.notify_institution_managers(
            institution,
            ntype=NotificationService.Type.INSTITUTION,
            title=_("New institution assigned"),
            message=_(
                "You have been assigned to institution {name}."
            ).format(
                name=institution.name,
            ),
            link="/institutions/select/",
        )

        return institution

    @staticmethod
    @transaction.atomic
    def update_institution(form):

        institution = form.save()

        NotificationService.notify_system_admins(
            ntype=NotificationService.Type.INSTITUTION,
            title=_("Institution updated"),
            message=_(
                "Institution {name} data has been updated."
            ).format(
                name=institution.name,
            ),
            link=f"/institutions/{institution.pk}/edit/",
        )

        NotificationService.notify_institution_managers(
            institution,
            ntype=NotificationService.Type.INSTITUTION,
            title=_("Institution updated"),
            message=_(
                "Institution {name} data has been updated."
            ).format(
                name=institution.name,
            ),
            link="/institutions/select/",
        )

        return institution
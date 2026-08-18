from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext as _

from accounts.models import User
from notifications.services import NotificationService
from .models import Parent


class ParentService:

    @staticmethod
    @transaction.atomic
    def create_parent(
        *,
        username,
        password,
        first_name,
        last_name,
        relationship,
        students,
    ):

        if User.objects.filter(username=username).exists():
            raise ValidationError(
                _("Username already exists.")
            )

        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=User.Role.PARENT,
        )

        parent = Parent.objects.create(
            user=user,
            relationship=relationship,
        )

        parent.students.set(students)

        institutions = set(
            student.institution
            for student in students
            if student.institution_id
        )

        parent_name = user.get_full_name() or user.username

        for institution in institutions:

            NotificationService.notify_institution_managers(
                institution,
                ntype=NotificationService.Type.PARENT,
                title=_("New parent added"),
                message=_(
                    "Parent {name} has been added to {institution}."
                ).format(
                    name=parent_name,
                    institution=institution.name,
                ),
                link="/parents/",
            )

        NotificationService.notify_user(
            user,
            ntype=NotificationService.Type.PARENT,
            title=_("Welcome!"),
            message=_(
                "Your parent account has been created. "
                "Please log in and change your password."
            ),
            link="/",
        )

        return parent

    @staticmethod
    @transaction.atomic
    def update_parent(
        *,
        parent,
        username,
        password,
        first_name,
        last_name,
        relationship,
        students,
    ):

        if User.objects.exclude(
            pk=parent.user.pk,
        ).filter(
            username=username,
        ).exists():
            raise ValidationError(
                _("Username already exists.")
            )

        parent.user.username = username
        parent.user.first_name = first_name
        parent.user.last_name = last_name

        if password:

            parent.user.set_password(password)

        parent.user.save()

        parent.relationship = relationship

        parent.save()

        parent.students.set(students)

        NotificationService.notify_user(
            parent.user,
            ntype=NotificationService.Type.PARENT,
            title=_("Profile updated"),
            message=_("Your parent data has been updated."),
            link="/",
        )

        return parent

    @staticmethod
    @transaction.atomic
    def delete_parent(parent):

        parent_user = parent.user

        institutions = set(
            student.institution
            for student in parent.students.all()
            if student.institution_id
        )

        parent_name = (
            parent_user.get_full_name()
            or parent_user.username
        )

        parent_user.delete()

        for institution in institutions:

            NotificationService.notify_institution_managers(
                institution,
                ntype=NotificationService.Type.PARENT,
                title=_("Parent removed"),
                message=_(
                    "Parent {name} has been removed."
                ).format(
                    name=parent_name,
                ),
                link="/parents/",
            )

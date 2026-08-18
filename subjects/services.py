from django.db import transaction
from django.utils.translation import gettext as _

from notifications.services import NotificationService

from .models import Subject


class SubjectService:

    @staticmethod
    @transaction.atomic
    def create_subject(form):

        subject = form.save()

        NotificationService.notify_institution_managers(
            subject.institution,
            ntype=NotificationService.Type.SUBJECT,
            title=_("New subject added"),
            message=_(
                "Subject {name} has been added to {institution}."
            ).format(
                name=subject.name,
                institution=subject.institution.name,
            ),
            link=f"/subjects/{subject.pk}/edit/",
        )

        if subject.teacher_id:

            NotificationService.notify_user(
                subject.teacher.user,
                ntype=NotificationService.Type.SUBJECT,
                title=_("New subject assigned"),
                message=_(
                    "Subject {name} has been assigned to you."
                ).format(
                    name=subject.name,
                ),
                link="/teachers/dashboard/",
            )

        SubjectService._notify_classroom_students(
            subject,
            title=_("New subject added"),
            message=_(
                "Subject {name} has been added to your class."
            ).format(
                name=subject.name,
            ),
        )

        return subject

    @staticmethod
    @transaction.atomic
    def update_subject(form):

        subject = form.save()

        NotificationService.notify_institution_managers(
            subject.institution,
            ntype=NotificationService.Type.SUBJECT,
            title=_("Subject updated"),
            message=_(
                "The data of subject {name} has been updated."
            ).format(
                name=subject.name,
            ),
            link=f"/subjects/{subject.pk}/edit/",
        )

        if subject.teacher_id:

            NotificationService.notify_user(
                subject.teacher.user,
                ntype=NotificationService.Type.SUBJECT,
                title=_("Subject updated"),
                message=_(
                    "Subject {name} assigned to you has been updated."
                ).format(
                    name=subject.name,
                ),
                link="/teachers/dashboard/",
            )

        return subject

    @staticmethod
    @transaction.atomic
    def delete_subject(subject):

        institution = subject.institution

        teacher_user = subject.teacher.user if subject.teacher_id else None

        subject_name = subject.name

        subject.delete()

        NotificationService.notify_institution_managers(
            institution,
            ntype=NotificationService.Type.SUBJECT,
            title=_("Subject deleted"),
            message=_(
                "Subject {name} has been removed."
            ).format(
                name=subject_name,
            ),
            link="/subjects/",
        )

        if teacher_user:

            NotificationService.notify_user(
                teacher_user,
                ntype=NotificationService.Type.SUBJECT,
                title=_("Subject removed"),
                message=_(
                    "Subject {name} assigned to you has been removed."
                ).format(
                    name=subject_name,
                ),
                link="/teachers/dashboard/",
            )

    @staticmethod
    def _notify_classroom_students(
        subject,
        *,
        title,
        message,
    ):

        if not subject.classroom_id:
            return

        for student in subject.classroom.students.select_related("user"):

            NotificationService.student_and_parents(
                student,
                ntype=NotificationService.Type.SUBJECT,
                title=title,
                message=message,
                student_link="/students/subjects/",
                parent_link="/",
            )
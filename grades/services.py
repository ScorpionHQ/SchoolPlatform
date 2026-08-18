from django.db import transaction
from django.utils.translation import gettext as _

from notifications.services import NotificationService

from .models import Grade


class GradeService:

    @staticmethod
    @transaction.atomic
    def create_grade(form):

        grade = form.save()

        GradeService._notify(grade, added=True)

        return grade

    @staticmethod
    @transaction.atomic
    def update_grade(form):

        grade = form.save()

        GradeService._notify(grade, added=False)

        return grade

    @staticmethod
    @transaction.atomic
    def delete_grade(grade):

        institution = grade.student.institution if grade.student_id else None

        student = grade.student if grade.student_id else None

        subject_name = grade.subject.name if grade.subject_id else ""

        grade.delete()

        if student:

            NotificationService.student_and_parents(
                student,
                ntype=NotificationService.Type.GRADE,
                title=_("Grade removed"),
                message=_(
                    "Your grade for {subject} has been removed."
                ).format(
                    subject=subject_name,
                ),
                student_link="/students/grades/",
                parent_link="/",
            )

        if institution:

            NotificationService.notify_institution_managers(
                institution,
                ntype=NotificationService.Type.GRADE,
                title=_("Grade removed"),
                message=_(
                    "A grade for subject {subject} has been removed."
                ).format(
                    subject=subject_name,
                ),
                link="/grades/",
            )

    @staticmethod
    def _notify(grade, *, added):

        student = grade.student if grade.student_id else None

        subject_name = grade.subject.name if grade.subject_id else ""

        score_text = str(grade.score)

        max_text = str(grade.max_score) if grade.max_score else ""

        message = _(
            "You received {score} in {subject}."
        ).format(
            score=score_text,
            subject=subject_name,
        )

        if max_text:

            message = _(
                "You received {score}/{max} in {subject}."
            ).format(
                score=score_text,
                max=max_text,
                subject=subject_name,
            )

        if student:

            NotificationService.student_and_parents(
                student,
                ntype=NotificationService.Type.GRADE,
                title=_("New grade") if added else _("Grade updated"),
                message=message,
                student_link="/students/grades/",
                parent_link="/",
            )

        if student and student.institution_id:

            NotificationService.notify_institution_managers(
                student.institution,
                ntype=NotificationService.Type.GRADE,
                title=(
                    _("New grade recorded")
                    if added
                    else _("Grade updated")
                ),
                message=_(
                    "{student} received {score} in {subject}."
                ).format(
                    student=(
                        student.user.get_full_name()
                        or student.student_code
                    ),
                    score=score_text,
                    subject=subject_name,
                ),
                link="/grades/",
            )
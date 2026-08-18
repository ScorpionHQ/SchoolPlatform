from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from notifications.services import NotificationService

from .models import Attendance


class AttendanceService:

    @staticmethod
    @transaction.atomic
    def create_attendance(form):

        attendance = form.save()

        AttendanceService._notify_record(attendance)

        return attendance

    @staticmethod
    @transaction.atomic
    def update_attendance(form):

        attendance = form.save()

        AttendanceService._notify_record(attendance)

        return attendance

    @staticmethod
    @transaction.atomic
    def delete_attendance(attendance):

        student = attendance.student if attendance.student_id else None

        AttendanceService._notify_student(
            attendance,
            title=_("Attendance record removed"),
            message=_(
                "Your attendance record for {date} has been removed."
            ).format(
                date=attendance.date,
            ),
        )

        attendance.delete()

        if student and student.institution_id:

            NotificationService.notify_institution_managers(
                student.institution,
                ntype=NotificationService.Type.ATTENDANCE,
                title=_("Attendance record removed"),
                message=_(
                    "An attendance record for {date} has been removed."
                ).format(
                    date=attendance.date,
                ),
                link="/attendance/",
            )

    @staticmethod
    def _notify_record(attendance):

        status = attendance.get_status_display()

        AttendanceService._notify_student(
            attendance,
            title=_("Attendance recorded"),
            message=_(
                "Your attendance on {date} was marked as {status}."
            ).format(
                date=attendance.date,
                status=status,
            ),
        )

        if attendance.student_id and attendance.student.institution_id:

            NotificationService.notify_institution_managers(
                attendance.student.institution,
                ntype=NotificationService.Type.ATTENDANCE,
                title=_("Attendance recorded"),
                message=_(
                    "Attendance was recorded for {student} on {date}."
                ).format(
                    student=(
                        attendance.student.user.get_full_name()
                        or attendance.student.student_code
                    ),
                    date=attendance.date,
                ),
                link="/attendance/",
            )

    @staticmethod
    def _notify_student(attendance, *, title, message):

        if not attendance.student_id:
            return

        NotificationService.student_and_parents(
            attendance.student,
            ntype=NotificationService.Type.ATTENDANCE,
            title=title,
            message=message,
            student_link="/students/attendance/",
            parent_link="/",
        )

    @staticmethod
    @transaction.atomic
    def save_attendance_session(
        *,
        classroom,
        subject,
        teacher,
        date,
        attendance_data,
    ):

        valid_statuses = {
            Attendance.Status.PRESENT,
            Attendance.Status.ABSENT,
            Attendance.Status.LATE,
            Attendance.Status.EXCUSED,
        }

        for item in attendance_data:

            if item["status"] not in valid_statuses:

                raise ValidationError(
                    _("Invalid attendance status provided.")
                )

        if Attendance.objects.filter(
            classroom=classroom,
            subject=subject,
            date=date,
        ).exists():
            raise ValidationError(
                _("Attendance has already been recorded for this class today.")
            )

        records = []

        for item in attendance_data:

            records.append(
                Attendance(
                    student=item["student"],
                    classroom=classroom,
                    subject=subject,
                    teacher=teacher,
                    date=date,
                    status=item["status"],
                )
            )

        Attendance.objects.bulk_create(records)

        for item in attendance_data:

            NotificationService.student_and_parents(
                item["student"],
                ntype=NotificationService.Type.ATTENDANCE,
                title=_("Attendance recorded"),
                message=_(
                    "Your attendance on {date} was marked as {status} "
                    "in {subject}."
                ).format(
                    date=date,
                    status=Attendance(item["status"]).get_status_display(),
                    subject=subject.name,
                ),
                student_link="/students/attendance/",
                parent_link="/",
            )

        if classroom.institution_id:

            NotificationService.notify_institution_managers(
                classroom.institution,
                ntype=NotificationService.Type.ATTENDANCE,
                title=_("Attendance session recorded"),
                message=_(
                    "Attendance was recorded for {count} students "
                    "in class {classroom} on {date}."
                ).format(
                    count=len(records),
                    classroom=classroom.name,
                    date=date,
                ),
                link="/attendance/",
            )

        return len(records)
import calendar as cal_module
import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from accounts.decorators import manager_required, role_required
from accounts.models import User

from .forms import AttendanceForm, AttendanceSessionForm
from .models import Attendance
from .services import AttendanceService
from students.models import Student


MONTH_NAMES = [
    _("January"), _("February"), _("March"), _("April"),
    _("May"), _("June"), _("July"), _("August"),
    _("September"), _("October"), _("November"), _("December"),
]

WEEKDAY_NAMES = [
    _("Sat"), _("Sun"), _("Mon"), _("Tue"),
    _("Wed"), _("Thu"), _("Fri"),
]


def _get_institution(request):
    """Return the current institution for the request, or None."""
    return getattr(request, "current_institution", None)


def _build_calendar_data(year, month, attendance_qs):
    """Return a list of weeks, each week a list of 7 day-cells."""
    first_day, num_days = cal_module.monthrange(year, month)
    today = timezone.localdate()

    day_map = {}
    for att in attendance_qs:
        if att.date.day not in day_map:
            day_map[att.date.day] = []
        day_map[att.date.day].append(att)

    weeks = []
    week = [None] * first_day
    for day in range(1, num_days + 1):
        date_obj = datetime.date(year, month, day)
        records = day_map.get(day, [])

        status_counts = {"present": 0, "absent": 0, "late": 0, "excused": 0}
        for r in records:
            status_counts[r.status] = status_counts.get(r.status, 0) + 1

        dominant = ""
        total = len(records)
        if total > 0:
            dominant = max(status_counts, key=status_counts.get)

        week.append({
            "day": day,
            "date": date_obj,
            "is_today": date_obj == today,
            "records": records,
            "total": total,
            "status_counts": status_counts,
            "dominant": dominant,
        })

        if len(week) == 7:
            weeks.append(week)
            week = []

    if week:
        while len(week) < 7:
            week.append(None)
        weeks.append(week)

    return weeks


@role_required(
    User.Role.TEACHER,
    User.Role.MANAGER,
    User.Role.SYSTEM_ADMIN,
    User.Role.ASSISTANT_MANAGER,
    User.Role.STUDENT,
    User.Role.PARENT,
)
def attendance_calendar(request):
    institution = _get_institution(request)
    user = request.user

    today = timezone.localdate()
    year = int(request.GET.get("year", today.year))
    month = int(request.GET.get("month", today.month))
    student_id = request.GET.get("student")
    q = request.GET.get("q", "").strip()

    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1

    base_qs = Attendance.objects.none()
    can_search = False
    selected_student = None
    students_qs = Student.objects.none()

    if user.role in (User.Role.MANAGER, User.Role.SYSTEM_ADMIN, User.Role.ASSISTANT_MANAGER, User.Role.TEACHER):
        can_search = True
        if institution:
            base_qs = Attendance.objects.filter(
                student__institution=institution,
            )
            students_qs = Student.objects.filter(
                institution=institution,
            ).select_related("user").order_by("user__first_name")
    elif user.role == User.Role.STUDENT:
        student = Student.objects.filter(user=user).first()
        if student:
            base_qs = Attendance.objects.filter(student=student)
            selected_student = student
    elif user.role == User.Role.PARENT:
        from parents.models import Parent
        parent_profile = Parent.objects.filter(user=user).first()
        if parent_profile:
            child_ids = parent_profile.students.values_list("pk", flat=True)
            base_qs = Attendance.objects.filter(student_id__in=child_ids)
            students_qs = Student.objects.filter(pk__in=child_ids).select_related("user").order_by("user__first_name")

    if q and can_search:
        students_qs = students_qs.filter(
            Q(user__first_name__icontains=q) | Q(user__last_name__icontains=q)
        )
        base_qs = base_qs.filter(student__in=students_qs)

    if student_id and can_search:
        try:
            selected_student = students_qs.get(pk=student_id)
            base_qs = base_qs.filter(student=selected_student)
        except (Student.DoesNotExist, ValueError):
            pass

    month_qs = base_qs.filter(date__year=year, date__month=month).select_related(
        "student", "student__user", "subject", "classroom",
    )

    weeks = _build_calendar_data(year, month, month_qs)

    stats = {
        "present": month_qs.filter(status=Attendance.Status.PRESENT).count(),
        "absent": month_qs.filter(status=Attendance.Status.ABSENT).count(),
        "late": month_qs.filter(status=Attendance.Status.LATE).count(),
        "excused": month_qs.filter(status=Attendance.Status.EXCUSED).count(),
    }
    stats["total"] = sum(stats.values())

    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    return render(
        request,
        "attendance/calendar.html",
        {
            "year": year,
            "month": month,
            "month_name": MONTH_NAMES[month - 1],
            "weeks": weeks,
            "weekdays": WEEKDAY_NAMES,
            "stats": stats,
            "prev_year": prev_year,
            "prev_month": prev_month,
            "next_year": next_year,
            "next_month": next_month,
            "today": today,
            "can_search": can_search,
            "students": students_qs,
            "selected_student": selected_student,
            "q": q,
            "current_student_id": student_id,
        },
    )


@manager_required
def attendance_list(request):
    institution = _get_institution(request)

    attendances = Attendance.objects.none()

    if institution:
        attendances = Attendance.objects.filter(
            student__institution=institution,
        ).select_related(
            "student",
            "teacher",
            "subject",
            "classroom",
        )

    q = request.GET.get("q")

    if q:
        attendances = attendances.filter(
            student__user__first_name__icontains=q,
        )

    paginator = Paginator(attendances, 10)

    page = request.GET.get("page")

    attendances = paginator.get_page(page)

    return render(
        request,
        "attendance/list.html",
        {
            "attendances": attendances,
        },
    )


@manager_required
def attendance_create(request):

    institution = _get_institution(request)

    if institution is None:

        messages.warning(
            request,
            _("Please select an institution first."),
        )

        return redirect("institutions:select")

    if request.method == "POST":

        form = AttendanceForm(
            request.POST,
            institution=institution,
        )

        if form.is_valid():

            AttendanceService.create_attendance(form)

            messages.success(
                request,
                _("Attendance recorded successfully."),
            )

            return redirect("attendance:list")

    else:

        form = AttendanceForm(
            institution=institution,
        )

    return render(
        request,
        "attendance/attendance_form.html",
        {
            "form": form,
        },
    )


@manager_required
def attendance_update(request, pk):

    institution = _get_institution(request)

    attendance = get_object_or_404(
        Attendance,
        pk=pk,
        student__institution=institution,
    )

    if request.method == "POST":

        form = AttendanceForm(
            request.POST,
            instance=attendance,
            institution=institution,
        )

        if form.is_valid():

            AttendanceService.update_attendance(form)

            messages.success(
                request,
                _("Attendance updated successfully."),
            )

            return redirect("attendance:list")

    else:

        form = AttendanceForm(
            instance=attendance,
            institution=institution,
        )

    return render(
        request,
        "attendance/attendance_form.html",
        {
            "form": form,
        },
    )


@manager_required
def attendance_delete(request, pk):

    institution = _get_institution(request)

    attendance = get_object_or_404(
        Attendance,
        pk=pk,
        student__institution=institution,
    )

    if request.method == "POST":

        AttendanceService.delete_attendance(
            attendance,
        )

        messages.success(
            request,
            _("Attendance deleted successfully."),
        )

        return redirect("attendance:list")

    return render(
        request,
        "attendance/attendance_confirm_delete.html",
        {
            "attendance": attendance,
        },
    )


@role_required(
    User.Role.TEACHER,
    User.Role.MANAGER,
    User.Role.SYSTEM_ADMIN,
    User.Role.ASSISTANT_MANAGER,
)
def attendance_session(request):

    students = None

    form = AttendanceSessionForm(
        request.POST or None,
        user=request.user,
        institution=_get_institution(request),
    )

    action = request.POST.get("action")

    if form.is_valid():

        classroom = form.cleaned_data["classroom"]

        students = Student.objects.select_related(
            "user",
        ).filter(
            classroom=classroom,
        ).order_by(
            "user__first_name",
        )

        if action == "save":

            attendance_data = []

            for student in students:

                raw_status = request.POST.get(
                    f"status_{student.id}",
                )

                status = (
                    raw_status
                    if raw_status in Attendance.Status.values
                    else Attendance.Status.PRESENT
                )

                attendance_data.append(
                    {
                        "student": student,
                        "status": status,
                    }
                )

            try:

                AttendanceService.save_attendance_session(
                    classroom=classroom,
                    subject=form.cleaned_data["subject"],
                    teacher=form.cleaned_data["teacher"],
                    date=form.cleaned_data["date"],
                    attendance_data=attendance_data,
                )

                messages.success(
                    request,
                    _("Attendance saved successfully."),
                )

                return redirect("attendance:list")

            except ValidationError as e:

                messages.error(
                    request,
                    str(e),
                )

    return render(
        request,
        "attendance/session.html",
        {
            "form": form,
            "students": students,
        },
    )

import os
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q, Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import (
    manager_required,
    parent_required,
    student_required,
)
from accounts.models import User
from attendance.models import Attendance
from billing.models import StudentFee
from classes.models import ClassRoom
from grades.models import Grade
from institutions.models import Institution
from parents.models import Parent
from students.models import Student
from subjects.models import Subject

try:
    from teachers.models import Teacher
except ImportError:
    Teacher = None


@login_required
def dashboard(request):

    if request.user.role == "student":
        return redirect("student_dashboard")

    if request.user.role == "teacher":
        return redirect("teachers:dashboard")

    if request.user.role == "parent":
        return redirect("parent_dashboard")

    if request.user.role in (
        User.Role.MANAGER,
        User.Role.ASSISTANT_MANAGER,
    ):
        return redirect("manager_dashboard")

    current_institution = getattr(
        request,
        "current_institution",
        None,
    )

    is_system_admin = (
        request.user.role == User.Role.SYSTEM_ADMIN
    )

    if is_system_admin:

        student_queryset = Student.objects
        teacher_queryset = (
            Teacher.objects
            if Teacher
            else Student.objects.none()
        )
        classroom_queryset = ClassRoom.objects
        subject_queryset = Subject.objects
        attendance_queryset = Attendance.objects
        grade_queryset = Grade.objects

    elif current_institution:

        student_queryset = Student.objects.filter(
            institution=current_institution,
        )
        teacher_queryset = (
            Teacher.objects.filter(
                institution=current_institution,
            )
            if Teacher
            else Student.objects.none()
        )
        classroom_queryset = ClassRoom.objects.filter(
            institution=current_institution,
        )
        subject_queryset = Subject.objects.filter(
            institution=current_institution,
        )
        attendance_queryset = Attendance.objects.filter(
            student__institution=current_institution,
        )
        grade_queryset = Grade.objects.filter(
            student__institution=current_institution,
        )

    else:

        student_queryset = Student.objects.none()
        teacher_queryset = Student.objects.none()
        classroom_queryset = ClassRoom.objects.none()
        subject_queryset = Subject.objects.none()
        attendance_queryset = Attendance.objects.none()
        grade_queryset = Grade.objects.none()

    recent_students = (
        student_queryset.select_related(
            "user",
            "classroom",
        )
        .order_by("-id")[:5]
    )

    context = {
     "student_count": student_queryset.count(),
     "teacher_count": teacher_queryset.count(),
     "classroom_count": classroom_queryset.count(),
     "institution_count": Institution.objects.count(),
     "subject_count": subject_queryset.count(),

     "attendance_today": attendance_queryset.filter(
         date=timezone.now().date(),
        ).count(),

     "grades_count": grade_queryset.count(),

     "recent_students": recent_students,

     "recent_grades": grade_queryset.select_related(
         "student__user",
         "subject",
        ).order_by("-exam_date")[:5],

     "recent_attendance": attendance_queryset.select_related(
         "student__user",
        ).order_by("-date")[:5],
    }

    return render(
        request,
        "core/dashboard.html",
        context,
    )


def _manager_institution(request):
    """The institution currently managed by a manager/assistant manager."""

    return getattr(request, "current_institution", None)


@manager_required
def manager_dashboard(request):

    institution = _manager_institution(request)

    if institution is None:

        from django.shortcuts import redirect as _redirect

        return _redirect("institutions:select")

    today = timezone.now().date()

    students = Student.objects.filter(
        institution=institution,
    )

    teachers = (
        Teacher.objects.filter(
            institution=institution,
        )
        if Teacher
        else Student.objects.none()
    )

    classrooms = ClassRoom.objects.filter(
        institution=institution,
    )

    subjects = Subject.objects.filter(
        institution=institution,
    )

    grades = Grade.objects.filter(
        student__institution=institution,
    )

    attendance = Attendance.objects.filter(
        student__institution=institution,
    )

    attendance_today = attendance.filter(
        date=today,
    )

    present_today = attendance_today.filter(
        status=Attendance.Status.PRESENT,
    ).count()

    absent_today = attendance_today.filter(
        status=Attendance.Status.ABSENT,
    ).count()

    late_today = attendance_today.filter(
        status=Attendance.Status.LATE,
    ).count()

    attendance_today_count = attendance_today.count()

    attendance_percentage = 0

    if attendance_today_count > 0:

        attendance_percentage = round(
            (present_today / attendance_today_count) * 100,
            1,
        )

    totals = grades.aggregate(
        total_score=Sum("score"),
        total_max=Sum("max_score"),
    )

    average_grade_percentage = 0

    if totals["total_max"]:

        average_grade_percentage = round(
            (totals["total_score"] / totals["total_max"]) * 100,
            1,
        )

    fee_stats = StudentFee.objects.filter(
        institution=institution,
    ).aggregate(
        total=Sum("amount"),
        paid=Sum("paid_amount"),
    )

    fee_total = fee_stats["total"] or 0

    fee_paid = fee_stats["paid"] or 0

    fee_pending = max(
        fee_total - fee_paid,
        0,
    )

    students_with_parents = Student.objects.filter(
        institution=institution,
        parents__isnull=False,
    ).count()

    trend_start = today - timedelta(days=6)

    trend_rows = (
        attendance.filter(date__gte=trend_start)
        .values("date", "status")
        .annotate(n=Count("id"))
    )

    trend_by_day = {}

    for row in trend_rows:

        trend_by_day.setdefault(row["date"], {})[
            row["status"]
        ] = row["n"]

    attendance_trend = []

    for offset in range(7):

        day = today - timedelta(days=6 - offset)

        counts = trend_by_day.get(day, {})

        attendance_trend.append(
            {
                "date": day,
                "label": day.strftime("%a"),
                "present": counts.get(
                    Attendance.Status.PRESENT, 0
                ),
                "absent": counts.get(
                    Attendance.Status.ABSENT, 0
                ),
                "late": counts.get(
                    Attendance.Status.LATE, 0
                ),
                "excused": counts.get(
                    Attendance.Status.EXCUSED, 0
                ),
            }
        )

    subject_avg_rows = (
        grades.values("subject__name")
        .annotate(average=Avg("score"))
        .order_by("subject__name")
    )

    subject_names = [
        row["subject__name"]
        for row in subject_avg_rows
    ]

    subject_averages = [
        round(row["average"] or 0, 1)
        for row in subject_avg_rows
    ]

    at_risk_ids = attendance_today.filter(
        status=Attendance.Status.ABSENT,
    ).values_list("student_id", flat=True).distinct()

    at_risk_students = (
        students.filter(id__in=at_risk_ids)
        .select_related("user", "classroom")[:8]
    )

    recent_absences = (
        attendance.filter(
            status=Attendance.Status.ABSENT,
        )
        .select_related(
            "student__user",
            "subject",
            "classroom",
        )
        .order_by("-date")[:8]
    )

    recent_grades = (
        grades.select_related(
            "student__user",
            "subject",
            "teacher__user",
        )
        .order_by("-exam_date")[:8]
    )

    context = {
        "institution": institution,
        "today": today,
        "student_count": students.count(),
        "teacher_count": teachers.count(),
        "classroom_count": classrooms.count(),
        "subject_count": subjects.count(),
        "grade_count": grades.count(),
        "attendance_count": attendance.count(),
        "attendance_today_count": attendance_today_count,
        "present_today": present_today,
        "absent_today": absent_today,
        "late_today": late_today,
        "attendance_percentage": attendance_percentage,
        "average_grade": grades.aggregate(
            average=Avg("score"),
        )["average"],
        "average_grade_percentage": average_grade_percentage,
        "fee_total": fee_total,
        "fee_paid": fee_paid,
        "fee_pending": fee_pending,
        "students_with_parents": students_with_parents,
        "attendance_trend": attendance_trend,
        "subject_names": subject_names,
        "subject_averages": subject_averages,
        "at_risk_students": at_risk_students,
        "at_risk_count": at_risk_ids.count(),
        "recent_absences": recent_absences,
        "recent_grades": recent_grades,
    }

    return render(
        request,
        "core/manager_dashboard.html",
        context,
    )


@manager_required
def manager_students(request):

    institution = _manager_institution(request)

    if institution is None:

        return redirect("institutions:select")

    students = Student.objects.filter(
        institution=institution,
    ).select_related(
        "user",
        "classroom",
    ).order_by(
        "student_code",
    )

    grade_stats = (
        Grade.objects.filter(
            student__institution=institution,
        )
        .values("student_id")
        .annotate(
            count=Count("id"),
            average=Avg("score"),
        )
    )

    grade_map = {
        row["student_id"]: row
        for row in grade_stats
    }

    attendance_stats = (
        Attendance.objects.filter(
            student__institution=institution,
        )
        .values("student_id")
        .annotate(
            total=Count("id"),
            present=Count(
                "id",
                filter=Q(status=Attendance.Status.PRESENT),
            ),
            absent=Count(
                "id",
                filter=Q(status=Attendance.Status.ABSENT),
            ),
        )
    )

    attendance_map = {
        row["student_id"]: row
        for row in attendance_stats
    }

    rows = []

    for student in students:

        grades = grade_map.get(student.id, {})
        attendance = attendance_map.get(student.id, {})

        attendance_count = attendance.get("total", 0)
        present_count = attendance.get("present", 0)

        attendance_percentage = 0

        if attendance_count > 0:

            attendance_percentage = round(
                (present_count / attendance_count) * 100,
                1,
            )

        rows.append(
            {
                "student": student,
                "classroom": student.classroom,
                "grade_count": grades.get("count", 0),
                "average_grade": grades.get("average"),
                "attendance_count": attendance_count,
                "attendance_percentage": attendance_percentage,
                "absent_count": attendance.get("absent", 0),
                "last_login": student.user.last_login,
                "is_active": student.user.is_active,
            }
        )

    rows.sort(
        key=lambda item: (
            item["average_grade"] or 0,
        ),
        reverse=True,
    )

    return render(
        request,
        "core/manager_students.html",
        {
            "institution": institution,
            "students": rows,
        },
    )


@manager_required
def manager_teachers(request):

    institution = _manager_institution(request)

    if institution is None:

        return redirect("institutions:select")

    today = timezone.now().date()

    teacher_queryset = (
        Teacher.objects.filter(
            institution=institution,
        ).select_related("user")
        if Teacher
        else Teacher.objects.none()
    )

    subject_stats = (
        Subject.objects.filter(
            teacher__in=teacher_queryset,
        )
        .values("teacher_id")
        .annotate(
            count=Count("id"),
            classrooms=Count("classroom", distinct=True),
        )
    )

    subject_map = {
        row["teacher_id"]: row
        for row in subject_stats
    }

    classroom_ids = list(
        Subject.objects.filter(
            teacher__in=teacher_queryset,
            classroom__isnull=False,
        ).values_list("classroom_id", flat=True).distinct()
    )

    classroom_student_counts = {
        row["classroom_id"]: row["n"]
        for row in Student.objects.filter(
            institution=institution,
            classroom_id__in=classroom_ids,
        ).values("classroom_id").annotate(n=Count("id"))
    }

    teacher_classroom_map = {}

    for row in (
        Subject.objects.filter(
            teacher__in=teacher_queryset,
            classroom__isnull=False,
        ).values("teacher_id", "classroom_id").distinct()
    ):

        teacher_classroom_map.setdefault(
            row["teacher_id"], set()
        ).add(row["classroom_id"])

    grade_stats = (
        Grade.objects.filter(
            teacher__in=teacher_queryset,
        )
        .values("teacher_id")
        .annotate(count=Count("id"))
    )

    grade_map = {
        row["teacher_id"]: row["count"]
        for row in grade_stats
    }

    attendance_stats = (
        Attendance.objects.filter(
            teacher__in=teacher_queryset,
        )
        .values("teacher_id")
        .annotate(
            count=Count("id"),
            today=Count(
                "id",
                filter=Q(date=today),
            ),
        )
    )

    attendance_map = {
        row["teacher_id"]: row
        for row in attendance_stats
    }

    teachers = []

    for teacher in teacher_queryset:

        subject_info = subject_map.get(teacher.id, {})

        teacher_classrooms = teacher_classroom_map.get(
            teacher.id, set()
        )

        students_count = sum(
            classroom_student_counts.get(
                classroom_id, 0
            )
            for classroom_id in teacher_classrooms
        )

        attendance_info = attendance_map.get(
            teacher.id, {}
        )

        teachers.append(
            {
                "teacher": teacher,
                "subjects_count": subject_info.get("count", 0),
                "students_count": students_count,
                "grades_count": grade_map.get(teacher.id, 0),
                "attendance_count": attendance_info.get("count", 0),
                "attendance_today": attendance_info.get("today", 0),
                "last_login": teacher.user.last_login,
                "is_active": teacher.user.is_active,
                "joined_at": teacher.hire_date or teacher.created_at,
            }
        )

    teachers.sort(
        key=lambda item: (
            item["grades_count"] + item["attendance_count"]
        ),
        reverse=True,
    )

    return render(
        request,
        "core/manager_teachers.html",
        {
            "institution": institution,
            "teachers": teachers,
        },
    )


@student_required
def student_dashboard(request):

    student = Student.objects.select_related(
        "user",
        "classroom",
    ).get(
        user=request.user,
    )

    grades = (
        Grade.objects.filter(
            student=student,
        )
        .select_related(
            "subject",
        )
        .order_by("-exam_date")
    )

    attendance = (
        Attendance.objects.filter(
            student=student,
        )
        .order_by("-date")
    )

    average_grade = grades.aggregate(
        average=Avg("score"),
    )["average"]

    totals = grades.aggregate(
        total_score=Sum("score"),
        total_max=Sum("max_score"),
    )

    average_grade_percentage = 0

    if totals["total_max"]:

        average_grade_percentage = round(
            (totals["total_score"] / totals["total_max"]) * 100,
            1,
        )

    attendance_count = attendance.count()

    present_count = attendance.filter(
        status=Attendance.Status.PRESENT,
    ).count()

    attendance_percentage = 0

    if attendance_count > 0:

        attendance_percentage = round(
            (present_count / attendance_count) * 100,
            1,
        )

    subjects = Subject.objects.filter(
        grades__student=student,
    ).distinct()

    subject_average_map = {
        row["subject_id"]: row["average"]
        for row in grades.values("subject_id").annotate(
            average=Avg("score"),
        )
    }

    subject_averages = []

    for subject in subjects:

        average = subject_average_map.get(subject.id)

        subject_averages.append(
            {
                "subject": subject,
                "average": average,
                "percentage": round(
                    (average or 0) * 100 / 100,
                    1,
                ) if average else None,
            }
        )

    subject_averages.sort(
        key=lambda item: item["average"] or 0,
        reverse=True,
    )

    grade_rows = [
        {
            "grade": grade,
            "percentage": round(
                (grade.score / grade.max_score) * 100,
                1,
            ) if grade.max_score else None,
        }
        for grade in grades[:8]
    ]

    classroom_stage = (
        student.classroom.stage
        if student.classroom_id
        else None
    )

    context = {
        "student": student,
        "grades": grade_rows,
        "attendance": attendance[:5],
        "subjects": subject_averages,
        "average_grade": average_grade,
        "average_grade_percentage": average_grade_percentage,
        "grade_count": grades.count(),
        "attendance_percentage": attendance_percentage,
        "attendance_count": attendance_count,
        "subject_count": subjects.count(),
        "stage": classroom_stage,
    }

    return render(
        request,
        "core/student_dashboard.html",
        context,
    )



@parent_required
def parent_dashboard(request):

    parent = request.user.parent_profile

    students = parent.students.select_related(
        "user",
        "classroom",
    )

    children = []

    for student in students:

        grades = (
            Grade.objects.filter(
                student=student,
            )
            .select_related(
                "subject",
            )
            .order_by("-exam_date")
        )

        attendance = Attendance.objects.filter(
            student=student,
        )

        attendance_count = attendance.count()

        present_count = attendance.filter(
            status=Attendance.Status.PRESENT,
        ).count()

        attendance_percentage = 0

        if attendance_count > 0:

            attendance_percentage = round(
                (present_count / attendance_count) * 100,
                1,
            )

        grade_stats = grades.aggregate(
            average=Avg("score"),
            total_score=Sum("score"),
            total_max=Sum("max_score"),
        )

        average_grade = grade_stats["average"]

        average_grade_percentage = 0

        if grade_stats["total_max"]:

            average_grade_percentage = round(
                (grade_stats["total_score"] / grade_stats["total_max"]) * 100,
                1,
            )

        subject_count = Subject.objects.filter(
            grades__student=student,
        ).distinct().count()

        grade_rows = [
            {
                "grade": grade,
                "percentage": round(
                    (grade.score / grade.max_score) * 100,
                    1,
                ) if grade.max_score else None,
            }
            for grade in grades[:5]
        ]

        children.append(
            {
                "student": student,
                "grades": grade_rows,
                "average_grade": average_grade,
                "average_grade_percentage": average_grade_percentage,
                "attendance_percentage": attendance_percentage,
                "subject_count": subject_count,
                "grade_count": grades.count(),
            }
        )

    return render(
        request,
        "core/parent_dashboard.html",
        {
            "children": children,
        },
    )


@parent_required
def parent_children(request):

    parent = get_object_or_404(
        Parent,
        user=request.user,
    )

    children = parent.students.select_related(
        "user",
        "classroom",
        "institution",
    ).all()

    return render(
        request,
        "core/parent_children.html",
        {
            "children": children,
        },
    )


@parent_required
def parent_grades(request):

    parent = get_object_or_404(
        Parent,
        user=request.user,
    )

    grades = Grade.objects.filter(
        student__in=parent.students.all(),
    ).select_related(
        "student__user",
        "subject",
        "teacher",
    ).order_by(
        "-exam_date",
    )

    return render(
        request,
        "core/parent_grades.html",
        {
            "grades": grades,
        },
    )


@parent_required
def parent_attendance(request):

    parent = get_object_or_404(
        Parent,
        user=request.user,
    )

    attendance = Attendance.objects.filter(
        student__in=parent.students.all(),
    ).select_related(
        "student__user",
        "subject",
        "teacher",
    ).order_by(
        "-date",
    )

    return render(
        request,
        "core/parent_attendance.html",
        {
            "attendance": attendance,
        },
    )


def error_400(request, exception=None):
    return render(
        request,
        "errors/400.html",
        status=400,
    )


def error_403(request, exception=None):
    return render(
        request,
        "errors/403.html",
        status=403,
    )


def error_404(request, exception=None):
    return render(
        request,
        "errors/404.html",
        status=404,
    )


def error_500(request):
    return render(
        request,
        "errors/500.html",
        status=500,
    )


def service_worker(request):
    path = os.path.join(settings.BASE_DIR, "static", "pwa", "sw.js")
    response = FileResponse(
        open(path, "rb"),
        content_type="application/javascript",
    )
    response["Service-Worker-Allowed"] = "/"
    response["Cache-Control"] = "no-cache"
    return response
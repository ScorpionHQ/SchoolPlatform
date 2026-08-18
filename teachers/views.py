from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _

from accounts.decorators import manager_required, teacher_required
from attendance.models import Attendance
from grades.models import Grade
from notifications.services import NotificationService
from students.models import Student
from subjects.models import Subject

from .forms import TeacherForm
from .models import Teacher
from .services import TeacherService


def _get_institution(request):
    """Return the current institution for the request, or None."""

    return getattr(request, "current_institution", None)


@manager_required
def teacher_list(request):

    institution = _get_institution(request)

    teachers = Teacher.objects.none()
    classrooms = []
    subjects_list = []

    if institution:

        classrooms = list(
            Subject.objects.filter(
                institution=institution,
                classroom__isnull=False,
            ).values_list(
                "classroom__id", "classroom__name", "classroom__level",
            ).distinct()
        )

        subjects_list = Subject.objects.filter(
            institution=institution,
        ).select_related("classroom").order_by("name")

        teachers = Teacher.objects.filter(
            institution=institution,
        ).select_related(
            "user",
            "institution",
        )

    q = request.GET.get("q", "").strip()
    classroom_id = request.GET.get("classroom")
    subject_id = request.GET.get("subject")

    if q:
        teachers = teachers.filter(
            Q(user__first_name__icontains=q)
            | Q(user__last_name__icontains=q)
            | Q(employee_code__icontains=q)
        )

    if subject_id:
        teachers = teachers.filter(subjects__id=subject_id).distinct()

    if classroom_id:
        teachers = teachers.filter(
            subjects__classroom__id=classroom_id,
        ).distinct()

    paginator = Paginator(teachers, 10)

    page = request.GET.get("page")

    teachers = paginator.get_page(page)

    return render(
        request,
        "teachers/list.html",
        {
            "teachers": teachers,
            "classrooms": classrooms,
            "subjects_list": subjects_list,
            "q": q,
            "selected_classroom": classroom_id,
            "selected_subject": subject_id,
        },
    )


@manager_required
def teacher_create(request):

    institution = _get_institution(request)

    if institution is None:

        messages.warning(
            request,
            _("Please select an institution first."),
        )

        return redirect("institutions:select")

    if request.method == "POST":

        form = TeacherForm(
            request.POST,
            institution=institution,
        )

        if form.is_valid():

            TeacherService.create_teacher(form)

            messages.success(
                request,
                _("Teacher created successfully."),
            )

            return redirect("teachers:list")

    else:

        form = TeacherForm(
            institution=institution,
        )

    return render(
        request,
        "teachers/teacher_form.html",
        {
            "form": form,
        },
    )


@manager_required
def teacher_update(request, pk):

    institution = _get_institution(request)

    teacher = get_object_or_404(
        Teacher,
        pk=pk,
        institution=institution,
    )

    if request.method == "POST":

        form = TeacherForm(
            request.POST,
            instance=teacher,
            institution=institution,
        )

        if form.is_valid():

            TeacherService.update_teacher(form)

            messages.success(
                request,
                _("Teacher updated successfully."),
            )

            return redirect("teachers:list")

    else:

        form = TeacherForm(
            instance=teacher,
            institution=institution,
        )

    return render(
        request,
        "teachers/teacher_form.html",
        {
            "form": form,
        },
    )


@manager_required
def teacher_delete(request, pk):

    institution = _get_institution(request)

    teacher = get_object_or_404(
        Teacher,
        pk=pk,
        institution=institution,
    )

    if request.method == "POST":

        TeacherService.delete_teacher(teacher)

        messages.success(
            request,
            _("Teacher deleted successfully."),
        )

        return redirect("teachers:list")

    return render(
        request,
        "teachers/teacher_confirm_delete.html",
        {
            "teacher": teacher,
        },
    )


@teacher_required
def teacher_dashboard(request):

    teacher = get_object_or_404(
        Teacher,
        user=request.user,
    )

    subjects = Subject.objects.filter(
        teacher=teacher,
    ).select_related(
        "classroom",
    )

    classrooms = []

    students_count = 0

    for subject in subjects:

        if (
            subject.classroom
            and subject.classroom not in classrooms
        ):

            classrooms.append(
                subject.classroom,
            )

            students_count += Student.objects.filter(
                classroom=subject.classroom,
            ).count()

    attendance_count = Attendance.objects.filter(
        teacher=teacher,
    ).count()

    grades_count = Grade.objects.filter(
        teacher=teacher,
    ).count()

    context = {
        "teacher": teacher,
        "subjects": subjects,
        "classrooms": classrooms,
        "students_count": students_count,
        "attendance_count": attendance_count,
        "grades_count": grades_count,
    }

    return render(
        request,
        "teachers/dashboard.html",
        context,
    )

@teacher_required
def my_students(request):

    teacher = get_object_or_404(
        Teacher,
        user=request.user,
    )

    subjects = Subject.objects.filter(
        teacher=teacher,
    ).select_related(
        "classroom",
    )

    classrooms = []

    for subject in subjects:

        if (
            subject.classroom
            and subject.classroom not in classrooms
        ):
            classrooms.append(subject.classroom)

    students = Student.objects.filter(
        classroom__in=classrooms,
    ).select_related(
        "user",
        "classroom",
    ).distinct()

    q = request.GET.get("q")

    if q:

        students = students.filter(
            user__first_name__icontains=q,
        )

    paginator = Paginator(
        students,
        10,
    )

    page = request.GET.get("page")

    students = paginator.get_page(page)

    return render(
        request,
        "teachers/my_students.html",
        {
            "students": students,
        },
    )

@teacher_required
def take_attendance(request):

    teacher = get_object_or_404(
        Teacher,
        user=request.user,
    )

    subjects = Subject.objects.filter(
        teacher=teacher,
    ).select_related(
        "classroom",
    )

    students = Student.objects.none()

    selected_subject = None

    if request.method == "POST":

        selected_subject = request.POST.get("subject")

        if selected_subject:

            subject = get_object_or_404(
                Subject,
                id=selected_subject,
                teacher=teacher,
            )

            students = Student.objects.filter(
                classroom=subject.classroom,
            ).select_related(
                "user",
            )

            if "save_attendance" in request.POST:

                from datetime import date

                for student in students:

                    status = request.POST.get(
                        f"status_{student.id}",
                    )

                    Attendance.objects.update_or_create(

                        student=student,
                        subject=subject,
                        date=date.today(),

                        defaults={
                            "teacher": teacher,
                            "classroom": subject.classroom,
                            "status": status,
                        },
                    )

                for student in students:

                    NotificationService.student_and_parents(
                        student,
                        ntype=NotificationService.Type.ATTENDANCE,
                        title=_("Attendance recorded"),
                        message=_(
                            "Your attendance on {date} was marked "
                            "in {subject}."
                        ).format(
                            date=date.today(),
                            subject=subject.name,
                        ),
                        student_link="/students/attendance/",
                        parent_link="/",
                    )

                NotificationService.notify_institution_managers(
                    subject.institution,
                    ntype=NotificationService.Type.ATTENDANCE,
                    title=_("Attendance session recorded"),
                    message=_(
                        "Attendance was recorded for {count} students "
                        "in class {classroom} on {date}."
                    ).format(
                        count=len(students),
                        classroom=getattr(
                            subject.classroom,
                            "name",
                            "",
                        ),
                        date=date.today(),
                    ),
                    link="/attendance/",
                )

                messages.success(
                    request,
                    _("Attendance saved successfully."),
                )

    context = {
        "subjects": subjects,
        "students": students,
        "selected_subject": selected_subject,
    }

    return render(
        request,
        "teachers/take_attendance.html",
        context,
    )

@teacher_required
def enter_grades(request):

    teacher = get_object_or_404(
        Teacher,
        user=request.user,
    )

    if request.method == "POST":

        subject = get_object_or_404(
            Subject,
            id=request.POST.get("subject_id"),
            teacher=teacher,
        )

        student = None

        student_id = request.POST.get("student_id")

        if student_id:

            student = Student.objects.filter(
                id=student_id,
                institution=subject.institution,
            ).first()

        if student is None:

            messages.error(
                request,
                _("Please choose a valid student for this subject."),
            )

            return redirect(
                f"{request.path}?subject={subject.id}"
            )

        exam_name = (request.POST.get("exam_name") or "").strip()

        if not exam_name:

            messages.error(
                request,
                _("Please provide an exam name."),
            )

            return redirect(
                f"{request.path}?subject={subject.id}"
            )

        try:

            score = Decimal(request.POST.get("score") or "0")
            max_score = Decimal(request.POST.get("max_score") or "0")

        except (InvalidOperation, ValueError, TypeError):

            messages.error(
                request,
                _("Score must be a valid number."),
            )

            return redirect(
                f"{request.path}?subject={subject.id}"
            )

        if max_score <= 0:

            messages.error(
                request,
                _("Maximum score must be greater than zero."),
            )

            return redirect(
                f"{request.path}?subject={subject.id}"
            )

        if score < 0 or score > max_score:

            messages.error(
                request,
                _("Score must be between 0 and the maximum score."),
            )

            return redirect(
                f"{request.path}?subject={subject.id}"
            )

        Grade.objects.update_or_create(
            student=student,
            subject=subject,
            exam_name=exam_name,
            defaults={
                "teacher": teacher,
                "score": score,
                "max_score": max_score,
                "note": request.POST.get("note"),
                "exam_date": request.POST.get("exam_date"),
            },
        )

        message = _(
            "You received {score}/{max} in {subject}."
        ).format(
            score=score,
            max=max_score,
            subject=subject.name,
        )

        NotificationService.student_and_parents(
            student,
            ntype=NotificationService.Type.GRADE,
            title=_("New grade"),
            message=message,
            student_link="/students/grades/",
            parent_link="/",
        )

        NotificationService.notify_institution_managers(
            subject.institution,
            ntype=NotificationService.Type.GRADE,
            title=_("New grade recorded"),
            message=_(
                "{student} received {score} in {subject}."
            ).format(
                student=(
                    student.user.get_full_name()
                    or student.student_code
                ),
                score=score,
                subject=subject.name,
            ),
            link="/grades/",
        )

        messages.success(
            request,
            _("Grade saved successfully."),
        )

        return redirect(
            f"{request.path}?subject={subject.id}"
        )

    subjects = Subject.objects.filter(
        teacher=teacher,
    ).select_related(
        "classroom",
    )

    selected_subject = request.GET.get("subject")

    students = Student.objects.none()

    subject = None

    if selected_subject:

        subject = get_object_or_404(
            Subject,
            id=selected_subject,
            teacher=teacher,
        )

        students = Student.objects.filter(
            classroom=subject.classroom,
        ).select_related(
            "user",
        ).order_by(
            "student_code",
        )

    existing_grades = {}

    if subject:

         for grade in Grade.objects.filter(
              subject=subject,
             ):

               existing_grades[grade.student_id] = grade

    context = {
        "teacher": teacher,
        "subjects": subjects,
        "subject": subject,
        "students": students,
        "existing_grades": existing_grades,
    }

    return render(
        request,
        "teachers/enter_grades.html",
        context,
    )
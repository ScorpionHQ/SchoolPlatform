import io
from datetime import datetime

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from accounts.decorators import manager_required, student_required
from notifications.services import NotificationService
from .forms import StudentCreationForm, StudentsImportForm
from .models import Student
from .pdf import build_credentials_pdf
from .services import ExcelImportError, StudentService


def _get_institution(request):
    """Return the current institution for the request, or None."""

    return getattr(request, "current_institution", None)


def _store_credentials(request, credentials, institution):
    """Remember recently created student credentials for a one-time PDF."""

    request.session["student_credentials"] = {
        "institution": institution.name,
        "at": timezone.now().isoformat(),
        "credentials": credentials,
    }


@manager_required
def student_list(request):

    institution = _get_institution(request)

    students = Student.objects.none()

    if institution:

        students = Student.objects.filter(
            institution=institution,
        ).select_related(
            "user",
            "institution",
            "classroom",
        )

    q = request.GET.get("q")

    if q:
        students = students.filter(
            user__first_name__icontains=q
        )

    paginator = Paginator(students, 10)

    page_number = request.GET.get("page")
    students = paginator.get_page(page_number)

    return render(
        request,
        "students/list.html",
        {
            "students": students,
        },
    )


@manager_required
def student_create(request):

    institution = _get_institution(request)

    if institution is None:

        messages.warning(
            request,
            _("Please select an institution first."),
        )

        return redirect("institutions:select")

    if request.method == "POST":

        form = StudentCreationForm(
            request.POST,
            institution=institution,
        )

        if form.is_valid():

            try:

                student = StudentService.create_student(
                    username=form.cleaned_data["username"],
                    password=form.cleaned_data["password"],
                    first_name=form.cleaned_data["first_name"],
                    last_name=form.cleaned_data["last_name"],
                    institution=institution,
                    classroom=form.cleaned_data["classroom"],
                    student_code=form.cleaned_data["student_code"],
                    gender=form.cleaned_data["gender"],
                    date_of_birth=form.cleaned_data["date_of_birth"],
                    address=form.cleaned_data["address"],
                    parent_phone=form.cleaned_data["parent_phone"],
                )

                generated_password = getattr(
                    student,
                    "generated_password",
                    None,
                )

                if generated_password:

                    full_name = (
                        student.user.get_full_name()
                        or student.student_code
                    )

                    _store_credentials(
                        request,
                        [
                            {
                                "code": student.user.login_code,
                                "username": student.user.username,
                                "name": full_name,
                                "password": generated_password,
                            }
                        ],
                        institution,
                    )

                    return redirect("students:created")

                messages.success(
                    request,
                    _("Student created successfully."),
                )

                return redirect("students:list")

            except ValidationError as e:

                form.add_error(None, e)

    else:

        form = StudentCreationForm(
            institution=institution,
        )

    return render(
        request,
        "students/student_form.html",
        {
            "form": form,
            "is_update": False,
        },
    )


@manager_required
def student_update(request, pk):

    institution = _get_institution(request)

    student = get_object_or_404(
        Student.objects.select_related("user"),
        pk=pk,
        institution=institution,
    )

    if request.method == "POST":

        form = StudentCreationForm(
            request.POST,
            is_update=True,
            institution=institution,
        )

        if form.is_valid():

            try:

                StudentService.update_student(
                    student=student,
                    username=form.cleaned_data["username"],
                    password=form.cleaned_data["password"],
                    first_name=form.cleaned_data["first_name"],
                    last_name=form.cleaned_data["last_name"],
                    institution=institution,
                    classroom=form.cleaned_data["classroom"],
                    student_code=form.cleaned_data["student_code"],
                    gender=form.cleaned_data["gender"],
                    date_of_birth=form.cleaned_data["date_of_birth"],
                    address=form.cleaned_data["address"],
                    parent_phone=form.cleaned_data["parent_phone"],
                )

                messages.success(
                    request,
                    _("Student updated successfully."),
                )

                return redirect("students:list")

            except ValidationError as e:

                form.add_error(None, e)

    else:

        form = StudentCreationForm(
            initial={
                "username": student.user.username,
                "first_name": student.user.first_name,
                "last_name": student.user.last_name,
                "student_code": student.student_code,
                "institution": institution,
                "classroom": student.classroom,
                "gender": student.gender,
                "date_of_birth": student.date_of_birth,
                "address": student.address,
                "parent_phone": student.parent_phone,
            },
            is_update=True,
            institution=institution,
        )

    return render(
        request,
        "students/student_form.html",
        {
            "form": form,
            "is_update": True,
        },
    )


@manager_required
def student_import(request):

    institution = _get_institution(request)

    if institution is None:

        messages.warning(
            request,
            _("Please select an institution first."),
        )

        return redirect("institutions:select")

    import_result = None

    if request.method == "POST":

        form = StudentsImportForm(
            request.POST,
            request.FILES,
            institution=institution,
        )

        if form.is_valid():

            try:

                import_result = StudentService.import_students(
                    excel_file=form.cleaned_data["excel_file"],
                    institution=institution,
                    classroom=form.cleaned_data["classroom"],
                    default_gender=form.cleaned_data["gender"],
                )

                if import_result["created_count"] > 0:

                    _store_credentials(
                        request,
                        import_result["credentials"],
                        institution,
                    )

                    messages.success(
                        request,
                        _(
                            "{count} students imported successfully."
                        ).format(
                            count=import_result["created_count"],
                        ),
                    )

                elif import_result["skipped_count"] == 0 and not import_result["errors"]:

                    messages.warning(
                        request,
                        _(
                            "No student data was found in the file. "
                            "Make sure the file contains student names "
                            "and the first row has column headers."
                        ),
                    )

                if import_result["skipped_count"] > 0:

                    messages.warning(
                        request,
                        _(
                            "{count} rows were skipped."
                        ).format(
                            count=import_result["skipped_count"],
                        ),
                    )

            except ExcelImportError as e:

                messages.error(
                    request,
                    "; ".join(e.messages),
                )

            except Exception:

                messages.error(
                    request,
                    _(
                        "An unexpected error occurred while importing students."
                    ),
                )

    else:

        form = StudentsImportForm(
            institution=institution,
        )

    return render(
        request,
        "students/import.html",
        {
            "form": form,
            "import_result": import_result,
        },
    )


@manager_required
def student_created(request):

    data = request.session.get("student_credentials")

    if not data or not data.get("credentials"):

        return redirect("students:list")

    return render(
        request,
        "students/created.html",
        {
            "data": data,
        },
    )


@manager_required
def student_credentials_pdf(request):

    data = request.session.get("student_credentials")

    if not data or not data.get("credentials"):

        messages.info(
            request,
            _("No recent student credentials found to download."),
        )

        return redirect("students:list")

    generated_at = None

    try:

        generated_at = datetime.fromisoformat(data["at"])

    except (KeyError, TypeError, ValueError):
        pass

    buffer = io.BytesIO()

    try:

        build_credentials_pdf(
            buffer,
            institution=data["institution"],
            credentials=data["credentials"],
            generated_at=generated_at,
        )

    except Exception:

        messages.error(
            request,
            _(
                "Could not generate the PDF file. "
                "Please try again."
            ),
        )

        return redirect("students:created")

    buffer.seek(0)

    response = HttpResponse(
        buffer.read(),
        content_type="application/pdf",
    )

    response["Content-Disposition"] = (
        'attachment; filename="student-credentials.pdf"'
    )

    return response


@manager_required
def student_delete(request, pk):

    institution = _get_institution(request)

    student = get_object_or_404(
        Student.objects.select_related("user"),
        pk=pk,
        institution=institution,
    )

    if request.method == "POST":

        student_name = (
            student.user.get_full_name()
            or student.student_code
        )

        institution = student.institution

        student.user.delete()

        NotificationService.notify_institution_managers(
            institution,
            ntype=NotificationService.Type.STUDENT,
            title=_("Student removed"),
            message=_(
                "Student {name} has been removed."
            ).format(
                name=student_name,
            ),
            link="/students/",
        )

        messages.success(
            request,
            _("Student deleted successfully."),
        )

        return redirect("students:list")

    return render(
        request,
        "students/student_confirm_delete.html",
        {
            "student": student,
        },
    )

@student_required
def student_subjects(request):

    student = get_object_or_404(
        Student,
        user=request.user,
    )

    subjects = []

    if student.classroom:
        subjects = student.classroom.subjects.all()

    return render(
        request,
        "students/subjects.html",
        {
            "student": student,
            "subjects": subjects,
        },
    )


@student_required
def student_grades(request):

    student = get_object_or_404(
        Student,
        user=request.user,
    )

    grades = student.grades.select_related(
        "subject",
        "teacher",
    )

    return render(
        request,
        "students/grades.html",
        {
            "student": student,
            "grades": grades,
        },
    )


@student_required
def student_attendance(request):

    student = get_object_or_404(
        Student,
        user=request.user,
    )

    attendance = student.attendance_records.select_related(
        "subject",
        "teacher",
    )

    return render(
        request,
        "students/attendance.html",
        {
            "student": student,
            "attendance": attendance,
        },
    )


@student_required
def student_profile(request):

    student = get_object_or_404(
        Student,
        user=request.user,
    )

    return render(
        request,
        "students/profile.html",
        {
            "student": student,
        },
    )
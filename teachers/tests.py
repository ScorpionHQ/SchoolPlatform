import io
from datetime import date

from django.test import TestCase
from django.urls import reverse
from openpyxl import Workbook

from accounts.models import User
from classes.models import ClassRoom
from grades.models import Grade
from institutions.models import Institution
from parents.models import Parent
from students.models import Student
from subjects.models import Subject
from teachers.models import Teacher


class TeacherPortalTests(TestCase):

    def setUp(self):

        self.institution = Institution.objects.create(
            name="Test School",
            short_name="TS",
        )

        self.classroom = ClassRoom.objects.create(
            name="Grade 5",
            institution=self.institution,
        )

        self.teacher_user = User.objects.create_user(
            username="teacher",
            password="teacherpass123",
            role=User.Role.TEACHER,
        )

        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            institution=self.institution,
            employee_code="TCH000001",
        )

        self.subject = Subject.objects.create(
            name="Mathematics",
            institution=self.institution,
            teacher=self.teacher,
            classroom=self.classroom,
        )

        self.student_user = User.objects.create_user(
            username="student",
            password="studentpass123",
            role=User.Role.STUDENT,
        )

        self.student = Student.objects.create(
            user=self.student_user,
            institution=self.institution,
            classroom=self.classroom,
            student_code="S000001",
        )

    def test_teacher_dashboard(self):

        self.client.force_login(self.teacher_user)

        response = self.client.get(
            reverse("teachers:dashboard"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "لوحة المعلم")

    def test_my_students(self):

        self.client.force_login(self.teacher_user)

        response = self.client.get(
            reverse("teachers:my_students"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "S000001")

    def test_enter_grades(self):

        self.client.force_login(self.teacher_user)

        response = self.client.get(
            reverse("teachers:enter_grades"),
        )

        self.assertEqual(response.status_code, 200)

    def test_teacher_cannot_access_manager_pages(self):

        self.client.force_login(self.teacher_user)

        response = self.client.get(
            reverse("students:list"),
        )

        self.assertEqual(response.status_code, 403)


class ParentPortalTests(TestCase):

    def setUp(self):

        self.institution = Institution.objects.create(
            name="Test School",
            short_name="TS",
        )

        self.classroom = ClassRoom.objects.create(
            name="Grade 5",
            institution=self.institution,
        )

        self.parent_user = User.objects.create_user(
            username="parent",
            password="parentpass123",
            role=User.Role.PARENT,
        )

        self.parent = Parent.objects.create(
            user=self.parent_user,
        )

        self.student_user = User.objects.create_user(
            username="student",
            password="studentpass123",
            role=User.Role.STUDENT,
        )

        self.student = Student.objects.create(
            user=self.student_user,
            institution=self.institution,
            classroom=self.classroom,
            student_code="S000001",
        )

        self.parent.students.add(self.student)

        self.subject = Subject.objects.create(
            name="Mathematics",
            institution=self.institution,
            classroom=self.classroom,
        )

    def test_parent_dashboard(self):

        self.client.force_login(self.parent_user)

        response = self.client.get(
            reverse("parent_dashboard"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "أبنائي")

    def test_parent_children(self):

        self.client.force_login(self.parent_user)

        response = self.client.get(
            reverse("parent_children"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "S000001")

    def test_parent_cannot_access_teacher_pages(self):

        self.client.force_login(self.parent_user)

        response = self.client.get(
            reverse("teachers:dashboard"),
        )

        self.assertEqual(response.status_code, 403)


class GradeAndAttendanceTests(TestCase):

    def setUp(self):

        self.institution = Institution.objects.create(
            name="Test School",
            short_name="TS",
        )

        self.classroom = ClassRoom.objects.create(
            name="Grade 5",
            institution=self.institution,
        )

        self.student_user = User.objects.create_user(
            username="student",
            password="studentpass123",
            role=User.Role.STUDENT,
        )

        self.student = Student.objects.create(
            user=self.student_user,
            institution=self.institution,
            classroom=self.classroom,
            student_code="S000001",
        )

        self.subject = Subject.objects.create(
            name="Mathematics",
            institution=self.institution,
            classroom=self.classroom,
        )

    def test_grade_creation(self):

        grade = Grade.objects.create(
            student=self.student,
            subject=self.subject,
            exam_name="Midterm",
            score=95,
            max_score=100,
            exam_date=date(2026, 1, 15),
        )

        self.assertEqual(
            Grade.objects.filter(student=self.student).count(),
            1,
        )
        self.assertEqual(grade.score, 95)

    def test_unique_grade_constraint(self):

        Grade.objects.create(
            student=self.student,
            subject=self.subject,
            exam_name="Midterm",
            score=95,
            max_score=100,
            exam_date=date(2026, 1, 15),
        )

        with self.assertRaises(Exception):
            Grade.objects.create(
                student=self.student,
                subject=self.subject,
                exam_name="Midterm",
                score=80,
                max_score=100,
                exam_date=date(2026, 2, 15),
            )

    def test_student_dashboard_shows_grades(self):

        self.client.force_login(self.student_user)

        response = self.client.get(
            reverse("student_dashboard"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "لوحة الطالب")


class EnterGradesPostTests(TestCase):

    def setUp(self):

        self.institution = Institution.objects.create(
            name="Test School",
            short_name="TS",
        )

        self.other_institution = Institution.objects.create(
            name="Other School",
            short_name="OS",
        )

        self.classroom = ClassRoom.objects.create(
            name="Grade 5",
            institution=self.institution,
        )

        self.other_classroom = ClassRoom.objects.create(
            name="Grade 6",
            institution=self.other_institution,
        )

        self.teacher_user = User.objects.create_user(
            username="teacher",
            password="teacherpass123",
            role=User.Role.TEACHER,
        )

        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            institution=self.institution,
            employee_code="TCH000002",
        )

        self.subject = Subject.objects.create(
            name="Mathematics",
            institution=self.institution,
            teacher=self.teacher,
            classroom=self.classroom,
        )

        self.other_teacher_user = User.objects.create_user(
            username="teacher2",
            password="teacherpass123",
            role=User.Role.TEACHER,
        )

        self.other_teacher = Teacher.objects.create(
            user=self.other_teacher_user,
            institution=self.institution,
            employee_code="TCH000003",
        )

        self.other_subject = Subject.objects.create(
            name="Science",
            institution=self.institution,
            teacher=self.other_teacher,
            classroom=self.classroom,
        )

        self.student_user = User.objects.create_user(
            username="student",
            password="studentpass123",
            role=User.Role.STUDENT,
        )

        self.student = Student.objects.create(
            user=self.student_user,
            institution=self.institution,
            classroom=self.classroom,
            student_code="S000001",
        )

        self.foreign_student = Student.objects.create(
            user=User.objects.create_user(
                username="foreign",
                password="studentpass123",
                role=User.Role.STUDENT,
            ),
            institution=self.other_institution,
            classroom=self.other_classroom,
            student_code="S000002",
        )

        self.client.force_login(self.teacher_user)

    def _post(self, **overrides):

        data = {
            "subject_id": self.subject.pk,
            "student_id": self.student.pk,
            "exam_name": "Midterm",
            "score": "90",
            "max_score": "100",
            "exam_date": "2026-06-01",
            "note": "",
        }

        data.update(overrides)

        return self.client.post(
            reverse("teachers:enter_grades"),
            data,
        )

    def _redirect_target(self, response):

        return response.url.split("?")[0]

    def test_valid_post_creates_grade(self):

        response = self._post()

        self.assertEqual(response.status_code, 302)

        grade = Grade.objects.get(student=self.student)

        self.assertEqual(grade.subject, self.subject)
        self.assertEqual(grade.score, 90)
        self.assertEqual(grade.max_score, 100)
        self.assertEqual(grade.teacher, self.teacher)

    def test_valid_post_updates_existing_grade(self):

        Grade.objects.create(
            student=self.student,
            subject=self.subject,
            exam_name="Midterm",
            score=80,
            max_score=100,
            exam_date=date(2026, 6, 1),
        )

        self._post(score="95")

        self.assertEqual(
            Grade.objects.filter(
                student=self.student,
                subject=self.subject,
                exam_name="Midterm",
            ).count(),
            1,
        )

        grade = Grade.objects.get(
            student=self.student,
            subject=self.subject,
            exam_name="Midterm",
        )

        self.assertEqual(grade.score, 95)

    def test_missing_student_id_rejected(self):

        response = self._post(student_id="")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Grade.objects.count(), 0)

    def test_student_from_other_institution_rejected(self):

        response = self._post(student_id=self.foreign_student.pk)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Grade.objects.count(), 0)

    def test_empty_exam_name_rejected(self):

        response = self._post(exam_name="   ")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Grade.objects.count(), 0)

    def test_non_numeric_score_rejected(self):

        response = self._post(score="abc")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Grade.objects.count(), 0)

    def test_max_score_zero_rejected(self):

        response = self._post(max_score="0")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Grade.objects.count(), 0)

    def test_score_above_max_rejected(self):

        response = self._post(score="150")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Grade.objects.count(), 0)

    def test_negative_score_rejected(self):

        response = self._post(score="-5")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Grade.objects.count(), 0)

    def test_subject_belongs_to_another_teacher(self):

        response = self._post(subject_id=self.other_subject.pk)

        self.assertEqual(response.status_code, 404)


class ExcelFileImportHelperTests(TestCase):

    def test_header_normalization_arabic_variants(self):

        from students.services import StudentService

        self.assertEqual(
            StudentService._normalize_header("أسماء الطالبات"),
            "اسما الطالبات",
        )

        self.assertEqual(
            StudentService._normalize_header("الاسم الأول"),
            "الاسم الاول",
        )

        self.assertEqual(
            StudentService._normalize_header("الاسم الكامل"),
            "الاسم الكامل",
        )

    def test_full_name_split(self):

        from students.services import StudentService

        first_name, last_name = StudentService._split_full_name(
            "احلام جاسم محمد ناصر",
        )

        self.assertEqual(first_name, "احلام")
        self.assertEqual(last_name, "جاسم محمد ناصر")

    def test_header_map_full_name_alias(self):

        from students.services import StudentService

        header_map = StudentService._build_header_map(
            ["التسلسل", "أسماء الطالبات", "الدرجة النهائية"],
        )

        self.assertIn("full_name", header_map)
        self.assertEqual(
            header_map["full_name"],
            1,
        )

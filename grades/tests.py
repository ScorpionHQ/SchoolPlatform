from datetime import date

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from classes.models import ClassRoom
from institutions.models import Institution
from notifications.models import Notification
from students.models import Student
from subjects.models import Subject
from teachers.models import Teacher

from .forms import GradeForm
from .models import Grade
from .services import GradeService


class GradeModelTests(TestCase):

    def setUp(self):

        self.institution = Institution.objects.create(
            name="Test School",
            short_name="TS",
        )

        self.student_user = User.objects.create_user(
            username="student",
            password="pass123",
            role=User.Role.STUDENT,
        )

        self.student = Student.objects.create(
            user=self.student_user,
            institution=self.institution,
            student_code="S000001",
        )

        self.subject = Subject.objects.create(
            name="Mathematics",
            institution=self.institution,
        )

    def test_unique_grade_per_exam(self):

        Grade.objects.create(
            student=self.student,
            subject=self.subject,
            exam_name="Midterm",
            score=90,
            max_score=100,
            exam_date=date(2026, 6, 1),
        )

        duplicate = Grade(
            student=self.student,
            subject=self.subject,
            exam_name="Midterm",
            score=80,
            max_score=100,
            exam_date=date(2026, 6, 1),
        )

        with self.assertRaises(Exception):

            duplicate.save()


class GradeServiceTests(TestCase):

    def setUp(self):

        self.institution = Institution.objects.create(
            name="Test School",
            short_name="TS",
        )

        self.manager = User.objects.create_user(
            username="manager",
            password="pass123",
            role=User.Role.MANAGER,
        )

        self.manager.institutions.add(self.institution)

        self.student_user = User.objects.create_user(
            username="student",
            password="pass123",
            role=User.Role.STUDENT,
        )

        self.student = Student.objects.create(
            user=self.student_user,
            institution=self.institution,
            student_code="S000001",
        )

        self.subject = Subject.objects.create(
            name="Mathematics",
            institution=self.institution,
        )

    def test_create_grade_notifies_student(self):

        data = {
            "student": self.student.pk,
            "subject": self.subject.pk,
            "teacher": "",
            "exam_name": "Midterm",
            "score": "90",
            "max_score": "100",
            "exam_date": "2026-06-01",
            "note": "",
        }

        form = GradeForm(
            data,
            institution=self.institution,
        )

        self.assertTrue(
            form.is_valid(),
            form.errors,
        )

        grade = GradeService.create_grade(form)

        self.assertEqual(grade.score, 90)

        self.assertTrue(
            Notification.objects.filter(
                user=self.student_user,
                type=Notification.Type.GRADE,
            ).exists()
        )


class GradeViewTests(TestCase):

    def setUp(self):

        self.institution = Institution.objects.create(
            name="Test School",
            short_name="TS",
        )

        self.manager = User.objects.create_user(
            username="manager",
            password="pass123",
            role=User.Role.MANAGER,
        )

        self.manager.institutions.add(self.institution)

        self.student_user = User.objects.create_user(
            username="student",
            password="pass123",
            role=User.Role.STUDENT,
        )

        self.student = Student.objects.create(
            user=self.student_user,
            institution=self.institution,
            student_code="S000001",
        )

        self.subject = Subject.objects.create(
            name="Mathematics",
            institution=self.institution,
        )

    def test_teacher_cannot_access_grades(self):

        teacher = User.objects.create_user(
            username="teacher",
            password="pass123",
            role=User.Role.TEACHER,
        )

        self.client.force_login(teacher)

        response = self.client.get(reverse("grades:list"))

        self.assertEqual(response.status_code, 403)

    def test_manager_can_create_grade(self):

        self.client.force_login(self.manager)

        response = self.client.post(
            reverse("grades:create"),
            {
                "student": self.student.pk,
                "subject": self.subject.pk,
                "teacher": "",
                "exam_name": "Midterm",
                "score": "90",
                "max_score": "100",
                "exam_date": "2026-06-01",
                "note": "",
            },
        )

        self.assertRedirects(
            response,
            reverse("grades:list"),
        )

        self.assertTrue(
            Grade.objects.filter(
                student=self.student,
                exam_name="Midterm",
            ).exists()
        )

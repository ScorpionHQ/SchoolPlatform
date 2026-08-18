from datetime import date

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase
from django.urls import reverse

from accounts.models import User
from classes.models import ClassRoom
from grades.models import Grade
from institutions.models import Institution
from parents.models import Parent
from students.models import Student
from subjects.models import Subject


class ManagerDashboardTests(TestCase):

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

        self.classroom = ClassRoom.objects.create(
            name="Grade 5",
            institution=self.institution,
            level="5",
            academic_year="2026",
        )

        self.student_user = User.objects.create_user(
            username="student",
            password="pass123",
            first_name="Sami",
            role=User.Role.STUDENT,
        )

        self.student = Student.objects.create(
            user=self.student_user,
            institution=self.institution,
            classroom=self.classroom,
            student_code="S000001",
        )

    def test_manager_dashboard_requires_login(self):

        response = self.client.get(
            reverse("manager_dashboard"),
        )

        self.assertEqual(response.status_code, 302)

    def test_manager_dashboard_shows_institution_stats(self):

        self.client.force_login(self.manager)

        response = self.client.get(
            reverse("manager_dashboard"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test School")

    def test_student_blocked_from_manager_dashboard(self):

        self.client.force_login(self.student_user)

        response = self.client.get(
            reverse("manager_dashboard"),
        )

        self.assertEqual(response.status_code, 403)


class StudentDashboardTests(TestCase):

    def setUp(self):

        self.institution = Institution.objects.create(
            name="Test School",
            short_name="TS",
        )

        self.student_user = User.objects.create_user(
            username="student",
            password="pass123",
            first_name="Sami",
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

        Grade.objects.create(
            student=self.student,
            subject=self.subject,
            exam_name="Midterm",
            score=90,
            max_score=100,
            exam_date=date(2026, 6, 1),
        )

    def test_student_dashboard_shows_average(self):

        self.client.force_login(self.student_user)

        response = self.client.get(
            reverse("student_dashboard"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "90")


class ParentDashboardTests(TestCase):

    def setUp(self):

        self.institution = Institution.objects.create(
            name="Test School",
            short_name="TS",
        )

        self.student_user = User.objects.create_user(
            username="student",
            password="pass123",
            first_name="Sami",
            role=User.Role.STUDENT,
        )

        self.student = Student.objects.create(
            user=self.student_user,
            institution=self.institution,
            student_code="S000001",
        )

        self.parent_user = User.objects.create_user(
            username="parent",
            password="pass123",
            first_name="Ali",
            role=User.Role.PARENT,
        )

        parent = Parent.objects.create(
            user=self.parent_user,
        )

        parent.students.add(self.student)

    def test_parent_dashboard_lists_children(self):

        self.client.force_login(self.parent_user)

        response = self.client.get(
            reverse("parent_dashboard"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sami")

    def test_student_blocked_from_parent_dashboard(self):

        self.client.force_login(self.student_user)

        response = self.client.get(
            reverse("parent_dashboard"),
        )

        self.assertEqual(response.status_code, 403)


class ErrorHandlerTests(TestCase):

    def test_404_renders_custom_page(self):

        response = self.client.get("/this-page-does-not-exist/")

        self.assertEqual(response.status_code, 404)

    def test_dashboard_redirects_anonymous_to_login(self):

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(
            reverse("login"),
            response.url,
        )


class ErrorHandlerViewFunctionTests(TestCase):

    def setUp(self):

        self.request = RequestFactory().get("/error/")

        self.request.user = AnonymousUser()

    def test_error_400_uses_400_template(self):

        from .views import error_400

        response = error_400(self.request)

        self.assertEqual(response.status_code, 400)
        self.assertContains(
            response,
            "⚠️",
            status_code=400,
        )
        self.assertNotContains(
            response,
            "🔍",
            status_code=400,
        )

    def test_error_403_uses_403_template(self):

        from .views import error_403

        response = error_403(self.request)

        self.assertEqual(response.status_code, 403)
        self.assertContains(
            response,
            "🚫",
            status_code=403,
        )

    def test_error_404_uses_404_template(self):

        from .views import error_404

        response = error_404(self.request)

        self.assertEqual(response.status_code, 404)
        self.assertContains(
            response,
            "🔍",
            status_code=404,
        )

    def test_error_500_uses_500_template(self):

        from .views import error_500

        response = error_500(self.request)

        self.assertEqual(response.status_code, 500)
        self.assertContains(
            response,
            "⚠️",
            status_code=500,
        )

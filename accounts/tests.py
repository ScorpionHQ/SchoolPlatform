from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from institutions.models import Institution
from parents.models import Parent
from students.models import Student
from teachers.models import Teacher

from .models import User


class LoginTests(TestCase):

    def setUp(self):

        self.institution = Institution.objects.create(
            name="Test School",
            short_name="TS",
        )

        self.admin = User.objects.create_user(
            username="admin",
            password="adminpass123",
            first_name="Admin",
            role=User.Role.SYSTEM_ADMIN,
        )

        self.teacher = User.objects.create_user(
            username="teacher",
            password="teacherpass123",
            first_name="Teacher",
            role=User.Role.TEACHER,
        )

        Teacher.objects.create(
            user=self.teacher,
            institution=self.institution,
            employee_code="TCH000001",
        )

        self.student = User.objects.create_user(
            username="student",
            password="studentpass123",
            first_name="Student",
            role=User.Role.STUDENT,
        )

        self.parent = User.objects.create_user(
            username="parent",
            password="parentpass123",
            first_name="Parent",
            role=User.Role.PARENT,
        )

    def test_login_with_correct_credentials(self):

        response = self.client.post(
            reverse("login"),
            {
                "login_code": self.admin.login_code,
                "password": "adminpass123",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("dashboard"))

    def test_login_with_wrong_password(self):

        response = self.client.post(
            reverse("login"),
            {
                "login_code": self.admin.login_code,
                "password": "wrongpass",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "تسجيل الدخول")

    def test_login_with_unknown_code(self):

        response = self.client.post(
            reverse("login"),
            {
                "login_code": "SYS999999",
                "password": "adminpass123",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(
            "_auth_user_id",
            self.client.session,
        )

    def test_login_redirects_by_role(self):

        cases = {
            self.teacher: reverse("teachers:dashboard"),
            self.student: reverse("student_dashboard"),
            self.parent: reverse("parent_dashboard"),
        }

        for user, expected_url in cases.items():

            self.client.logout()

            response = self.client.post(
                reverse("login"),
                {
                    "login_code": user.login_code,
                    "password": {
                        self.teacher: "teacherpass123",
                        self.student: "studentpass123",
                        self.parent: "parentpass123",
                    }[user],
                },
            )

            self.assertRedirects(
                response,
                expected_url,
                fetch_redirect_response=False,
            )

    def test_logout(self):

        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("logout"),
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("login"))
        self.assertNotIn(
            "_auth_user_id",
            self.client.session,
        )

    def test_logout_get_rejected(self):

        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("logout"),
        )

        self.assertEqual(response.status_code, 405)


class ProfileTests(TestCase):

    def setUp(self):

        self.institution = Institution.objects.create(
            name="Test School",
            short_name="TS",
        )

        self.student_user = User.objects.create_user(
            username="student",
            password="studentpass123",
            role=User.Role.STUDENT,
        )

        Student.objects.create(
            user=self.student_user,
            institution=self.institution,
            student_code="S000001",
        )

        self.parent_user = User.objects.create_user(
            username="parent",
            password="parentpass123",
            role=User.Role.PARENT,
        )

        Parent.objects.create(
            user=self.parent_user,
        )

        self.teacher_user = User.objects.create_user(
            username="teacher",
            password="teacherpass123",
            role=User.Role.TEACHER,
        )

        Teacher.objects.create(
            user=self.teacher_user,
            institution=self.institution,
            employee_code="TCH000001",
        )

        self.manager = User.objects.create_user(
            username="manager",
            password="managerpass123",
            role=User.Role.MANAGER,
        )

    def test_profile_requires_login(self):

        response = self.client.get(
            reverse("profile"),
        )

        self.assertEqual(response.status_code, 302)

    def test_student_profile(self):

        self.student_user.profile_image = SimpleUploadedFile(
            "test.jpg", b"\xff\xd8\xff\xe0", content_type="image/jpeg"
        )
        self.student_user.save(update_fields=["profile_image"])

        self.client.force_login(self.student_user)

        response = self.client.get(
            reverse("profile"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "My Profile")

    def test_manager_profile(self):

        self.client.force_login(self.manager)

        response = self.client.get(
            reverse("profile"),
        )

        self.assertEqual(response.status_code, 200)


class PasswordChangeTests(TestCase):

    def setUp(self):

        self.user = User.objects.create_user(
            username="student",
            password="oldpass123",
            first_name="Student",
            role=User.Role.STUDENT,
            must_change_password=True,
        )

    def test_force_password_change_middleware_redirects(self):

        self.client.force_login(self.user)

        response = self.client.get(
            reverse("student_dashboard"),
        )

        self.assertRedirects(
            response,
            reverse("change_password"),
        )

    def test_change_password_success(self):

        self.client.force_login(self.user)

        response = self.client.post(
            reverse("change_password"),
            {
                "current_password": "oldpass123",
                "new_password": "newpass123",
                "confirm_password": "newpass123",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.user.refresh_from_db()
        self.assertFalse(self.user.must_change_password)
        self.assertTrue(self.user.check_password("newpass123"))

    def test_change_password_wrong_current(self):

        self.client.force_login(self.user)

        response = self.client.post(
            reverse("change_password"),
            {
                "current_password": "wrongpass",
                "new_password": "newpass123",
                "confirm_password": "newpass123",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.must_change_password)

    def test_change_password_mismatch(self):

        self.client.force_login(self.user)

        response = self.client.post(
            reverse("change_password"),
            {
                "current_password": "oldpass123",
                "new_password": "newpass123",
                "confirm_password": "different123",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.must_change_password)


class RoleAccessTests(TestCase):

    def setUp(self):

        self.manager = User.objects.create_user(
            username="manager",
            password="managerpass123",
            role=User.Role.MANAGER,
        )

        self.teacher = User.objects.create_user(
            username="teacher",
            password="teacherpass123",
            role=User.Role.TEACHER,
        )

        self.student = User.objects.create_user(
            username="student",
            password="studentpass123",
            role=User.Role.STUDENT,
        )

    def test_teacher_dashboard_blocks_student(self):

        self.client.force_login(self.student)

        response = self.client.get(
            reverse("teachers:dashboard"),
        )

        self.assertEqual(response.status_code, 403)

    def test_student_dashboard_blocks_teacher(self):

        self.client.force_login(self.teacher)

        response = self.client.get(
            reverse("student_dashboard"),
        )

        self.assertEqual(response.status_code, 403)

    def test_manager_dashboard_redirects_student_to_student_panel(self):

        self.client.force_login(self.student)

        response = self.client.get(
            reverse("dashboard"),
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse("student_dashboard"),
            fetch_redirect_response=False,
        )

    def test_manager_dashboard_redirects_teacher_to_teacher_panel(self):

        self.client.force_login(self.teacher)

        response = self.client.get(
            reverse("dashboard"),
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse("teachers:dashboard"),
            fetch_redirect_response=False,
        )

    def test_anonymous_access_redirects_to_login(self):

        response = self.client.get(
            reverse("dashboard"),
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(
            reverse("login"),
            response.url,
        )

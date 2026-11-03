import os
import shutil
import tempfile
from io import BytesIO
from unittest import mock

from django.contrib.messages import get_messages
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from PIL import Image

from institutions.models import Institution
from parents.models import Parent
from students.models import Student
from teachers.models import Teacher

from .models import AuditLog, User


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

        cache.clear()

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

        self.assertTrue(
            AuditLog.objects.filter(
                action=AuditLog.Action.LOGIN,
                user=self.admin,
            ).exists()
        )

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

        self.assertTrue(
            AuditLog.objects.filter(
                action=AuditLog.Action.LOGOUT,
                user=self.admin,
            ).exists()
        )

    def test_logout_get_rejected(self):

        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("logout"),
        )

        self.assertEqual(response.status_code, 405)


@override_settings(
    LOGIN_MAX_ATTEMPTS=3,
    LOGIN_LOCKOUT_SECONDS=900,
)
class LoginRateLimitTests(TestCase):

    def setUp(self):

        cache.clear()

        self.addCleanup(cache.clear)

        self.institution = Institution.objects.create(
            name="Rate Limit School",
            short_name="RL",
        )

        self.user = User.objects.create_user(
            username="rate-limit-user",
            password="correctpass123",
            role=User.Role.SYSTEM_ADMIN,
        )

    def _post(self, login_code=None, password="wrongpass"):

        return self.client.post(
            reverse("login"),
            {
                "login_code": login_code or self.user.login_code,
                "password": password,
            },
        )

    def test_login_is_blocked_after_too_many_failures(self):

        for _ in range(3):
            self.assertEqual(self._post().status_code, 200)

        response = self._post()

        self.assertEqual(response.status_code, 429)
        self.assertContains(response, "محاولات", status_code=429)

    def test_correct_password_is_blocked_while_locked(self):

        for _ in range(3):
            self._post()

        response = self._post(password="correctpass123")

        self.assertEqual(response.status_code, 429)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_successful_login_clears_failures(self):

        self._post()
        self._post()

        response = self._post(password="correctpass123")

        self.assertEqual(response.status_code, 302)

        self.client.logout()

        self.assertEqual(self._post().status_code, 200)
        self.assertEqual(self._post().status_code, 200)
        self.assertEqual(self._post().status_code, 200)

    def test_many_codes_from_one_ip_are_blocked(self):

        for index in range(15):

            self._post(login_code=f"SYS99999{index:02d}")

        response = self._post()

        self.assertEqual(response.status_code, 429)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class PasswordResetTests(TestCase):

    def setUp(self):

        cache.clear()

        self.user = User.objects.create_user(
            username="reset-user",
            password="oldpass12345",
            email="reset@example.com",
            role=User.Role.TEACHER,
            must_change_password=True,
        )

    def _request_reset(self, login_code=None):

        return self.client.post(
            reverse("password_reset"),
            {
                "login_code": login_code or self.user.login_code,
            },
        )

    def _confirm_url(self):

        return reverse(
            "password_reset_confirm",
            kwargs={
                "uidb64": urlsafe_base64_encode(
                    force_bytes(self.user.pk),
                ),
                "token": default_token_generator.make_token(self.user),
            },
        )

    def test_request_sends_one_email(self):

        response = self._request_reset()

        self.assertRedirects(
            response,
            reverse("login"),
            fetch_redirect_response=False,
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["reset@example.com"])
        self.assertIn(
            "password-reset/",
            mail.outbox[0].body,
        )

    def test_unknown_code_sends_nothing(self):

        response = self._request_reset(login_code="SYS999999")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 0)

    def test_account_without_email_sends_nothing(self):

        self.user.email = ""
        self.user.save(update_fields=["email"])

        response = self._request_reset()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 0)

    def test_valid_link_sets_new_password(self):

        response = self.client.get(
            self._confirm_url(),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)

        confirm_url = response.redirect_chain[-1][0]

        response = self.client.post(
            confirm_url,
            {
                "new_password": "NewStrongPass!2026",
                "confirm_password": "NewStrongPass!2026",
            },
        )

        self.assertRedirects(
            response,
            reverse("login"),
            fetch_redirect_response=False,
        )

        self.user.refresh_from_db()

        self.assertTrue(
            self.user.check_password("NewStrongPass!2026"),
        )
        self.assertFalse(self.user.must_change_password)

    def test_invalid_link_shows_a_message(self):

        response = self.client.get(
            reverse(
                "password_reset_confirm",
                kwargs={
                    "uidb64": "abc",
                    "token": "invalid-token",
                },
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "غير صالح")


class BootstrapAdminCommandTests(TestCase):

    def _run(self, **env):

        from io import StringIO

        from django.core.management import call_command

        out = StringIO()

        with mock.patch.dict(os.environ, env, clear=False):

            call_command(
                "bootstrap_admin",
                stdout=out,
            )

        return out.getvalue()

    def test_creates_the_first_system_admin(self):

        output = self._run(BOOTSTRAP_ADMIN_PASSWORD="TempPass!2026")

        user = User.objects.get(role=User.Role.SYSTEM_ADMIN)

        self.assertEqual(user.username, "admin")
        self.assertTrue(user.login_code.startswith("SYS"))
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.must_change_password)
        self.assertTrue(user.check_password("TempPass!2026"))
        self.assertIn("Created", output)

    def test_does_nothing_without_a_password(self):

        self._run()

        self.assertFalse(
            User.objects.filter(role=User.Role.SYSTEM_ADMIN).exists()
        )

    def test_is_idempotent(self):

        self._run(BOOTSTRAP_ADMIN_PASSWORD="TempPass!2026")
        self._run(BOOTSTRAP_ADMIN_PASSWORD="AnotherPass!2026")

        self.assertEqual(
            User.objects.filter(role=User.Role.SYSTEM_ADMIN).count(),
            1,
        )


class MissingProfileMiddlewareTests(TestCase):

    def setUp(self):

        self.institution = Institution.objects.create(
            name="Missing Profile School",
            short_name="MP",
        )

        self.student_user = User.objects.create_user(
            username="no-profile-student",
            password="studentpass123",
            role=User.Role.STUDENT,
        )

    def test_student_without_profile_is_redirected(self):

        self.client.force_login(self.student_user)

        response = self.client.get(
            reverse("student_dashboard"),
            HTTP_ACCEPT="text/html",
        )

        self.assertRedirects(
            response,
            reverse("profile"),
            fetch_redirect_response=False,
        )

    def test_profile_page_is_still_reachable(self):

        self.client.force_login(self.student_user)

        response = self.client.get(
            reverse("profile"),
            HTTP_ACCEPT="text/html",
        )

        self.assertEqual(response.status_code, 200)

    def test_non_html_requests_are_not_intercepted(self):

        self.client.force_login(self.student_user)

        response = self.client.post(
            reverse("logout"),
            HTTP_ACCEPT="application/json",
        )

        self.assertRedirects(
            response,
            reverse("login"),
            fetch_redirect_response=False,
        )
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_student_with_profile_is_not_redirected(self):

        Student.objects.create(
            user=self.student_user,
            institution=self.institution,
            student_code="S000900",
        )

        self.client.force_login(self.student_user)

        response = self.client.get(
            reverse("student_dashboard"),
            HTTP_ACCEPT="text/html",
        )

        self.assertEqual(response.status_code, 200)


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
        self.assertContains(response, "ملفي الشخصي")

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


class ProfilePhotoTests(TestCase):

    def setUp(self):

        self.media_root = tempfile.mkdtemp(
            prefix="profile-photo-tests-",
        )

        self.settings_override = override_settings(
            MEDIA_ROOT=self.media_root,
        )
        self.settings_override.enable()

        self.addCleanup(self.settings_override.disable)
        self.addCleanup(
            shutil.rmtree,
            self.media_root,
            True,
        )

        self.institution = Institution.objects.create(
            name="Photo School",
            short_name="PS",
        )

        self.student = User.objects.create_user(
            username="photo-student",
            password="studentpass123",
            first_name="Photo",
            role=User.Role.STUDENT,
        )

        Student.objects.create(
            user=self.student,
            institution=self.institution,
            student_code="S100001",
        )

        self.client.force_login(self.student)

    def _image_bytes(self, size=(1200, 900), image_format="PNG"):

        buffer = BytesIO()

        Image.new(
            "RGB",
            size,
            (20, 40, 60),
        ).save(buffer, format=image_format)

        return buffer.getvalue()

    def _upload(self, content, name="photo.png", content_type="image/png", **extra):

        data = {
            "profile_image": SimpleUploadedFile(
                name,
                content,
                content_type=content_type,
            ),
        }

        data.update(extra)

        return self.client.post(
            reverse("upload_photo"),
            data,
        )

    def test_upload_page_renders(self):

        response = self.client.get(
            reverse("upload_photo"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="photo-input"')

    def test_photo_is_optional(self):

        response = self.client.get(
            reverse("profile"),
        )

        self.assertEqual(response.status_code, 200)

    def test_student_dashboard_is_not_blocked_without_photo(self):

        response = self.client.get(
            reverse("student_dashboard"),
        )

        self.assertEqual(response.status_code, 200)

    def test_upload_valid_photo(self):

        response = self._upload(
            self._image_bytes(),
        )

        self.assertRedirects(
            response,
            reverse("student_dashboard"),
            fetch_redirect_response=False,
        )

        self.student.refresh_from_db()

        self.assertTrue(self.student.profile_image)
        self.assertTrue(
            self.student.profile_image.name.endswith(".jpg"),
        )

    def test_uploaded_photo_is_resized(self):

        self._upload(
            self._image_bytes(size=(2400, 1800)),
        )

        self.student.refresh_from_db()

        with self.student.profile_image.open("rb") as handle:

            image = Image.open(handle)

            self.assertLessEqual(
                max(image.size),
                800,
            )

            self.assertEqual(
                image.format,
                "JPEG",
            )

    def test_rejects_invalid_image(self):

        response = self._upload(
            b"this is not an image",
        )

        self.assertEqual(response.status_code, 200)

        self.student.refresh_from_db()

        self.assertFalse(self.student.profile_image)
        self.assertContains(response, "ليس صورة صالحة")

    def test_rejects_oversized_image(self):

        response = self._upload(
            b"x" * (5 * 1024 * 1024 + 1),
        )

        self.assertEqual(response.status_code, 200)

        self.student.refresh_from_db()

        self.assertFalse(self.student.profile_image)
        self.assertContains(response, "أقل من 5")

    def test_external_next_is_ignored(self):

        response = self._upload(
            self._image_bytes(),
            next="https://evil.example.com/steal",
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("student_dashboard"),
        )

    def test_internal_next_is_used(self):

        response = self._upload(
            self._image_bytes(),
            next=reverse("profile"),
        )

        self.assertRedirects(
            response,
            reverse("profile"),
            fetch_redirect_response=False,
        )

    def test_skip_button_continues(self):

        response = self.client.post(
            reverse("upload_photo"),
            {
                "skip": "1",
            },
        )

        self.assertRedirects(
            response,
            reverse("student_dashboard"),
            fetch_redirect_response=False,
        )

    def test_reminder_message_is_sent_once(self):

        response = self.client.get(
            reverse("profile"),
            HTTP_ACCEPT="text/html",
        )

        messages_list = [
            str(message)
            for message in get_messages(response.wsgi_request)
        ]

        self.assertTrue(
            any("صورة" in message for message in messages_list),
        )

        response = self.client.get(
            reverse("profile"),
            HTTP_ACCEPT="text/html",
        )

        messages_list = [
            str(message)
            for message in get_messages(response.wsgi_request)
        ]

        self.assertFalse(
            any("صورة" in message for message in messages_list),
        )

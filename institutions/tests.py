from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from classes.models import ClassRoom
from students.models import Student

from .models import Institution
from .tenant import SESSION_KEY, institutions_for_user, resolve_institution


class TenantIsolationTests(TestCase):

    def setUp(self):

        self.first_institution = Institution.objects.create(
            name="First School",
            short_name="FS",
        )

        self.second_institution = Institution.objects.create(
            name="Second School",
            short_name="SS",
        )

        self.manager = User.objects.create_user(
            username="manager",
            password="managerpass123",
            role=User.Role.MANAGER,
        )

        self.manager.institutions.add(
            self.first_institution,
            self.second_institution,
        )

        self.other_manager = User.objects.create_user(
            username="other_manager",
            password="managerpass123",
            role=User.Role.MANAGER,
        )

        self.other_manager.institutions.add(
            self.second_institution,
        )

    def test_institutions_for_user_returns_assigned_only(self):

        institutions = institutions_for_user(self.other_manager)

        self.assertEqual(
            list(institutions),
            [self.second_institution],
        )

    def test_system_admin_sees_all_institutions(self):

        admin = User.objects.create_user(
            username="admin",
            password="adminpass123",
            role=User.Role.SYSTEM_ADMIN,
        )

        self.assertEqual(
            institutions_for_user(admin).count(),
            Institution.objects.count(),
        )

    def test_resolve_institution_prefers_session(self):

        available, institution = resolve_institution(
            self.manager,
            {
                SESSION_KEY: self.second_institution.pk,
            },
        )

        self.assertEqual(institution, self.second_institution)

        self.assertEqual(
            set(available),
            {
                self.first_institution,
                self.second_institution,
            },
        )

    def test_resolve_institution_ignores_invalid_session(self):

        available, institution = resolve_institution(
            self.other_manager,
            {
                SESSION_KEY: self.first_institution.pk,
            },
        )

        self.assertNotEqual(institution, self.first_institution)

        self.assertEqual(institution, self.second_institution)

    def test_manager_only_sees_own_students(self):

        first_student = Student.objects.create(
            user=User.objects.create_user(
                username="student1",
                password="studentpass123",
                role=User.Role.STUDENT,
            ),
            institution=self.first_institution,
            student_code="S000001",
        )

        Student.objects.create(
            user=User.objects.create_user(
                username="student2",
                password="studentpass123",
                role=User.Role.STUDENT,
            ),
            institution=self.second_institution,
            student_code="S000002",
        )

        self.client.force_login(self.other_manager)

        session = self.client.session
        session[SESSION_KEY] = self.second_institution.pk
        session.save()

        response = self.client.get(
            reverse("students:list"),
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "S000002")

        self.assertNotContains(response, "S000001")


class ManagerInstitutionSelectionTests(TestCase):

    def setUp(self):

        self.first_institution = Institution.objects.create(
            name="First School",
            short_name="FS",
        )

        self.second_institution = Institution.objects.create(
            name="Second School",
            short_name="SS",
        )

        self.manager = User.objects.create_user(
            username="manager",
            password="managerpass123",
            role=User.Role.MANAGER,
        )

        self.manager.institutions.add(
            self.first_institution,
            self.second_institution,
        )

    def test_manager_login_with_multiple_institutions_goes_to_select(self):

        response = self.client.post(
            reverse("login"),
            {
                "login_code": self.manager.login_code,
                "password": "managerpass123",
            },
        )

        self.assertRedirects(
            response,
            reverse("institutions:select"),
            fetch_redirect_response=False,
        )

    def test_select_page_lists_only_assigned_institutions(self):

        self.client.force_login(self.manager)

        response = self.client.get(
            reverse("institutions:select"),
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "First School")
        self.assertContains(response, "Second School")

    def test_switch_sets_session(self):

        self.client.force_login(self.manager)

        response = self.client.post(
            reverse("institutions:switch"),
            {
                "institution_id": self.second_institution.pk,
            },
        )

        self.assertRedirects(
            response,
            reverse("dashboard"),
            fetch_redirect_response=False,
        )

        self.assertEqual(
            self.client.session[SESSION_KEY],
            self.second_institution.pk,
        )

    def test_switch_rejects_unassigned_institution(self):

        other = Institution.objects.create(
            name="Third School",
            short_name="TS",
        )

        self.client.force_login(self.manager)

        self.client.post(
            reverse("institutions:switch"),
            {
                "institution_id": other.pk,
            },
        )

        self.assertNotEqual(
            self.client.session.get(SESSION_KEY),
            other.pk,
        )


class InstitutionSwitchSecurityTests(TestCase):

    def setUp(self):

        self.institution = Institution.objects.create(
            name="First School",
            short_name="FS",
        )

        self.manager = User.objects.create_user(
            username="manager",
            password="managerpass123",
            role=User.Role.MANAGER,
        )

        self.manager.institutions.add(self.institution)

    def test_switch_with_external_next_url_redirects_to_dashboard(self):

        self.client.force_login(self.manager)

        for external in (
            "https://evil.example.com",
            "http://evil.example.com",
            "//evil.example.com",
        ):

            response = self.client.post(
                reverse("institutions:switch"),
                {
                    "institution_id": self.institution.pk,
                    "next": external,
                },
            )

            self.assertRedirects(
                response,
                reverse("dashboard"),
                fetch_redirect_response=False,
            )

    def test_switch_with_local_next_url_redirects_there(self):

        self.client.force_login(self.manager)

        response = self.client.post(
            reverse("institutions:switch"),
            {
                "institution_id": self.institution.pk,
                "next": "/students/",
            },
        )

        self.assertRedirects(
            response,
            "/students/",
            fetch_redirect_response=False,
        )

    def test_switch_get_redirects_to_dashboard(self):

        self.client.force_login(self.manager)

        response = self.client.get(
            reverse("institutions:switch"),
        )

        self.assertRedirects(
            response,
            reverse("dashboard"),
            fetch_redirect_response=False,
        )


class ClassIsolationTests(TestCase):

    def setUp(self):

        self.first_institution = Institution.objects.create(
            name="First School",
            short_name="FS",
        )

        self.second_institution = Institution.objects.create(
            name="Second School",
            short_name="SS",
        )

        self.manager = User.objects.create_user(
            username="manager",
            password="managerpass123",
            role=User.Role.MANAGER,
        )

        self.manager.institutions.add(
            self.second_institution,
        )

        ClassRoom.objects.create(
            institution=self.first_institution,
            name="Class A",
            level=1,
        )

        ClassRoom.objects.create(
            institution=self.second_institution,
            name="Class B",
            level=1,
        )

    def test_manager_sees_only_own_classes(self):

        self.client.force_login(self.manager)

        session = self.client.session
        session[SESSION_KEY] = self.second_institution.pk
        session.save()

        response = self.client.get(
            reverse("classes:list"),
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "Class B")
        self.assertNotContains(response, "Class A")

    def test_classroom_form_locks_current_institution(self):

        self.client.force_login(self.manager)

        session = self.client.session
        session[SESSION_KEY] = self.second_institution.pk
        session.save()

        response = self.client.get(
            reverse("classes:create"),
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            f'name="institution"',
        )

        self.assertContains(
            response,
            'value="{}"'.format(self.second_institution.pk),
        )

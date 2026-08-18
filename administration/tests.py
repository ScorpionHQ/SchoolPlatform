from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from institutions.models import Institution


class AdministrationTests(TestCase):

    def setUp(self):

        self.admin = get_user_model().objects.create_user(
            username="sysadmin",
            password="Test12345!",
            role=get_user_model().Role.SYSTEM_ADMIN,
        )

        self.manager = get_user_model().objects.create_user(
            username="manager",
            password="Test12345!",
            role=get_user_model().Role.MANAGER,
        )

        self.institution = Institution.objects.create(
            name="Test School",
            short_name="TS",
        )

    def _login(self, user):

        self.client.login(
            username=user.username,
            password="Test12345!",
        )

    def test_dashboard_requires_system_admin(self):

        self._login(self.manager)

        response = self.client.get(
            reverse("administration:dashboard"),
        )

        self.assertEqual(response.status_code, 403)

    def test_dashboard_renders_for_system_admin(self):

        self._login(self.admin)

        response = self.client.get(
            reverse("administration:dashboard"),
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "إدارة النظام")

    def test_user_list_shows_users(self):

        self._login(self.admin)

        response = self.client.get(
            reverse("administration:user_list"),
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "sysadmin")
        self.assertContains(response, "manager")

    def test_user_create(self):

        self._login(self.admin)

        url = reverse("administration:user_create")

        response = self.client.post(
            url,
            {
                "username": "new_teacher",
                "password": "Test12345!",
                "first_name": "New",
                "last_name": "Teacher",
                "role": "teacher",
                "gender": "female",
                "phone_number": "",
                "is_active": "on",
                "must_change_password": "",
            },
        )

        user = get_user_model().objects.get(
            username="new_teacher",
        )

        self.assertEqual(user.role, "teacher")
        self.assertEqual(user.gender, "female")
        self.assertTrue(user.is_active)
        self.assertTrue(user.check_password("Test12345!"))

    def test_user_create_requires_password(self):

        self._login(self.admin)

        url = reverse("administration:user_create")

        response = self.client.post(
            url,
            {
                "username": "no_pass",
                "password": "",
                "first_name": "",
                "last_name": "",
                "role": "teacher",
                "gender": "",
                "phone_number": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            get_user_model().objects.filter(
                username="no_pass",
            ).exists()
        )

    def test_user_update_changes_gender(self):

        self._login(self.admin)

        url = reverse(
            "administration:user_update",
            kwargs={"pk": self.manager.pk},
        )

        response = self.client.post(
            url,
            {
                "username": self.manager.username,
                "password": "",
                "first_name": "Male",
                "last_name": "Manager",
                "role": "manager",
                "gender": "male",
                "phone_number": "",
                "is_active": "on",
                "must_change_password": "",
            },
        )

        self.manager.refresh_from_db()

        self.assertEqual(self.manager.gender, "male")
        self.assertTrue(self.manager.check_password("Test12345!"))

    def test_user_delete(self):

        self._login(self.admin)

        target = get_user_model().objects.create_user(
            username="doomed",
            password="Test12345!",
            role=get_user_model().Role.PARENT,
        )

        url = reverse(
            "administration:user_delete",
            kwargs={"pk": target.pk},
        )

        response = self.client.post(url)

        self.assertRedirects(
            response,
            reverse("administration:user_list"),
        )

        self.assertFalse(
            get_user_model().objects.filter(
                pk=target.pk,
            ).exists()
        )

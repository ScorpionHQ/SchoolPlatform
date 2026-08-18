from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from institutions.models import Institution

from .models import ClassRoom


class ClassRoomModelTests(TestCase):

    def setUp(self):

        self.institution = Institution.objects.create(
            name="Test School",
            short_name="TS",
        )

    def test_str(self):

        classroom = ClassRoom.objects.create(
            name="Grade 5",
            institution=self.institution,
            level="5",
            academic_year="2026",
        )

        self.assertEqual(str(classroom), "Grade 5 - 5")

    def test_unique_constraint_per_institution(self):

        ClassRoom.objects.create(
            name="Grade 5",
            institution=self.institution,
            level="5",
            academic_year="2026",
        )

        duplicate = ClassRoom(
            name="Grade 5",
            institution=self.institution,
            level="5",
            academic_year="2026",
        )

        with self.assertRaises(ValidationError):

            duplicate.full_clean()


class ClassRoomViewTests(TestCase):

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

    def test_teacher_cannot_access_classes(self):

        teacher = User.objects.create_user(
            username="teacher",
            password="pass123",
            role=User.Role.TEACHER,
        )

        self.client.force_login(teacher)

        response = self.client.get(reverse("classes:list"))

        self.assertEqual(response.status_code, 403)

    def test_manager_can_list_classes(self):

        ClassRoom.objects.create(
            name="Grade 5",
            institution=self.institution,
            level="5",
            academic_year="2026",
        )

        self.client.force_login(self.manager)

        response = self.client.get(reverse("classes:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Grade 5")

    def test_manager_can_create_classroom(self):

        self.client.force_login(self.manager)

        response = self.client.post(
            reverse("classes:create"),
            {
                "institution": self.institution.pk,
                "stage": ClassRoom.Stage.PRIMARY,
                "name": "Grade 6",
                "level": "6",
                "academic_year": "2026",
            },
        )

        self.assertRedirects(
            response,
            reverse("classes:list"),
        )

        self.assertTrue(
            ClassRoom.objects.filter(name="Grade 6").exists()
        )

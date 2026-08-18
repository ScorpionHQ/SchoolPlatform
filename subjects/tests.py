from datetime import date

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from classes.models import ClassRoom
from institutions.models import Institution
from notifications.models import Notification
from teachers.models import Teacher

from .forms import SubjectForm
from .models import Subject
from .services import SubjectService


class SubjectModelTests(TestCase):

    def setUp(self):

        self.institution = Institution.objects.create(
            name="Test School",
            short_name="TS",
        )

    def test_str(self):

        subject = Subject.objects.create(
            name="Mathematics",
            institution=self.institution,
        )

        self.assertEqual(str(subject), "Mathematics")

    def test_ordering_by_name(self):

        Subject.objects.create(
            name="Zoo",
            institution=self.institution,
        )

        Subject.objects.create(
            name="Arabic",
            institution=self.institution,
        )

        names = list(
            Subject.objects.values_list("name", flat=True)
        )

        self.assertEqual(names, ["Arabic", "Zoo"])


class SubjectServiceTests(TestCase):

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

        self.subject = Subject.objects.create(
            name="Mathematics",
            institution=self.institution,
        )

    def test_create_subject(self):

        data = {
            "institution": self.institution.pk,
            "classroom": "",
            "teacher": "",
            "name": "Science",
            "code": "SCI",
            "description": "",
        }

        form = SubjectForm(
            data,
            institution=self.institution,
        )

        self.assertTrue(
            form.is_valid(),
            form.errors,
        )

        subject = SubjectService.create_subject(form)

        self.assertEqual(subject.name, "Science")

        self.assertTrue(
            Notification.objects.filter(
                user=self.manager,
                type=Notification.Type.SUBJECT,
            ).exists()
        )

    def test_delete_subject_removes_record(self):

        SubjectService.delete_subject(self.subject)

        self.assertFalse(
            Subject.objects.filter(pk=self.subject.pk).exists()
        )


class SubjectViewTests(TestCase):

    def setUp(self):

        self.institution = Institution.objects.create(
            name="Test School",
            short_name="TS",
        )

        self.classroom = ClassRoom.objects.create(
            name="Grade 5",
            institution=self.institution,
            level="5",
            academic_year="2026",
        )

        self.manager = User.objects.create_user(
            username="manager",
            password="pass123",
            role=User.Role.MANAGER,
        )

        self.manager.institutions.add(self.institution)

        self.teacher_user = User.objects.create_user(
            username="teacher",
            password="pass123",
            role=User.Role.TEACHER,
        )

        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            institution=self.institution,
            employee_code="T001",
        )

    def test_teacher_cannot_access_subjects(self):

        self.client.force_login(self.teacher_user)

        response = self.client.get(reverse("subjects:list"))

        self.assertEqual(response.status_code, 403)

    def test_manager_can_list_subjects(self):

        Subject.objects.create(
            name="Mathematics",
            institution=self.institution,
        )

        self.client.force_login(self.manager)

        response = self.client.get(reverse("subjects:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mathematics")

    def test_manager_can_create_subject(self):

        self.client.force_login(self.manager)

        response = self.client.post(
            reverse("subjects:create"),
            {
                "institution": self.institution.pk,
                "classroom": self.classroom.pk,
                "teacher": self.teacher.pk,
                "name": "Science",
                "code": "SCI",
                "description": "Physics and chemistry.",
            },
        )

        self.assertRedirects(
            response,
            reverse("subjects:list"),
        )

        subject = Subject.objects.get(name="Science")

        self.assertEqual(subject.institution, self.institution)
        self.assertEqual(subject.teacher, self.teacher)

    def test_subject_scoped_to_own_institution(self):

        other = Institution.objects.create(
            name="Other School",
            short_name="OS",
        )

        Subject.objects.create(
            name="Private",
            institution=other,
        )

        self.client.force_login(self.manager)

        response = self.client.get(reverse("subjects:list"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Private")

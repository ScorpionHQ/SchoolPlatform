from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from institutions.models import Institution
from students.models import Student

from .models import Parent
from .services import ParentService


class ParentServiceTests(TestCase):

    def setUp(self):

        self.institution = Institution.objects.create(
            name="Test School",
            short_name="TS",
        )

        self.student_user = User.objects.create_user(
            username="child",
            password="pass123",
            role=User.Role.STUDENT,
        )

        self.student = Student.objects.create(
            user=self.student_user,
            institution=self.institution,
            student_code="S000001",
        )

    def test_create_parent_links_students(self):

        parent = ParentService.create_parent(
            username="parent1",
            password="pass123",
            first_name="Ali",
            last_name="Ahmed",
            relationship="Father",
            students=[self.student],
        )

        self.assertEqual(parent.user.role, User.Role.PARENT)
        self.assertEqual(
            list(parent.students.all()),
            [self.student],
        )

    def test_create_parent_rejects_duplicate_username(self):

        ParentService.create_parent(
            username="parent1",
            password="pass123",
            first_name="Ali",
            last_name="Ahmed",
            relationship="Father",
            students=[self.student],
        )

        with self.assertRaises(ValidationError):

            ParentService.create_parent(
                username="parent1",
                password="pass123",
                first_name="Sara",
                last_name="Ahmed",
                relationship="Mother",
                students=[self.student],
            )

    def test_delete_parent_removes_user(self):

        parent = ParentService.create_parent(
            username="parent1",
            password="pass123",
            first_name="Ali",
            last_name="Ahmed",
            relationship="Father",
            students=[self.student],
        )

        parent_user = parent.user

        ParentService.delete_parent(parent)

        self.assertFalse(
            User.objects.filter(pk=parent_user.pk).exists()
        )


class ParentViewTests(TestCase):

    def setUp(self):

        self.institution = Institution.objects.create(
            name="Test School",
            short_name="TS",
        )

        self.student_user = User.objects.create_user(
            username="child",
            password="pass123",
            role=User.Role.STUDENT,
        )

        self.student = Student.objects.create(
            user=self.student_user,
            institution=self.institution,
            student_code="S000001",
        )

        self.manager = User.objects.create_user(
            username="manager",
            password="pass123",
            role=User.Role.MANAGER,
        )

        self.manager.institutions.add(self.institution)

    def test_teacher_cannot_access_parents(self):

        teacher = User.objects.create_user(
            username="teacher",
            password="pass123",
            role=User.Role.TEACHER,
        )

        self.client.force_login(teacher)

        response = self.client.get(reverse("parents:list"))

        self.assertEqual(response.status_code, 403)

    def test_manager_can_create_parent(self):

        self.client.force_login(self.manager)

        response = self.client.post(
            reverse("parents:create"),
            {
                "first_name": "Ali",
                "last_name": "Ahmed",
                "username": "parent1",
                "password": "pass123",
                "confirm_password": "pass123",
                "relationship": "Father",
                "students": [self.student.pk],
            },
        )

        self.assertRedirects(
            response,
            reverse("parents:list"),
        )

        parent = Parent.objects.get(user__username="parent1")

        self.assertEqual(parent.relationship, "Father")
        self.assertEqual(
            list(parent.students.all()),
            [self.student],
        )

    def test_manager_can_list_parents(self):

        ParentService.create_parent(
            username="parent1",
            password="pass123",
            first_name="Ali",
            last_name="Ahmed",
            relationship="Father",
            students=[self.student],
        )

        self.client.force_login(self.manager)

        response = self.client.get(reverse("parents:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ali")

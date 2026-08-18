from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from classes.models import ClassRoom
from institutions.models import Institution
from notifications.models import Notification
from students.models import Student
from subjects.models import Subject
from teachers.models import Teacher

from .models import Attendance
from .services import AttendanceService


class AttendanceModelTests(TestCase):

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

    def test_unique_together(self):

        Attendance.objects.create(
            student=self.student,
            subject=self.subject,
            date=date(2026, 6, 1),
            status=Attendance.Status.PRESENT,
        )

        duplicate = Attendance(
            student=self.student,
            subject=self.subject,
            date=date(2026, 6, 1),
            status=Attendance.Status.ABSENT,
        )

        with self.assertRaises(Exception):

            duplicate.save()


class AttendanceServiceTests(TestCase):

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

    def test_save_attendance_session(self):

        count = AttendanceService.save_attendance_session(
            classroom=self.classroom,
            subject=self.subject,
            teacher=self.teacher,
            date=date(2026, 6, 1),
            attendance_data=[
                {
                    "student": self.student,
                    "status": Attendance.Status.PRESENT,
                },
            ],
        )

        self.assertEqual(count, 1)

        self.assertTrue(
            Attendance.objects.filter(
                student=self.student,
                date=date(2026, 6, 1),
            ).exists()
        )

        self.assertTrue(
            Notification.objects.filter(
                user=self.student_user,
                type=Notification.Type.ATTENDANCE,
            ).exists()
        )

    def test_session_rejects_duplicate_recording(self):

        AttendanceService.save_attendance_session(
            classroom=self.classroom,
            subject=self.subject,
            teacher=self.teacher,
            date=date(2026, 6, 1),
            attendance_data=[
                {
                    "student": self.student,
                    "status": Attendance.Status.PRESENT,
                },
            ],
        )

        with self.assertRaises(ValidationError):

            AttendanceService.save_attendance_session(
                classroom=self.classroom,
                subject=self.subject,
                teacher=self.teacher,
                date=date(2026, 6, 1),
                attendance_data=[
                    {
                        "student": self.student,
                        "status": Attendance.Status.ABSENT,
                    },
                ],
            )


class AttendanceViewTests(TestCase):

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

    def test_teacher_cannot_access_attendance(self):

        teacher = User.objects.create_user(
            username="teacher",
            password="pass123",
            role=User.Role.TEACHER,
        )

        self.client.force_login(teacher)

        response = self.client.get(reverse("attendance:list"))

        self.assertEqual(response.status_code, 403)

    def test_manager_can_list_attendance(self):

        Attendance.objects.create(
            student=self.student,
            subject=self.subject,
            date=date(2026, 6, 1),
            status=Attendance.Status.PRESENT,
        )

        self.client.force_login(self.manager)

        response = self.client.get(reverse("attendance:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mathematics")

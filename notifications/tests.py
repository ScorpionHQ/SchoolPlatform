from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase
from django.urls import reverse

from accounts.models import User
from institutions.models import Institution
from parents.models import Parent
from students.models import Student

from .context_processors import notifications_context
from .models import Notification
from .services import NotificationService


def _user(username, role):
    return User.objects.create_user(
        username=username,
        password="pass12345",
        role=role,
    )


class NotificationModelTests(TestCase):

    def setUp(self):

        self.user = _user("user", User.Role.STUDENT)

        self.notification = Notification.objects.create(
            user=self.user,
            type=Notification.Type.GRADE,
            title="New grade",
            message="You received 90.",
            link="/students/grades/",
        )

    def test_str(self):
        self.assertEqual(str(self.notification), "New grade")

    def test_defaults_unread_and_system_type_when_omitted(self):

        notification = Notification.objects.create(
            user=self.user,
            title="Hello",
        )

        self.assertFalse(notification.is_read)
        self.assertEqual(notification.type, Notification.Type.SYSTEM)

    def test_ordering_newest_first(self):

        Notification.objects.create(
            user=self.user,
            title="Older",
        )

        Notification.objects.create(
            user=self.user,
            title="Newest",
        )

        self.assertEqual(
            Notification.objects.first().title,
            "Newest",
        )


class NotificationServiceTests(TestCase):

    def setUp(self):

        self.institution = Institution.objects.create(
            name="Notify School",
            short_name="NS",
        )

        self.manager = _user("manager", User.Role.MANAGER)
        self.manager.institutions.add(self.institution)

        self.assistant = _user(
            "assistant",
            User.Role.ASSISTANT_MANAGER,
        )
        self.assistant.institutions.add(self.institution)

        self.system_admin = _user(
            "sysadmin",
            User.Role.SYSTEM_ADMIN,
        )

        self.student_user = _user("student", User.Role.STUDENT)

        self.student = Student.objects.create(
            user=self.student_user,
            institution=self.institution,
            student_code="S100001",
        )

    def test_notify_users_skips_none(self):

        created = NotificationService.notify_users(
            [None, self.manager, None],
            ntype=Notification.Type.SYSTEM,
            title="Hi",
        )

        self.assertEqual(len(created), 1)

        self.assertEqual(
            Notification.objects.filter(user=self.manager).count(),
            1,
        )

    def test_notify_user(self):

        notification = NotificationService.notify_user(
            self.manager,
            ntype=Notification.Type.SYSTEM,
            title="Hi",
            message="Welcome",
        )

        self.assertEqual(len(notification), 1)
        self.assertEqual(notification[0].user, self.manager)

    def test_institution_managers_includes_manager_roles_only(self):

        from accounts.models import User as U

        U.objects.create_user(
            username="teacher",
            password="x12345678",
            role=U.Role.TEACHER,
        ).institutions.add(self.institution)

        managers = NotificationService.institution_managers(
            self.institution
        )

        self.assertIn(self.manager, managers)
        self.assertIn(self.assistant, managers)
        self.assertEqual(managers.count(), 2)

    def test_notify_institution_managers(self):

        NotificationService.notify_institution_managers(
            self.institution,
            ntype=Notification.Type.STUDENT,
            title="New student",
            message="A student joined.",
        )

        self.assertEqual(
            Notification.objects.filter(user=self.manager).count(),
            1,
        )

        self.assertEqual(
            Notification.objects.filter(user=self.assistant).count(),
            1,
        )

        self.assertEqual(
            Notification.objects.filter(user=self.system_admin).count(),
            0,
        )

    def test_system_admins(self):

        NotificationService.notify_system_admins(
            ntype=Notification.Type.SYSTEM,
            title="Alert",
            message="Server notice.",
        )

        self.assertEqual(
            Notification.objects.filter(user=self.system_admin).count(),
            1,
        )

    def test_student_and_parents_notifies_both(self):

        parent_user = _user("parent", User.Role.PARENT)

        parent = Parent.objects.create(user=parent_user)

        parent.students.add(self.student)

        NotificationService.student_and_parents(
            self.student,
            ntype=Notification.Type.ATTENDANCE,
            title="Absent",
            message="Was absent today.",
            student_link="/students/attendance/",
            parent_link="/",
        )

        self.assertEqual(
            Notification.objects.filter(
                user=self.student_user,
            ).count(),
            1,
        )

        self.assertEqual(
            Notification.objects.filter(
                user=parent_user,
            ).count(),
            1,
        )

    def test_student_and_parents_handles_none_student(self):

        created = NotificationService.student_and_parents(
            None,
            ntype=Notification.Type.SYSTEM,
            title="Hi",
        )

        self.assertEqual(created, [])

    def test_send_email_delivery_does_not_raise(self):
        """Email delivery is a no-op when SMTP is not configured."""

        NotificationService.send_email_delivery(
            self.manager,
            "Subject",
            "Body",
        )


class NotificationViewTests(TestCase):

    def setUp(self):

        self.user = _user("user", User.Role.STUDENT)

        self.other = _user("other", User.Role.STUDENT)

        self.notification = Notification.objects.create(
            user=self.user,
            type=Notification.Type.GRADE,
            title="Grade posted",
            message="You received 90 in Math.",
            link="/students/grades/",
        )

        Notification.objects.create(
            user=self.other,
            type=Notification.Type.GRADE,
            title="Other user",
        )

    def _login(self):
        self.client.force_login(self.user)

    def test_list_requires_login(self):

        response = self.client.get(reverse("notifications:list"))

        self.assertEqual(response.status_code, 302)

    def test_list_shows_own_notifications_only(self):

        self._login()

        response = self.client.get(reverse("notifications:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Grade posted")
        self.assertNotContains(response, "Other user")

    def test_mark_read_sets_flag_and_redirects_to_link(self):

        self._login()

        response = self.client.post(
            reverse(
                "notifications:mark_read",
                args=[self.notification.pk],
            )
        )

        self.assertRedirects(
            response,
            "/students/grades/",
            fetch_redirect_response=False,
        )

        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_mark_read_redirects_to_list_when_no_link(self):

        self._login()

        self.notification.link = ""
        self.notification.save(update_fields=["link"])

        response = self.client.post(
            reverse(
                "notifications:mark_read",
                args=[self.notification.pk],
            )
        )

        self.assertRedirects(
            response,
            reverse("notifications:list"),
        )

    def test_mark_read_get_does_not_mark(self):

        self._login()

        self.client.get(
            reverse(
                "notifications:mark_read",
                args=[self.notification.pk],
            )
        )

        self.notification.refresh_from_db()
        self.assertFalse(self.notification.is_read)

    def test_mark_read_scoped_to_owner(self):

        self._login()

        other_notification = Notification.objects.get(
            user=self.other,
        )

        response = self.client.post(
            reverse(
                "notifications:mark_read",
                args=[other_notification.pk],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_mark_all_read(self):

        self._login()

        Notification.objects.create(
            user=self.user,
            title="Second",
        )

        Notification.objects.create(
            user=self.user,
            title="Third",
        )

        response = self.client.post(
            reverse("notifications:mark_all_read"),
        )

        self.assertRedirects(
            response,
            reverse("notifications:list"),
        )

        self.assertEqual(
            Notification.objects.filter(
                user=self.user,
                is_read=False,
            ).count(),
            0,
        )

        self.assertEqual(
            Notification.objects.filter(
                user=self.other,
                is_read=False,
            ).count(),
            1,
        )

    def test_unread_count_json(self):

        self._login()

        response = self.client.get(
            reverse("notifications:unread_count")
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"count": 1})

    def test_unread_count_zero_when_all_read(self):

        self._login()

        Notification.objects.all().update(is_read=True)

        response = self.client.get(
            reverse("notifications:unread_count")
        )

        self.assertEqual(response.json(), {"count": 0})


class NotificationContextProcessorTests(TestCase):

    def test_anonymous_user_gets_zero(self):

        request = RequestFactory().get("/")

        request.user = AnonymousUser()

        result = notifications_context(request)

        self.assertEqual(
            result["unread_notifications_count"],
            0,
        )

    def test_authenticated_user_gets_count(self):

        user = _user("user", User.Role.STUDENT)

        Notification.objects.create(user=user, title="One")

        request = RequestFactory().get("/")

        request.user = user

        result = notifications_context(request)

        self.assertEqual(
            result["unread_notifications_count"],
            1,
        )

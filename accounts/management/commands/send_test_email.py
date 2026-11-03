"""Verify the outgoing email configuration.

Password reset is the only flow that needs email, and a silent failure there
is hard to notice. Run this once after setting the SMTP variables:

    python manage.py send_test_email someone@example.com
"""

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import gettext_lazy as _


class Command(BaseCommand):

    help = "Send a test message to check the email settings."

    def add_arguments(self, parser):

        parser.add_argument(
            "recipient",
            help="Address that receives the test message.",
        )

    def handle(self, *args, **options):

        recipient = options["recipient"].strip()

        if not recipient:

            raise CommandError("A recipient address is required.")

        self.stdout.write(f"Backend: {settings.EMAIL_BACKEND}")

        if settings.EMAIL_HOST:

            self.stdout.write(
                f"Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}"
            )

        else:

            self.stdout.write(
                "EMAIL_HOST is empty, so messages go to the server logs."
            )

        try:

            sent = send_mail(
                subject=str(_("SchoolPlatform email test")),
                message=str(
                    _(
                        "This message confirms that the platform can send "
                        "email. If you received it, password reset works."
                    )
                ),
                from_email=None,
                recipient_list=[recipient],
                fail_silently=False,
            )

        except Exception as error:

            raise CommandError(f"Email delivery failed: {error}") from error

        if not sent:

            raise CommandError("The email backend reported no delivery.")

        self.stdout.write(
            self.style.SUCCESS(f"Test message sent to {recipient}.")
        )

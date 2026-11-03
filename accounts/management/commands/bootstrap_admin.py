"""Create the first system administrator on a brand-new deployment.

Render has no remote shell in its free plan, so a fresh database would have no
way to reach the Django admin. This command is safe to run on every deploy: it
does nothing once a system administrator exists.

Set ``BOOTSTRAP_ADMIN_PASSWORD`` (and optionally ``BOOTSTRAP_ADMIN_USERNAME``)
in the host's environment variables. The account is created with
``must_change_password`` so the temporary password cannot be kept.
"""

import os

from django.core.management.base import BaseCommand

from accounts.models import User


class Command(BaseCommand):

    help = "Create the initial system administrator if none exists."

    def handle(self, *args, **options):

        password = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD", "")

        if not password:

            self.stdout.write(
                "BOOTSTRAP_ADMIN_PASSWORD is not set; skipping."
            )

            return

        if User.objects.filter(role=User.Role.SYSTEM_ADMIN).exists():

            self.stdout.write("A system administrator already exists.")

            return

        username = (
            os.environ.get("BOOTSTRAP_ADMIN_USERNAME", "admin").strip()
            or "admin"
        )

        if User.objects.filter(username=username).exists():

            self.stdout.write(
                f"The username {username} is already taken; skipping."
            )

            return

        user = User.objects.create_superuser(
            username=username,
            password=password,
            role=User.Role.SYSTEM_ADMIN,
            must_change_password=True,
            first_name=os.environ.get("BOOTSTRAP_ADMIN_FIRST_NAME", ""),
            last_name=os.environ.get("BOOTSTRAP_ADMIN_LAST_NAME", ""),
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Created the system administrator "
                f"{user.username} ({user.login_code})."
            )
        )

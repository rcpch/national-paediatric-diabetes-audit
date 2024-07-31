import os

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from project.npda.models import NPDAUser


class Command(BaseCommand):
    help = "Create a default NPDA superuser, pulling in values set in environment variables: LOCAL_DEV_ADMIN_EMAIL and LOCAL_DEV_ADMIN_PASSWORD."

    def handle(self, *args, **kwargs):

        # Grab environment variables
        LOCAL_DEV_ADMIN_EMAIL = os.environ.get("LOCAL_DEV_ADMIN_PASSWORD", None)
        LOCAL_DEV_ADMIN_PASSWORD = os.environ.get("LOCAL_DEV_ADMIN_PASSWORD", None)

        # Set default values if environment variables are not set
        if LOCAL_DEV_ADMIN_EMAIL is None or LOCAL_DEV_ADMIN_PASSWORD is None:
            DEFAULT_VALUE_LOCAL_DEV_ADMIN_EMAIL = "incubator@rcpch.ac.uk"
            DEFAULT_VALUE_LOCAL_DEV_ADMIN_PASSWORD = "devp@ssword12345"

            self.stdout.write(
                self.style.ERROR(
                    f"NOTE: LOCAL_DEV_ADMIN_EMAIL and LOCAL_DEV_ADMIN_PASSWORD environment variables are not set, so defaulting to the values:\n\nLOCAL_DEV_ADMIN_EMAIL={DEFAULT_VALUE_LOCAL_DEV_ADMIN_EMAIL}\nLOCAL_DEV_ADMIN_PASSWORD={DEFAULT_VALUE_LOCAL_DEV_ADMIN_PASSWORD}"
                )
            )
            LOCAL_DEV_ADMIN_EMAIL = DEFAULT_VALUE_LOCAL_DEV_ADMIN_EMAIL
            LOCAL_DEV_ADMIN_PASSWORD = DEFAULT_VALUE_LOCAL_DEV_ADMIN_PASSWORD

        # Create superuser if it doesn't already exist
        if not NPDAUser.objects.filter(email=LOCAL_DEV_ADMIN_EMAIL).exists():
            NPDAUser.objects.create_superuser(
                first_name="SuperuserAda",
                last_name="Lovelace",
                email=LOCAL_DEV_ADMIN_EMAIL,
                password=LOCAL_DEV_ADMIN_PASSWORD,
                is_active=True,
                is_staff=True,
                is_superuser=True,
                role=4,  # also sets is_rcpch_staff=True
            )
            self.stdout.write(self.style.SUCCESS("Successfully created the superuser."))
        else:
            self.stdout.write(self.style.WARNING("Superuser already exists."))

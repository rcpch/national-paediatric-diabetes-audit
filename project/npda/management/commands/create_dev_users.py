import os

from django.apps import apps
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from project.constants.user import (
    AUDIT_CENTRE_COORDINATOR,
    AUDIT_CENTRE_EDITOR,
    AUDIT_CENTRE_READER
)

class Command(BaseCommand):
    help = "Create test users using the base set in environment variables: LOCAL_DEV_ADMIN_EMAIL and LOCAL_DEV_ADMIN_PASSWORD."

    def create_user_if_not_exists(self, email, first_name, surname, password, role):
        user_model = get_user_model()

        if not user_model.objects.filter(email=email).exists():
            user_model.objects.create_or_update_user(
                first_name=first_name,
                surname=surname,
                email=email,
                password=password,
                role=role,
                is_active=True,
                pz_code="PZ999",  # RCPCH
                is_primary_employer=True
            )
            
            self.stdout.write(self.style.SUCCESS(f"Successfully created {email}."))
        else:
            self.stdout.write(self.style.WARNING(f"{email} already exists."))

    def handle(self, *args, **kwargs):
        user_model = get_user_model()

        # Grab environment variables
        local_dev_admin_email = os.environ.get("LOCAL_DEV_ADMIN_EMAIL", None)
        password = os.environ.get("LOCAL_DEV_ADMIN_PASSWORD", None)

        if not local_dev_admin_email or not password:
            self.stdout.write(self.style.WARNING("LOCAL_DEV_ADMIN_EMAIL or LOCAL_DEV_ADMIN_PASSWORD not set. Not creating any test users."))

        (local_part, domain) = local_dev_admin_email.split("@")

        coordinator_dev_email = f"{local_part}+coordinator@{domain}"
        editor_dev_email = f"{local_part}+editor@{domain}"
        reader_dev_email = f"{local_part}+reader@{domain}"
        
        if not user_model.objects.filter(email=local_dev_admin_email).exists():
            user_model.objects.create_superuser(
                first_name="SuperuserAda",
                surname="Lovelace",
                email=local_dev_admin_email,
                password=password
            )
            
            self.stdout.write(self.style.SUCCESS(f"Successfully created {local_dev_admin_email}."))
        else:
            self.stdout.write(self.style.WARNING(f"{local_dev_admin_email} already exists."))
        
        self.create_user_if_not_exists(
            email=coordinator_dev_email,
            first_name="CoordinatorAda",
            surname="Lovelace",
            password=password,
            role=AUDIT_CENTRE_COORDINATOR,
        )

        self.create_user_if_not_exists(
            email=editor_dev_email,
            first_name="EditorAda",
            surname="Lovelace",
            password=password,
            role=AUDIT_CENTRE_EDITOR,
        )

        self.create_user_if_not_exists(
            email=reader_dev_email,
            first_name="ReaderAda",
            surname="Lovelace",
            password=password,
            role=AUDIT_CENTRE_READER,
        )
        


import os

from django.apps import apps
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from project.constants.user import (
    AUDIT_CENTRE_COORDINATOR,
    AUDIT_CENTRE_EDITOR,
    AUDIT_CENTRE_READER,
    RCPCH_AUDIT_TEAM,
)

from project.npda.models import PaediatricDiabetesUnit, OrganisationEmployer

class Command(BaseCommand):
    help = "Create test users using the base set in environment variables: LOCAL_DEV_ADMIN_EMAIL and LOCAL_DEV_ADMIN_PASSWORD."

    def create_user_if_not_exists(self, pz_code, email, first_name, surname, password, role, is_rcpch_audit_team_member=False):
        user_model = get_user_model()

        if not user_model.objects.filter(email=email).exists():
            user = user_model.objects.create_or_update_user(
                first_name=first_name,
                surname=surname,
                email=email,
                password=password,
                role=role,
                is_active=True,
                pz_code=pz_code,
                is_primary_employer=True,
                is_rcpch_audit_team_member=is_rcpch_audit_team_member
            )
            
            self.stdout.write(self.style.SUCCESS(f"Successfully created {email}."))
        else:
            self.stdout.write(self.style.WARNING(f"{email} already exists."))
            user = user_model.objects.get(email=email)
        
        return user

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
        rcpch_audit_team_email = f"{local_part}+rcpch_audit_team@{domain}"
        
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
            pz_code="PZ999",
            email=coordinator_dev_email,
            first_name="CoordinatorAda",
            surname="Lovelace",
            password=password,
            role=AUDIT_CENTRE_COORDINATOR,
        )

        self.create_user_if_not_exists(
            pz_code="PZ999",
            email=editor_dev_email,
            first_name="EditorAda",
            surname="Lovelace",
            password=password,
            role=AUDIT_CENTRE_EDITOR,
        )

        self.create_user_if_not_exists(
            pz_code="PZ999",
            email=reader_dev_email,
            first_name="ReaderAda",
            surname="Lovelace",
            password=password,
            role=AUDIT_CENTRE_READER,
        )

        self.create_user_if_not_exists(
            pz_code="PZ999",
            email=rcpch_audit_team_email,
            first_name="RCPCHAuditTeamAda",
            surname="Lovelace",
            password=password,
            role=RCPCH_AUDIT_TEAM,
            is_rcpch_audit_team_member=True
        )

        # Test inactive split unit (https://github.com/rcpch/national-paediatric-diabetes-audit/issues/924)
        # PZ003 was split into PZ251 and PZ252
        split_user = self.create_user_if_not_exists(
            pz_code="PZ251",
            email=f"{local_part}+split@{domain}",
            first_name="SplitUnitAda",
            surname="Lovelace",
            password=password,
            role=AUDIT_CENTRE_COORDINATOR,
        )

        OrganisationEmployer.objects.create(
            paediatric_diabetes_unit=PaediatricDiabetesUnit.objects.get(pz_code="PZ003"),
            npda_user=split_user,
            is_primary_employer=False,
        )




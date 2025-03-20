# Python imports
from os import path
import csv

# Django import
from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

# NPDA imports
from project.npda.general_functions import group_for_role

PaediatricDiabetesUnit = apps.get_model("npda", "PaediatricDiabetesUnit")
OrganisationEmployer = apps.get_model("npda", "OrganisationEmployer")
NPDAUser = apps.get_model("npda", "NPDAUser")


class Command(BaseCommand):
    help = "Import users into NPDA from a CSV file."

    """
    ROLES = (
    (AUDIT_CENTRE_COORDINATOR, "Coordinator"), # 1
    (AUDIT_CENTRE_EDITOR, "Editor"), # 2
    (AUDIT_CENTRE_READER, "Reader"), # 3
    (RCPCH_AUDIT_TEAM, "RCPCH Audit Team"), # 4
    (RCPCH_AUDIT_PATIENT_FAMILY, "RCPCH Audit Children and Family"), # 7
)
"""

    def add_arguments(self, parser):
        parser.add_argument("file", type=str, help="Path to the CSV file to import.")

    def handle(self, *args, **options):
        file_path = options["file"]

        if not path.exists(file_path):
            raise CommandError(f"File does not exist: {file_path}")

        with open(file_path, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                first_name = row["first_name"]
                surname = row["surname"]
                title = row["title"]
                email = row["email"].lower()
                role = row["role"]
                pz_code = row["pz_code"]

                # find the PZ code
                try:
                    pdu = PaediatricDiabetesUnit.objects.get(pz_code=pz_code)
                except PaediatricDiabetesUnit.DoesNotExist:
                    raise CommandError(
                        f"Paediatric Diabetes Unit with code {pz_code} does not exist."
                    )

                # find the group
                group = group_for_role(role)
                if not group:
                    raise CommandError(f"Group for role {role} does not exist.")

                # create or update the user
                if NPDAUser.objects.filter(email=email).exists():
                    user = NPDAUser.objects.get(email=email)
                else:
                    user = NPDAUser()

                user.first_name = first_name
                user.surname = surname
                user.title = title
                user.email = email
                user.is_active = True
                user.is_staff = False  # staff we will create manually
                user.is_superuser = False  # superusers we will create manually
                user.is_rcpch_audit_team_member = (
                    False  # audit team members we will create manually
                )
                user.is_rcpch_staff = False  # staff we will create manually
                user.is_patient_or_carer = False  # patients we will create manually
                user.view_preference = 1  # PDU view
                user.date_joined = timezone.now()
                user.role = role
                user.email_confirmed = False
                user.password_last_set = timezone.now()
                user.set_unusable_password()
                user.save()
                # add the user to the group
                user.groups.add(group)

                # create the organisation employer
                OrganisationEmployer.objects.create(
                    paediatric_diabetes_unit=pdu,
                    npda_user=user,
                    is_primary_employer=True,
                )

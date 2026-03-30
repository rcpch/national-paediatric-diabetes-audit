# Python imports
import csv
import logging
from os import path

# Django import
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger(__name__)


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

        user_model = get_user_model()

        with open(file_path) as file:
            reader = csv.DictReader(file)

            index = 0
            unique_emails = set()

            for row in reader:
                first_name = row["first_name"]
                surname = row["surname"]
                title = row["title"]
                email = row["email"].lower()
                role = int(row["role"])
                pz_code = row["pz_code"]

                user = user_model.objects.create_or_update_user(
                    email=email,
                    password=None,
                    role=role,
                    pz_code=pz_code,
                    title=title,
                    first_name=first_name,
                    surname=surname,
                    # primary employer is the first row we see for that email
                    is_primary_employer=email not in unique_emails,
                )

                index += 1
                unique_emails.add(email)

                logger.info(
                    f"User {email} successfully created in {pz_code}. Groups: {[group.name for group in user.groups.all()]}"
                )

        logger.info(
            f"🔥 {index} rows processed, {len(unique_emails)} users successfully created or updated."
        )

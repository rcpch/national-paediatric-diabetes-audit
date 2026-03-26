import json
import collections

from asgiref.sync import async_to_sync
import numpy as np

from django.apps import apps
from django.core.management.base import BaseCommand
from django.utils import timezone

from project.constants.csv_headings import csv_definition_for
from project.npda.models import NPDAUser, PaediatricDiabetesUnit, Submission
from project.npda.general_functions.csv import (
    csv_upload,
    csv_parse,
    create_csv_submission,
    tidy_up_old_submissions,
)


class Command(BaseCommand):
    help = (
        "Upload a CSV file. Command line equivalent of uploading via the web interface"
    )

    def add_arguments(self, parser):
        parser.add_argument("--file", type=str, required=True, help="File to upload")

        parser.add_argument(
            "--user",
            type=int,
            required=True,
            help="NPDA ID (primary key) of the user uploading the file",
        )

        parser.add_argument(
            "--pz-code",
            type=str,
            help="PZ code of the PDU for the upload",
        )

        parser.add_argument(
            "--audit-year",
            type=str,
            required=True,
            help="Audit year for the upload",
        )

        parser.add_argument(
            "--import-as-questionnaire-entries",
            action="store_true",
            help="""Import data from the file as if it were submitted using the questionnaire.
                    Assign each row to a PDU using the 'PDU Number' column".
                    Will create a questionnaire submission for each PDU in the file.
                    If any submissions already exist no data will be imported.
                    Designed for bulk import patient data from the old platform.""",
        )

        parser.add_argument(
            "--merge-into-existing-questionnaire-submissions",
            action="store_true",
            help="""Requires --import-as-questionnaire-entries.
                    Adds patients to the existing questionnaire submission for each PDU.
                    If the submission does not already exist, one is created.
                    For each row we look up the patient by NHS number (unique reference number in Jersey)
                    and will only add data for patients that do not already exist""",
        )

    def print_errors(self, errors):
        for row, errors_by_field in errors.items():
            # Zero based indexing and +1 for the header
            print(f"\tRow {row + 2}:")
            for field, error in errors_by_field.items():
                print(f"\t\t{field}: {error}")

    def upload_csv_to_single_pdu(
        self, audit_year, pdu_pz_code, user, parsed_csv, csv_file_bytes, csv_file_name
    ):
        pdu = PaediatricDiabetesUnit.objects.get(pz_code=pdu_pz_code)
        AuditPeriod = apps.get_model("npda", "AuditPeriod")
        audit_period = AuditPeriod.objects.filter(start_date__year=audit_year).first()

        submission = create_csv_submission(
            pdu=pdu,
            audit_year=audit_year,  # compatibility
            audit_period=audit_period,
            csv_file_bytes=csv_file_bytes,
            csv_file_name=csv_file_name,
            user=user,
        )

        errors = async_to_sync(csv_upload)(
            dataframe=parsed_csv.df,
            errors_to_return=parsed_csv.errors_to_return,
            csv_file_name=csv_file_name,
            submission=submission,
        )

        tidy_up_old_submissions(pdu=pdu, new_submission=submission)

        if errors:
            print(f"Errors during upload:")
            self.print_errors(errors)

    def upload_as_questionnaire_entries(
        self,
        audit_year,
        pdu_pz_code,
        user,
        parsed_csv,
        csv_file_name,
        merge_into_existing_questionnaire_submissions=False,
    ):
        df = parsed_csv.df

        if parsed_csv.errors_to_return:
            print(f"Errors during parsing:")
            self.print_errors(parsed_csv.errors_to_return)

        # Remember the row from the original CSV file, even though we are about to slice it by PDU
        df = df.assign(row_index=np.arange(df.shape[0]))

        pz_codes_that_need_submissions = set()
        pz_codes_that_already_have_submissions = set()

        submissions_by_pz_code = {}

        audit_period = (
            apps.get_model("npda", "AuditPeriod")
            .objects.filter(start_date__year=audit_year)
            .first()
        )

        for pz_code in df["PDU Number"].unique():
            try:
                pdu = PaediatricDiabetesUnit.objects.get(pz_code=pz_code)
            except PaediatricDiabetesUnit.DoesNotExist:
                raise ValueError(f"Invalid PDU Number: {pz_code}")

            try:
                submission = Submission.objects.get(
                    paediatric_diabetes_unit=pdu,
                    audit_period=audit_period,
                    submission_active=True,
                )
            except Submission.DoesNotExist:
                submission = None

            if submission:
                if merge_into_existing_questionnaire_submissions:
                    submissions_by_pz_code[pz_code] = submission
                else:
                    pz_codes_that_already_have_submissions.add(pz_code)
            else:
                pz_codes_that_need_submissions.add(pz_code)

        if (
            not merge_into_existing_questionnaire_submissions
            and len(pz_codes_that_already_have_submissions) > 0
        ):
            raise ValueError(
                f"Submissions already exist for the following PDUs: {pz_codes_that_already_have_submissions}"
            )

        for pz_code in pz_codes_that_need_submissions:
            pdu = PaediatricDiabetesUnit.objects.get(pz_code=pz_code)
            audit_period = (
                apps.get_model("npda", "AuditPeriod")
                .objects.filter(start_date__year=audit_year)
                .first()
            )
            submission = Submission.objects.create(
                audit_period=audit_period,
                paediatric_diabetes_unit=pdu,
                submission_active=True,
                submission_by=user,
                submission_date=timezone.now(),
            )

            submissions_by_pz_code[pz_code] = submission

        for pz_code, submission in submissions_by_pz_code.items():
            pdu_df = df[df["PDU Number"] == pz_code]

            identifier_field = (
                "unique_reference_number" if pz_code == "PZ248" else "nhs_number"
            )
            identifier_column = csv_definition_for(identifier_field)["heading"]

            existing_patient_identifiers = submission.patients.values_list(
                identifier_field, flat=True
            )

            if existing_patient_identifiers:
                print(
                    f"Skipping the following patients as they are already in the submission:"
                )
                for identifier in existing_patient_identifiers:
                    print(f"\t{identifier}")
                    pdu_df = pdu_df[pdu_df[identifier_column] != identifier]

            # HACK: eagerly load paediatric_diabetes_unit to avoid crash doing it later from the async context in csv_upload
            submission.paediatric_diabetes_unit

            errors = async_to_sync(csv_upload)(
                dataframe=pdu_df,
                errors_to_return=collections.defaultdict(
                    lambda: collections.defaultdict(list)
                ),
                csv_file_name=csv_file_name,
                submission=submission,
                allow_empty_visits=True,
                save_errors_on_submission=False,
            )

            if errors:
                print(f"Errors found during import for {pz_code}:")
                self.print_errors(errors)

    def handle(self, *args, **options):
        user_pk = options["user"]
        user = NPDAUser.objects.get(pk=user_pk)

        audit_year = int(options["audit_year"])

        if options["import_as_questionnaire_entries"] and options["pz_code"]:
            raise ValueError(
                "Cannot specify both --pz-code and --use-pz-codes-from-file"
            )

        if not options["import_as_questionnaire_entries"] and not options["pz_code"]:
            raise ValueError(
                "Must specify either --pz-code or --use-pz-codes-from-file"
            )

        if options["import_as_questionnaire_entries"]:
            pdu_pz_code = None
        else:
            pdu_pz_code = options["pz_code"]

        with open(options["file"], "rb") as f:
            csv_file_name = f.name
            csv_file_bytes = f.read()

        parsed_csv = csv_parse(options["file"])

        if pdu_pz_code:
            self.upload_csv_to_single_pdu(
                audit_year, pdu_pz_code, user, parsed_csv, csv_file_bytes, csv_file_name
            )
        else:
            self.upload_as_questionnaire_entries(
                audit_year,
                pdu_pz_code,
                user,
                parsed_csv,
                csv_file_name,
                options["merge_into_existing_questionnaire_submissions"],
            )

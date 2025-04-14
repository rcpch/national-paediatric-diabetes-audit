import json

from asgiref.sync import async_to_sync

from django.core.management.base import BaseCommand
from django.utils import timezone

from project.npda.models import (
    NPDAUser,
    PaediatricDiabetesUnit,
    Submission
)
from project.npda.general_functions import get_current_audit_year
from project.npda.general_functions.csv import (
    csv_upload,
    csv_parse,
    csv_header,
    create_csv_submission,
    tidy_up_old_submissions
)


class Command(BaseCommand):
    help = (
        "Upload a CSV file. Command line equivalent of uploading via the web interface"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            required=True,
            help="File to upload"
        )

        parser.add_argument(
            "--user",
            type=int,
            required=True,
            help="NPDA ID (primary key) of the user uploading the file"
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
                    Designed for bulk import patient data from the old platform."""
        )

    def upload_csv_to_single_pdu(self, audit_year, pdu_pz_code, user, parsed_csv, csv_file_bytes, csv_file_name):
        pdu = PaediatricDiabetesUnit.objects.get(pz_code=pdu_pz_code)

        submission = async_to_sync(create_csv_submission)(
            pdu=pdu,
            audit_year=audit_year,
            csv_file_bytes=csv_file_bytes,
            csv_file_name=csv_file_name,
            user=user
        )   
    
        errors = async_to_sync(csv_upload)(
            dataframe=parsed_csv.df,
            errors_to_return=parsed_csv.errors_to_return,
            csv_file_name=csv_file_name,
            submission=submission
        )

        async_to_sync(tidy_up_old_submissions)(
            pdu=pdu,
            new_submission=submission
        )

        return errors
    
    def upload_as_questionnaire_entries(self, audit_year, pdu_pz_code, user, parsed_csv):
        df = parsed_csv.df

        pz_codes_that_need_submissions = set()
        pz_codes_that_already_have_submissions = set()

        for pz_code in df["PDU Number"].unique():
            try:
                pdu = PaediatricDiabetesUnit.objects.get(pz_code=pz_code)
            except PaediatricDiabetesUnit.DoesNotExist:
                raise ValueError(f"Invalid PDU Number: {pz_code}")
            
            has_existing_submission = Submission.objects.filter(
                paediatric_diabetes_unit=pdu,
                audit_year=audit_year,
                submission_active=True
            ).exists()

            if(has_existing_submission):
                pz_codes_that_already_have_submissions.add(pz_code)
            else:
                pz_codes_that_need_submissions.add(pz_code)
        
        if len(pz_codes_that_already_have_submissions) > 0:
            raise ValueError(
                f"Submissions already exist for the following PDUs: {pz_codes_that_already_have_submissions}"
            )
        
        submissions_by_pz_code = {}

        for pz_code in pz_codes_that_need_submissions:
            pdu = PaediatricDiabetesUnit.objects.get(pz_code=pz_code)

            submission = Submission.objects.create(
                audit_year=audit_year,
                paediatric_diabetes_unit=pdu,
                submission_active=True,
                submission_by=user,
                submission_date=timezone.now()
            )

            submissions_by_pz_code[pz_code] = submission


    def handle(self, *args, **options):
        user_pk = options["user"]
        user = NPDAUser.objects.get(pk=user_pk)

        if options["audit_year"]:
            audit_year = int(options["audit_year"])
        else:
            # TODO MRB: replace this with AuditPeriod before merging https://github.com/rcpch/national-paediatric-diabetes-audit/pull/865
            audit_year = get_current_audit_year()

        if options["import_as_questionnaire_entries"] and options["pz_code"]:
            raise ValueError("Cannot specify both --pz-code and --use-pz-codes-from-file")

        if not options["import_as_questionnaire_entries"] and not options["pz_code"]:
            raise ValueError("Must specify either --pz-code or --use-pz-codes-from-file")

        if options["import_as_questionnaire_entries"]:
            pdu_pz_code = None
        else:
            pdu_pz_code = options["pz_code"]

        is_jersey = pdu_pz_code == "PZ248"

        with open(options["file"], "rb") as f:
            csv_file_name = f.name
            csv_file_bytes = f.read()

        parsed_csv = csv_parse(options["file"], is_jersey=is_jersey)

        if pdu_pz_code:
            errors = self.upload_csv_to_single_pdu(
                audit_year, pdu_pz_code, user, parsed_csv, csv_file_bytes, csv_file_name
            )
        else:
            errors = self.upload_as_questionnaire_entries(
                audit_year, pdu_pz_code, user, parsed_csv
            )

        if errors:
            print(json.dumps(errors))

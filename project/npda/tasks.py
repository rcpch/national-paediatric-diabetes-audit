import logging
import io

from celery import shared_task
from asgiref.sync import async_to_sync

from project.npda.models.paediatric_diabetes_unit import PaediatricDiabetesUnit
from project.npda.models.submission import Submission
from project.npda.general_functions.csv import (
    csv_parse,
    csv_upload,
    tidy_up_old_submissions,
)

logger = logging.getLogger(__name__)


@shared_task
def test_task():
    logger.info("Hello from the Celery test task!")
    logger.info("These are the PDUs registered in the database:")

    for pdu in PaediatricDiabetesUnit.objects.all():
        logger.info(f"\t{pdu.lead_organisation_name} [{pdu.pz_code}]")


@shared_task
def upload_csv_task(submission_id):
    logger.info("Hello from the Celery upload csv task!")

    submission = Submission.objects.get(id=submission_id)

    logger.info(f"This is the submission to process: {submission} [{submission.id}]")

    # Determine the dataset year from the CSV data (use integer year)
    try:
        dataset_year = submission.audit_period.get_dataset_year()
    except Exception:
        # Fallback to 2021 for safety
        logger.exception(
            "Failed to determine audit year from submission.audit_period; defaulting to 2021"
        )
        dataset_year = 2021

    # CSV parsing errors are done inline in the route that handles the file upload
    parsed_csv = csv_parse(io.BytesIO(submission.csv_file), dataset_year=dataset_year)

    csv_upload_sync = async_to_sync(csv_upload)

    csv_upload_sync(
        dataframe=parsed_csv.df,
        errors_to_return=parsed_csv.errors_to_return,
        csv_file_name=submission.csv_file_name,
        submission=submission,
    )

    logger.info(f"Processed submission {submission.id}. Activating it now")
    submission.submission_active = True
    submission.save()

    tidy_up_old_submissions(
        pdu=submission.paediatric_diabetes_unit,
        new_submission=submission,
    )

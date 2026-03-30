import io
import logging

from asgiref.sync import async_to_sync
from django_tasks import task

from project.npda.general_functions.csv import (
    csv_parse,
    csv_upload,
    tidy_up_old_submissions,
)
from project.npda.models.paediatric_diabetes_unit import PaediatricDiabetesUnit
from project.npda.models.submission import Submission

logger = logging.getLogger(__name__)


@task()
def test_task():
    logger.info("Hello from the Django test task!")
    logger.info("These are the PDUs registered in the database:")

    for pdu in PaediatricDiabetesUnit.objects.all():
        logger.info(f"\t{pdu.lead_organisation_name} [{pdu.pz_code}]")


@task()
def upload_csv_task(submission_id):
    logger.info("Hello from the Django upload csv task!")

    submission = Submission.objects.get(id=submission_id)

    logger.info(f"This is the submission to process: {submission} [{submission.id}]")

    # CSV parsing errors are done inline in the route that handles the file upload
    parsed_csv = csv_parse(io.BytesIO(submission.csv_file))

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

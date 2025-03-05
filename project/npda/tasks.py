from celery import shared_task
import logging

from project.npda.models.paediatric_diabetes_unit import PaediatricDiabetesUnit

logger = logging.getLogger(__name__)


@shared_task
def test_task():
    logger.info("Hello from the Celery test task!")
    logger.info("These are the PDUs registered in the database:")

    for pdu in PaediatricDiabetesUnit.objects.all():
        logger.info(f"\t{pdu.lead_organisation_name} [{pdu.pz_code}]")
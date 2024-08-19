import logging
from django.apps import apps
from django.db import DatabaseError
from project.npda.general_functions import (
    get_all_pz_codes_with_their_trust_and_primary_organisation,
)

logger = logging.getLogger(__name__)


def paediatric_diabetes_units_seeder():
    """
    Seed the database with paediatric diabetes units
    """

    PaediatricDiabetesUnit = apps.get_model("npda", "PaediatricDiabetesUnit")

    # Get all PZ codes with their trust and primary organisation
    # seed = True means that we are fetching the data from the RCPCH API as JSON rather than as a list of choices
    if PaediatricDiabetesUnit.objects.count() > 0:
        logger.info("PaediatricDiabetesUnit records already exist in the database")
        return

    pdus = get_all_pz_codes_with_their_trust_and_primary_organisation()

    for pdu in pdus:
        try:
            parent_ods_code = (pdu.get("parent") or {}).get("ods_code")
            parent_name = (pdu.get("parent") or {}).get("name")
            PaediatricDiabetesUnit.objects.update_or_create(
                pz_code=pdu["pz_code"],
                defaults={
                    "lead_organisation_ods_code": pdu["primary_organisation"][
                        "ods_code"
                    ],
                    "lead_organisation_name": pdu["primary_organisation"]["name"],
                    "parent_ods_code": parent_ods_code,
                    "parent_name": parent_name,
                },
            )
        except DatabaseError as e:
            logger.error(f"Error creating PaediatricDiabetesUnit: {e}")
            continue

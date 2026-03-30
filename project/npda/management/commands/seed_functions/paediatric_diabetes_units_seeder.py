import logging

from django.apps import apps
from django.contrib.gis.geos import Point
from django.db import DatabaseError

from project.npda.general_functions import (
    fetch_organisation_by_ods_code,
    get_all_pz_codes_with_their_trust_and_primary_organisation,
)

logger = logging.getLogger(__name__)

RCPCH_TESTING_PDUS = {
    "PZ999": "ROYAL COLLEGE OF PAEDIATRICS AND CHILD HEALTH",  # RCPCH Internal Testing
    "PZ998": "EXTERNAL TESTING",  # (eg pen test, NPDA network managers)
    "PZ997": "AUTOMATED TESTING",
}


def add_geocoordinates(pdu):
    if pdu.lead_organisation_geocoordinates is None:
        geocoordinates = fetch_organisation_by_ods_code(
            ods_code=pdu.lead_organisation_ods_code
        )
        pdu.lead_organisation_geocoordinates = Point(
            x=geocoordinates["longitude"],
            y=geocoordinates["latitude"],
            srid=4326,
        )
    pdu.save()
    logger.info(f"Geocoordinates for {pdu.lead_organisation_name} updated")


def paediatric_diabetes_units_seeder():
    """
    Seed the database with paediatric diabetes units
    """

    PaediatricDiabetesUnit = apps.get_model("npda", "PaediatricDiabetesUnit")

    # Get all PZ codes with their trust and primary organisation
    # seed = True means that we are fetching the data from the RCPCH API as JSON rather than as a list of choices
    if PaediatricDiabetesUnit.objects.count() > 0:
        logger.info(
            "PaediatricDiabetesUnit records already exist in the database. Updating existing records..."
        )
        pass

    pdus = get_all_pz_codes_with_their_trust_and_primary_organisation()

    for pdu in pdus:
        pz_code = pdu.get("pz_code")

        if pz_code in RCPCH_TESTING_PDUS:
            continue

        try:
            parent_ods_code = (pdu.get("parent") or {}).get("ods_code")
            parent_name = (pdu.get("parent") or {}).get("name")
            network_name = (pdu.get("paediatric_diabetes_network") or {}).get("name")
            network_code = (pdu.get("paediatric_diabetes_network") or {}).get("pn_code")
            lead_organisation_ods_code = (pdu.get("primary_organisation") or {}).get(
                "ods_code"
            )
            lead_organisation_name = pdu.get("name")
            last_updated = pdu.get("last_updated") or None
            active = pdu.get("active") or False

            if not lead_organisation_ods_code:
                logger.warning(
                    f"Primary organisation ODS code not found for PDU: {pz_code}"
                )
                continue
            if not parent_ods_code:
                logger.warning(f"Parent ODS code not found for PDU: {pz_code}")
                continue
            if not parent_name:
                logger.warning(f"Parent name not found for PDU: {pz_code}")
                continue
            if not network_name:
                logger.warning(f"Network name not found for PDU: {pz_code}")
                continue
            if not network_code:
                logger.warning(f"Network code not found for PDU: {pz_code}")
                continue
            if not pz_code:
                logger.warning(f"PZ code not found for PDU: {pz_code}")
                continue

            new_pdu, created = PaediatricDiabetesUnit.objects.update_or_create(
                pz_code=pz_code,
                defaults={
                    "lead_organisation_ods_code": lead_organisation_ods_code,
                    "lead_organisation_name": lead_organisation_name,
                    "parent_ods_code": parent_ods_code,
                    "parent_name": parent_name,
                    "paediatric_diabetes_network_code": network_code,
                    "paediatric_diabetes_network_name": network_name,
                    "active": active,
                    "last_updated": last_updated,
                },
            )

            add_geocoordinates(new_pdu)
        except DatabaseError as e:
            logger.error(f"Error creating PaediatricDiabetesUnit: {e}")
            continue

    for pz_code, name in RCPCH_TESTING_PDUS.items():
        try:
            pdu, created = PaediatricDiabetesUnit.objects.update_or_create(
                pz_code=pz_code,
                defaults={
                    "lead_organisation_ods_code": "8HV48",
                    "lead_organisation_name": name,
                    "parent_ods_code": "PZ999",
                    "parent_name": "Royal College of Paediatrics and Child Health",
                    "active": True,
                },
            )

            add_geocoordinates(pdu)
        except DatabaseError as e:
            logger.error(f"Error creating testing PaediatricDiabetesUnit: {e}")
            continue

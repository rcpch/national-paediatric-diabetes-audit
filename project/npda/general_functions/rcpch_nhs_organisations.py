"""
This module contains functions that are used to extract NHS organisations from the RCPCH dataset.
"""

# python imports
import requests
import logging
from typing import Union, Dict, Any, List, Tuple

# django imports
from django.apps import apps
from django.conf import settings
from django.db import DatabaseError
from django.forms.models import model_to_dict
from requests.exceptions import HTTPError

# RCPCH imports
from project.constants.organisations_objects import OrganisationRCPCH


# Logging
logger = logging.getLogger(__name__)


def get_nhs_organisation(ods_code: str) -> Union[OrganisationRCPCH, Dict[str, Any]]:
    """
    This function returns details of an NHS organisation against an ODS code from the RCPCH dataset.
    """

    url = (
        f"{settings.RCPCH_NHS_ORGANISATIONS_API_URL}/organisations/?ods_code={ods_code}"
    )

    organisation_details = _get_nhs_organisation_from_url(url)

    return organisation_details


def _get_nhs_organisation_from_url(
    url: str,
) -> Union[OrganisationRCPCH, Dict[str, Any]]:
    """
    Fetch NHS organisation details from the given URL using the provided ODS code.

    Args:
        ods_code (str): The ODS code of the NHS organisation.
        url (str): The URL to fetch the NHS organisation details from.

    Returns:
        dict: The details of the NHS organisation if the request is successful,
              or an error message if the request fails.
    """
    ERROR_STRING = "An error occurred while fetching NHS organisation details."
    try:
        response = requests.get(url=url, timeout=10)
        response.raise_for_status()
        # Convert response to OrganisationRCPCH object
        return OrganisationRCPCH.from_json(response.json()[0])
    except HTTPError as http_err:
        logger.error(
            f"HTTP error occurred fetching organisation details from {url=}: {http_err.response.text}"
        )
        return {"error": ERROR_STRING}
    except Exception as err:
        logger.error(
            f"An error occurred fetching organisation details from {url=}: {err}"
        )
        return {"error": ERROR_STRING}


def get_all_nhs_organisations() -> List[Tuple[str, str]]:
    """
    This function returns all NHS organisations from the RCPCH dataset and returns them to the caller as a list of tuples.
    These are typically used in Django forms as choices.

    url = f"{settings.RCPCH_NHS_ORGANISATIONS_API_URL}/organisations/limited"
    If error reaching the API, it returns a list with a single tuple containing:
        [("999", "An error occurred while fetching NHS organisations.")].

    Returns:
        List[Tuple[str, str]]: A list of tuples containing the ODS code and name of NHS organisations.
    """
    url = f"{settings.RCPCH_NHS_ORGANISATIONS_API_URL}/organisations/limited"
    ERROR_RESPONSE = [("999", "An error occurred while fetching NHS organisations.")]

    try:
        response = requests.get(url=url, timeout=10)  # times out after 10 seconds
        response.raise_for_status()

        # Convert the response to choices list
        organisation_list = [
            (organisation.get("ods_code"), organisation.get("name"))
            for organisation in response.json()
        ]

        return organisation_list
    except HTTPError as e:
        logger.error(f"HTTP error occurred: {e.response.text}")
        return ERROR_RESPONSE
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return ERROR_RESPONSE


def get_all_nhs_organisations_affiliated_with_paediatric_diabetes_unit() -> (
    List[Tuple[str, str]]
):
    """
    This function returns all NHS organisations from the RCPCH dataset that are affiliated with a paediatric diabetes unit.
    If an error occurs while fetching the data, it returns a list with a single tuple containing:
        [("999", "An error occurred while fetching NHS organisations.")].

    Returns:
        List[Tuple[str, str]]: A list of tuples containing the ODS code and name of NHS organisations.
    """
    url = f"{settings.RCPCH_NHS_ORGANISATIONS_API_URL}/organisations/paediatric-diabetes-units"
    ERROR_RESPONSE = [("999", "An error occurred while fetching NHS organisations.")]

    try:
        response = requests.get(url=url, timeout=10)  # times out after 10 seconds
        response.raise_for_status()

        # Convert the response to choices list
        organisation_list = [
            (organisation.get("ods_code"), organisation.get("name"))
            for organisation in response.json()
        ]

        return organisation_list
    except HTTPError as e:
        logger.error(f"HTTP error occurred: {e.response.text}")
        return ERROR_RESPONSE
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return ERROR_RESPONSE


def get_all_pz_codes_with_their_trust_and_primary_organisation() -> (
    List[Tuple[str, str]]
):
    """
    This function returns all NHS organisations from the RCPCH dataset that are affiliated with a paediatric diabetes unit.
    Accepts a seed parameter - if True, it will seed the database with the data.
    If False, it will return the data as a list of tuples.

    If an error occurs while fetching the data, it returns a list with a single tuple containing:
        [("999", "An error occurred while fetching NHS organisations.")].

    Returns:
        List[Tuple[str, str]]: A list of tuples containing the ODS code and name of NHS organisations.
    """
    url = f"{settings.RCPCH_NHS_ORGANISATIONS_API_URL}/paediatric_diabetes_units/trust"
    ERROR_RESPONSE = [("999", "An error occurred while fetching NHS organisations.")]

    try:
        response = requests.get(url=url, timeout=10)  # times out after 10 seconds
        response.raise_for_status()

        return response.json()

    except HTTPError as e:
        logger.error(f"HTTP error occurred: {e.response.text}")
        return ERROR_RESPONSE
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return ERROR_RESPONSE


def maintain_paediatric_diabetes_unit_records_against_rcpch_nhs_organisations_API():
    """
    This function checks if the NHS organisations in the RCPCH dataset match the locally stored PZ codes.
    If there are any mismatches, it logs the mismatch and updates the local database with the correct data.
    """
    PaediatricDiabetesUnit = apps.get_model("npda", "PaediatricDiabetesUnit")

    # Get all PZ codes with their trust and primary organisation
    pdus = get_all_pz_codes_with_their_trust_and_primary_organisation()

    # Check if the NHS organisations in the RCPCH dataset match the locally stored PZ codes
    logger.info(
        f"Checking PaediatricDiabetesUnit list against RCPCH NHS Organisations API..."
    )
    for pdu in pdus:

        # Check if the PZ code exists in the local database
        pdu_obj = None
        if PaediatricDiabetesUnit.objects.filter(pz_code=pdu["pz_code"]).exists():
            pdu_obj = PaediatricDiabetesUnit.objects.get(pz_code=pdu["pz_code"])

        # update or create the PaediatricDiabetesUnit
        parent_ods_code = (pdu.get("parent") or {}).get("ods_code")
        parent_name = (pdu.get("parent") or {}).get("name")

        try:
            new_pdu, created = PaediatricDiabetesUnit.objects.update_or_create(
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
        except Exception as e:
            logger.error(f"Error creating PaediatricDiabetesUnit: {e}")
            pass

        if created:
            logger.info(
                f"Created PaediatricDiabetesUnit: {new_pdu.pz_code} ({new_pdu.lead_organisation_name})"
            )
        else:
            if pdu_obj is not None:
                if model_to_dict(pdu_obj) != model_to_dict(new_pdu):
                    logger.info(
                        f"{new_pdu.pz_code} ({new_pdu.lead_organisation_name}) was updated."
                    )

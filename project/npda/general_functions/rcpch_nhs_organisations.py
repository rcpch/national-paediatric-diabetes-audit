"""
This module contains functions that are used to extract NHS organisations from the RCPCH dataset.
"""

# python imports
import requests
import logging
from typing import Union, Dict, Any, List, Tuple

# django imports
from django.conf import settings
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


# [
#   {
#     "ods_code": "RGT01",
#     "name": "ADDENBROOKE'S HOSPITAL",
#     "website": "https://www.cuh.nhs.uk/",
#     "address1": "HILLS ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "01223 245151",
#     "city": "CAMBRIDGE",
#     "county": "CAMBRIDGESHIRE",
#     "latitude": 52.17513275,
#     "longitude": 0.140753239,
#     "postcode": "CB2 0QQ",
#     "geocode_coordinates": "SRID=27700;POINT (0.140753239 52.17513275)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ041"
#     },
#     "trust": {
#       "ods_code": "RGT",
#       "name": "CAMBRIDGE UNIVERSITY HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "CAMBRIDGE BIOMEDICAL CAMPUS",
#       "address_line_2": "HILLS ROAD",
#       "town": "CAMBRIDGE",
#       "postcode": "CB2 0QQ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000056",
#       "name": "NHS Cambridgeshire and Peterborough Integrated Care Board",
#       "ods_code": "QUE"
#     },
#     "nhs_england_region": {
#       "region_code": "Y61",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000007",
#       "name": "East of England"
#     },
#     "openuk_network": {
#       "name": "Eastern Paediatric Epilepsy Network",
#       "boundary_identifier": "EPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RCF22",
#     "name": "AIREDALE GENERAL HOSPITAL",
#     "website": "https://www.airedaletrust.nhs.uk/",
#     "address1": "SKIPTON ROAD",
#     "address2": "STEETON",
#     "address3": "",
#     "telephone": "",
#     "city": "KEIGHLEY",
#     "county": "WEST YORKSHIRE",
#     "latitude": 53.8979454,
#     "longitude": -1.962710142,
#     "postcode": "BD20 6TD",
#     "geocode_coordinates": "SRID=27700;POINT (-1.962710142 53.8979454)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ047"
#     },
#     "trust": {
#       "ods_code": "RCF",
#       "name": "AIREDALE NHS FOUNDATION TRUST",
#       "address_line_1": "AIREDALE GENERAL HOSPITAL",
#       "address_line_2": "SKIPTON ROAD",
#       "town": "KEIGHLEY",
#       "postcode": "BD20 6TD",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000054",
#       "name": "NHS West Yorkshire Integrated Care Board",
#       "ods_code": "QWO"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Yorkshire Paediatric Neurology Network",
#       "boundary_identifier": "YPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },

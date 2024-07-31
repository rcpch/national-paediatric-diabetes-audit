# Python imports
import logging
from typing import Tuple, List, Union

# third party libraries
import requests
from requests.exceptions import HTTPError

# npda imports
from django.conf import settings

# Logging
logger = logging.getLogger(__name__)

# Define custom return types
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class OrganisationODSAndName:
    ods_code: str
    name: str


@dataclass
class PDUWithOrganisations:
    pz_code: str
    organisations: list[OrganisationODSAndName]


def get_all_pdus_with_grouped_organisations() -> List[PDUWithOrganisations]:
    """
    Returns all PDUs from the RCPCH NHS Organisations API with member organisations nested under each PDU.

    Returns:
        List[PDUWithOrganisations]: A list of PDUWithOrganisations instances.
    """
    BASE_URL = settings.RCPCH_NHS_ORGANISATIONS_API_URL
    request_url = f"{BASE_URL}/paediatric_diabetes_units/organisations/"

    try:
        response = requests.get(url=request_url, timeout=10)
        response.raise_for_status()
    except HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err.response.text}")
        raise Exception("PDUs not found") from http_err
    except Exception as err:
        logger.error(f"An error occurred: {err}")
        raise Exception("PDUs not found") from err

    logger.warning(f"Response JSON: {response.json()}")

    data = response.json()
    pdus = [
        PDUWithOrganisations(
            pz_code=pdu["pz_code"],
            organisations=[
                OrganisationODSAndName(**org) for org in pdu["organisations"]
            ],
        )
        for pdu in data
    ]

    return pdus


def get_all_pdus_list_choices() -> List[Tuple[str, str]]:
    """
    Fetches all Paediatric Diabetes Units (PDUs) from the RCPCH NHS Organisations API
    and returns them as a sorted list of choices for Django forms.

    Returns:
        List[Tuple[str, str]]: A sorted list of tuples containing PDU codes and their names, or an error value if PDUs are not found.
    """
    url = settings.RCPCH_NHS_ORGANISATIONS_API_URL
    request_url = f"{url}/paediatric_diabetes_units/extended"

    try:
        response = requests.get(request_url, timeout=10)  # times out after 10 seconds
        response.raise_for_status()
        pdu_list = response.json()

        # Sort the PDU list by the PZ code. If PZ code after the first 2 characters is invalid (i.e. not a number), then sort it to the end.
        sorted_pdu_list = sorted(
            [(pdu["pz_code"], pdu["pz_code"]) for pdu in pdu_list],
            key=lambda x: int(x[1][2:]) if x[1][2:].isdigit() else float("inf"),
        )
        return sorted_pdu_list
    except HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err.response.text}")
    except Exception as err:
        logger.error(f"An error occurred: {err}")

    # Return an error value in the same format
    return [("error", "PDUs not found")]


def get_single_pdu_from_pz_code(pz_number: str) -> Union[PDUWithOrganisations, dict]:
    """
    Fetches a specific Paediatric Diabetes Unit (PDU) with its associated organisations from the RCPCH NHS Organisations API.

    Args:
        pz_number (str): The PZ code of the Paediatric Diabetes Unit.

    Returns:
        Union[PDUWithOrganisations, dict]: A PDUWithOrganisations object if the request is successful, or a dictionary indicating an error.
    """
    url = settings.RCPCH_NHS_ORGANISATIONS_API_URL
    request_url = f"{url}/paediatric_diabetes_units/organisations/?pz_code={pz_number}"

    try:
        response = requests.get(request_url, timeout=10)  # times out after 10 seconds
        response.raise_for_status()
        data = response.json()[0]
        pdu = PDUWithOrganisations(
            pz_code=data["pz_code"],
            organisations=[
                OrganisationODSAndName(**org) for org in data["organisations"]
            ],
        )
        return pdu
    except HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err.response.text}")
    except Exception as err:
        logger.error(f"An error occurred: {err}")

    # Return an error value in the same format
    return {"error": f"{pz_number=} not found"}


# TODO MRB: this should return dataclasses too
def get_single_pdu_from_ods_code(
    ods_code: str,
) -> PDUWithOrganisations:
    """
    Fetches a specific Paediatric Diabetes Unit (PDU) with its associated organisations from the RCPCH NHS Organisations API using the ODS code.

    Args:
        ods_code (str): The ODS code of the Paediatric Diabetes Unit.

    Returns:
        list[PDUWithOrganisations]: A list of PDUWithOrganisations objects. Error values if PDUs are not found.
    """
    # Ensure the ODS code is uppercase
    ods_code = ods_code.upper()

    url = settings.RCPCH_NHS_ORGANISATIONS_API_URL
    request_url = f"{url}/paediatric_diabetes_units/sibling-organisations/{ods_code}"

    try:
        response = requests.get(request_url, timeout=10)  # times out after 10 seconds
        response.raise_for_status()
        data = response.json()[0]
        logger.warning(f"Data: {data}")
        return PDUWithOrganisations(
            pz_code=data["pz_code"],
            organisations=[
                OrganisationODSAndName(name=org["name"], ods_code=org["ods_code"])
                for org in data["organisations"]
            ],
        )
    except HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err.response.text}")
    except Exception as err:
        logger.error(f"An error occurred: {err}\n{ods_code=}{response.json()=}")

    # Return an error value in the same format
    return PDUWithOrganisations(
        pz_code="error",
        organisations=[OrganisationODSAndName(ods_code="error", name="PDUs not found")],
    )

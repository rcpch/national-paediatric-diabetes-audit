# third party libraries
import requests
from requests.exceptions import HTTPError

# npda imports
from django.conf import settings


def retrieve_pdus():
    """
    Returns all PDUs from the RCPCH NHS Organisations API
    """

    url = settings.RCPCH_NHS_ORGANISATIONS_API_URL
    request_url = f"{url}/paediatric_diabetes_units/organisations/"

    try:
        response = requests.get(
            url=request_url,
            timeout=10,  # times out after 10 seconds
        )
        response.raise_for_status()
    except HTTPError as e:
        print(e.response.text)
        raise Exception("PDUs not found")

    return response.json()


def retrieve_pdu(pz_number):
    """
    Returns GP practice as an object from NHS API against a postcode
    """

    url = settings.RCPCH_NHS_ORGANISATIONS_API_URL
    request_url = f"{url}/paediatric_diabetes_units/organisations/?pz_code={pz_number}"

    try:
        response = requests.get(
            url=request_url,
            timeout=10,  # times out after 10 seconds
        )
        response.raise_for_status()
    except HTTPError as e:
        print(e.response.text)
        raise Exception(f"{pz_number} not found")

    return response.json()


def retrieve_pdu_from_organisation_ods_code(ods_code):
    """
    Returns GP practice as an object from NHS API against a postcode
    """
    # must be uppercase
    ods_code = ods_code.upper()

    url = settings.RCPCH_NHS_ORGANISATIONS_API_URL
    request_url = f"{url}/paediatric_diabetes_units/sibling-organisations/{ods_code}/"

    try:
        response = requests.get(
            url=request_url,
            timeout=10,  # times out after 10 seconds
        )
        response.raise_for_status()
    except HTTPError as e:
        print(e.response.text)
        raise Exception(f"{ods_code} not found")

    return response.json()

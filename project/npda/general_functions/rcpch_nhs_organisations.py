"""
This module contains functions that are used to extract NHS organisations from the RCPCH dataset.
"""

# python imports
import requests

# django imports
from django.conf import settings
from requests.exceptions import HTTPError

# RCPCH imports


def get_nhs_organisation(ods_code: str):
    """
    This function returns details of an NHS organisation against an ODS code from the RCPCH dataset.
    """

    url = f"{settings.RCPCH_NHS_ORGANISATIONS_URL}/organisations/?ods_code={ods_code}"

    try:
        response = requests.get(
            url=url,
            timeout=10,  # times out after 10 seconds
        )
        response.raise_for_status()
    except HTTPError as e:
        print(e.response.text)
        raise Exception(f"{ods_code} not found")

    return response.json()[0]


def get_all_nhs_organisations():
    """
    This function returns all NHS organisations from the RCPCH dataset.
    """

    url = f"{settings.RCPCH_NHS_ORGANISATIONS_URL}/organisations"

    try:
        response = requests.get(
            url=url,
            timeout=10,  # times out after 10 seconds
        )
        response.raise_for_status()
    except HTTPError as e:
        print(e.response.text)
        raise Exception("No NHS organisations found")

    return response.json()

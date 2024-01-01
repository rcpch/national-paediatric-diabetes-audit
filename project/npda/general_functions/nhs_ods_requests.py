# python

# django

# third party libraries
import requests
from requests.exceptions import HTTPError

# npda imports
from django.conf import settings


def gp_practice_for_postcode(postcode: str):
    """
    Returns GP practice as an object from NHS API against a postcode
    """

    url = settings.NHS_SPINE_SERVICES_URL
    request_url = (
        f"{url}/organisations/?PostCode={postcode}&Status=Active&PrimaryRoleId=RO177"
    )

    try:
        response = requests.get(
            url=request_url,
            timeout=10,  # times out after 10 seconds
        )
        response.raise_for_status()
    except HTTPError as e:
        print(e.response.text)
        raise Exception(f"{postcode} not found")

    return response.json()["Organisations"][0]["OrgId"]


def gp_details_for_ods_code(ods_code: str):
    """
    Returns address, name and long/lat for ods code
    """

    url = f"{settings.NHS_SPINE_SERVICES_URL}/organisations/{ods_code}"

    try:
        response = requests.get(
            url=url,
            timeout=10,  # times out after 10 seconds
        )
        response.raise_for_status()
    except HTTPError as e:
        return {"error": e}

    return response.json()["Organisations"][0]

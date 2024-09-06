# python
import logging

# django

# third party libraries
import requests
from requests.exceptions import HTTPError

# npda imports
from django.conf import settings

# Logging
logger = logging.getLogger(__name__)


def gp_ods_code_for_postcode(postcode: str):
    url = settings.NHS_SPINE_SERVICES_URL
    request_url = (
        f"{url}/organisations/?PostCode={postcode}&Status=Active&PrimaryRoleId=RO177"
    )

    response = requests.get(
        url=request_url,
        timeout=10,  # times out after 10 seconds
    )

    response = requests.get(
        url=request_url,
        timeout=10,  # times out after 10 seconds
    )
    response.raise_for_status()

    organisations = response.json()["Organisations"]

    if len(organisations) > 0:
        return organisations[0]["OrgId"]


def gp_details_for_ods_code(ods_code: str):
    url = f"{settings.NHS_SPINE_SERVICES_URL}/organisations/{ods_code}"

    try:
        response = requests.get(
            url=url,
            timeout=10,  # times out after 10 seconds
        )

        if response.status == 404:
            return None

        response.raise_for_status()
    except HTTPError as e:
        return {"error": e}

    return response.json()["Organisation"]

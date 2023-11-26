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

    request_url = f"/organisations?PostCode={postcode}&PrimaryRoleId=RO177"

    try:
        response = requests.get(
            url=request_url,
            headers={
                "subscription-key": f"{settings.NHS_ODS_API_URL_SUBSCRIPTION_KEY}"
            },
            timeout=10,  # times out after 10 seconds
        )
        response.raise_for_status()
    except HTTPError as e:
        print(e.response.text)

    return response.json()["Organisations"][0]["OrgId"]


def gp_details_for_ods_code(ods_code: str):
    """
    Returns address, name and long/lat for ods code
    """

    request_url = f"{settings.NHS_ODS_API_URL}&search={ods_code}"

    try:
        response = requests.get(
            url=request_url,
            headers={
                "subscription-key": f"{settings.NHS_ODS_API_URL_SUBSCRIPTION_KEY}"
            },
            timeout=10,  # times out after 10 seconds
        )
        response.raise_for_status()
    except HTTPError as e:
        print(e.response.text)

    return response.json()["value"][0]

# python

# django

# third party libraries
import requests
from requests.exceptions import HTTPError

# npda imports
from django.conf import settings


def validate_postcode(postcode):
    """
    Tests if postcode is valid
    Returns boolean
    """

    request_url = f"{settings.POSTCODE_API_BASE_URL}/postcodes/{postcode}.json"

    try:
        response = requests.get(
            url=request_url,
            timeout=10,  # times out after 10 seconds
        )
        response.raise_for_status()
    except HTTPError as e:
        print(e.response.text)
        return False

    return True

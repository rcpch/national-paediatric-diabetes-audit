# python
import logging

# django

# third party libraries
import requests
from requests.exceptions import HTTPError

# npda imports
from django.conf import settings
from django.core.exceptions import ValidationError


# Logging
logger = logging.getLogger(__name__)


# TODO MRB: check all callers are checking the return value
def validate_postcode(postcode):
    """
    Tests if postcode is valid
    Returns boolean
    """

    request_url = f"{settings.POSTCODE_API_BASE_URL}/postcodes/{postcode}.json"
    
    response = requests.get(
        url=request_url,
        timeout=10,  # times out after 10 seconds
    )

    match response.status_code:
        case 200:
            return True
        
        case 404:
            return False

        case _:
            response.raise_for_status()

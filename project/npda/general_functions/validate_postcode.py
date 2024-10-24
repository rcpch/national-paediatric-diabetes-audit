# python
import logging

# django
from django.conf import settings

# third party libraries

# npda imports
from ..httpx_client import async_client


async def validate_postcode(postcode):
    """
    Tests if postcode is valid
    Returns boolean
    """

    request_url = f"{settings.POSTCODE_API_BASE_URL}/postcodes/{postcode}.json"

    response = await async_client.get().get(
        url=request_url,
        timeout=10,  # times out after 10 seconds
    )
    response.raise_for_status()

    return {
        "normalised_postcode": response.json()["data"]["id"]
    }
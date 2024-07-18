# python

# django

# third party libraries
import httpx

# npda imports
from django.conf import settings

from asgiref.sync import async_to_sync


async def avalidate_postcode(postcode, async_client):
    """
    Tests if postcode is valid
    Returns boolean
    """

    request_url = f"{settings.POSTCODE_API_BASE_URL}/postcodes/{postcode}.json"

    try:
        response = await async_client.get(
            url=request_url,
            timeout=10,  # times out after 10 seconds
        )
        response.raise_for_status()
    except httpx.HTTPError as e:
        print(e.response.text)
        return False

    return True

def validate_postcode(postcode):
    async def wrapper():
        async with httpx.AsyncClient() as client:
            return avalidate_postcode(postcode, client)
    
    return async_to_sync(wrapper)()

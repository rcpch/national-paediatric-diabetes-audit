# python
import logging 

# django

# third party libraries
import httpx
from requests.exceptions import HTTPError

# npda imports
from django.conf import settings

from ...general_functions.async_helpers import httpx_async_to_sync

# Logging
logger = logging.getLogger(__name__)

async def agp_practice_for_postcode(postcode: str, async_client: http.AsyncClient):
    """
    Returns GP practice as an object from NHS API against a postcode
    """

    url = settings.NHS_SPINE_SERVICES_URL
    request_url = (
        f"{url}/organisations/?PostCode={postcode}&Status=Active&PrimaryRoleId=RO177"
    )

    try:
        response = await async_client.get(
            url=request_url,
            timeout=10,  # times out after 10 seconds
        )
        response.raise_for_status()
    except HTTPError as e:
        print(e.response.text)
        raise Exception(f"{postcode} not found")

    organisations = response.json()["Organisations"]

    if len(organisations) > 0:
        return organisations[0]["OrgId"]

gp_practice_for_postcode = httpx_async_to_sync(agp_practice_for_postcode)

async def agp_details_for_ods_code(ods_code: str, async_client: httpx.AsyncClient):
    """
    Returns address, name and long/lat for ods code
    """

    url = f"{settings.NHS_SPINE_SERVICES_URL}/organisations/{ods_code}"

    try:
        response = await async_client.get(
            url=url,
            timeout=10,  # times out after 10 seconds
        )
        response.raise_for_status()
    except HTTPError as e:
        return {"error": e}
    
    logger.warning(response.json())
    return response.json()["Organisation"]

gp_details_for_ods_code = httpx_async_to_sync(gp_details_for_ods_code)

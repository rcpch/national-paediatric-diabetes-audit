"""
Calculates the index of multiple deprivation for a given postcode
"""

# Standard imports
import logging
import httpx

# Third party imports
from django.conf import settings

# RCPCH imports
from ...constants import UNKNOWN_POSTCODES_NO_SPACES
from ...general_functions.async_helpers import httpx_async_to_sync

# Logging setup
logger = logging.getLogger(__name__)


async def aimd_for_postcode(user_postcode: str, async_client: httpx.AsyncClient) -> int:
    """
    Makes an API call to the RCPCH Census Platform with postcode and quantile_type
    Postcode - can have spaces or not - this is processed by the API
    Quantile - this is an integer representing what quantiles are requested (eg quintile, decile etc)
    """

    # Skips the calculation if the postcode is on the 'unknown' list
    if user_postcode.replace(" ", "") not in UNKNOWN_POSTCODES_NO_SPACES:
        try:
            response = await async_client.get(
                url=f"{settings.RCPCH_CENSUS_PLATFORM_URL}/index_of_multiple_deprivation_quantile?postcode={user_postcode}&quantile=5",
                headers={"Subscription-Key": f"{settings.RCPCH_CENSUS_PLATFORM_TOKEN}"},
                timeout=10,  # times out after 10 seconds
            )
        except Exception as error:
            logger.error(f"Cannot calculate deprivation score for {user_postcode}: {error}")
            return None

        if response.status_code != 200:
            logger.error(
                f"Cannot calculate deprivation score for {user_postcode}. Response status {response.status_code}"
            )
            return None

        return response.json()["result"]["data_quantile"]

imd_for_postcode = httpx_async_to_sync(aimd_for_postcode)

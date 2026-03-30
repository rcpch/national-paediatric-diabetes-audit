# python
import logging
from dataclasses import dataclass

# third party libraries
import httpx

# django
from django.conf import settings
from django.contrib.gis.geos import Point

# npda imports
logger = logging.getLogger(__name__)


@dataclass
class ValidatedPostcode:
    normalised_postcode: str
    lon: float
    lat: float

    @property
    def location_wgs84(self) -> Point:
        """
        The SRID (Spatial Reference System Identifier) 27700 refers to the British National Grid (BNG), a common system used for mapping in the UK. It uses Eastings and Northings, rather than longitude & latitude.
        This system is different from the more common geographic coordinate systems like WGS 84 (SRID 4326), which is used by most global datasets including GPS and many web APIs.
        Coordinates from the ONS data therefore need transforming from WGS 84 (SRID 4326) to British National Grid (SRID 27700).
        Both are included here and stored in the model, as the shape files for the UK health boundaries are produced as BNG, rather than WGS84.
        """
        return Point(self.lon, self.lat, srid=4326)

    @property
    def location_bng(self) -> Point:
        return self.location_wgs84.transform(27700, clone=True)


async def lookup_postcode(
    postcode: str, async_client: httpx.AsyncClient
) -> ValidatedPostcode | None:
    response = await make_postcode_api_request(f"postcodes/{postcode}", async_client)
    return handle_postcode_api_response(response)


async def lookup_terminated_postcode(
    postcode: str, async_client: httpx.AsyncClient
) -> ValidatedPostcode | None:
    response = await make_postcode_api_request(
        f"terminated_postcodes/{postcode}", async_client
    )
    return handle_postcode_api_response(response)


def random_postcode_under_outcode_sync(outcode: str) -> ValidatedPostcode | None:
    with httpx.Client() as client:
        response = make_postcode_api_request(
            f"random/postcodes?outcode={outcode}", client
        )
        return handle_postcode_api_response(response)


def make_postcode_api_request(
    path: str, client: httpx.Client | httpx.AsyncClient
) -> httpx.Response:
    return client.get(
        url=f"{settings.POSTCODES_IO_API_URL}/{path}",
        headers={"Ocp-Apim-Subscription-Key": settings.POSTCODES_IO_API_KEY},
        timeout=10,  # times out after 10 seconds
    )


def handle_postcode_api_response(response: httpx.Response) -> ValidatedPostcode | None:
    if response.status_code == 404:
        return None

    response.raise_for_status()

    result = response.json()["result"]

    return ValidatedPostcode(
        normalised_postcode=result["postcode"],
        lon=result["longitude"],
        lat=result["latitude"],
    )

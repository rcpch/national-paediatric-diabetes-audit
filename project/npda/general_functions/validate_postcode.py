# python
import logging
import requests
from dataclasses import dataclass

# django
from django.conf import settings
from django.contrib.gis.geos import Point

# third party libraries
import httpx

# npda imports
logger = logging.getLogger(__name__)


@dataclass
class ValidatedPostcode:
    normalised_postcode: str
    lon: float
    lat: float
    location_bng: Point
    location_wgs84: Point


def transform_lon_lat(lon: float, lat: float) -> tuple[Point, Point]:
    """
    The SRID (Spatial Reference System Identifier) 27700 refers to the British National Grid (BNG), a common system used for mapping in the UK. It uses Eastings and Northings, rather than longitude & latitude.
    This system is different from the more common geographic coordinate systems like WGS 84 (SRID 4326), which is used by most global datasets including GPS and many web APIs.
    Coordinates from the ONS data therefore need transforming from WGS 84 (SRID 4326) to British National Grid (SRID 27700).
    Both are included here and stored in the model, as the shape files for the UK health boundaries are produced as BNG, rather than WGS84.
    """
    # Create a Point in WGS 84
    location_wgs84 = Point(lon, lat, srid=4326)

    # Transform to British National Grid (SRID 27700) - this has Eastings and Northings, rather than longitude and latitude.
    location_bng = location_wgs84.transform(27700, clone=True)

    return location_bng, location_wgs84


async def validate_postcode(postcode: str, async_client: httpx.AsyncClient) -> ValidatedPostcode | None:
    response = await async_client.get(
        url=f"{settings.POSTCODES_IO_API_URL}/postcodes/{postcode}",
        headers={"Ocp-Apim-Subscription-Key": settings.POSTCODES_IO_API_KEY},
        timeout=10,  # times out after 10 seconds
    )

    if response.status_code == 404:
        return None

    response.raise_for_status()

    result = response.json()["result"]

    normalised_postcode = result["postcode"]

    lon = result["longitude"]
    lat = result["latitude"]

    location_bng, location_wgs84 = transform_lon_lat(lon, lat)

    return ValidatedPostcode(
        normalised_postcode=normalised_postcode,
        lon=lon,
        lat=lat,
        location_bng=location_bng,
        location_wgs84=location_wgs84,
    )

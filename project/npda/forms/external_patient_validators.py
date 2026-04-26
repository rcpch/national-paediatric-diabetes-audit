import asyncio
import logging
from dataclasses import dataclass

from asgiref.sync import async_to_sync
from django.core.exceptions import ValidationError
from httpx import AsyncClient, HTTPError

from ...constants.postcodes import is_jersey_postcode, skip_api_validation_for_postcode
from ..general_functions import (
    ValidatedPostcode,
    country_from_validated_postcode,
    gp_details_for_ods_code,
    gp_ods_code_for_postcode,
    imd_for_postcode,
    lookup_postcode,
    lookup_terminated_postcode,
)

logger = logging.getLogger(__name__)


@dataclass
class PatientExternalValidationResult:
    postcode: str | ValidationError | None
    location_bng: str | None
    location_wgs84: str | None
    gp_practice_ods_code: str | ValidationError | None
    gp_practice_postcode: str | ValidationError | None
    index_of_multiple_deprivation_quintile: str | None


def future_resolve(value):
    future = asyncio.Future()
    future.set_result(value)
    return future


async def _lookup_postcode(
    postcode: str | None, async_client: AsyncClient
) -> ValidatedPostcode | None:
    if postcode:
        try:
            normalised_postcode = await lookup_postcode(postcode, async_client)

            if not normalised_postcode:
                normalised_postcode = await lookup_terminated_postcode(
                    postcode, async_client
                )

                if not normalised_postcode:
                    raise ValidationError(
                        "Invalid postcode %(postcode)s", params={"postcode": postcode}
                    )

            return normalised_postcode
        except HTTPError as err:
            logger.warning(f"Error validating postcode {postcode} {err}", exc_info=True)


async def _imd_for_postcode(
    postcode: str | None,
    async_client: AsyncClient,
    imd_year: int | None = None,
    country: str | None = None,
) -> str | None:
    if (
        postcode
        and not skip_api_validation_for_postcode(postcode)
        and not is_jersey_postcode(postcode)
    ):
        try:
            imd = await imd_for_postcode(
                postcode,
                async_client,
                year=imd_year,
                country=country,
            )

            return imd
        except HTTPError as err:
            logger.warning(
                f"Cannot calculate deprivation score for {postcode} {err}",
                exc_info=True,
            )


async def _gp_details_from_ods_code(
    ods_code: str | None, async_client: AsyncClient
) -> tuple[str, str] | None:
    try:
        result = await gp_details_for_ods_code(ods_code, async_client)

        if not result:
            raise ValidationError(
                "Could not find GP practice with ODS code %(ods_code)s",
                params={"ods_code": ods_code},
            )
        else:
            postcode = result["GeoLoc"]["Location"]["PostCode"]
            return [ods_code, postcode]
    except HTTPError as err:
        logger.warning(
            f"Error looking up GP practice by ODS code {ods_code} {err}", exc_info=True
        )


async def _gp_details_from_postcode(
    gp_practice_postcode: str, async_client: AsyncClient
) -> tuple[str, str] | None:
    try:
        result = await _lookup_postcode(gp_practice_postcode, async_client)

        if not result:
            raise ValidationError(
                "Invalid GP practice with postcode %(postcode)s",
                params={"postcode": gp_practice_postcode},
            )

        normalised_postcode = result.normalised_postcode

        ods_code = await gp_ods_code_for_postcode(normalised_postcode, async_client)

        if not ods_code:
            raise ValidationError(
                "Could not find GP practice with postcode %(postcode)s",
                params={"postcode": gp_practice_postcode},
            )
        else:
            return [ods_code, normalised_postcode]
    except HTTPError as err:
        logger.warning(
            f"Error looking up GP practice by postcode {normalised_postcode} {err}",
            exc_info=True,
        )


# Parallelise lookups to external APIs to speed up processing patients in a CSV upload
async def validate_patient_async(
    postcode: str | None,
    gp_practice_ods_code: str | None,
    gp_practice_postcode: str | None,
    async_client: AsyncClient,
    england_imd_year: int | None = None,
) -> PatientExternalValidationResult:
    ret = PatientExternalValidationResult(None, None, None, None, None, None)

    # Call postcodes.io to validate and return the normalised postcode with location data
    if skip_api_validation_for_postcode(postcode):
        lookup_postcode_task = future_resolve(None)
    else:
        lookup_postcode_task = _lookup_postcode(postcode, async_client)

    # If we already have the GP practice ODS code, we can skip the postcode lookup
    if gp_practice_ods_code:
        gp_details_task = _gp_details_from_ods_code(gp_practice_ods_code, async_client)
    elif gp_practice_postcode:
        gp_details_task = _gp_details_from_postcode(gp_practice_postcode, async_client)
    else:
        gp_details_task = future_resolve(None)

    # This is the Python equivalent of Promise.allSettled
    # Run all the postcode validation task first, then check for errors
    # If there are no errors, run the the rest of the postcode validation tasks
    [
        validated_postcode,
        gp_details,
    ] = await asyncio.gather(
        lookup_postcode_task,
        gp_details_task,
        return_exceptions=True,
    )

    if type(validated_postcode) is ValidationError:
        # assign error to original field
        ret.postcode = validated_postcode

        # The postcode is invalid. There's no point calling the IMD API
        imd_task = future_resolve(None)
    elif isinstance(validated_postcode, Exception):
        raise validated_postcode
    elif validated_postcode is None:
        # We may have skipped validation entirely (see above)
        if skip_api_validation_for_postcode(postcode):
            ret.postcode = postcode
            # No location data available

        # The postcode does not exist or we skipped it. There's no point calling the IMD API
        imd_task = future_resolve(None)
    else:
        ret.postcode = validated_postcode.normalised_postcode
        ret.location_bng = validated_postcode.location_bng
        ret.location_wgs84 = validated_postcode.location_wgs84

        postcode_country = country_from_validated_postcode(validated_postcode)

        imd_year = None
        if england_imd_year is not None and postcode_country == "england":
            imd_year = england_imd_year

        imd_task = _imd_for_postcode(
            validated_postcode.normalised_postcode,
            async_client,
            imd_year=imd_year,
            country=postcode_country,
        )

    index_of_multiple_deprivation_quintile = await imd_task

    if (
        isinstance(index_of_multiple_deprivation_quintile, Exception)
        and type(index_of_multiple_deprivation_quintile) is not ValidationError
    ):
        raise index_of_multiple_deprivation_quintile
    else:
        ret.index_of_multiple_deprivation_quintile = (
            index_of_multiple_deprivation_quintile
        )

    if type(gp_details) is ValidationError:
        if gp_practice_ods_code:
            # Assign error to original field
            ret.gp_practice_ods_code = gp_details
        else:
            ret.gp_practice_postcode = gp_details
    elif isinstance(gp_details, Exception):
        raise gp_details
    elif gp_details:
        [gp_practice_ods_code, gp_practice_postcode] = gp_details

        ret.gp_practice_ods_code = gp_practice_ods_code
        ret.gp_practice_postcode = gp_practice_postcode

    return ret


def validate_patient_sync(
    postcode: str,
    gp_practice_ods_code: str | None,
    gp_practice_postcode: str | None,
    england_imd_year: int | None = None,
) -> PatientExternalValidationResult:
    async def wrapper():
        async with AsyncClient() as client:
            ret = await validate_patient_async(
                postcode,
                gp_practice_ods_code,
                gp_practice_postcode,
                client,
                england_imd_year=england_imd_year,
            )
            return ret

    return async_to_sync(wrapper)()

import logging
from dataclasses import dataclass
from datetime import date

import asyncio
from asgiref.sync import async_to_sync

from django.core.exceptions import ValidationError
from httpx import HTTPError, AsyncClient

from ..general_functions import (
    gp_details_for_ods_code,
    gp_ods_code_for_postcode,
    validate_postcode,
    imd_for_postcode,
    calculate_centiles_z_scores,
    ValidatedPostcode,
)

from ...constants.postcodes import skip_api_validation_for_postcode

logger = logging.getLogger(__name__)


@dataclass
class PatientExternalValidationResult:
    postcode: str | ValidationError | None
    location_bng: str | None
    location_wgs84: str | None
    gp_practice_ods_code: str | ValidationError | None
    gp_practice_postcode: str | ValidationError | None
    index_of_multiple_deprivation_quintile: str | None


async def _validate_postcode(
    postcode: str | None, async_client: AsyncClient
) -> ValidatedPostcode | None:
    if postcode:
        if skip_api_validation_for_postcode(postcode):
            return postcode

        try:
            normalised_postcode = await validate_postcode(postcode, async_client)

            if not normalised_postcode:
                raise ValidationError(
                    "Invalid postcode %(postcode)s", params={"postcode": postcode}
                )
            return normalised_postcode
        except HTTPError as err:
            logger.warning(f"Error validating postcode {postcode} {err}", exc_info=True)


async def _imd_for_postcode(
    postcode: str | None, async_client: AsyncClient
) -> str | None:
    if postcode and not skip_api_validation_for_postcode(postcode):
        try:
            imd = await imd_for_postcode(postcode, async_client)

            return imd
        except HTTPError as err:
            logger.warning(f"Cannot calculate deprivation score for {postcode} {err}", exc_info=True)


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
        logger.warning(f"Error looking up GP practice by ODS code {ods_code} {err}", exc_info=True)


async def _gp_details_from_postcode(
    gp_practice_postcode: str, async_client: AsyncClient
) -> tuple[str, str] | None:
    try:
        result = await validate_postcode(
            gp_practice_postcode, async_client
        )

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
        logger.warning(f"Error looking up GP practice by postcode {normalised_postcode} {err}", exc_info=True)


# Run lookups to external APIs asynchronously to speed up CSV upload by processing patients in parallel
async def validate_patient_async(
    postcode: str,
    gp_practice_ods_code: str | None,
    gp_practice_postcode: str | None,
    async_client: AsyncClient,
) -> PatientExternalValidationResult:
    ret = PatientExternalValidationResult(None, None, None, None, None, None)

    # Set up all the promises
    validate_postcode_task = _validate_postcode(postcode, async_client)

    # If we already have the GP practice ODS code, we can skip the postcode lookup
    if gp_practice_ods_code:
        gp_details_task = _gp_details_from_ods_code(gp_practice_ods_code, async_client)
    elif gp_practice_postcode:
        gp_details_task = _gp_details_from_postcode(gp_practice_postcode, async_client)
    else:
        gp_details_task = asyncio.Future()
        gp_details_task.set_result(None)

    # This is the Python equivalent of Promise.allSettled
    # Run all the postcode validation task first, then check for errors
    # If there are no errors, run the the rest of the postcode validation tasks
    [
        postcode,
        gp_details,
    ] = await asyncio.gather(
        validate_postcode_task,
        gp_details_task,
        return_exceptions=True,
    )

    if isinstance(postcode, Exception) and not type(postcode) is ValidationError:
        raise postcode  # postcode has an error that is not to do with validation
    else:
        if type(postcode) is ValidationError or postcode is None:
            ret.postcode = postcode
            
            # the postcode is invalid. There is no point in running the IMD task
            index_of_multiple_deprivation_quintile = None
        else:
            ret.postcode = postcode.normalised_postcode
            ret.location_bng = postcode.location_bng
            ret.location_wgs84 = postcode.location_wgs84

            index_of_multiple_deprivation_quintile = await _imd_for_postcode(postcode.normalised_postcode, async_client)

        if (
            isinstance(index_of_multiple_deprivation_quintile, Exception)
            and not type(index_of_multiple_deprivation_quintile) is ValidationError
        ):
            raise index_of_multiple_deprivation_quintile
        else:
            ret.index_of_multiple_deprivation_quintile = (
                index_of_multiple_deprivation_quintile
            )

    # run the GP details task
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
    postcode: str, gp_practice_ods_code: str | None, gp_practice_postcode: str | None
) -> PatientExternalValidationResult:
    async def wrapper():
        async with AsyncClient() as client:
            ret = await validate_patient_async(
                postcode, gp_practice_ods_code, gp_practice_postcode, client
            )
            return ret

    return async_to_sync(wrapper)()

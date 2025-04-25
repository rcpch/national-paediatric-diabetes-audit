import pytest
from unittest.mock import AsyncMock, patch

from httpx import HTTPError
from django.core.exceptions import ValidationError

from project.npda.tests.factories.patient_factory import (
    VALID_FIELDS,
    VALID_FIELDS_WITH_GP_POSTCODE,
    INDEX_OF_MULTIPLE_DEPRIVATION_QUINTILE,
    GP_POSTCODE_NO_SPACES,
    GP_POSTCODE_WITH_SPACES,
    PATIENT_POSTCODE_NO_SPACES,
    PATIENT_POSTCODE_WITH_SPACES,
    VALID_PATIENT_POSTCODE,
    VALID_GP_POSTCODE,
    JERSEY_PATIENT_POSTCODE_NO_SPACES,
    JERSEY_PATIENT_POSTCODE_WITH_SPACES,
    JERSEY_GP_POSTCODE_NO_SPACES,
    JERSEY_GP_POSTCODE_WITH_SPACES,
    VALID_JERSEY_PATIENT_POSTCODE,
    VALID_JERSEY_GP_POSTCODE
)

from project.npda.forms.external_patient_validators import validate_patient_async

async_client = AsyncMock()

MOCK_GP_DETAILS_FOR_ODS_CODE = {
    "GeoLoc": {
        "Location": {
            "PostCode": VALID_FIELDS_WITH_GP_POSTCODE["gp_practice_postcode"]
        }
    }
}

# We don't want to call remote services in unit tests
@pytest.fixture(autouse=True)
def mock_remote_calls():
    with patch("project.npda.forms.external_patient_validators.lookup_postcode", AsyncMock(return_value=VALID_PATIENT_POSTCODE)):
        with patch("project.npda.forms.external_patient_validators.gp_details_for_ods_code", AsyncMock(return_value=MOCK_GP_DETAILS_FOR_ODS_CODE)):
            with patch("project.npda.forms.external_patient_validators.gp_ods_code_for_postcode", AsyncMock(return_value=VALID_FIELDS["gp_practice_ods_code"])):
                with patch("project.npda.forms.external_patient_validators.imd_for_postcode", AsyncMock(return_value=INDEX_OF_MULTIPLE_DEPRIVATION_QUINTILE)):
                    yield None


async def test_validate_patient():
    result = await validate_patient_async(
        postcode=VALID_FIELDS["postcode"],
        gp_practice_ods_code=VALID_FIELDS["gp_practice_ods_code"],
        gp_practice_postcode=None,
        async_client=async_client
    )

    assert(result.postcode == VALID_PATIENT_POSTCODE.normalised_postcode)
    assert(result.location_bng == VALID_PATIENT_POSTCODE.location_bng)
    assert(result.location_wgs84 == VALID_PATIENT_POSTCODE.location_wgs84)
    assert(result.gp_practice_ods_code == VALID_FIELDS["gp_practice_ods_code"])
    assert(result.gp_practice_postcode == VALID_FIELDS_WITH_GP_POSTCODE["gp_practice_postcode"])
    assert(result.index_of_multiple_deprivation_quintile == INDEX_OF_MULTIPLE_DEPRIVATION_QUINTILE)


async def test_normalised_postcode_saved():
    result = await validate_patient_async(
        postcode=PATIENT_POSTCODE_NO_SPACES,
        gp_practice_ods_code=None,
        gp_practice_postcode=None,
        async_client=async_client
    )

    assert(result.postcode == PATIENT_POSTCODE_WITH_SPACES)


async def test_invalid_postcode():
    with patch("project.npda.forms.external_patient_validators.lookup_postcode", AsyncMock(return_value=None)):
        with patch("project.npda.forms.external_patient_validators.lookup_terminated_postcode", AsyncMock(return_value=None)):
            result = await validate_patient_async(
                postcode="INVALID",
                gp_practice_ods_code=None,
                gp_practice_postcode=None,
                async_client=async_client
            )

            assert(type(result.postcode) is ValidationError)


@pytest.mark.parametrize(
    "postcode",
    [
        pytest.param("ZZ993CZ"),
        pytest.param("ZZ99 3GZ"),
        pytest.param("ZZ993GZ"),
        pytest.param("ZZ99 3GZ"),
        pytest.param("ZZ991WZ"),
        pytest.param("ZZ99 1WZ"),
        pytest.param("ZZ993VZ"),
        pytest.param("ZZ99 3VZ"),
        pytest.param("ZZ99 6UZ"),
    ],
)
async def test_special_nhs_postcodes(postcode):
    with patch("project.npda.forms.external_patient_validators.lookup_postcode") as mock_lookup_postcode:
        with patch("project.npda.forms.external_patient_validators.imd_for_postcode") as mock_imd_for_postcode:
                result = await validate_patient_async(
                    postcode=postcode,
                    gp_practice_ods_code=None,
                    gp_practice_postcode=None,
                    async_client=async_client
                )

                assert(result.postcode == postcode)
                
                assert not mock_lookup_postcode.called
                assert not mock_imd_for_postcode.called


async def test_http_error_validating_postcode():
    with patch("project.npda.forms.external_patient_validators.lookup_postcode", AsyncMock(side_effect=HTTPError("oopsie!"))):
        result = await validate_patient_async(
            postcode="INVALID",
            gp_practice_ods_code=None,
            gp_practice_postcode=None,
            async_client=async_client
        )

        assert(result.postcode is None)


async def test_unexpected_error_validating_postcode():
    with patch("project.npda.forms.external_patient_validators.lookup_postcode", AsyncMock(side_effect=RuntimeError("oopsie!"))):
        with pytest.raises(RuntimeError):
            await validate_patient_async(
                postcode=VALID_FIELDS["postcode"],
                gp_practice_ods_code=None,
                gp_practice_postcode=None,
                async_client=async_client
            )


async def test_invalid_postcode_for_index_of_multiple_deprivation():
    with patch("project.npda.forms.external_patient_validators.imd_for_postcode", AsyncMock(return_value=None)):
        result = await validate_patient_async(
            postcode="INVALID",
            gp_practice_ods_code=None,
            gp_practice_postcode=None,
            async_client=async_client
        )

        assert(result.index_of_multiple_deprivation_quintile is None)


async def test_http_error_calculating_index_of_multiple_deprivation():
    with patch("project.npda.forms.external_patient_validators.imd_for_postcode", AsyncMock(side_effect=HTTPError("oopsie!"))):
        result = await validate_patient_async(
            postcode=VALID_FIELDS["postcode"],
            gp_practice_ods_code=None,
            gp_practice_postcode=None,
            async_client=async_client
        )

        assert(result.index_of_multiple_deprivation_quintile is None)


async def test_http_error_calculating_index_of_multiple_deprivation():
    with patch("project.npda.forms.external_patient_validators.imd_for_postcode", AsyncMock(side_effect=RuntimeError("oopsie!"))):
        with pytest.raises(RuntimeError):
            await validate_patient_async(
                postcode=VALID_FIELDS["postcode"],
                gp_practice_ods_code=None,
                gp_practice_postcode=None,
                async_client=async_client
            )


async def test_validate_patient_with_gp_practice_ods_code():
    result = await validate_patient_async(
        postcode=None,
        gp_practice_ods_code=VALID_FIELDS["gp_practice_ods_code"],
        gp_practice_postcode=None,
        async_client=async_client
    )

    assert(result.gp_practice_ods_code == VALID_FIELDS["gp_practice_ods_code"])
    assert(result.gp_practice_postcode == VALID_FIELDS_WITH_GP_POSTCODE["gp_practice_postcode"])


async def test_invalid_gp_practice_ods_code():
    with patch("project.npda.forms.external_patient_validators.gp_details_for_ods_code", AsyncMock(return_value=None)):
        result = await validate_patient_async(
            postcode=None,
            gp_practice_ods_code="INVALID",
            gp_practice_postcode=None,
            async_client=async_client
        )

        assert(type(result.gp_practice_ods_code) is ValidationError)


async def test_http_error_validating_gp_practice_ods_code():
    with patch("project.npda.forms.external_patient_validators.gp_details_for_ods_code", AsyncMock(side_effect=HTTPError("oopsie!"))):
        result = await validate_patient_async(
            postcode=None,
            gp_practice_ods_code=VALID_FIELDS["gp_practice_ods_code"],
            gp_practice_postcode=None,
            async_client=async_client
        )

        assert(result.gp_practice_ods_code is None)


async def test_unexpected_error_validating_gp_practice_ods_code():
    with patch("project.npda.forms.external_patient_validators.gp_details_for_ods_code", AsyncMock(side_effect=RuntimeError("oopsie!"))):
        with pytest.raises(RuntimeError):
            await validate_patient_async(
                postcode=None,
                gp_practice_ods_code=VALID_FIELDS["gp_practice_ods_code"],
                gp_practice_postcode=None,
                async_client=async_client
            )


@patch("project.npda.forms.external_patient_validators.lookup_postcode", AsyncMock(return_value=VALID_GP_POSTCODE))
async def test_validate_patient_with_gp_practice_postcode():
    result = await validate_patient_async(
        postcode=None,
        gp_practice_ods_code=None,
        gp_practice_postcode=VALID_FIELDS_WITH_GP_POSTCODE["gp_practice_postcode"],
        async_client=async_client
    )

    assert(result.gp_practice_ods_code == VALID_FIELDS["gp_practice_ods_code"])
    assert(result.gp_practice_postcode == VALID_FIELDS_WITH_GP_POSTCODE["gp_practice_postcode"])


async def test_normalised_postcode_used_for_call_to_nhs_spine():
    # The NHS API only returns results if you have a space between the parts of the postcode
    with patch("project.npda.forms.external_patient_validators.lookup_postcode", AsyncMock(return_value=VALID_GP_POSTCODE)):
        with patch("project.npda.forms.external_patient_validators.gp_ods_code_for_postcode") as mock_gp_ods_code_for_postcode:
            result = await validate_patient_async(
                postcode=None,
                gp_practice_ods_code=None,
                gp_practice_postcode=GP_POSTCODE_NO_SPACES,
                async_client=async_client
            )

            mock_gp_ods_code_for_postcode.assert_called_once_with(GP_POSTCODE_WITH_SPACES, async_client)

            assert(result.gp_practice_postcode == GP_POSTCODE_WITH_SPACES)


async def test_gp_practice_postcode_does_not_return_result_from_spine():
    with patch("project.npda.forms.external_patient_validators.gp_ods_code_for_postcode", AsyncMock(return_value=None)):
        result = await validate_patient_async(
            postcode=None,
            gp_practice_ods_code=None,
            gp_practice_postcode="INVALID",
            async_client=async_client
        )

        assert(type(result.gp_practice_postcode) is ValidationError)


# https://github.com/rcpch/national-paediatric-diabetes-audit/issues/931
async def test_invalid_gp_practice_postcode():
    with patch("project.npda.forms.external_patient_validators.lookup_postcode", AsyncMock(return_value=None)):
        with patch("project.npda.forms.external_patient_validators.lookup_terminated_postcode", AsyncMock(return_value=None)):
            with patch("project.npda.forms.external_patient_validators.gp_ods_code_for_postcode") as mock:
                result = await validate_patient_async(
                    postcode=None,
                    gp_practice_ods_code=None,
                    gp_practice_postcode="INVALID",
                    async_client=async_client
                )

                # Passing None to the API call returned a 406 Not Acceptable so we want to check we don't call
                # the spine at all
                assert not mock.called
                assert(type(result.gp_practice_postcode) is ValidationError)


async def test_http_error_validating_gp_practice_postcode():
    with patch("project.npda.forms.external_patient_validators.gp_ods_code_for_postcode", AsyncMock(side_effect=HTTPError("oopsie!"))):
        result = await validate_patient_async(
            postcode=None,
            gp_practice_ods_code=None,
            gp_practice_postcode=VALID_FIELDS_WITH_GP_POSTCODE["gp_practice_postcode"],
            async_client=async_client
        )

        assert(result.gp_practice_postcode is None)


async def test_unexpected_error_validating_gp_practice_postcode():
    with patch("project.npda.forms.external_patient_validators.gp_ods_code_for_postcode", AsyncMock(side_effect=RuntimeError("oopsie!"))):
        with pytest.raises(RuntimeError):
            await validate_patient_async(
                postcode=None,
                gp_practice_ods_code=None,
                gp_practice_postcode=VALID_FIELDS_WITH_GP_POSTCODE["gp_practice_postcode"],
                async_client=async_client
            )


async def test_jersey_patient():
    lookup_postcode_return_values = [
        VALID_JERSEY_PATIENT_POSTCODE,
        VALID_JERSEY_GP_POSTCODE
    ]

    with patch("project.npda.forms.external_patient_validators.lookup_postcode", AsyncMock(side_effect=lookup_postcode_return_values)):
        with patch("project.npda.forms.external_patient_validators.gp_ods_code_for_postcode", AsyncMock(return_value="JER012")):
            with patch("project.npda.forms.external_patient_validators.imd_for_postcode") as mock_imd_for_postcode:
                result = await validate_patient_async(
                    postcode=JERSEY_PATIENT_POSTCODE_NO_SPACES,
                    gp_practice_ods_code=None,
                    gp_practice_postcode=JERSEY_GP_POSTCODE_NO_SPACES,
                    async_client=async_client
                )

                assert(result.postcode == JERSEY_PATIENT_POSTCODE_WITH_SPACES)
                assert(result.location_bng == VALID_JERSEY_PATIENT_POSTCODE.location_bng)
                assert(result.location_wgs84 == VALID_JERSEY_PATIENT_POSTCODE.location_wgs84)
                assert(result.gp_practice_ods_code == "JER012")
                assert(result.gp_practice_postcode == VALID_JERSEY_GP_POSTCODE.normalised_postcode)
                assert(result.index_of_multiple_deprivation_quintile is None)

                assert not mock_imd_for_postcode.called


async def test_terminated_postcode_endpoint_not_called_for_live_postcode():
    with patch("project.npda.forms.external_patient_validators.lookup_postcode", AsyncMock(return_value=VALID_PATIENT_POSTCODE)) as mock_lookup_postcode:
        with patch("project.npda.forms.external_patient_validators.lookup_terminated_postcode") as mock_lookup_terminated_postcode:
            result = await validate_patient_async(
                postcode=PATIENT_POSTCODE_NO_SPACES,
                gp_practice_ods_code=VALID_FIELDS["gp_practice_ods_code"],
                gp_practice_postcode=None,
                async_client=async_client
            )

            assert(result.postcode == VALID_PATIENT_POSTCODE.normalised_postcode)
            assert(not mock_lookup_terminated_postcode.called)


async def test_terminated_postcode():
    with patch("project.npda.forms.external_patient_validators.lookup_postcode", AsyncMock(return_value=None)) as mock_lookup_postcode:
        with patch("project.npda.forms.external_patient_validators.lookup_terminated_postcode", AsyncMock(return_value=VALID_PATIENT_POSTCODE)) as mock_lookup_terminated_postcode:
            result = await validate_patient_async(
                postcode=PATIENT_POSTCODE_NO_SPACES,
                gp_practice_ods_code=VALID_FIELDS["gp_practice_ods_code"],
                gp_practice_postcode=None,
                async_client=async_client
            )

            assert(result.postcode == VALID_PATIENT_POSTCODE.normalised_postcode)
            assert(mock_lookup_postcode.called)
from datetime import date
from unittest.mock import AsyncMock, Mock, patch

import pytest
from django.core.exceptions import ValidationError
from httpx import HTTPError

from project.npda.forms.external_visit_validators import (
    VisitExternalValidationResult,
    validate_visit_async,
)

async_client = AsyncMock()

VALID_FIELDS = {
    "birth_date": date(2018, 1, 1),
    "observation_date": date(2021, 1, 1),
    "sex": 1,
    "height": 123,
    "weight": 35,
    "async_client": async_client,
}

EMPTY_RESULT = VisitExternalValidationResult(None, None, None, None)

VALIDATION_ERROR = ValidationError("invalid!")
HTTP_ERROR = HTTPError("oopsie!")


async def test_missing_birth_date():
    with patch(
        "project.npda.forms.external_visit_validators.calculate_centiles_z_scores"
    ) as mock:
        result = await validate_visit_async(**(VALID_FIELDS | {"birth_date": None}))

        assert result == EMPTY_RESULT
        assert not mock.called


async def test_missing_observation_date():
    with patch(
        "project.npda.forms.external_visit_validators.calculate_centiles_z_scores"
    ) as mock:
        result = await validate_visit_async(
            **(VALID_FIELDS | {"observation_date": None})
        )

        assert result == EMPTY_RESULT
        assert not mock.called


async def test_missing_sex():
    with patch(
        "project.npda.forms.external_visit_validators.calculate_centiles_z_scores"
    ) as mock:
        result = await validate_visit_async(**(VALID_FIELDS | {"sex": None}))

        assert result == EMPTY_RESULT
        assert not mock.called


async def test_invalid_sex():
    with patch(
        "project.npda.forms.external_visit_validators.calculate_centiles_z_scores"
    ) as mock:
        result = await validate_visit_async(**(VALID_FIELDS | {"sex": 999}))

        assert result == EMPTY_RESULT
        assert not mock.called


async def test_missing_height():
    with patch(
        "project.npda.forms.external_visit_validators.calculate_centiles_z_scores",
        AsyncMock(return_value=(1, 2)),
    ) as mock:
        result = await validate_visit_async(**(VALID_FIELDS | {"height": None}))

        assert result.height_result is None

        assert result.weight_result.centile == 1
        assert result.weight_result.sds == 2

        assert result.bmi is None
        assert result.bmi_result is None

        assert mock.call_count == 1


async def test_missing_weight():
    with patch(
        "project.npda.forms.external_visit_validators.calculate_centiles_z_scores",
        AsyncMock(return_value=(1, 2)),
    ) as mock:
        result = await validate_visit_async(**(VALID_FIELDS | {"weight": None}))

        assert result.height_result.centile == 1
        assert result.height_result.sds == 2

        assert result.weight_result is None

        assert result.bmi is None
        assert result.bmi_result is None

        assert mock.call_count == 1


async def test_zero_height():
    with patch(
        "project.npda.forms.external_visit_validators.calculate_centiles_z_scores",
        AsyncMock(return_value=(1, 2)),
    ) as mock:
        result = await validate_visit_async(**(VALID_FIELDS | {"height": 0}))

        assert result.height_result is None

        assert result.weight_result.centile == 1
        assert result.weight_result.sds == 2

        assert result.bmi is None
        assert result.bmi_result is None

        assert mock.call_count == 1


async def test_zero_weight():
    with patch(
        "project.npda.forms.external_visit_validators.calculate_centiles_z_scores",
        AsyncMock(return_value=(1, 2)),
    ) as mock:
        result = await validate_visit_async(**(VALID_FIELDS | {"weight": 0}))

        assert result.height_result.centile == 1
        assert result.height_result.sds == 2

        assert result.weight_result is None

        assert result.bmi is None
        assert result.bmi_result is None

        assert mock.call_count == 1


async def test_negative_height():
    with patch(
        "project.npda.forms.external_visit_validators.calculate_centiles_z_scores",
        AsyncMock(return_value=(1, 2)),
    ) as mock:
        result = await validate_visit_async(**(VALID_FIELDS | {"height": -2}))

        assert result.height_result is None

        assert result.weight_result.centile == 1
        assert result.weight_result.sds == 2

        assert result.bmi is None
        assert result.bmi_result is None

        assert mock.call_count == 1


async def test_negative_weight():
    with patch(
        "project.npda.forms.external_visit_validators.calculate_centiles_z_scores",
        AsyncMock(return_value=(1, 2)),
    ) as mock:
        result = await validate_visit_async(**(VALID_FIELDS | {"weight": -2}))

        assert result.height_result.centile == 1
        assert result.height_result.sds == 2

        assert result.weight_result is None

        assert result.bmi is None
        assert result.bmi_result is None

        assert mock.call_count == 1


# https://github.com/rcpch/national-paediatric-diabetes-audit/issues/577
async def test_over_20_yo():
    with patch(
        "project.npda.forms.external_visit_validators.calculate_centiles_z_scores",
        AsyncMock(return_value=(1, 2)),
    ) as mock:
        result = await validate_visit_async(
            **(
                VALID_FIELDS
                | {
                    "birth_date": date(2000, 1, 1),
                    "observation_date": date(2021, 1, 1),
                }
            )
        )

        assert result.height_result.centile == 1
        assert result.height_result.sds == 2

        assert result.weight_result.centile == 1
        assert result.weight_result.sds == 2

        for call in mock.mock_calls:
            call_date = call.kwargs["observation_date"]

            # Can't do growth charts > 20 year olds so clamp to day before their 20th birthday
            assert call_date == date(2019, 12, 31)


async def test_invalid_bmi():
    with patch(
        "project.npda.forms.external_visit_validators.calculate_centiles_z_scores",
        AsyncMock(return_value=(1, 2)),
    ):
        with patch(
            "project.npda.forms.external_visit_validators.calculate_bmi",
            Mock(return_value=None),
        ):
            result = await validate_visit_async(**VALID_FIELDS)

            assert result.bmi is None
            assert result.bmi_result is None


async def test_validation_error():
    with patch(
        "project.npda.forms.external_visit_validators.calculate_centiles_z_scores",
        AsyncMock(side_effect=VALIDATION_ERROR),
    ) as mock:
        result = await validate_visit_async(**VALID_FIELDS)

        assert result.height_result is VALIDATION_ERROR
        assert result.weight_result is VALIDATION_ERROR

        assert result.bmi == 23.1
        assert result.bmi_result is VALIDATION_ERROR

        assert mock.call_count == 3


async def test_ignores_http_error():
    with patch(
        "project.npda.forms.external_visit_validators.calculate_centiles_z_scores",
        AsyncMock(side_effect=HTTP_ERROR),
    ) as mock:
        result = await validate_visit_async(**VALID_FIELDS)

        assert result.height_result is None
        assert result.weight_result is None

        assert result.bmi == 23.1
        assert result.bmi_result is None

        assert mock.call_count == 3


async def test_passes_through_unexpected_error():
    with patch(
        "project.npda.forms.external_visit_validators.calculate_centiles_z_scores",
        AsyncMock(side_effect=Exception("oopsie!")),
    ) as mock:
        with pytest.raises(Exception):  # noqa: B017
            await validate_visit_async(**VALID_FIELDS)

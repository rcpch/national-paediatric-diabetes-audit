"""Tests for the CalculateKPIS class.
Also contains utils / helper functions for testing the CalculateKPIS class.
"""

import logging
from dataclasses import fields
from datetime import date
from typing import List

import pytest
from dateutil.relativedelta import relativedelta

from project.constants.diabetes_treatment import TREATMENT_TYPES
from project.constants.diabetes_types import DIABETES_TYPES
from project.constants.hba1c_format import HBA1C_FORMATS
from project.constants.retinal_screening_results import \
    RETINAL_SCREENING_RESULTS
from project.constants.smoking_status import SMOKING_STATUS
from project.npda.general_functions.kpis import CalculateKPIS, KPIResult
from project.npda.general_functions.model_utils import \
    print_instance_field_attrs
from project.npda.models import Patient, Visit
from project.npda.tests.factories.patient_factory import PatientFactory
from project.npda.tests.factories.visit_factory import VisitFactory

# Logging
logger = logging.getLogger(__name__)


# HELPERS
def assert_kpi_result_equal(expected: KPIResult, actual: KPIResult) -> None:
    """
    Asserts that two KPIResult objects are equal by comparing their fields and provides
    a detailed error message if they are not.

    :param expected: The expected KPIResult object.
    :param actual: The actual KPIResult object.
    :raises AssertionError: If the fields in the KPIResult objects differ.
    """
    if isinstance(expected, KPIResult) is False:
        raise TypeError(
            f"expected must be of type KPIResult (current: {type(expected)}"
        )
    if isinstance(actual, KPIResult) is False:
        raise TypeError(
            f"actual must be of type KPIResult (current: {type(actual)}"
        )

    mismatches = []

    if expected.total_eligible != actual.total_eligible:
        mismatches.append(
            f"total_eligible: expected {expected.total_eligible}, got {actual.total_eligible}"
        )

    if expected.total_passed != actual.total_passed:
        mismatches.append(
            f"total_passed: expected {expected.total_passed}, got {actual.total_passed}"
        )

    if expected.total_ineligible != actual.total_ineligible:
        mismatches.append(
            f"total_ineligible: expected {expected.total_ineligible}, got {actual.total_ineligible}"
        )

    if expected.total_failed != actual.total_failed:
        mismatches.append(
            f"total_failed: expected {expected.total_failed}, got {actual.total_failed}"
        )

    if mismatches:
        mismatch_details = "\n".join(mismatches)
        raise AssertionError(f"KPIResult mismatch:\n{mismatch_details}")


@pytest.mark.django_db
def test_ensure_mocked_audit_date_range_is_correct(AUDIT_START_DATE):
    """Ensure that the mocked audit date range is correct."""
    calc_kpis = CalculateKPIS(
        pz_code="mocked_pz_code", calculation_date=AUDIT_START_DATE
    )

    assert calc_kpis.audit_start_date == date(
        2024, 4, 1
    ), f"Mocked audit start date incorrect!"
    assert calc_kpis.audit_end_date == date(
        2025, 3, 31
    ), f"Mocked audit end date incorrect!"



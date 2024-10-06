"""Tests for the CalculateKPIS class.
Also contains utils / helper functions for testing the CalculateKPIS class.
"""

import logging
from datetime import date

import pytest

from project.npda.kpi_class.kpis import CalculateKPIS, KPIResult
from project.npda.models.patient import Patient

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
        raise TypeError(f"actual must be of type KPIResult (current: {type(actual)}")

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
        pz_codes=["mocked_pz_code"], calculation_date=AUDIT_START_DATE
    )

    assert calc_kpis.audit_start_date == date(
        2024, 4, 1
    ), f"Mocked audit start date incorrect!"
    assert calc_kpis.audit_end_date == date(
        2025, 3, 31
    ), f"Mocked audit end date incorrect!"


@pytest.mark.django_db
def test_kpi_calculations_dont_break_when_no_patients(AUDIT_START_DATE):
    """Tests none of the KPIs break when no patients are present.

    Just runs all KPI calculations with no patients present.
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    kpi_calculations_object = CalculateKPIS(
        pz_codes=["PZ130"], calculation_date=AUDIT_START_DATE
    ).calculate_kpis_for_patients()

    for kpi, results in kpi_calculations_object["calculated_kpi_values"].items():
        # remove the kpi_label key from the results
        results.pop("kpi_label", None)

        values = list(results.values())

        assert all(
            [isinstance(value, int) or isinstance(value, float) for value in values]
        ), f"KPI {kpi} has non-integer values: {results}"

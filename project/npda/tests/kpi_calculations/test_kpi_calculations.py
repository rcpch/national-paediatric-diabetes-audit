"""Tests for the CalculateKPIS class."""

from datetime import date, timedelta
from dataclasses import fields
import logging
from typing import List
import pytest

from project.npda.general_functions.kpis import CalculateKPIS, KPIResult
from project.npda.general_functions.model_utils import print_instance_field_attrs
from project.npda.models import Patient, Visit
from project.npda.tests.factories.patient_factory import PatientFactory

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

    if expected.total_ineligible != actual.total_ineligible:
        mismatches.append(
            f"total_ineligible: expected {expected.total_ineligible}, got {actual.total_ineligible}"
        )

    if expected.total_passed != actual.total_passed:
        mismatches.append(
            f"total_passed: expected {expected.total_passed}, got {actual.total_passed}"
        )

    if expected.total_failed != actual.total_failed:
        mismatches.append(
            f"total_failed: expected {expected.total_failed}, got {actual.total_failed}"
        )

    if mismatches:
        mismatch_details = "\n".join(mismatches)
        raise AssertionError(f"KPIResult mismatch:\n{mismatch_details}")


@pytest.fixture
def AUDIT_START_DATE():
    """AUDIT_START_DATE is Day 2 of the first audit period"""
    return date(year=2024, month=4, day=1)


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


@pytest.mark.django_db
def test_kpi_calculation_1(AUDIT_START_DATE):
    """Tests that KPI1 is calculated correctly."""

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    N_PATIENTS_ELIGIBLE = N_PATIENTS_PASS = 3
    N_PATIENTS_INELIGIBLE = N_PATIENTS_FAIL = 4

    # Create  Patients and Visits that should PASS KPI1
    eligible_patients: List[Patient] = PatientFactory.create_batch(
        size=N_PATIENTS_ELIGIBLE, visit__visit_date=AUDIT_START_DATE + timedelta(days=1)
    )

    # Create Patients and Visits that should FAIL KPI1
    # Visit date before audit period
    ineligible_patients_visit_date: List[Patient] = PatientFactory.create_batch(
        size=N_PATIENTS_INELIGIBLE,
        visit__visit_date=AUDIT_START_DATE - timedelta(days=10),
    )
    # Above age 25 at start of audit period
    ineligible_patients_too_old: List[Patient] = PatientFactory.create_batch(
        size=N_PATIENTS_INELIGIBLE,
        date_of_birth=AUDIT_START_DATE - timedelta(days=365 * 26),
    )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(pz_code="PZ130", calculation_date=AUDIT_START_DATE)

    EXPECTED_KPIRESULT = KPIResult(
        total_eligible=N_PATIENTS_ELIGIBLE,
        total_passed=N_PATIENTS_PASS,
        # We have 2 sets of ineligible patients
        total_ineligible=N_PATIENTS_INELIGIBLE * 2,
        total_failed=N_PATIENTS_FAIL * 2,
    )

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT, actual=calc_kpis.calculate_kpi_1_total_eligible()
    )


@pytest.mark.django_db
def test_kpi_calculation_2(AUDIT_START_DATE):
    """Tests that KPI2 is calculated correctly.

    Essentialy KPI1 but also check date of diagnosis within audit period
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    N_PATIENTS_ELIGIBLE = N_PATIENTS_PASS = 3
    N_PATIENTS_INELIGIBLE = N_PATIENTS_FAIL = 4

    # Create  Patients and Visits that should PASS KPI2
    eligible_patients: List[Patient] = PatientFactory.create_batch(
        size=N_PATIENTS_ELIGIBLE,
        visit__visit_date=AUDIT_START_DATE + timedelta(days=2),
        diagnosis_date=AUDIT_START_DATE + timedelta(days=10),
    )

    # Create Patients and Visits that should FAIL KPI2
    # Visit date before audit period
    ineligible_patients_visit_date: List[Patient] = PatientFactory.create_batch(
        size=N_PATIENTS_INELIGIBLE,
        visit__visit_date=AUDIT_START_DATE - timedelta(days=10),
    )
    # Diagnosis date before audit period
    ineligible_patients_diagnosis_date: List[Patient] = PatientFactory.create_batch(
        size=N_PATIENTS_INELIGIBLE,
        diagnosis_date=AUDIT_START_DATE - timedelta(days=10),
    )
    # Above age 25 at start of audit period
    ineligible_patients_too_old: List[Patient] = PatientFactory.create_batch(
        size=N_PATIENTS_INELIGIBLE,
        date_of_birth=AUDIT_START_DATE - timedelta(days=365 * 26),
    )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(pz_code="PZ130", calculation_date=AUDIT_START_DATE)

    EXPECTED_KPIRESULT = KPIResult(
        total_eligible=N_PATIENTS_ELIGIBLE,
        total_passed=N_PATIENTS_PASS,
        # We have 2 sets of ineligible patients
        total_ineligible=N_PATIENTS_INELIGIBLE * 3,
        total_failed=N_PATIENTS_FAIL * 3,
    )

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT,
        actual=calc_kpis.calculate_kpi_2_total_new_diagnoses(),
    )

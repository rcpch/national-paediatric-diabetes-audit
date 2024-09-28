"""Tests for the Outcomes KPIs."""

import logging
from typing import List

import pytest
from dateutil.relativedelta import relativedelta

from project.constants.diabetes_types import DIABETES_TYPES
from project.constants.hospital_admission_reasons import \
    HOSPITAL_ADMISSION_REASONS
from project.constants.smoking_status import SMOKING_STATUS
from project.npda.general_functions.kpis import CalculateKPIS, KPIResult
from project.npda.models import Patient
from project.npda.tests.factories.patient_factory import PatientFactory
from project.npda.tests.factories.visit_factory import VisitFactory
from project.npda.tests.kpi_calculations.test_kpi_calculations import \
    assert_kpi_result_equal

# Logging
logger = logging.getLogger(__name__)

@pytest.mark.skip(reason="Confirm calc issue https://github.com/orgs/rcpch/projects/13/views/1?pane=issue&itemId=81441322")
@pytest.mark.django_db
def test_kpi_calculation_44(AUDIT_START_DATE):
    """Tests that KPI44 is calculated correctly.

    Numerator: Mean of HbA1c measurements (item 17) within the audit
    period, excluding measurements taken within 90 days of diagnosis
    NOTE: The mean for each patient is calculated. We then calculate the
    mean of the means.

    Denominator: Total number of eligible patients (measure 1)
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create  Patients and Visits that should be eligible (KPI1)
    eligible_criteria = {
        "visit__visit_date": AUDIT_START_DATE + relativedelta(days=2),
        "date_of_birth": AUDIT_START_DATE - relativedelta(days=365 * 10),
    }

    # Create passing pts

    #Create failing pts


    # Create Patients and Visits that should be excluded
    # Visit date before audit period
    ineligible_patient_visit_date = PatientFactory(
        postcode="ineligible_patient_visit_date",
        visit__visit_date=AUDIT_START_DATE - relativedelta(days=10),
        visit__treatment=1,
    )
    # Above age 25 at start of audit period
    ineligible_patient_too_old = PatientFactory(
        postcode="ineligible_patient_too_old",
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 26),
        visit__treatment=1,
    )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(
        pz_code="PZ130", calculation_date=AUDIT_START_DATE
    )

    EXPECTED_TOTAL_ELIGIBLE = 6
    EXPECTED_TOTAL_INELIGIBLE = 2
    EXPECTED_TOTAL_PASSED = 2
    EXPECTED_TOTAL_FAILED = 4

    EXPECTED_KPIRESULT = KPIResult(
        total_eligible=EXPECTED_TOTAL_ELIGIBLE,
        total_passed=EXPECTED_TOTAL_PASSED,
        total_ineligible=EXPECTED_TOTAL_INELIGIBLE,
        total_failed=EXPECTED_TOTAL_FAILED,
    )

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT,
        actual=calc_kpis.calculate_kpi_44_mean_hba1c(),
    )

@pytest.mark.skip(reason="Confirm calc issue https://github.com/orgs/rcpch/projects/13/views/1?pane=issue&itemId=81441322")
@pytest.mark.django_db
def test_kpi_calculation_45(AUDIT_START_DATE):
    """Tests that KPI45 is calculated correctly.

    Numerator: median of HbA1c measurements (item 17) within the audit
    period, excluding measurements taken within 90 days of diagnosis
    NOTE: The median for each patient is calculated. We then calculate the
    median of the medians.

    Denominator: Total number of eligible patients (measure 1)
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create  Patients and Visits that should be eligible (KPI1)
    eligible_criteria = {
        "visit__visit_date": AUDIT_START_DATE + relativedelta(days=2),
        "date_of_birth": AUDIT_START_DATE - relativedelta(days=365 * 10),
    }

    # Create passing pts

    # Create failing pts


    # Create Patients and Visits that should be excluded
    # Visit date before audit period
    ineligible_patient_visit_date = PatientFactory(
        postcode="ineligible_patient_visit_date",
        visit__visit_date=AUDIT_START_DATE - relativedelta(days=10),
        visit__treatment=1,
    )
    # Above age 25 at start of audit period
    ineligible_patient_too_old = PatientFactory(
        postcode="ineligible_patient_too_old",
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 26),
        visit__treatment=1,
    )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(
        pz_code="PZ130", calculation_date=AUDIT_START_DATE
    )

    EXPECTED_TOTAL_ELIGIBLE = 6
    EXPECTED_TOTAL_INELIGIBLE = 2
    EXPECTED_TOTAL_PASSED = 2
    EXPECTED_TOTAL_FAILED = 4

    EXPECTED_KPIRESULT = KPIResult(
        total_eligible=EXPECTED_TOTAL_ELIGIBLE,
        total_passed=EXPECTED_TOTAL_PASSED,
        total_ineligible=EXPECTED_TOTAL_INELIGIBLE,
        total_failed=EXPECTED_TOTAL_FAILED,
    )

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT,
        actual=calc_kpis.calculate_kpi_45_median_hba1c(),
    )

@pytest.mark.django_db
def test_kpi_calculation_46(AUDIT_START_DATE):
    """Tests that KPI46 is calculated correctly.

    Numerator:Total number of admissions with a valid reason for admission
    (item 50) AND with a start date (item 48) OR discharge date (item 49)
    within the audit period
    NOTE: There can be more than one admission per patient, but eliminate
    duplicate entries

    Denominator: Total number of eligible patients (measure 1)
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create  Patients and Visits that should be eligible (KPI1)
    eligible_criteria = {
        "visit__visit_date": AUDIT_START_DATE + relativedelta(days=2),
        "date_of_birth": AUDIT_START_DATE - relativedelta(days=365 * 10),
    }

    # Create passing pts
    passing_valid_admission_reason_and_admission_within_audit_range = PatientFactory(
        # KPI1 eligible
        **eligible_criteria,
        # valid admission reason
        visit__hospital_admission_reason=HOSPITAL_ADMISSION_REASONS[0][0],
        # admission date within audit range
        visit__hospital_admission_date=AUDIT_START_DATE + relativedelta(days=2),
    )
    passing_valid_admission_reason_and_discharge_within_audit_range = PatientFactory(
        # KPI1 eligible
        **eligible_criteria,
        # valid admission reason
        visit__hospital_admission_reason=HOSPITAL_ADMISSION_REASONS[-1][0],
        # discharge date within audit range
        visit__hospital_discharge_date=AUDIT_START_DATE + relativedelta(days=2),
    )

    # Create failing pts
    failing_invalid_admission_reason = PatientFactory(
        # KPI1 eligible
        **eligible_criteria,
        # invalid admission reason
        visit__hospital_admission_reason='42',
        # admission date within audit range
        visit__hospital_admission_date=AUDIT_START_DATE + relativedelta(days=2),
    )
    failing_both_admission_outside_audit_date = PatientFactory(
        # KPI1 eligible
        **eligible_criteria,
        # valid admission reason
        visit__hospital_admission_reason=HOSPITAL_ADMISSION_REASONS[-1][0],
        # admission date outside audit range
        visit__hospital_admission_date=AUDIT_START_DATE - relativedelta(days=2),
    )


    # Create Patients and Visits that should be excluded
    # Visit date before audit period
    ineligible_patient_visit_date = PatientFactory(
        postcode="ineligible_patient_visit_date",
        visit__visit_date=AUDIT_START_DATE - relativedelta(days=10),
        visit__treatment=1,
    )
    # Above age 25 at start of audit period
    ineligible_patient_too_old = PatientFactory(
        postcode="ineligible_patient_too_old",
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 26),
        visit__treatment=1,
    )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(
        pz_code="PZ130", calculation_date=AUDIT_START_DATE
    )

    EXPECTED_TOTAL_ELIGIBLE = 4
    EXPECTED_TOTAL_INELIGIBLE = 2
    EXPECTED_TOTAL_PASSED = 2
    EXPECTED_TOTAL_FAILED = 2

    EXPECTED_KPIRESULT = KPIResult(
        total_eligible=EXPECTED_TOTAL_ELIGIBLE,
        total_passed=EXPECTED_TOTAL_PASSED,
        total_ineligible=EXPECTED_TOTAL_INELIGIBLE,
        total_failed=EXPECTED_TOTAL_FAILED,
    )

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT,
        actual=calc_kpis.calculate_kpi_46_number_of_admissions(),
    )
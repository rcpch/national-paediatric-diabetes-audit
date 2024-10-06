"""Tests for the Glucose Monitoring KPIS."""

import pytest
from dateutil.relativedelta import relativedelta

from project.npda.kpi_class.kpis import CalculateKPIS, KPIResult
from project.npda.models import Patient
from project.npda.tests.factories.patient_factory import PatientFactory
from project.npda.tests.kpi_calculations.test_kpi_calculations import (
    assert_kpi_result_equal,
)


@pytest.mark.django_db
def test_kpi_calculation_21(AUDIT_START_DATE):
    """Tests that KPI21 is calculated correctly.

    Numerator: Number of eligible patients whose most recent entry (based on visit date) for blood glucose monitoring (item 22) is either 2 = Flash glucose monitor or 3 = Modified flash glucose monitor (e.g. with MiaoMiao, Blucon etc.)

    Denominator: Total number of eligible patients (measure 1)
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create  Patients and Visits that should be eligible
    eligible_criteria = {
        "visit__visit_date": AUDIT_START_DATE + relativedelta(days=2),
        "date_of_birth": AUDIT_START_DATE - relativedelta(days=365 * 10),
    }
    passing_glucose_monitoring_2 = PatientFactory(
        # KPI1 eligible
        **eligible_criteria,
        # most recent observation for blood glucose monitoring (item 22) is either 2 = Flash glucose monitor or 3 = Modified flash glucose monitor (e.g. with MiaoMiao, Blucon etc.)
        visit__glucose_monitoring=2,
    )
    passing_glucose_monitoring_3 = PatientFactory(
        # KPI1 eligible
        **eligible_criteria,
        # most recent observation for blood glucose monitoring (item 22) is either 2 = Flash glucose monitor or 3 = Modified flash glucose monitor (e.g. with MiaoMiao, Blucon etc.)
        visit__glucose_monitoring=3,
    )

    for val in (1, 4, 5, 6):
        failing_glucose_monitoring_not_2_or_3 = PatientFactory(
            # KPI1 eligible
            **eligible_criteria,
            # most recent observation for blood glucose monitoring (item 22) is NOT either 2 = Flash glucose monitor or 3 = Modified flash glucose monitor (e.g. with MiaoMiao, Blucon etc.)
            visit__glucose_monitoring=val,
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
    calc_kpis = CalculateKPIS(pz_codes=["PZ130"], calculation_date=AUDIT_START_DATE)

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
        actual=calc_kpis.calculate_kpi_21_flash_glucose_monitor(),
    )


@pytest.mark.django_db
def test_kpi_calculation_22(AUDIT_START_DATE):
    """Tests that KPI22 is calculated correctly.

    Numerator: Number of eligible patients whose most recent entry (based on visit date) for blood glucose monitoring (item 22) is  4 = Real time continuous glucose monitor with alarms

    Denominator: Total number of eligible patients (measure 1)
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create  Patients and Visits that should be eligible
    eligible_criteria = {
        "visit__visit_date": AUDIT_START_DATE + relativedelta(days=2),
        "date_of_birth": AUDIT_START_DATE - relativedelta(days=365 * 10),
    }
    passing_glucose_monitoring_4 = PatientFactory(
        # KPI1 eligible
        **eligible_criteria,
        # most recent observation for  blood glucose monitoring (item 22) is  4 = Real time continuous glucose monitor with alarms
        visit__glucose_monitoring=4,
    )

    for val in (1, 2, 3, 5, 6):
        failing_glucose_monitoring_not_2_or_3 = PatientFactory(
            # KPI1 eligible
            **eligible_criteria,
            # most recent observation for  blood glucose monitoring (item 22) is NOT  4 = Real time continuous glucose monitor with alarms
            visit__glucose_monitoring=val,
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
    calc_kpis = CalculateKPIS(pz_codes=["PZ130"], calculation_date=AUDIT_START_DATE)

    EXPECTED_TOTAL_ELIGIBLE = 6
    EXPECTED_TOTAL_INELIGIBLE = 2
    EXPECTED_TOTAL_PASSED = 1
    EXPECTED_TOTAL_FAILED = 5

    EXPECTED_KPIRESULT = KPIResult(
        total_eligible=EXPECTED_TOTAL_ELIGIBLE,
        total_passed=EXPECTED_TOTAL_PASSED,
        total_ineligible=EXPECTED_TOTAL_INELIGIBLE,
        total_failed=EXPECTED_TOTAL_FAILED,
    )

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT,
        actual=calc_kpis.calculate_kpi_22_real_time_cgm_with_alarms(),
    )


@pytest.mark.django_db
def test_kpi_calculation_23(AUDIT_START_DATE):
    """Tests that KPI23 is calculated correctly.

    Denominator: Total number of eligible patients with Type 1 diabetes (measure 2)

    Numerator: Number of eligible patients whose most recent entry (based on visit date) for blood glucose monitoring (item 22) is  4 = Real time continuous glucose monitor with alarms
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create  Patients and Visits that should be eligible
    eligible_criteria = {
        "visit__visit_date": AUDIT_START_DATE + relativedelta(days=2),
        "date_of_birth": AUDIT_START_DATE - relativedelta(days=365 * 10),
        # KPI 2
        "diagnosis_date": AUDIT_START_DATE + relativedelta(days=10),
    }
    passing_glucose_monitoring_4 = PatientFactory(
        # KPI1 eligible
        **eligible_criteria,
        # most recent observation for  blood glucose monitoring (item 22) is  4 = Real time continuous glucose monitor with alarms
        visit__glucose_monitoring=4,
    )

    for val in (1, 2, 3, 5, 6):
        failing_glucose_monitoring_not_2_or_3 = PatientFactory(
            # KPI1 eligible
            **eligible_criteria,
            # most recent observation for  blood glucose monitoring (item 22) is NOT  4 = Real time continuous glucose monitor with alarms
            visit__glucose_monitoring=val,
        )

    # Create Patients and Visits that should be excluded
    # Visit date before audit period
    ineligible_patient_visit_date = PatientFactory(
        postcode="ineligible_patient_visit_date",
        visit__visit_date=AUDIT_START_DATE - relativedelta(days=10),
        visit__glucose_monitoring=4,
    )
    # Above age 25 at start of audit period
    ineligible_patient_too_old = PatientFactory(
        postcode="ineligible_patient_too_old",
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 26),
        visit__glucose_monitoring=1,
    )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(pz_codes=["PZ130"], calculation_date=AUDIT_START_DATE)

    EXPECTED_TOTAL_ELIGIBLE = 6
    EXPECTED_TOTAL_INELIGIBLE = 2
    EXPECTED_TOTAL_PASSED = 1
    EXPECTED_TOTAL_FAILED = 5

    EXPECTED_KPIRESULT = KPIResult(
        total_eligible=EXPECTED_TOTAL_ELIGIBLE,
        total_passed=EXPECTED_TOTAL_PASSED,
        total_ineligible=EXPECTED_TOTAL_INELIGIBLE,
        total_failed=EXPECTED_TOTAL_FAILED,
    )

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT,
        actual=calc_kpis.calculate_kpi_23_type1_real_time_cgm_with_alarms(),
    )

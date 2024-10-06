"""Tests for the Outcomes KPIs."""

import logging
from typing import List

import pytest
from dateutil.relativedelta import relativedelta

from project.constants.albuminuria_stage import ALBUMINURIA_STAGES
from project.constants.diabetes_types import DIABETES_TYPES
from project.constants.hospital_admission_reasons import \
    HOSPITAL_ADMISSION_REASONS
from project.constants.smoking_status import SMOKING_STATUS
from project.constants.yes_no_unknown import YES_NO_UNKNOWN
from project.npda.general_functions.kpis import CalculateKPIS, KPIResult
from project.npda.models import Patient
from project.npda.tests.factories.patient_factory import PatientFactory
from project.npda.tests.factories.visit_factory import VisitFactory
from project.npda.tests.kpi_calculations.test_kpi_calculations import \
    assert_kpi_result_equal

# Logging
logger = logging.getLogger(__name__)


@pytest.mark.django_db
def test_kpi_calculation_44(AUDIT_START_DATE):
    """Tests that KPI44 is calculated correctly.

    SINGLE NUMBER: Mean of HbA1c measurements (item 17) within the audit
    period, excluding measurements taken within 90 days of diagnosis
    NOTE: The median for each patient is calculated. We then calculate the
    mean of the medians.

    Denominator: Total number of eligible patients (measure 1)
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create  Patients and Visits that should be eligible (KPI1)
    DIAGNOSIS_DATE = AUDIT_START_DATE - relativedelta(days=90)
    eligible_criteria = {
        "visit__visit_date": AUDIT_START_DATE + relativedelta(days=2),
        "date_of_birth": AUDIT_START_DATE - relativedelta(days=365 * 10),
    }

    # Create passing pts
    pt_1_hba1cs = [45, 46, 47]
    passing_pt_1_median_46 = PatientFactory(
        # KPI1 eligible
        **eligible_criteria,
        postcode="passing_pt_1_median_46",
        # HbA1c measurements within the audit period and after 90 days of diagnosis
        visit__hba1c_date=DIAGNOSIS_DATE + relativedelta(days=91),
        visit__hba1c=pt_1_hba1cs[0],
    )
    # 2 more HbA1c measurements
    VisitFactory(
        patient=passing_pt_1_median_46,
        visit_date=AUDIT_START_DATE + relativedelta(months=3),
        # HbA1c measurements within the audit period and after 90 days of diagnosis
        hba1c_date=DIAGNOSIS_DATE + relativedelta(months=3),
        hba1c=pt_1_hba1cs[1],
    )
    VisitFactory(
        patient=passing_pt_1_median_46,
        visit_date=AUDIT_START_DATE + relativedelta(months=6),
        # HbA1c measurements within the audit period and after 90 days of diagnosis
        hba1c_date=DIAGNOSIS_DATE + relativedelta(days=6),
        hba1c=pt_1_hba1cs[2],
    )

    pt_2_hba1cs = [47, 48, 49]
    passing_pt_2_median_48 = PatientFactory(
        # KPI1 eligible
        **eligible_criteria,
        postcode="passing_pt_2_median_48",
        # HbA1c measurements within the audit period and after 90 days of diagnosis
        visit__hba1c_date=DIAGNOSIS_DATE + relativedelta(days=91),
        visit__hba1c=pt_2_hba1cs[0],
    )
    # 2 more HbA1c measurements
    VisitFactory(
        patient=passing_pt_2_median_48,
        visit_date=AUDIT_START_DATE + relativedelta(months=3),
        # HbA1c measurements within the audit period and after 90 days of diagnosis
        hba1c_date=DIAGNOSIS_DATE + relativedelta(months=3),
        hba1c=pt_2_hba1cs[1],
    )
    VisitFactory(
        patient=passing_pt_2_median_48,
        visit_date=AUDIT_START_DATE + relativedelta(months=6),
        # HbA1c measurements within the audit period and after 90 days of diagnosis
        hba1c_date=DIAGNOSIS_DATE + relativedelta(months=6),
        hba1c=pt_2_hba1cs[2],
    )
    # This measurement should NOT be counted
    VisitFactory(
        patient=passing_pt_2_median_48,
        visit_date=DIAGNOSIS_DATE + relativedelta(days=89),
        # HbA1c measurement is within 90 days of diagnosis
        hba1c_date=DIAGNOSIS_DATE + relativedelta(days=89),
        hba1c=1,  # ridiculously low to skew numbers if counted
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

    medians = list(map(calculate_median, [pt_1_hba1cs, pt_2_hba1cs]))
    EXPECTED_MEAN = sum(medians) / len(medians)

    EXPECTED_TOTAL_ELIGIBLE = 2
    EXPECTED_TOTAL_INELIGIBLE = 2
    EXPECTED_TOTAL_PASSED = EXPECTED_MEAN # Stores the mean
    EXPECTED_TOTAL_FAILED = -1 # Not used

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


@pytest.mark.skip(
    reason="Confirm calc issue https://github.com/orgs/rcpch/projects/13/views/1?pane=issue&itemId=81441322"
)
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
        visit__hospital_admission_date=AUDIT_START_DATE
        + relativedelta(days=2),
    )
    passing_valid_admission_reason_and_discharge_within_audit_range = PatientFactory(
        # KPI1 eligible
        **eligible_criteria,
        # valid admission reason
        visit__hospital_admission_reason=HOSPITAL_ADMISSION_REASONS[-1][0],
        # discharge date within audit range
        visit__hospital_discharge_date=AUDIT_START_DATE
        + relativedelta(days=2),
    )

    # Create failing pts
    failing_invalid_admission_reason = PatientFactory(
        # KPI1 eligible
        **eligible_criteria,
        # invalid admission reason
        visit__hospital_admission_reason="42",
        # admission date within audit range
        visit__hospital_admission_date=AUDIT_START_DATE
        + relativedelta(days=2),
    )
    failing_both_admission_outside_audit_date = PatientFactory(
        # KPI1 eligible
        **eligible_criteria,
        # valid admission reason
        visit__hospital_admission_reason=HOSPITAL_ADMISSION_REASONS[-1][0],
        # admission date outside audit range
        visit__hospital_admission_date=AUDIT_START_DATE
        - relativedelta(days=2),
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


@pytest.mark.django_db
def test_kpi_calculation_47(AUDIT_START_DATE):
    """Tests that KPI47 is calculated correctly.

    Numerator:Total number of admissions with a reason for admission
    (item 50) that is 2 = DKA AND with a start date (item 48) OR
    discharge date (item 49) within the audit period
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
    passing_valid_dka_admission_reason_and_admission_within_audit_range = PatientFactory(
        # KPI1 eligible
        **eligible_criteria,
        # valid dka admission reason
        visit__hospital_admission_reason=HOSPITAL_ADMISSION_REASONS[1][0],
        # admission date within audit range
        visit__hospital_admission_date=AUDIT_START_DATE
        + relativedelta(days=2),
    )
    passing_valid_dka_admission_reason_and_discharge_within_audit_range = PatientFactory(
        # KPI1 eligible
        **eligible_criteria,
        # valid dka admission reason
        visit__hospital_admission_reason=HOSPITAL_ADMISSION_REASONS[1][0],
        # discharge date within audit range
        visit__hospital_discharge_date=AUDIT_START_DATE
        + relativedelta(days=2),
    )

    # Create failing pts
    failing_invalid_admission_reason_not_dka = PatientFactory(
        # KPI1 eligible
        **eligible_criteria,
        # invalid admission reason
        visit__hospital_admission_reason=HOSPITAL_ADMISSION_REASONS[0][0],
        # admission date within audit range
        visit__hospital_admission_date=AUDIT_START_DATE
        + relativedelta(days=2),
    )
    failing_both_admission_outside_audit_date = PatientFactory(
        # KPI1 eligible
        **eligible_criteria,
        # valid admission reason
        visit__hospital_admission_reason=HOSPITAL_ADMISSION_REASONS[0][0],
        # admission date outside audit range
        visit__hospital_admission_date=AUDIT_START_DATE
        - relativedelta(days=2),
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
        actual=calc_kpis.calculate_kpi_47_number_of_dka_admissions(),
    )


@pytest.mark.django_db
def test_kpi_calculation_48(AUDIT_START_DATE):
    """Tests that KPI48 is calculated correctly.

    Numerator:Total number of eligible patients with at least one entry for
    Psychological Support (item 39) that is 1 = Yes within the audit period
    (based on visit date)

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
    passing_valid_psych_support = PatientFactory(
        postcode="passing_valid_psych_support",
        # KPI1 eligible
        **eligible_criteria,
        # psych support required
        visit__psychological_additional_support_status=YES_NO_UNKNOWN[0][0],
    )
    # Second visit only with psych support
    passing_patient_second_visit_valid_psych = PatientFactory(
        postcode="passing_patient_second_visit_valid_psych",
        # KPI7 eligible
        **eligible_criteria,
        # KPI 48 specific
        visit__psychological_additional_support_status=None,
    )
    # create 2nd visit with psych status valid
    VisitFactory(
        visit_date=AUDIT_START_DATE + relativedelta(days=2),
        patient=passing_patient_second_visit_valid_psych,
        psychological_additional_support_status=YES_NO_UNKNOWN[0][0],
    )

    # Create failing pts
    failing_invalid_psych_support_no = PatientFactory(
        postcode="failing_invalid_psych_support_no",
        # KPI1 eligible
        **eligible_criteria,
        visit__psychological_additional_support_status=YES_NO_UNKNOWN[1][0],
    )
    failing_invalid_psych_support_unknown = PatientFactory(
        postcode="failing_invalid_psych_support_unknown",
        # KPI1 eligible
        **eligible_criteria,
        visit__psychological_additional_support_status=YES_NO_UNKNOWN[2][0],
    )
    failing_invalid_psych_support_none = PatientFactory(
        postcode="failing_invalid_psych_support_none",
        # KPI1 eligible
        **eligible_criteria,
        visit__psychological_additional_support_status=None,
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

    EXPECTED_TOTAL_ELIGIBLE = 5
    EXPECTED_TOTAL_INELIGIBLE = 2
    EXPECTED_TOTAL_PASSED = 2
    EXPECTED_TOTAL_FAILED = 3

    EXPECTED_KPIRESULT = KPIResult(
        total_eligible=EXPECTED_TOTAL_ELIGIBLE,
        total_passed=EXPECTED_TOTAL_PASSED,
        total_ineligible=EXPECTED_TOTAL_INELIGIBLE,
        total_failed=EXPECTED_TOTAL_FAILED,
    )

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT,
        actual=calc_kpis.calculate_kpi_48_required_additional_psychological_support(),
    )


@pytest.mark.django_db
def test_kpi_calculation_49(AUDIT_START_DATE):
    """Tests that KPI49 is calculated correctly.

    Numerator: Total number of eligible patients whose most recent
    entry for for Albuminuria Stage (item 31) based on observation date
    (item 30) is 2 = Microalbuminuria or 3 = Macroalbuminuria

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
    passing_microalbuminuria = PatientFactory(
        postcode="passing_microalbuminuria",
        # KPI1 eligible
        **eligible_criteria,
        # microalbuminuria
        visit__albuminuria_stage=ALBUMINURIA_STAGES[1][0],
    )
    # Second visit only with valid albuminuria stage
    passing_macroalbuminuria = PatientFactory(
        postcode="passing_macroalbuminuria",
        # KPI1 eligible
        **eligible_criteria,
        # macroalbuminuria
        visit__albuminuria_stage=None,
    )
    # create 2nd visit with valid albuminuria stage
    VisitFactory(
        visit_date=AUDIT_START_DATE + relativedelta(days=2),
        patient=passing_macroalbuminuria,
        albuminuria_stage=ALBUMINURIA_STAGES[2][0],
    )

    # Create failing pts
    failing_normoalbuminuria = PatientFactory(
        postcode="failing_normoalbuminuria",
        # KPI1 eligible
        **eligible_criteria,
        visit__albuminuria_stage=ALBUMINURIA_STAGES[0][0],
    )
    failing_unknown_albuminuria = PatientFactory(
        postcode="failing_unknown_albuminuria",
        # KPI1 eligible
        **eligible_criteria,
        visit__albuminuria_stage=ALBUMINURIA_STAGES[3][0],
    )
    failing_none_albuminuria = PatientFactory(
        postcode="failing_none_albuminuria",
        # KPI1 eligible
        **eligible_criteria,
        visit__albuminuria_stage=None,
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

    EXPECTED_TOTAL_ELIGIBLE = 5
    EXPECTED_TOTAL_INELIGIBLE = 2
    EXPECTED_TOTAL_PASSED = 2
    EXPECTED_TOTAL_FAILED = 3

    EXPECTED_KPIRESULT = KPIResult(
        total_eligible=EXPECTED_TOTAL_ELIGIBLE,
        total_passed=EXPECTED_TOTAL_PASSED,
        total_ineligible=EXPECTED_TOTAL_INELIGIBLE,
        total_failed=EXPECTED_TOTAL_FAILED,
    )

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT,
        actual=calc_kpis.calculate_kpi_49_albuminuria_present(),
    )


def calculate_median(values):
    # Sort the list of integers
    sorted_values = sorted(values)
    n = len(sorted_values)

    if n == 0:
        raise ValueError("The list is empty, cannot compute median.")

    # If the length of the list is odd, return the middle element
    if n % 2 == 1:
        return sorted_values[n // 2]
    else:
        # If the length of the list is even, return the average of the two middle elements
        middle1 = sorted_values[n // 2 - 1]
        middle2 = sorted_values[n // 2]
        return (middle1 + middle2) / 2
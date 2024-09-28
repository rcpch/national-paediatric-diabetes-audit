"""Tests for the 7 Key Processes KPIs."""
import pytest
from dateutil.relativedelta import relativedelta

from project.constants.diabetes_types import DIABETES_TYPES
from project.constants.hba1c_format import HBA1C_FORMATS
from project.constants.retinal_screening_results import \
    RETINAL_SCREENING_RESULTS
from project.npda.general_functions.kpis import CalculateKPIS, KPIResult
from project.npda.models import Patient
from project.npda.tests.factories.patient_factory import PatientFactory
from project.npda.tests.kpi_calculations.test_kpi_calculations import \
    assert_kpi_result_equal


@pytest.mark.django_db
def test_kpi_calculation_25(AUDIT_START_DATE):
    """Tests that KPI25 is calculated correctly.

    Numerator: Number of eligible patients with at least one valid entry for HbA1c value (item 17) with an observation date (item 19) within the audit period

    Denominator: Number of patients with Type 1 diabetes with a complete year of care in the audit period (measure 5)
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create  Patients and Visits that should be eligible (KPI5)
    eligible_criteria = {
        # KPI5 base criteria
        "visit__visit_date": AUDIT_START_DATE + relativedelta(days=2),
        "date_of_birth": AUDIT_START_DATE - relativedelta(days=365 * 10),
        # KPI 5 specific eligibility are any of the following:
        # Date of diagnosis NOT within the audit period
        "diagnosis_date": AUDIT_START_DATE - relativedelta(days=2),
        # Date of leaving service NOT within the audit period
        # transfer date only not None if they have left
        "transfer__date_leaving_service": None,
        # Date of death NOT within the audit period"
        "death_date": None,
    }

    # Passing patients
    passing_patient_valid_hba1c_within_audit_period_1 = PatientFactory(
        postcode="passing_patient_valid_hba1c_within_audit_period_1",
        # KPI5 eligible
        **eligible_criteria,
        # valid HBa1c value within audit period
        visit__hba1c=60.00,
        visit__hba1c_format=HBA1C_FORMATS[0][0],  # mmol/mol
        visit__hba1c_date=AUDIT_START_DATE + relativedelta(days=2),
    )
    passing_patient_valid_hba1c_within_audit_period_2 = PatientFactory(
        postcode="passing_patient_valid_hba1c_within_audit_period_2",
        # KPI5 eligible
        **eligible_criteria,
        # valid HBa1c value within audit period
        visit__hba1c=62.00,
        visit__hba1c_format=HBA1C_FORMATS[0][0],  # mmol/mol
        visit__hba1c_date=AUDIT_START_DATE + relativedelta(days=10),
    )

    # Failing patients
    # No Hba1c value within audit period
    failing_patient_no_hba1c_within_audit_period = PatientFactory(
        postcode="failing_patient_no_hba1c_within_audit_period",
        # KPI5 eligible
        **eligible_criteria,
        # No Hba1c value within audit period
        visit__hba1c=None,
        visit__hba1c_date=None,
    )

    # Create Patients and Visits that should be ineligble
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
    # KPI5 specific
    ineligible_patient_diag_within_audit_period = PatientFactory(
        postcode="ineligible_patient_diag_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of diagnosis within the audit period
        diagnosis_date=AUDIT_START_DATE + relativedelta(days=2),
    )
    ineligible_patient_date_leaving_within_audit_period = PatientFactory(
        postcode="ineligible_patient_date_leaving_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of leaving service within the audit period
        transfer__date_leaving_service=AUDIT_START_DATE
        + relativedelta(days=2),
    )
    ineligible_patient_death_within_audit_period = PatientFactory(
        postcode="ineligible_patient_death_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of death within the audit period"
        death_date=AUDIT_START_DATE + relativedelta(days=2),
    )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(
        pz_code="PZ130", calculation_date=AUDIT_START_DATE
    )

    EXPECTED_TOTAL_ELIGIBLE = 3
    EXPECTED_TOTAL_INELIGIBLE = 5
    EXPECTED_TOTAL_PASSED = 2
    EXPECTED_TOTAL_FAILED = 1

    EXPECTED_KPIRESULT = KPIResult(
        total_eligible=EXPECTED_TOTAL_ELIGIBLE,
        total_passed=EXPECTED_TOTAL_PASSED,
        total_ineligible=EXPECTED_TOTAL_INELIGIBLE,
        total_failed=EXPECTED_TOTAL_FAILED,
    )

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT,
        actual=calc_kpis.calculate_kpi_25_hba1c(),
    )


@pytest.mark.django_db
def test_kpi_calculation_26(AUDIT_START_DATE):
    """Tests that KPI26 is calculated correctly.

    Numerator: Number of eligible patients at least one valid entry for Patient Height (item 14) and for Patient Weight (item 15) with an observation date (item 16) within the audit period

    Denominator: Number of patients with Type 1 diabetes with a complete year of care in the audit period (measure 5)
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create  Patients and Visits that should be eligible (KPI5)
    eligible_criteria = {
        # KPI5 base criteria
        "visit__visit_date": AUDIT_START_DATE + relativedelta(days=2),
        "date_of_birth": AUDIT_START_DATE - relativedelta(days=365 * 10),
        # KPI 5 specific eligibility are any of the following:
        # Date of diagnosis NOT within the audit period
        "diagnosis_date": AUDIT_START_DATE - relativedelta(days=2),
        # Date of leaving service NOT within the audit period
        # transfer date only not None if they have left
        "transfer__date_leaving_service": None,
        # Date of death NOT within the audit period"
        "death_date": None,
    }

    # Passing patients
    passing_patient_valid_ht_wt_within_audit_period_1 = PatientFactory(
        postcode="passing_patient_valid_ht_wt_within_audit_period_1",
        # KPI5 eligible
        **eligible_criteria,
        # valid ht wt values within audit period
        visit__height=140.0,
        visit__weight=40.0,
        visit__height_weight_observation_date=AUDIT_START_DATE
        + relativedelta(days=2),
    )
    passing_patient_valid_ht_wt_within_audit_period_2 = PatientFactory(
        postcode="passing_patient_valid_ht_wt_within_audit_period_2",
        # KPI5 eligible
        **eligible_criteria,
        # valid ht wt values within audit period
        visit__height=160.0,
        visit__weight=50.0,
        visit__height_weight_observation_date=AUDIT_START_DATE
        + relativedelta(days=2),
    )

    # Failing patients
    # No ht wt value within audit period
    failing_patient_no_ht_wt_within_audit_period = PatientFactory(
        postcode="failing_patient_no_ht_wt_within_audit_period",
        # KPI5 eligible
        **eligible_criteria,
        # No ht wt value within audit period
        visit__height=None,
        visit__weight=None,
        visit__height_weight_observation_date=None,
    )
    # Ht wt value before audit period
    failing_patient_ht_wt_before_audit_period = PatientFactory(
        postcode="failing_patient_ht_wt_before_audit_period",
        # KPI5 eligible
        **eligible_criteria,
        # ht wt value before audit period
        visit__height=160.0,
        visit__weight=50.0,
        visit__height_weight_observation_date=AUDIT_START_DATE
        - relativedelta(days=2),
    )

    # Create Patients and Visits that should be ineligble
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
    # KPI5 specific
    ineligible_patient_diag_within_audit_period = PatientFactory(
        postcode="ineligible_patient_diag_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of diagnosis within the audit period
        diagnosis_date=AUDIT_START_DATE + relativedelta(days=2),
    )
    ineligible_patient_date_leaving_within_audit_period = PatientFactory(
        postcode="ineligible_patient_date_leaving_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of leaving service within the audit period
        transfer__date_leaving_service=AUDIT_START_DATE
        + relativedelta(days=2),
    )
    ineligible_patient_death_within_audit_period = PatientFactory(
        postcode="ineligible_patient_death_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of death within the audit period"
        death_date=AUDIT_START_DATE + relativedelta(days=2),
    )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(
        pz_code="PZ130", calculation_date=AUDIT_START_DATE
    )

    EXPECTED_TOTAL_ELIGIBLE = 4
    EXPECTED_TOTAL_INELIGIBLE = 5
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
        actual=calc_kpis.calculate_kpi_26_bmi(),
    )


@pytest.mark.django_db
def test_kpi_calculation_27(AUDIT_START_DATE):
    """Tests that KPI27 is calculated correctly.

    Numerator: Number of eligible patients with at least one entry for Thyroid function observation date (item 34) within the audit period

    Denominator: Number of patients with Type 1 diabetes with a complete year of care in the audit period (measure 5)
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create  Patients and Visits that should be eligible (KPI5)
    eligible_criteria = {
        # KPI5 base criteria
        "visit__visit_date": AUDIT_START_DATE + relativedelta(days=2),
        "date_of_birth": AUDIT_START_DATE - relativedelta(days=365 * 10),
        # KPI 5 specific eligibility are any of the following:
        # Date of diagnosis NOT within the audit period
        "diagnosis_date": AUDIT_START_DATE - relativedelta(days=2),
        # Date of leaving service NOT within the audit period
        # transfer date only not None if they have left
        "transfer__date_leaving_service": None,
        # Date of death NOT within the audit period"
        "death_date": None,
    }

    # Passing patients
    passing_patient_thryoid_function_date_within_audit_period_1 = PatientFactory(
        postcode="passing_patient_valid_hba1c_within_audit_period_1",
        # KPI5 eligible
        **eligible_criteria,
        # valid thryoid function date within audit period
        visit__thyroid_function_date=AUDIT_START_DATE + relativedelta(days=2),
    )
    passing_patient_valid_thryoid_function_within_audit_period_2 = PatientFactory(
        postcode="passing_patient_valid_thryoid_function_within_audit_period_2",
        # KPI5 eligible
        **eligible_criteria,
        # valid thryoid function date within audit period
        visit__thyroid_function_date=AUDIT_START_DATE + relativedelta(days=12),
    )

    # Failing patients
    # No thyroid function date within audit period
    failing_patient_no_thyroid_fn = PatientFactory(
        postcode="failing_patient_no_thyroid_fn",
        # KPI5 eligible
        **eligible_criteria,
        # no thyroid fn
        visit__thyroid_function_date=None,
    )
    # thryoid fn before audit period
    failing_patient_thyroid_before_audit_period = PatientFactory(
        postcode="failing_patient_thyroid_before_audit_period",
        # KPI5 eligible
        **eligible_criteria,
        # thyroid date before audit period
        visit__thyroid_function_date=AUDIT_START_DATE - relativedelta(days=2),
    )

    # Create Patients and Visits that should be ineligble
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
    # KPI5 specific
    ineligible_patient_diag_within_audit_period = PatientFactory(
        postcode="ineligible_patient_diag_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of diagnosis within the audit period
        diagnosis_date=AUDIT_START_DATE + relativedelta(days=2),
    )
    ineligible_patient_date_leaving_within_audit_period = PatientFactory(
        postcode="ineligible_patient_date_leaving_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of leaving service within the audit period
        transfer__date_leaving_service=AUDIT_START_DATE
        + relativedelta(days=2),
    )
    ineligible_patient_death_within_audit_period = PatientFactory(
        postcode="ineligible_patient_death_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of death within the audit period"
        death_date=AUDIT_START_DATE + relativedelta(days=2),
    )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(
        pz_code="PZ130", calculation_date=AUDIT_START_DATE
    )

    EXPECTED_TOTAL_ELIGIBLE = 4
    EXPECTED_TOTAL_INELIGIBLE = 5
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
        actual=calc_kpis.calculate_kpi_27_thyroid_screen(),
    )


@pytest.mark.django_db
def test_kpi_calculation_28(AUDIT_START_DATE):
    """Tests that KPI28 is calculated correctly.

    Numerator: Number of eligible patients with a valid entry for systolic measurement (item 23) with an observation date (item 25) within the audit period

    Denominator: Number of patients with Type 1 diabetes aged 12+ with a complete year of care in audit period (measure 6)

    # NOTE: Does not need a valid diastolic measurement
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create  Patients and Visits that should be eligible (KPI6)
    eligible_criteria = {
        # First needs to be KPI1 eligible
        # Age 12 and above at the start of the audit period
        "date_of_birth": AUDIT_START_DATE - relativedelta(years=12),
        # Diagnosis of Type 1 diabetes
        "diabetes_type": DIABETES_TYPES[0][0],
        # KPI 6 specific = an observation within the audit period
        "visit__height_weight_observation_date": AUDIT_START_DATE
        + relativedelta(days=2),
        # Also has same exclusions as KPI 5
        # Date of diagnosis NOT within the audit period
        "diagnosis_date": AUDIT_START_DATE - relativedelta(days=2),
        # Date of leaving service NOT within the audit period
        # transfer date only not None if they have left
        "transfer__date_leaving_service": None,
        # Date of death NOT within the audit period"
        "death_date": None,
    }

    # Passing patients
    passing_patient_systolic_bp_within_audit_period_1 = PatientFactory(
        postcode="passing_patient_systolic_bp_within_audit_period_1",
        # KPI6 eligible
        **eligible_criteria,
        # valid bp date within audit period
        visit__systolic_blood_pressure=120,
        visit__blood_pressure_observation_date=AUDIT_START_DATE
        + relativedelta(days=2),
    )
    passing_patient_systolic_bp_within_audit_period_2 = PatientFactory(
        postcode="passing_patient_systolic_bp_within_audit_period_2",
        # KPI6 eligible
        **eligible_criteria,
        # valid bp date within audit period
        visit__systolic_blood_pressure=130,
        visit__blood_pressure_observation_date=AUDIT_START_DATE
        + relativedelta(days=5),
    )

    # Failing patients
    # No systolic date within audit period
    failing_patient_no_systolic = PatientFactory(
        postcode="failing_patient_no_systolic",
        # KPI6 eligible
        **eligible_criteria,
        # no systolic date
        visit__systolic_blood_pressure=None,
        visit__blood_pressure_observation_date=None,
    )
    # systolic before audit period
    failing_patient_systolic_before_audit = PatientFactory(
        postcode="failing_patient_systolic_before_audit",
        # KPI6 eligible
        **eligible_criteria,
        # systolic date before audit period
        visit__systolic_blood_pressure=120,
        visit__blood_pressure_observation_date=AUDIT_START_DATE
        - relativedelta(days=2),
    )

    # Create Patients and Visits that should be ineligble
    ineligible_patient_diag_within_audit_period = PatientFactory(
        postcode="ineligible_patient_diag_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of diagnosis within the audit period
        diagnosis_date=AUDIT_START_DATE + relativedelta(days=2),
    )
    ineligible_patient_date_leaving_within_audit_period = PatientFactory(
        postcode="ineligible_patient_date_leaving_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of leaving service within the audit period
        transfer__date_leaving_service=AUDIT_START_DATE
        + relativedelta(days=2),
    )
    ineligible_patient_death_within_audit_period = PatientFactory(
        postcode="ineligible_patient_death_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of death within the audit period"
        death_date=AUDIT_START_DATE + relativedelta(days=2),
    )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(
        pz_code="PZ130", calculation_date=AUDIT_START_DATE
    )

    EXPECTED_TOTAL_ELIGIBLE = 4
    EXPECTED_TOTAL_INELIGIBLE = 3
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
        actual=calc_kpis.calculate_kpi_28_blood_pressure(),
    )


@pytest.mark.django_db
def test_kpi_calculation_29(AUDIT_START_DATE):
    """Tests that KPI29 is calculated correctly.

     Numerator: Number of eligible patients with at entry for Urinary Albumin Level (item 29) with an observation date (item 30) within the audit period

    Denominator: Number of patients with Type 1 diabetes aged 12+ with a complete year of care in audit period (measure 6)
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create  Patients and Visits that should be eligible (KPI6)
    eligible_criteria = {
        # First needs to be KPI1 eligible
        # Age 12 and above at the start of the audit period
        "date_of_birth": AUDIT_START_DATE - relativedelta(years=12),
        # Diagnosis of Type 1 diabetes
        "diabetes_type": DIABETES_TYPES[0][0],
        # KPI 6 specific = an observation within the audit period
        "visit__height_weight_observation_date": AUDIT_START_DATE
        + relativedelta(days=2),
        # Also has same exclusions as KPI 5
        # Date of diagnosis NOT within the audit period
        "diagnosis_date": AUDIT_START_DATE - relativedelta(days=2),
        # Date of leaving service NOT within the audit period
        # transfer date only not None if they have left
        "transfer__date_leaving_service": None,
        # Date of death NOT within the audit period"
        "death_date": None,
    }

    # Passing patients
    passing_patient_urinary_albumin_within_audit_period_1 = PatientFactory(
        postcode="passing_patient_urinary_albumin_within_audit_period_1",
        # KPI6 eligible
        **eligible_criteria,
        # valid ACR within audit period
        visit__albumin_creatinine_ratio=2,
        visit__albumin_creatinine_ratio_date=AUDIT_START_DATE
        + relativedelta(days=2),
    )
    passing_patient_urinary_albumin_within_audit_period_2 = PatientFactory(
        postcode="passing_patient_urinary_albumin_within_audit_period_2",
        # KPI6 eligible
        **eligible_criteria,
        # valid ACR within audit period
        visit__albumin_creatinine_ratio=3,
        visit__albumin_creatinine_ratio_date=AUDIT_START_DATE
        + relativedelta(days=27),
    )

    # Failing patients
    # No urinary albumin within audit period
    failing_patient_no_acr = PatientFactory(
        postcode="failing_patient_no_acr",
        # KPI6 eligible
        **eligible_criteria,
        # no ACR
        visit__albumin_creatinine_ratio=None,
        visit__albumin_creatinine_ratio_date=None,
    )
    # urinary_albumin before audit period
    failing_patient_urinary_albumin_before_audit = PatientFactory(
        postcode="failing_patient_urinary_albumin_before_audit",
        # KPI6 eligible
        **eligible_criteria,
        # ACR before audit period
        visit__albumin_creatinine_ratio=3,
        visit__albumin_creatinine_ratio_date=AUDIT_START_DATE
        - relativedelta(days=2),
    )

    # Create Patients and Visits that should be ineligble
    ineligible_patient_diag_within_audit_period = PatientFactory(
        postcode="ineligible_patient_diag_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of diagnosis within the audit period
        diagnosis_date=AUDIT_START_DATE + relativedelta(days=2),
    )
    ineligible_patient_date_leaving_within_audit_period = PatientFactory(
        postcode="ineligible_patient_date_leaving_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of leaving service within the audit period
        transfer__date_leaving_service=AUDIT_START_DATE
        + relativedelta(days=2),
    )
    ineligible_patient_death_within_audit_period = PatientFactory(
        postcode="ineligible_patient_death_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of death within the audit period"
        death_date=AUDIT_START_DATE + relativedelta(days=2),
    )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(
        pz_code="PZ130", calculation_date=AUDIT_START_DATE
    )

    EXPECTED_TOTAL_ELIGIBLE = 4
    EXPECTED_TOTAL_INELIGIBLE = 3
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
        actual=calc_kpis.calculate_kpi_29_urinary_albumin(),
    )


@pytest.mark.django_db
def test_kpi_calculation_30(AUDIT_START_DATE):
    """Tests that KPI30 is calculated correctly.

    Numerator: Number of eligible patients with at least one entry for Retinal Screening Result (item 28) is either 1 = Normal or 2 = Abnormal AND the observation date (item 27) is within the audit period

    Denominator: Number of patients with Type 1 diabetes aged 12+ with a complete year of care in audit period (measure 6)
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create  Patients and Visits that should be eligible (KPI6)
    eligible_criteria = {
        # First needs to be KPI1 eligible
        # Age 12 and above at the start of the audit period
        "date_of_birth": AUDIT_START_DATE - relativedelta(years=12),
        # Diagnosis of Type 1 diabetes
        "diabetes_type": DIABETES_TYPES[0][0],
        # KPI 6 specific = an observation within the audit period
        "visit__height_weight_observation_date": AUDIT_START_DATE
        + relativedelta(days=2),
        # Also has same exclusions as KPI 5
        # Date of diagnosis NOT within the audit period
        "diagnosis_date": AUDIT_START_DATE - relativedelta(days=2),
        # Date of leaving service NOT within the audit period
        # transfer date only not None if they have left
        "transfer__date_leaving_service": None,
        # Date of death NOT within the audit period"
        "death_date": None,
    }

    # Passing patients
    passing_patient_retinal_screen_within_audit_period_1 = PatientFactory(
        postcode="passing_patient_retinal_screen_within_audit_period_1",
        # KPI6 eligible
        **eligible_criteria,
        # valid retinal screen within audit period
        visit__retinal_screening_result=RETINAL_SCREENING_RESULTS[0][0],
        visit__retinal_screening_observation_date=AUDIT_START_DATE
        + relativedelta(days=2),
    )
    passing_patient_urinary_albumin_within_audit_period_2 = PatientFactory(
        postcode="passing_patient_urinary_albumin_within_audit_period_2",
        # KPI6 eligible
        **eligible_criteria,
        # valid retinal screen within audit period
        visit__retinal_screening_result=RETINAL_SCREENING_RESULTS[1][0],
        visit__retinal_screening_observation_date=AUDIT_START_DATE
        + relativedelta(days=32),
    )

    # Failing patients
    failing_patient_invalid_retinal_screen = PatientFactory(
        postcode="failing_patient_no_retinal_screen",
        # KPI6 eligible
        **eligible_criteria,
        # invalid retinal_screen
        visit__retinal_screening_result=RETINAL_SCREENING_RESULTS[2][0],
        visit__retinal_screening_observation_date=AUDIT_START_DATE
        + relativedelta(days=32),
    )
    # No retinal_screen within audit period
    failing_patient_no_retinal_screen = PatientFactory(
        postcode="failing_patient_no_retinal_screen",
        # KPI6 eligible
        **eligible_criteria,
        # no retinal_screen
        visit__retinal_screening_result=None,
        visit__retinal_screening_observation_date=None,
    )
    # retinal_screen before audit period
    failing_patient_retinal_screen_before_audit = PatientFactory(
        postcode="failing_patient_retinal_screen_before_audit",
        # KPI6 eligible
        **eligible_criteria,
        # retinal_screen before audit period
        visit__retinal_screening_result=RETINAL_SCREENING_RESULTS[2][0],
        visit__retinal_screening_observation_date=AUDIT_START_DATE
        - relativedelta(days=2),
    )

    # Create Patients and Visits that should be ineligble
    ineligible_patient_diag_within_audit_period = PatientFactory(
        postcode="ineligible_patient_diag_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of diagnosis within the audit period
        diagnosis_date=AUDIT_START_DATE + relativedelta(days=2),
    )
    ineligible_patient_date_leaving_within_audit_period = PatientFactory(
        postcode="ineligible_patient_date_leaving_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of leaving service within the audit period
        transfer__date_leaving_service=AUDIT_START_DATE
        + relativedelta(days=2),
    )
    ineligible_patient_death_within_audit_period = PatientFactory(
        postcode="ineligible_patient_death_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of death within the audit period"
        death_date=AUDIT_START_DATE + relativedelta(days=2),
    )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(
        pz_code="PZ130", calculation_date=AUDIT_START_DATE
    )

    EXPECTED_TOTAL_ELIGIBLE = 5
    EXPECTED_TOTAL_INELIGIBLE = 3
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
        actual=calc_kpis.calculate_kpi_30_retinal_screening(),
    )


@pytest.mark.django_db
def test_kpi_calculation_31(AUDIT_START_DATE):
    """Tests that KPI31 is calculated correctly.

    Numerator: Number of eligible patients with at least one entry for Foot Examination Date (item 26) within the audit period

    Denominator: Number of patients with Type 1 diabetes aged 12+ with a complete year of care in audit period (measure 6)
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create  Patients and Visits that should be eligible (KPI6)
    eligible_criteria = {
        # First needs to be KPI1 eligible
        # Age 12 and above at the start of the audit period
        "date_of_birth": AUDIT_START_DATE - relativedelta(years=12),
        # Diagnosis of Type 1 diabetes
        "diabetes_type": DIABETES_TYPES[0][0],
        # KPI 6 specific = an observation within the audit period
        "visit__height_weight_observation_date": AUDIT_START_DATE
        + relativedelta(days=2),
        # Also has same exclusions as KPI 5
        # Date of diagnosis NOT within the audit period
        "diagnosis_date": AUDIT_START_DATE - relativedelta(days=2),
        # Date of leaving service NOT within the audit period
        # transfer date only not None if they have left
        "transfer__date_leaving_service": None,
        # Date of death NOT within the audit period"
        "death_date": None,
    }

    # Passing patients
    passing_patient_foot_exam_within_audit_period_1 = PatientFactory(
        postcode="passing_patient_foot_exam_within_audit_period_1",
        # KPI6 eligible
        **eligible_criteria,
        # valid foot exam within audit period
        visit__foot_examination_observation_date=AUDIT_START_DATE
        + relativedelta(days=2),
    )
    passing_patient_foot_exam_within_audit_period_2 = PatientFactory(
        postcode="passing_patient_foot_exam_within_audit_period_2",
        # KPI6 eligible
        **eligible_criteria,
        # valid foot exam within audit period
        visit__foot_examination_observation_date=AUDIT_START_DATE
        + relativedelta(days=7),
    )

    # Failing patients
    # No foot_exam within audit period
    failing_patient_no_retinal_screen = PatientFactory(
        postcode="failing_patient_no_retinal_screen",
        # KPI6 eligible
        **eligible_criteria,
        # no foot_exam
        visit__foot_examination_observation_date=None,
    )
    # foot_exam before audit period
    failing_patient_foot_exam_before_audit = PatientFactory(
        postcode="failing_patient_foot_exam_before_audit",
        # KPI6 eligible
        **eligible_criteria,
        # foot_exam before audit period
        visit__foot_examination_observation_date=AUDIT_START_DATE
        - relativedelta(days=2),
    )

    # Create Patients and Visits that should be ineligble
    ineligible_patient_diag_within_audit_period = PatientFactory(
        postcode="ineligible_patient_diag_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of diagnosis within the audit period
        diagnosis_date=AUDIT_START_DATE + relativedelta(days=2),
    )
    ineligible_patient_date_leaving_within_audit_period = PatientFactory(
        postcode="ineligible_patient_date_leaving_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of leaving service within the audit period
        transfer__date_leaving_service=AUDIT_START_DATE
        + relativedelta(days=2),
    )
    ineligible_patient_death_within_audit_period = PatientFactory(
        postcode="ineligible_patient_death_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of death within the audit period"
        death_date=AUDIT_START_DATE + relativedelta(days=2),
    )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(
        pz_code="PZ130", calculation_date=AUDIT_START_DATE
    )

    EXPECTED_TOTAL_ELIGIBLE = 4
    EXPECTED_TOTAL_INELIGIBLE = 3
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
        actual=calc_kpis.calculate_kpi_31_foot_examination(),
    )


@pytest.mark.skip(
    reason="KPI32 calculation definition needs to be confirmed, just stubbed out for now, issue #274 https://github.com/orgs/rcpch/projects/13/views/1?pane=issue&itemId=79836032"
)
@pytest.mark.django_db
def test_kpi_calculation_32(AUDIT_START_DATE):
    """Tests that KPI32 is calculated correctly.

    COUNT: Number of eligible patients with care processes 25,26,27,28,29, and 31 completed in the audit period

    NOTE: Excludes Retinal screening, as this only needs to be completed every 2 years

    Eligible patients = KPI_5_TOTAL_ELIGIBLE + KPI_6_TOTAL_ELIGIBLE
    PASS = of eligible patients, how many completed KPI 25-29, 31, 32 (exclude 30 retinal screening)
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create  Patients and Visits that should be eligible (KPI5 & KPI6)
    elibible_criteria_base = {
        # Diagnosis of Type 1 diabetes
        "diabetes_type": DIABETES_TYPES[0][0],
        # Date of diagnosis NOT within the audit period
        "diagnosis_date": AUDIT_START_DATE - relativedelta(days=2),
        # Date of leaving service NOT within the audit period
        "transfer__date_leaving_service": None,
        # Date of death NOT within the audit period"
        "death_date": None,
    }
    eligible_criteria_kpi_5 = {
        # a visit date or admission date within the audit period
        "visit__visit_date": AUDIT_START_DATE + relativedelta(days=2),
        # Below the age of 25 at the start of the audit period
        "date_of_birth": AUDIT_START_DATE - relativedelta(days=365 * 10),
    }
    eligible_criteria_kpi_6 = {
        # Age 12 and above at the start of the audit period
        "date_of_birth": AUDIT_START_DATE - relativedelta(years=12),
        # an observation within the audit period
        "visit__height_weight_observation_date": AUDIT_START_DATE
        + relativedelta(days=2),
    }

    eligible_criteria = {
        **elibible_criteria_base,
        **eligible_criteria_kpi_5,
        **eligible_criteria_kpi_6,
    }

    # Passing patients

    # Failing patients

    # Create Patients and Visits that should be ineligble

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(
        pz_code="PZ130", calculation_date=AUDIT_START_DATE
    )

    EXPECTED_TOTAL_ELIGIBLE = 4
    EXPECTED_TOTAL_INELIGIBLE = 3
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
        actual=calc_kpis.calculate_kpi_32_health_check_completion_rate(),
    )
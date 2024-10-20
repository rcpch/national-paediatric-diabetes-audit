"""Tests for the 7 Key Processes KPIs."""

import logging
from typing import List

import pytest
from dateutil.relativedelta import relativedelta

from project.constants.diabetes_types import DIABETES_TYPES
from project.constants.smoking_status import SMOKING_STATUS
from project.npda.kpi_class.kpis import CalculateKPIS, KPIResult
from project.npda.models import Patient
from project.npda.tests.factories.patient_factory import PatientFactory
from project.npda.tests.factories.visit_factory import VisitFactory
from project.npda.tests.kpi_calculations.test_calculate_kpis import \
    assert_kpi_result_equal

# Logging
logger = logging.getLogger(__name__)


@pytest.mark.django_db
def test_kpi_calculation_41(AUDIT_START_DATE, AUDIT_END_DATE):
    """Tests that KPI41 is calculated correctly.

    Numerator: Number of eligible patients with an entry for Coeliac Disease Screening Date (item 36) within 90 days of Date of Diabetes Diagnosis (item 7)

    Denominator: Number of patients with Type 1 diabetes who were diagnosed at least 90 days before the end of the audit period.

     NOTE: denominator is essentially KPI7 (total new T1DM diagnoses) plus
        extra filter for coeliac diagnosis < (AUDIT_END_DATE - 90 DAYS)
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create  Patients and Visits that should be eligible (KPI7)
    DIAB_DIAGNOSIS_91D_BEFORE_END = AUDIT_END_DATE - relativedelta(days=91)
    eligible_criteria = {
        "visit__visit_date": DIAB_DIAGNOSIS_91D_BEFORE_END - relativedelta(months=2),
        "date_of_birth": AUDIT_START_DATE - relativedelta(years=10),
        "diabetes_type": DIABETES_TYPES[0][0],
        # any other observation date
        "visit__height_weight_observation_date": DIAB_DIAGNOSIS_91D_BEFORE_END,
        # KPI 41 specific
        "diagnosis_date": DIAB_DIAGNOSIS_91D_BEFORE_END,
    }

    # Passing patients
    # coeliac screen < 90D before T1DM diagnosis
    passing_patient_1 = PatientFactory(
        postcode="passing_patient_1",
        # KPI7 eligible
        **eligible_criteria,
        # KPI 41 specific
        visit__coeliac_screen_date=DIAB_DIAGNOSIS_91D_BEFORE_END
        - relativedelta(days=90),
    )
    # only 2nd visit has coeliac screen
    passing_patient_2 = PatientFactory(
        postcode="passing_patient_2",
        # KPI7 eligible
        **eligible_criteria,
        # KPI 41 specific
        visit__coeliac_screen_date=None,
    )
    # create 2nd visit with coeliac screen < 90 days after T1DM diagnosis
    VisitFactory(
        patient=passing_patient_2,
        coeliac_screen_date=DIAB_DIAGNOSIS_91D_BEFORE_END + relativedelta(days=90),
    )

    # Failing patients
    # new T1DM diagnosis but no coeliac screen
    failing_patient_1_no_coeliac_screen = PatientFactory(
        postcode="failing_patient_1_no_coeliac_screen",
        # KPI7 eligible
        **eligible_criteria,
        # KPI 41 specific
        visit__coeliac_screen_date=None,
    )
    # new T1DM diagnosis lt 90 days audit end but coeliac screen 91 days after
    # overriding diagnosis date so coeliac screen will be within audit end
    eligible_criteria_with_diag_92D_before_end = eligible_criteria.copy()
    eligible_criteria_with_diag_92D_before_end["diagnosis_date"] = (
        AUDIT_END_DATE - relativedelta(days=92)
    )
    failing_patient_2_coeliac_91D_after_diag = PatientFactory(
        postcode="failing_patient_2_coeliac_91D_after_diag",
        # KPI7 eligible
        **eligible_criteria_with_diag_92D_before_end,
        # KPI 41 specific
        visit__coeliac_screen_date=eligible_criteria_with_diag_92D_before_end[
            "diagnosis_date"
        ]
        + relativedelta(days=91),
    )

    # Create Patients and Visits that should be ineligble (KPI7)
    ineligible_patient_not_t1dm = PatientFactory(
        postcode="ineligible_patient_not_t1dm",
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # not T1DM
        diabetes_type=DIABETES_TYPES[1][0],
        # Date of diagnosis inside the audit period
        diagnosis_date=AUDIT_START_DATE + relativedelta(days=2),
    )
    ineligible_patient_diag_outside_audit_period = PatientFactory(
        postcode="ineligible_patient_diag_outside_audit_period",
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # T1DM
        diabetes_type=DIABETES_TYPES[0][0],
        # Date of diagnosis outside the audit period
        diagnosis_date=AUDIT_START_DATE - relativedelta(days=2),
    )
    ineligible_patient_diag_90D_before_end = PatientFactory(
        postcode="ineligible_patient_diag_90D_before_end",
        visit__visit_date=AUDIT_END_DATE - relativedelta(days=2),
        # T1DM
        diabetes_type=DIABETES_TYPES[0][0],
        # Date of diag 2 days before end of audit period
        diagnosis_date=AUDIT_END_DATE - relativedelta(days=90),
        visit__coeliac_screen_date=AUDIT_END_DATE - relativedelta(days=90),
    )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(calculation_date=AUDIT_START_DATE)
    # Need to be mocked as not using public `calculate_kpis_for_*` methods
    calc_kpis.patients = Patient.objects.all()
    calc_kpis.total_patients_count = Patient.objects.count()

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
        actual=calc_kpis.calculate_kpi_41_coeliac_disease_screening(),
    )


@pytest.mark.django_db
def test_kpi_calculation_42(AUDIT_START_DATE, AUDIT_END_DATE):
    """Tests that KPI42 is calculated correctly.

    Numerator: Number of eligible patients with an entry for Thyroid Function Observation Date (item 34) within 90 days (<= | >=) of Date of Diabetes Diagnosis (item 7)

    Denominator: Number of patients with Type 1 diabetes who were diagnosed at least 90 days before the end of the audit period

    (NOTE: measure 7 AND diabetes diagnosis date < (AUDIT_END_DATE - 90 days))
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create  Patients and Visits that should be eligible (KPI7)
    DIAB_DIAGNOSIS_91D_BEFORE_END = AUDIT_END_DATE - relativedelta(days=91)
    eligible_criteria = {
        "visit__visit_date": DIAB_DIAGNOSIS_91D_BEFORE_END - relativedelta(months=2),
        "date_of_birth": AUDIT_START_DATE - relativedelta(years=10),
        "diabetes_type": DIABETES_TYPES[0][0],
        # any other observation date
        "visit__height_weight_observation_date": DIAB_DIAGNOSIS_91D_BEFORE_END,
        # KPI 42 specific
        "diagnosis_date": DIAB_DIAGNOSIS_91D_BEFORE_END,
    }

    # Passing patients
    # thyroid_function_date < 90D before T1DM diagnosis
    passing_patient_1 = PatientFactory(
        postcode="passing_patient_1",
        # KPI7 eligible
        **eligible_criteria,
        # KPI 42 specific
        visit__thyroid_function_date=DIAB_DIAGNOSIS_91D_BEFORE_END
        - relativedelta(days=90),
    )
    # only 2nd visit has thyroid_function_date
    passing_patient_2 = PatientFactory(
        postcode="passing_patient_2",
        # KPI7 eligible
        **eligible_criteria,
        # KPI 42 specific
        visit__thyroid_function_date=None,
    )
    # create 2nd visit with thyroid_function_date < 90 days after T1DM diagnosis
    VisitFactory(
        patient=passing_patient_2,
        thyroid_function_date=DIAB_DIAGNOSIS_91D_BEFORE_END + relativedelta(days=90),
    )

    # Failing patients
    # new T1DM diagnosis but no thyroid_function_date
    failing_patient_1_no_thyroid_fn_date = PatientFactory(
        postcode="failing_patient_1_no_thyroid_fn_date",
        # KPI7 eligible
        **eligible_criteria,
        # KPI 42 specific
        visit__thyroid_function_date=None,
    )
    # new T1DM diagnosis lt 90 days audit end but thyroid_function_date 91 days after
    # overriding diagnosis date so thyroid_function_date will be within audit end
    eligible_criteria_with_diag_92D_before_end = eligible_criteria.copy()
    eligible_criteria_with_diag_92D_before_end["diagnosis_date"] = (
        AUDIT_END_DATE - relativedelta(days=92)
    )
    failing_patient_2_thyroid_fn_date_91D_after_diag = PatientFactory(
        postcode="failing_patient_2_thyroid_fn_date_91D_after_diag",
        # KPI7 eligible
        **eligible_criteria_with_diag_92D_before_end,
        # KPI 42 specific
        visit__thyroid_function_date=eligible_criteria_with_diag_92D_before_end[
            "diagnosis_date"
        ]
        + relativedelta(days=91),
    )

    # Create Patients and Visits that should be ineligble (KPI7)
    ineligible_patient_not_t1dm = PatientFactory(
        postcode="ineligible_patient_not_t1dm",
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # not T1DM
        diabetes_type=DIABETES_TYPES[1][0],
        # Date of diagnosis inside the audit period
        diagnosis_date=AUDIT_START_DATE + relativedelta(days=2),
    )
    ineligible_patient_diag_outside_audit_period = PatientFactory(
        postcode="ineligible_patient_diag_outside_audit_period",
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # T1DM
        diabetes_type=DIABETES_TYPES[0][0],
        # Date of diagnosis outside the audit period
        diagnosis_date=AUDIT_START_DATE - relativedelta(days=2),
    )
    ineligible_patient_diag_90D_before_end = PatientFactory(
        postcode="ineligible_patient_diag_90D_before_end",
        visit__visit_date=AUDIT_END_DATE - relativedelta(days=2),
        # T1DM
        diabetes_type=DIABETES_TYPES[0][0],
        # Date of diag 2 days before end of audit period
        diagnosis_date=AUDIT_END_DATE - relativedelta(days=90),
        visit__thyroid_function_date=AUDIT_END_DATE - relativedelta(days=90),
    )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(calculation_date=AUDIT_START_DATE)
    # Need to be mocked as not using public `calculate_kpis_for_*` methods
    calc_kpis.patients = Patient.objects.all()
    calc_kpis.total_patients_count = Patient.objects.count()

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
        actual=calc_kpis.calculate_kpi_42_thyroid_disease_screening(),
    )


@pytest.mark.django_db
def test_kpi_calculation_43(AUDIT_START_DATE, AUDIT_END_DATE):
    """Tests that KPI43 is calculated correctly.

    Numerator: Number of eligible patients with an entry for Carbohydrate
    Counting Education (item 42) within 7 days before or 14 days after the
    Date of Diabetes Diagnosis (item 7)

    Denominator: Number of patients with Type 1 diabetes who were diagnosed
    at least 14 days before the end of the audit period (<= | >=)

    (NOTE: Measure 7 AND diabetes diagnosis date < (AUDIT_END_DATE - 14 days))
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create  Patients and Visits that should be eligible (KPI7)
    DIAB_DIAGNOSIS_15D_BEFORE_END = AUDIT_END_DATE - relativedelta(days=15)
    eligible_criteria = {
        "visit__visit_date": DIAB_DIAGNOSIS_15D_BEFORE_END - relativedelta(months=2),
        "date_of_birth": AUDIT_START_DATE - relativedelta(years=10),
        "diabetes_type": DIABETES_TYPES[0][0],
        # any other observation date
        "visit__height_weight_observation_date": DIAB_DIAGNOSIS_15D_BEFORE_END,
        # KPI 42 specific
        "diagnosis_date": DIAB_DIAGNOSIS_15D_BEFORE_END,
    }

    # Passing patients
    # carbohydrate_counting_level_three_education_date 7 days before T1DM diagnosis
    passing_patient_1 = PatientFactory(
        postcode="passing_patient_1",
        # KPI7 eligible
        **eligible_criteria,
        # KPI 42 specific
        visit__carbohydrate_counting_level_three_education_date=DIAB_DIAGNOSIS_15D_BEFORE_END
        - relativedelta(days=7),
    )
    # only 2nd visit has carbohydrate_counting_level_three_education_date
    passing_patient_2 = PatientFactory(
        postcode="passing_patient_2",
        # KPI7 eligible
        **eligible_criteria,
        # KPI 42 specific
        visit__carbohydrate_counting_level_three_education_date=None,
    )
    # create 2nd visit with carbohydrate_counting_level_three_education_date
    # 14 days after T1DM diagnosis
    VisitFactory(
        patient=passing_patient_2,
        carbohydrate_counting_level_three_education_date=DIAB_DIAGNOSIS_15D_BEFORE_END
        + relativedelta(days=14),
    )

    # Failing patients
    # new T1DM diagnosis but no carbohydrate_counting_level_three_education_date
    failing_patient_1_no_carb_count_date = PatientFactory(
        postcode="failing_patient_1_no_carb_count_date",
        # KPI7 eligible
        **eligible_criteria,
        # KPI 42 specific
        visit__carbohydrate_counting_level_three_education_date=None,
    )
    # new T1DM diagnosis lt 15 days audit end but
    # carbohydrate_counting_level_three_education_date 15 days after
    eligible_criteria_with_diag_15D_before_end = eligible_criteria.copy()
    # overriding diagnosis date so
    # carbohydrate_counting_level_three_education_date will be within audit end
    eligible_criteria_with_diag_15D_before_end["diagnosis_date"] = (
        AUDIT_END_DATE - relativedelta(days=15)
    )
    failing_patient_2_carb_count_date_15D_after_diag = PatientFactory(
        postcode="failing_patient_2_carb_count_date_15D_after_diag",
        # KPI7 eligible
        **eligible_criteria_with_diag_15D_before_end,
        # KPI 42 specific
        visit__carbohydrate_counting_level_three_education_date=eligible_criteria_with_diag_15D_before_end[
            "diagnosis_date"
        ]
        + relativedelta(days=15),
    )

    # Create Patients and Visits that should be ineligble (KPI7)
    ineligible_patient_not_t1dm = PatientFactory(
        postcode="ineligible_patient_not_t1dm",
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # not T1DM
        diabetes_type=DIABETES_TYPES[1][0],
        # Date of diagnosis inside the audit period
        diagnosis_date=AUDIT_START_DATE + relativedelta(days=2),
    )
    ineligible_patient_diag_outside_audit_period = PatientFactory(
        postcode="ineligible_patient_diag_outside_audit_period",
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # T1DM
        diabetes_type=DIABETES_TYPES[0][0],
        # Date of diagnosis outside the audit period
        diagnosis_date=AUDIT_START_DATE - relativedelta(days=2),
    )
    ineligible_patient_diag_14D_before_end = PatientFactory(
        postcode="ineligible_patient_diag_14D_before_end",
        visit__visit_date=AUDIT_END_DATE - relativedelta(days=2),
        # T1DM
        diabetes_type=DIABETES_TYPES[0][0],
        # Date of diag 2 days before end of audit period
        diagnosis_date=AUDIT_END_DATE - relativedelta(days=14),
        visit__carbohydrate_counting_level_three_education_date=AUDIT_END_DATE
        - relativedelta(days=14),
    )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(calculation_date=AUDIT_START_DATE)
    # Need to be mocked as not using public `calculate_kpis_for_*` methods
    calc_kpis.patients = Patient.objects.all()
    calc_kpis.total_patients_count = Patient.objects.count()

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
        actual=calc_kpis.calculate_kpi_43_carbohydrate_counting_education(),
    )

"""Tests for the 7 Key Processes KPIs."""

import logging
from typing import List

import pytest
from dateutil.relativedelta import relativedelta

from project.constants.diabetes_types import DIABETES_TYPES
from project.constants.smoking_status import SMOKING_STATUS
from project.npda.general_functions.kpis import CalculateKPIS, KPIResult
from project.npda.models import Patient
from project.npda.tests.factories.patient_factory import PatientFactory
from project.npda.tests.factories.visit_factory import VisitFactory
from project.npda.tests.kpi_calculations.test_kpi_calculations import \
    assert_kpi_result_equal

# Logging
logger = logging.getLogger(__name__)

@pytest.mark.django_db
def test_kpi_calculation_41(AUDIT_START_DATE, AUDIT_END_DATE):
    """Tests that KPI41 is calculated correctly.

    Numerator: Number of eligible patients with an entry for Coeliac Disease Screening Date (item 36) within 90 days of Date of Diabetes Diagnosis (item 7)

    Denominator: Number of patients with Type 1 diabetes who were diagnosed with Coeliac at least 90 days before the end of the audit period.

     NOTE: denominator is essentially KPI7 (total new T1DM diagnoses) plus
        extra filter for coeliac diagnosis < (AUDIT_END_DATE - 90 DAYS)
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create  Patients and Visits that should be eligible (KPI7)
    DIAB_DIAGNOSIS_89D_BEFORE_END = AUDIT_END_DATE - relativedelta(days=89)
    eligible_criteria = {
        "visit__visit_date": DIAB_DIAGNOSIS_89D_BEFORE_END
        - relativedelta(months=2),
        "date_of_birth": AUDIT_START_DATE - relativedelta(year=10),
        "diabetes_type": DIABETES_TYPES[0][0],
        "diagnosis_date": DIAB_DIAGNOSIS_89D_BEFORE_END,
        # any other observation date
        'visit__height_weight_observation_date': DIAB_DIAGNOSIS_89D_BEFORE_END,
    }



    # Passing patients
    # coeliac screen < 90D before T1DM diagnosis
    passing_patient_1 = PatientFactory(
        postcode="passing_patient_1",
        # KPI7 eligible
        **eligible_criteria,
        # KPI 41 specific
        visit__coeliac_screen_date=DIAB_DIAGNOSIS_89D_BEFORE_END
        - relativedelta(days=89),
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
        visit_date=DIAB_DIAGNOSIS_89D_BEFORE_END - relativedelta(days=10),
        coeliac_screen_date=DIAB_DIAGNOSIS_89D_BEFORE_END
        + relativedelta(days=89),
    )


    # Failing patients
    # new T1DM diagnosis but no coeliac screen
    failing_patient_2 = PatientFactory(
        postcode="failing_patient_2",
        # KPI7 eligible
        **eligible_criteria,
        # KPI 41 specific
        visit__coeliac_screen_date=None,
    )
    # new T1DM diagnosis but coeliac screen 91 days after
    # overriding diagnosis date so coeliac screen will be within audit end
    DIAB_DIAG_DATE = AUDIT_END_DATE - relativedelta(days=91)
    eligible_criteria_without_diag_date = {
        k: v for k, v in eligible_criteria.items() if k != "diagnosis_date"
    }
    failing_patient_2 = PatientFactory(
        postcode="failing_patient_2",
        # KPI7 eligible
        **eligible_criteria_without_diag_date,
        # KPI 41 specific
        diagnosis_date=DIAB_DIAG_DATE,
        visit__coeliac_screen_date=DIAB_DIAG_DATE + relativedelta(days=91),
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
    ineligible_patient_diag_lt_90D_before_end = PatientFactory(
        postcode="ineligible_patient_diag_lt_90D_before_end",
        visit__visit_date=AUDIT_END_DATE - relativedelta(days=2),
        # T1DM
        diabetes_type=DIABETES_TYPES[0][0],
        # Date of diag 2 days before end of audit period
        diagnosis_date=AUDIT_END_DATE - relativedelta(days=2),
        visit__coeliac_screen_date=AUDIT_END_DATE - relativedelta(days=2),
    )
    # additionally patient that is eligible for kpi7  but diabetes diagnosis
    # 90 days before end of audit period
    ineligible_pt_diab_diag_eq_90D_before_end = PatientFactory(
        postcode="ineligible_pt_diab_diag_eq_90D_before_end",
        # KPI7 eligible
        visit__visit_date=AUDIT_END_DATE - relativedelta(days=2),
        # T1DM
        diabetes_type=DIABETES_TYPES[0][0],
        # KPI 41 specific
        diagnosis_date = AUDIT_END_DATE - relativedelta(days=90),
        visit__coeliac_screen_date=AUDIT_END_DATE - relativedelta(days=90),
    )

    calc_kpis = CalculateKPIS(
        pz_code="PZ130",
        calculation_date=AUDIT_START_DATE,
    )

    EXPECTED_TOTAL_ELIGIBLE = 4
    EXPECTED_TOTAL_INELIGIBLE = 4
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


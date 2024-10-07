"""Tests for the 7 Key Processes KPIs."""

from typing import List

import pytest
from dateutil.relativedelta import relativedelta

from project.constants.diabetes_types import DIABETES_TYPES
from project.constants.smoking_status import SMOKING_STATUS
from project.npda.kpi_class.kpis import CalculateKPIS, KPIResult
from project.npda.models import Patient
from project.npda.tests.factories.patient_factory import PatientFactory
from project.npda.tests.factories.visit_factory import VisitFactory
from project.npda.tests.kpi_calculations.test_kpi_calculations import (
    assert_kpi_result_equal,
)


@pytest.mark.django_db
def test_kpi_calculation_33(AUDIT_START_DATE):
    """Tests that KPI33 is calculated correctly.

    Calculates KPI 32: HbA1c 4+ (%)

    Numerator: Number of eligible patients with at least four entries for HbA1c value (item 17) with an observation date (item 19) within the audit period

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
    passing_patient_1 = PatientFactory(
        postcode="passing_patient_1",
        # KPI5 eligible
        **eligible_criteria,
    )
    passing_visits_1 = VisitFactory.create_batch(
        size=4,
        patient=passing_patient_1,
        visit_date=AUDIT_START_DATE,
        hba1c=46,
        hba1c_date=AUDIT_START_DATE + relativedelta(days=2),
    )
    passing_patient_2 = PatientFactory(
        postcode="passing_patient_2",
        # KPI5 eligible
        **eligible_criteria,
    )
    passing_visits_2 = VisitFactory.create_batch(
        size=5,
        patient=passing_patient_2,
        visit_date=AUDIT_START_DATE,
        hba1c=43,
        hba1c_date=AUDIT_START_DATE + relativedelta(days=6),
    )
    # 1 of the Visits has no HbA1c
    passing_patient_3 = PatientFactory(
        postcode="passing_patient_3",
        # KPI5 eligible
        **eligible_criteria,
        visit__hba1c=None,
        visit__hba1c_date=None,
    )
    for i in range(4):
        VisitFactory(
            patient=passing_patient_3,
            visit_date=AUDIT_START_DATE,
            hba1c=46,
            hba1c_date=AUDIT_START_DATE + relativedelta(days=i),
        )

    # Failing patients
    # < 4 hba1c
    failing_patient_1 = PatientFactory(
        postcode="failing_patient_1",
        # KPI5 eligible
        **eligible_criteria,
    )
    failing_visits_1 = VisitFactory.create_batch(
        size=3,
        patient=failing_patient_1,
        visit_date=AUDIT_START_DATE,
        hba1c=46,
        hba1c_date=AUDIT_START_DATE + relativedelta(days=2),
    )
    # No hba1c
    failing_patient_2 = PatientFactory(
        postcode="failing_patient_2",
        # KPI5 eligible
        **eligible_criteria,
    )
    failing_visits_2 = VisitFactory.create_batch(
        size=4,
        patient=failing_patient_2,
        visit_date=AUDIT_START_DATE,
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
        transfer__date_leaving_service=AUDIT_START_DATE + relativedelta(days=2),
    )
    ineligible_patient_death_within_audit_period = PatientFactory(
        postcode="ineligible_patient_death_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of death within the audit period"
        death_date=AUDIT_START_DATE + relativedelta(days=2),
    )

    calc_kpis = CalculateKPIS(
        pz_codes=["PZ130"],
        calculation_date=AUDIT_START_DATE,
    )

    EXPECTED_TOTAL_ELIGIBLE = 5
    EXPECTED_TOTAL_INELIGIBLE = 5
    EXPECTED_TOTAL_PASSED = 3
    EXPECTED_TOTAL_FAILED = 2

    EXPECTED_KPIRESULT = KPIResult(
        total_eligible=EXPECTED_TOTAL_ELIGIBLE,
        total_passed=EXPECTED_TOTAL_PASSED,
        total_ineligible=EXPECTED_TOTAL_INELIGIBLE,
        total_failed=EXPECTED_TOTAL_FAILED,
    )

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT,
        actual=calc_kpis.calculate_kpi_33_hba1c_4plus(),
    )


@pytest.mark.django_db
def test_kpi_calculation_34(AUDIT_START_DATE):
    """Tests that KPI34 is calculated correctly.

    Numerator: Number of eligible patients with an entry for Psychological Screening Date (item 38) within the audit period

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
    passing_patient_1 = PatientFactory(
        postcode="passing_patient_1",
        # KPI5 eligible
        **eligible_criteria,
        # KPI 34 specific
        visit__psychological_screening_assessment_date=AUDIT_START_DATE
        + relativedelta(days=2),
    )
    # second visit has a valid psychological screening date
    passing_patient_2 = PatientFactory(
        postcode="passing_patient_2",
        # KPI5 eligible
        **eligible_criteria,
        # KPI 34 specific
        visit__psychological_screening_assessment_date=None,
    )
    # create 2nd visit
    VisitFactory(
        patient=passing_patient_2,
        visit_date=AUDIT_START_DATE + relativedelta(days=5),
        psychological_screening_assessment_date=AUDIT_START_DATE
        + relativedelta(days=5),
    )

    # Failing patients
    # outside audit period
    failing_patient_1 = PatientFactory(
        postcode="failing_patient_1",
        # KPI5 eligible
        **eligible_criteria,
        # KPI 34 specific
        visit__psychological_screening_assessment_date=AUDIT_START_DATE
        - relativedelta(days=2),
    )
    # No psychological screening
    failing_patient_2 = PatientFactory(
        postcode="failing_patient_2",
        # KPI5 eligible
        **eligible_criteria,
        # KPI 34 specific
        visit__psychological_screening_assessment_date=None,
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
        transfer__date_leaving_service=AUDIT_START_DATE + relativedelta(days=2),
    )
    ineligible_patient_death_within_audit_period = PatientFactory(
        postcode="ineligible_patient_death_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of death within the audit period"
        death_date=AUDIT_START_DATE + relativedelta(days=2),
    )

    calc_kpis = CalculateKPIS(
        pz_codes=["PZ130"],
        calculation_date=AUDIT_START_DATE,
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
        actual=calc_kpis.calculate_kpi_34_psychological_assessment(),
    )


@pytest.mark.django_db
def test_kpi_calculation_35(AUDIT_START_DATE):
    """Tests that KPI35 is calculated correctly.

    Numerator: Number of eligible patients with at least one entry for Smoking Status (item 40) that is either 1 = Non-smoker or 2 = Curent smoker within the audit period (based on visit date)

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
    passing_patient_1 = PatientFactory(
        postcode="passing_patient_1",
        # KPI6 eligible
        **eligible_criteria,
        # KPI 35 specific
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=5),
        visit__smoking_status=SMOKING_STATUS[0][0],
    )
    # second visit has a valid smoking status
    passing_patient_2 = PatientFactory(
        postcode="passing_patient_2",
        # KPI6 eligible
        **eligible_criteria,
        # KPI 35 specific
        visit__visit_date=None,
        visit__smoking_status=None,
    )
    # create 2nd visit
    VisitFactory(
        patient=passing_patient_2,
        # KPI 6 specific = an observation within the audit period
        height_weight_observation_date=AUDIT_START_DATE + relativedelta(days=5),
        visit_date=AUDIT_START_DATE + relativedelta(days=5),
        smoking_status=SMOKING_STATUS[1][0],
    )

    # Failing patients
    # other smoking status
    failing_patient_1 = PatientFactory(
        postcode="failing_patient_1",
        # KPI5 eligible
        **eligible_criteria,
        # KPI 35 specific
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=5),
        visit__smoking_status=SMOKING_STATUS[2][0],
    )
    # No smoke screening
    failing_patient_2 = PatientFactory(
        postcode="failing_patient_2",
        # KPI5 eligible
        **eligible_criteria,
        # KPI 35 specific
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=5),
        visit__smoking_status=None,
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
        transfer__date_leaving_service=AUDIT_START_DATE + relativedelta(days=2),
    )
    ineligible_patient_death_within_audit_period = PatientFactory(
        postcode="ineligible_patient_death_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of death within the audit period"
        death_date=AUDIT_START_DATE + relativedelta(days=2),
    )

    calc_kpis = CalculateKPIS(
        pz_codes=["PZ130"],
        calculation_date=AUDIT_START_DATE,
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
        actual=calc_kpis.calculate_kpi_35_smoking_status_screened(),
    )


@pytest.mark.django_db
def test_kpi_calculation_36(AUDIT_START_DATE):
    """Tests that KPI36 is calculated correctly.

    Numerator: Number of eligible patients with an entry for Date of Smoking Cessation Referral (item 41) within the audit period

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
        "visit__visit_date": AUDIT_START_DATE + relativedelta(days=5),
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
    passing_patient_1 = PatientFactory(
        postcode="passing_patient_1",
        # KPI5 eligible
        **eligible_criteria,
        # KPI 35 specific
        visit__smoking_cessation_referral_date=AUDIT_START_DATE + relativedelta(days=2),
    )
    # only second visit has a valid smoking cessation referral
    passing_patient_2 = PatientFactory(
        postcode="passing_patient_2",
        # KPI5 eligible
        **eligible_criteria,
        # KPI 35 specific
        visit__smoking_cessation_referral_date=None,
    )
    # create 2nd visit
    VisitFactory(
        patient=passing_patient_2,
        visit_date=AUDIT_START_DATE + relativedelta(days=5),
        smoking_cessation_referral_date=AUDIT_START_DATE + relativedelta(days=32),
    )

    # Failing patients
    # No smoke cessation referral
    failing_patient_2 = PatientFactory(
        postcode="failing_patient_2",
        # KPI5 eligible
        **eligible_criteria,
        # KPI 35 specific
        visit__smoking_cessation_referral_date=None,
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
        transfer__date_leaving_service=AUDIT_START_DATE + relativedelta(days=2),
    )
    ineligible_patient_death_within_audit_period = PatientFactory(
        postcode="ineligible_patient_death_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of death within the audit period"
        death_date=AUDIT_START_DATE + relativedelta(days=2),
    )

    calc_kpis = CalculateKPIS(
        pz_codes=["PZ130"],
        calculation_date=AUDIT_START_DATE,
    )

    EXPECTED_TOTAL_ELIGIBLE = 3
    EXPECTED_TOTAL_INELIGIBLE = 3
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
        actual=calc_kpis.calculate_kpi_36_referral_to_smoking_cessation_service(),
    )


@pytest.mark.django_db
def test_kpi_calculation_37(AUDIT_START_DATE):
    """Tests that KPI37 is calculated correctly.

    Numerator: Numer of eligible patients with at least one entry for Additional Dietitian Appointment Offered (item 43) that is 1 = Yes within the audit period (based on visit date)

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
    passing_patient_1 = PatientFactory(
        postcode="passing_patient_1",
        # KPI5 eligible
        **eligible_criteria,
        # KPI 37 specific
        visit__dietician_additional_appointment_offered=1,
    )
    # only second visit has a valid dietician appt offered
    passing_patient_2 = PatientFactory(
        postcode="passing_patient_2",
        # KPI5 eligible
        **eligible_criteria,
        # KPI 37 specific
        visit__dietician_additional_appointment_offered=None,
    )
    # create 2nd visit
    VisitFactory(
        patient=passing_patient_2,
        visit_date=AUDIT_START_DATE + relativedelta(days=5),
        dietician_additional_appointment_offered=1,
    )

    # Failing patients
    # No dietician appt offered
    failing_patient_2 = PatientFactory(
        postcode="failing_patient_2",
        # KPI5 eligible
        **eligible_criteria,
        # KPI 37 specific
        visit__dietician_additional_appointment_offered=None,
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
        transfer__date_leaving_service=AUDIT_START_DATE + relativedelta(days=2),
    )
    ineligible_patient_death_within_audit_period = PatientFactory(
        postcode="ineligible_patient_death_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of death within the audit period"
        death_date=AUDIT_START_DATE + relativedelta(days=2),
    )

    calc_kpis = CalculateKPIS(
        pz_codes=["PZ130"],
        calculation_date=AUDIT_START_DATE,
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
        actual=calc_kpis.calculate_kpi_37_additional_dietetic_appointment_offered(),
    )


@pytest.mark.django_db
def test_kpi_calculation_38(AUDIT_START_DATE):
    """Tests that KPI38 is calculated correctly.

    Numerator: Number of eligible patients with at least one entry for Additional Dietitian Appointment Date (item 44) within the audit year

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
    passing_patient_1 = PatientFactory(
        postcode="passing_patient_1",
        # KPI5 eligible
        **eligible_criteria,
        # KPI 38 specific
        visit__dietician_additional_appointment_date=AUDIT_START_DATE
        + relativedelta(days=30),
    )
    # only second visit has a valid additional dietician appt
    passing_patient_2 = PatientFactory(
        postcode="passing_patient_2",
        # KPI5 eligible
        **eligible_criteria,
        # KPI 38 specific
        visit__dietician_additional_appointment_date=None,
    )
    # create 2nd visit
    VisitFactory(
        patient=passing_patient_2,
        visit_date=AUDIT_START_DATE + relativedelta(days=5),
        dietician_additional_appointment_date=AUDIT_START_DATE + relativedelta(days=4),
    )

    # Failing patients
    # No additional dietician appt
    failing_patient_2 = PatientFactory(
        postcode="failing_patient_2",
        # KPI5 eligible
        **eligible_criteria,
        # KPI 38 specific
        visit__dietician_additional_appointment_date=None,
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
        transfer__date_leaving_service=AUDIT_START_DATE + relativedelta(days=2),
    )
    ineligible_patient_death_within_audit_period = PatientFactory(
        postcode="ineligible_patient_death_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of death within the audit period"
        death_date=AUDIT_START_DATE + relativedelta(days=2),
    )

    calc_kpis = CalculateKPIS(
        pz_codes=["PZ130"],
        calculation_date=AUDIT_START_DATE,
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
        actual=calc_kpis.calculate_kpi_38_patients_attending_additional_dietetic_appointment(),
    )


@pytest.mark.django_db
def test_kpi_calculation_39(AUDIT_START_DATE):
    """Tests that KPI39 is calculated correctly.

    Numerator: Number of eligible patients with at least one entry for Influzena Immunisation Recommended (item 24) within the audit period

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
    passing_patient_1 = PatientFactory(
        postcode="passing_patient_1",
        # KPI5 eligible
        **eligible_criteria,
        # KPI 39 specific
        visit__flu_immunisation_recommended_date=AUDIT_START_DATE
        + relativedelta(days=30),
    )
    # only second visit has a valid influenza immunisation recommended
    passing_patient_2 = PatientFactory(
        postcode="passing_patient_2",
        # KPI5 eligible
        **eligible_criteria,
        # KPI 39 specific
        visit__flu_immunisation_recommended_date=None,
    )
    # create 2nd visit
    VisitFactory(
        patient=passing_patient_2,
        visit_date=AUDIT_START_DATE + relativedelta(days=5),
        flu_immunisation_recommended_date=AUDIT_START_DATE + relativedelta(days=4),
    )

    # Failing patients
    # No influenza immunisation recommended
    failing_patient_2 = PatientFactory(
        postcode="failing_patient_2",
        # KPI5 eligible
        **eligible_criteria,
        # KPI 39 specific
        visit__flu_immunisation_recommended_date=None,
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
        transfer__date_leaving_service=AUDIT_START_DATE + relativedelta(days=2),
    )
    ineligible_patient_death_within_audit_period = PatientFactory(
        postcode="ineligible_patient_death_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of death within the audit period"
        death_date=AUDIT_START_DATE + relativedelta(days=2),
    )

    calc_kpis = CalculateKPIS(
        pz_codes=["PZ130"],
        calculation_date=AUDIT_START_DATE,
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
        actual=calc_kpis.calculate_kpi_39_influenza_immunisation_recommended(),
    )


@pytest.mark.django_db
def test_kpi_calculation_40(AUDIT_START_DATE):
    """Tests that KPI40 is calculated correctly.

    Numerator:Number of eligible patients with at least one entry for Sick
    Day Rules (item 47) within the audit period

    Denominator: Total number of eligible patients (measure 1)
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create  Patients and Visits that should be eligible (KPI1)
    eligible_criteria = {
        "visit__visit_date": AUDIT_START_DATE + relativedelta(days=2),
        "date_of_birth": AUDIT_START_DATE - relativedelta(days=365 * 10),
    }

    # Passing patients
    passing_patient_1 = PatientFactory(
        postcode="passing_patient_1",
        # KPI1 eligible
        **eligible_criteria,
        # KPI 40 specific
        visit__sick_day_rules_training_date=AUDIT_START_DATE + relativedelta(days=30),
    )
    # only second visit has a valid sick day rule
    passing_patient_2 = PatientFactory(
        postcode="passing_patient_2",
        # KPI1 eligible
        **eligible_criteria,
        # KPI 40 specific
        visit__sick_day_rules_training_date=None,
    )
    # create 2nd visit
    VisitFactory(
        patient=passing_patient_2,
        visit_date=AUDIT_START_DATE + relativedelta(days=5),
        sick_day_rules_training_date=AUDIT_START_DATE + relativedelta(days=4),
    )

    # Failing patients
    # No sick day rule
    failing_patient_2 = PatientFactory(
        postcode="failing_patient_2",
        # KPI5 eligible
        **eligible_criteria,
        # KPI 40 specific
        visit__sick_day_rules_training_date=None,
    )

    # Create Patients and Visits that should be ineligble (KPI1)
    # Visit date before audit period
    ineligible_patients_visit_date: List[Patient] = PatientFactory(
        visit__visit_date=AUDIT_START_DATE - relativedelta(days=10),
    )
    # Above age 25 at start of audit period
    ineligible_patients_too_old: List[Patient] = PatientFactory(
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 26),
    )

    calc_kpis = CalculateKPIS(
        pz_codes=["PZ130"],
        calculation_date=AUDIT_START_DATE,
    )

    EXPECTED_TOTAL_ELIGIBLE = 3
    EXPECTED_TOTAL_INELIGIBLE = 2
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
        actual=calc_kpis.calculate_kpi_40_sick_day_rules_advice(),
    )

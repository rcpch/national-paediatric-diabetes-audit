"""Tests for the CalculateKPIS class."""

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
        size=N_PATIENTS_ELIGIBLE,
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=1),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
    )

    # Create Patients and Visits that should FAIL KPI1
    # Visit date before audit period
    ineligible_patients_visit_date: List[Patient] = (
        PatientFactory.create_batch(
            size=N_PATIENTS_INELIGIBLE,
            visit__visit_date=AUDIT_START_DATE - relativedelta(days=10),
        )
    )
    # Above age 25 at start of audit period
    ineligible_patients_too_old: List[Patient] = PatientFactory.create_batch(
        size=N_PATIENTS_INELIGIBLE,
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 26),
    )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(
        pz_code="PZ130", calculation_date=AUDIT_START_DATE
    )

    EXPECTED_KPIRESULT = KPIResult(
        total_eligible=N_PATIENTS_ELIGIBLE,
        total_passed=N_PATIENTS_PASS,
        # We have 2 sets of ineligible patients
        total_ineligible=N_PATIENTS_INELIGIBLE * 2,
        total_failed=N_PATIENTS_FAIL * 2,
    )

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT,
        actual=calc_kpis.calculate_kpi_1_total_eligible(),
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
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        diagnosis_date=AUDIT_START_DATE + relativedelta(days=10),
    )

    # Create Patients and Visits that should FAIL KPI2
    # Visit date before audit period
    ineligible_patients_visit_date: List[Patient] = (
        PatientFactory.create_batch(
            size=N_PATIENTS_INELIGIBLE,
            visit__visit_date=AUDIT_START_DATE - relativedelta(days=10),
        )
    )
    # Diagnosis date before audit period
    ineligible_patients_diagnosis_date: List[Patient] = (
        PatientFactory.create_batch(
            size=N_PATIENTS_INELIGIBLE,
            diagnosis_date=AUDIT_START_DATE - relativedelta(days=10),
        )
    )
    # Above age 25 at start of audit period
    ineligible_patients_too_old: List[Patient] = PatientFactory.create_batch(
        size=N_PATIENTS_INELIGIBLE,
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 26),
    )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(
        pz_code="PZ130", calculation_date=AUDIT_START_DATE
    )

    EXPECTED_KPIRESULT = KPIResult(
        total_eligible=N_PATIENTS_ELIGIBLE,
        total_passed=N_PATIENTS_PASS,
        # We have 3 sets of ineligible patients
        total_ineligible=N_PATIENTS_INELIGIBLE * 3,
        total_failed=N_PATIENTS_FAIL * 3,
    )

    # First set kpi1 result of total eligible
    calc_kpis.calculate_kpi_1_total_eligible()

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT,
        actual=calc_kpis.calculate_kpi_2_total_new_diagnoses(),
    )


@pytest.mark.django_db
def test_kpi_calculation_3(AUDIT_START_DATE):
    """Tests that KPI3 is calculated correctly.

    Essentialy KPI1 but also check Diagnosis of Type 1 diabetes
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    N_PATIENTS_ELIGIBLE = N_PATIENTS_PASS = 3
    N_PATIENTS_INELIGIBLE = N_PATIENTS_FAIL = 4

    # Create  Patients and Visits that should PASS KPI3
    eligible_patients: List[Patient] = PatientFactory.create_batch(
        size=N_PATIENTS_ELIGIBLE,
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # T1DM
        diabetes_type=DIABETES_TYPES[0][0],
    )

    # Create Patients and Visits that should FAIL KPI3
    # Visit date before audit period
    ineligible_patients_visit_date: List[Patient] = (
        PatientFactory.create_batch(
            size=N_PATIENTS_INELIGIBLE,
            visit__visit_date=AUDIT_START_DATE - relativedelta(days=10),
        )
    )
    # Above age 25 at start of audit period
    ineligible_patients_too_old: List[Patient] = PatientFactory.create_batch(
        size=N_PATIENTS_INELIGIBLE,
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 26),
    )
    # Diab type is not T1DM before audit period
    ineligible_patients_diab_type: List[Patient] = PatientFactory.create_batch(
        size=N_PATIENTS_INELIGIBLE, diabetes_type=DIABETES_TYPES[-1][0]
    )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(
        pz_code="PZ130", calculation_date=AUDIT_START_DATE
    )

    EXPECTED_KPIRESULT = KPIResult(
        total_eligible=N_PATIENTS_ELIGIBLE,
        total_passed=N_PATIENTS_PASS,
        # We have 3 sets of ineligible patients
        total_ineligible=N_PATIENTS_INELIGIBLE * 3,
        total_failed=N_PATIENTS_FAIL * 3,
    )

    # First set self.total_kpi_1_eligible_pts_base_query_set result
    # of total eligible
    calc_kpis.calculate_kpi_1_total_eligible()

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT,
        actual=calc_kpis.calculate_kpi_3_total_t1dm(),
    )


@pytest.mark.django_db
def test_kpi_calculation_4(AUDIT_START_DATE):
    """Tests that KPI4 is calculated correctly.

    Essentialy KPI1 but also check
        Age 12 and above years at the start of the audit period
        & Diagnosis of Type 1 diabetes
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    N_PATIENTS_ELIGIBLE = N_PATIENTS_PASS = 3
    N_PATIENTS_INELIGIBLE = N_PATIENTS_FAIL = 4

    # Create  Patients and Visits that should PASS KPI4
    eligible_patients: List[Patient] = PatientFactory.create_batch(
        size=N_PATIENTS_ELIGIBLE,
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        # T1DM
        diabetes_type=DIABETES_TYPES[0][0],
        # 12 years old exactly at start of audit period
        date_of_birth=AUDIT_START_DATE - relativedelta(years=12),
    )

    # Create Patients and Visits that should FAIL KPI4
    # Visit date before audit period
    ineligible_patients_visit_date: List[Patient] = (
        PatientFactory.create_batch(
            size=N_PATIENTS_INELIGIBLE,
            visit__visit_date=AUDIT_START_DATE - relativedelta(days=10),
        )
    )
    # Above age 25 at start of audit period
    ineligible_patients_too_old: List[Patient] = PatientFactory.create_batch(
        size=N_PATIENTS_INELIGIBLE,
        date_of_birth=AUDIT_START_DATE - relativedelta(years=26),
    )
    # Diab type is not T1DM before audit period
    ineligible_patients_diab_type: List[Patient] = PatientFactory.create_batch(
        size=N_PATIENTS_INELIGIBLE, diabetes_type=DIABETES_TYPES[-1][0]
    )
    # age 1day less than 12yo at start of audit period
    ineligible_patients_lt_12yo: List[Patient] = PatientFactory.create_batch(
        size=N_PATIENTS_INELIGIBLE,
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 11),
    )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(
        pz_code="PZ130", calculation_date=AUDIT_START_DATE
    )

    EXPECTED_KPIRESULT = KPIResult(
        total_eligible=N_PATIENTS_ELIGIBLE,
        total_passed=N_PATIENTS_PASS,
        # We have 4 sets of ineligible patients
        total_ineligible=N_PATIENTS_INELIGIBLE * 4,
        total_failed=N_PATIENTS_FAIL * 4,
    )

    # First set self.total_kpi_1_eligible_pts_base_query_set result
    # of total eligible
    calc_kpis.calculate_kpi_1_total_eligible()

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT,
        actual=calc_kpis.calculate_kpi_4_total_t1dm_gte_12yo(),
    )


@pytest.mark.django_db
def test_kpi_calculation_5(AUDIT_START_DATE):
    """Tests that KPI5 is calculated correctly.

    Essentialy KPI1 but also check

        Excluding
        * Date of diagnosis within the audit period
        * Date of leaving service within the audit period
        * Date of death within the audit period"
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create  Patients and Visits that should be included
    eligible_patient_diag_NOT_within_audit_period = PatientFactory(
        postcode="eligible_patient_diag_NOT_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of diagnosis within the audit period
        diagnosis_date=AUDIT_START_DATE - relativedelta(days=2),
    )

    eligible_patient_date_leaving_NOT_within_audit_period = PatientFactory(
        postcode="eligible_patient_date_leaving_NOT_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of leaving service within the audit period
        # transfer date only not None if they have left
        transfer__date_leaving_service=None,
    )

    eligible_patient_death_NOT_within_audit_period = PatientFactory(
        postcode="eligible_patient_death_NOT_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of death within the audit period"
        death_date=None,
    )

    # Create Patients and Visits that should FAIL KPI3
    # Visit date before audit period
    ineligible_patient_visit_date: List[Patient] = PatientFactory(
        postcode="ineligible_patient_visit_date",
        visit__visit_date=AUDIT_START_DATE - relativedelta(days=10),
    )
    # Above age 25 at start of audit period
    ineligible_patient_too_old: List[Patient] = PatientFactory(
        postcode="ineligible_patient_too_old",
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 26),
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

    EXPECTED_KPIRESULT = KPIResult(
        total_eligible=EXPECTED_TOTAL_ELIGIBLE,
        total_passed=EXPECTED_TOTAL_ELIGIBLE,
        total_ineligible=EXPECTED_TOTAL_INELIGIBLE,
        total_failed=EXPECTED_TOTAL_INELIGIBLE,
    )

    # First set self.total_kpi_1_eligible_pts_base_query_set result
    # of total eligible
    calc_kpis.calculate_kpi_1_total_eligible()

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT,
        actual=calc_kpis.calculate_kpi_5_total_t1dm_complete_year(),
    )


@pytest.mark.django_db
def test_kpi_calculation_6(AUDIT_START_DATE):
    """Tests that KPI6 is calculated correctly.

    Inclusions:
        * Age 12 and above at the start of the audit period
        * Diagnosis of Type 1 diabetes
        * an observation within the audit period

    Essentialy KPI5 exclusions:
        Excluding
        * Date of diagnosis within the audit period
        * Date of leaving service within the audit period
        * Date of death within the audit period"
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create  Patients and Visits that should PASS KPI3
    observation_field_names = [
        "height_weight_observation_date",
        "hba1c_date",
        "blood_pressure_observation_date",
        "albumin_creatinine_ratio_date",
        "total_cholesterol_date",
        "thyroid_function_date",
        "coeliac_screen_date",
        "psychological_screening_assessment_date",
    ]
    # Loop through each observation field name and create a patient with an
    # observation date within the audit period for that field
    for field_name in observation_field_names:
        eligible_patient_pt_obs = PatientFactory(
            # string field without validation, just using for debugging
            # postcode=f"eligible_patient_{field_name}",
            # KPI1 eligible
            # Age 12 and above at the start of the audit period
            date_of_birth=AUDIT_START_DATE - relativedelta(years=12),
            # Diagnosis of Type 1 diabetes
            diabetes_type=DIABETES_TYPES[0][0],
            # an observation within the audit period
            **{
                f"visit__{field_name}": AUDIT_START_DATE
                + relativedelta(days=2)
            },
        )

    # Create Patients and Visits that should FAIL KPI3
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

    EXPECTED_TOTAL_ELIGIBLE = len(observation_field_names)
    EXPECTED_TOTAL_INELIGIBLE = 3

    EXPECTED_KPIRESULT = KPIResult(
        total_eligible=EXPECTED_TOTAL_ELIGIBLE,
        total_passed=EXPECTED_TOTAL_ELIGIBLE,
        total_ineligible=EXPECTED_TOTAL_INELIGIBLE,
        total_failed=EXPECTED_TOTAL_INELIGIBLE,
    )

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT,
        actual=calc_kpis.calculate_kpi_6_total_t1dm_complete_year_gte_12yo(),
    )


@pytest.mark.django_db
def test_kpi_calculation_7(AUDIT_START_DATE):
    """Tests that KPI7 is calculated correctly.

    Total number of patients with:
        * a valid NHS number
        * an observation within the audit period
        * Age 0-24 years at the start of the audit period
        * Diagnosis of Type 1 diabetes
        * Date of diagnosis within the audit period
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    observation_field_names = [
        "height_weight_observation_date",
        "hba1c_date",
        "blood_pressure_observation_date",
        "albumin_creatinine_ratio_date",
        "total_cholesterol_date",
        "thyroid_function_date",
        "coeliac_screen_date",
        "psychological_screening_assessment_date",
    ]
    # Loop through each observation field name and create a patient with an
    # observation date within the audit period for that field
    for field_name in observation_field_names:
        eligible_patient_pt_obs = PatientFactory(
            # string field without validation, just using for debugging
            postcode=f"eligible_patient_{field_name}",
            # KPI1 eligible
            # Age 12 and above at the start of the audit period
            date_of_birth=AUDIT_START_DATE - relativedelta(years=12),
            # Diagnosis of Type 1 diabetes
            diabetes_type=DIABETES_TYPES[0][0],
            # Diagnosis date within audit date range
            diagnosis_date=AUDIT_START_DATE + relativedelta(days=2),
            # an observation within the audit period
            **{
                f"visit__{field_name}": AUDIT_START_DATE
                + relativedelta(days=2)
            },
        )

    # Create Patients and Visits that should BE EXCLUDED
    ineligible_patient_not_t1dm = PatientFactory(
        postcode="ineligible_patient_not_t1dm",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # T1DM
        diabetes_type=DIABETES_TYPES[1][0],
        # Date of diagnosis inside the audit period
        diagnosis_date=AUDIT_START_DATE + relativedelta(days=2),
    )
    ineligible_patient_diag_outside_audit_period = PatientFactory(
        postcode="ineligible_patient_diag_outside_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # T1DM
        diabetes_type=DIABETES_TYPES[0][0],
        # Date of diagnosis outside the audit period
        diagnosis_date=AUDIT_START_DATE - relativedelta(days=2),
    )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(
        pz_code="PZ130", calculation_date=AUDIT_START_DATE
    )
    # First set self.total_kpi_1_eligible_pts_base_query_set result
    # of total eligible
    calc_kpis.calculate_kpi_1_total_eligible()

    EXPECTED_TOTAL_ELIGIBLE = len(observation_field_names)
    EXPECTED_TOTAL_INELIGIBLE = 2

    EXPECTED_KPIRESULT = KPIResult(
        total_eligible=EXPECTED_TOTAL_ELIGIBLE,
        total_passed=EXPECTED_TOTAL_ELIGIBLE,
        total_ineligible=EXPECTED_TOTAL_INELIGIBLE,
        total_failed=EXPECTED_TOTAL_INELIGIBLE,
    )

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT,
        actual=calc_kpis.calculate_kpi_7_total_new_diagnoses_t1dm(),
    )


@pytest.mark.django_db
def test_kpi_calculation_8(AUDIT_START_DATE):
    """Tests that KPI8 is calculated correctly.

    Essentialy KPI1 but also check
        * Date of death within the audit period"
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create  Patients and Visits that should be included
    eligible_patient_death_within_audit_period = PatientFactory(
        postcode="eligible_patient_diag_NOT_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # death_date within the audit period
        death_date=AUDIT_START_DATE + relativedelta(days=2),
    )

    # Create Patients and Visits that should be excluded
    # Visit date before audit period
    ineligible_patient_visit_date: List[Patient] = PatientFactory(
        postcode="ineligible_patient_visit_date",
        visit__visit_date=AUDIT_START_DATE - relativedelta(days=10),
    )
    # Above age 25 at start of audit period
    ineligible_patient_too_old: List[Patient] = PatientFactory(
        postcode="ineligible_patient_too_old",
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 26),
    )

    # KPI8 specific
    ineligible_patient_death_outside_audit_period = PatientFactory(
        postcode="ineligible_patient_death_outside_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of death outside the audit period"
        death_date=AUDIT_START_DATE - relativedelta(days=2),
    )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(
        pz_code="PZ130", calculation_date=AUDIT_START_DATE
    )

    EXPECTED_TOTAL_ELIGIBLE = 1
    EXPECTED_TOTAL_INELIGIBLE = 3

    EXPECTED_KPIRESULT = KPIResult(
        total_eligible=EXPECTED_TOTAL_ELIGIBLE,
        total_passed=EXPECTED_TOTAL_ELIGIBLE,
        total_ineligible=EXPECTED_TOTAL_INELIGIBLE,
        total_failed=EXPECTED_TOTAL_INELIGIBLE,
    )

    # First set self.total_kpi_1_eligible_pts_base_query_set result
    # of total eligible
    calc_kpis.calculate_kpi_1_total_eligible()

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT,
        actual=calc_kpis.calculate_kpi_8_total_deaths(),
    )


@pytest.mark.django_db
def test_kpi_calculation_9(AUDIT_START_DATE):
    """Tests that KPI9 is calculated correctly.

    Essentialy KPI1 but also check
        * Date of death within the audit period"
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create  Patients and Visits that should be included
    eligible_patient_leaving_date_within_audit_period = PatientFactory(
        postcode="eligible_patient_diag_NOT_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # leaving_date within the audit period
        transfer__date_leaving_service=AUDIT_START_DATE
        + relativedelta(days=2),
    )

    # Create Patients and Visits that should be excluded
    # Visit date before audit period
    ineligible_patient_visit_date: List[Patient] = PatientFactory(
        postcode="ineligible_patient_visit_date",
        visit__visit_date=AUDIT_START_DATE - relativedelta(days=10),
    )
    # Above age 25 at start of audit period
    ineligible_patient_too_old: List[Patient] = PatientFactory(
        postcode="ineligible_patient_too_old",
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 26),
    )

    # KPI9 specific
    ineligible_patient_no_leaving_date = PatientFactory(
        postcode="ineligible_patient_no_leaving_date",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # has not left
        transfer__date_leaving_service=None,
    )
    ineligible_patient_leaving_date_outside_audit_period = PatientFactory(
        postcode="ineligible_patient_leaving_date_outside_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of leaving_date outside the audit period"
        transfer__date_leaving_service=AUDIT_START_DATE
        - relativedelta(days=2),
    )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(
        pz_code="PZ130", calculation_date=AUDIT_START_DATE
    )

    EXPECTED_TOTAL_ELIGIBLE = 1
    EXPECTED_TOTAL_INELIGIBLE = 4

    EXPECTED_KPIRESULT = KPIResult(
        total_eligible=EXPECTED_TOTAL_ELIGIBLE,
        total_passed=EXPECTED_TOTAL_ELIGIBLE,
        total_ineligible=EXPECTED_TOTAL_INELIGIBLE,
        total_failed=EXPECTED_TOTAL_INELIGIBLE,
    )

    # First set self.total_kpi_1_eligible_pts_base_query_set result
    # of total eligible
    calc_kpis.calculate_kpi_1_total_eligible()

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT,
        actual=calc_kpis.calculate_kpi_9_total_service_transitions(),
    )


@pytest.mark.django_db
def test_kpi_calculation_10(AUDIT_START_DATE):
    """Tests that KPI10 is calculated correctly.

    Essentialy KPI1 but also check
        * most recent observation for item 37 (based on visit date) is 1 = Yes
        // NOTE: item37 is _Has the patient been recommended a Gluten-free diet?_
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create  Patients and Visits that should be included
    eligible_patient_most_recent_gluten_free_diet_is_1 = PatientFactory(
        postcode="eligible_patient_diag_NOT_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # most recent observation for item 37 (based on visit date) is 1 = Yes
        visit__gluten_free_diet=1,
    )

    # Create Patients and Visits that should be excluded
    # Visit date before audit period
    ineligible_patient_visit_date: List[Patient] = PatientFactory(
        postcode="ineligible_patient_visit_date",
        visit__visit_date=AUDIT_START_DATE - relativedelta(days=10),
    )
    # Above age 25 at start of audit period
    ineligible_patient_too_old: List[Patient] = PatientFactory(
        postcode="ineligible_patient_too_old",
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 26),
    )

    # KPI10 specific
    ineligible_patient_most_recent_additional_dietitian_appt_offerred_is_not_1 = PatientFactory(
        postcode="ineligible_patient_most_recent_additional_dietitian_appt_offerred_is_not_1",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # most recent observation for item 37 (based on visit date) is not 1
        visit__gluten_free_diet=2,
    )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(
        pz_code="PZ130", calculation_date=AUDIT_START_DATE
    )

    EXPECTED_TOTAL_ELIGIBLE = 1
    EXPECTED_TOTAL_INELIGIBLE = 3

    EXPECTED_KPIRESULT = KPIResult(
        total_eligible=EXPECTED_TOTAL_ELIGIBLE,
        total_passed=EXPECTED_TOTAL_ELIGIBLE,
        total_ineligible=EXPECTED_TOTAL_INELIGIBLE,
        total_failed=EXPECTED_TOTAL_INELIGIBLE,
    )

    # First set self.total_kpi_1_eligible_pts_base_query_set result
    # of total eligible
    calc_kpis.calculate_kpi_1_total_eligible()

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT,
        actual=calc_kpis.calculate_kpi_10_total_coeliacs(),
    )


@pytest.mark.django_db
def test_kpi_calculation_11(AUDIT_START_DATE):
    """Tests that KPI11 is calculated correctly.

    KPI1 PLUS
    who:
        * most recent observation for item 35 (based on visit date) is either 2 = Thyroxine for hypothyroidism or 3 = Antithyroid medication for hyperthyroidism
        // NOTE: item35 is _At time of, or following measurement of thyroid function, was the patient prescribed any thyroid treatment?_
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create  Patients and Visits that should be included
    eligible_patient_most_recent_thyroid_treatment_status_is_2 = PatientFactory(
        postcode="eligible_patient_most_recent_thyroid_treatment_status_is_2",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # most recent observation for item 35 (based on visit date) is 2
        visit__thyroid_treatment_status=2,
    )
    eligible_patient_most_recent_thyroid_treatment_status_is_3 = PatientFactory(
        postcode="eligible_patient_most_recent_thyroid_treatment_status_is_3",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # most recent observation for item 35 (based on visit date) is 2
        visit__thyroid_treatment_status=3,
    )

    # Create Patients and Visits that should be excluded
    # Visit date before audit period
    ineligible_patient_visit_date: List[Patient] = PatientFactory(
        postcode="ineligible_patient_visit_date",
        visit__visit_date=AUDIT_START_DATE - relativedelta(days=10),
    )
    # Above age 25 at start of audit period
    ineligible_patient_too_old: List[Patient] = PatientFactory(
        postcode="ineligible_patient_too_old",
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 26),
    )

    # KPI11 specific
    ineligible_patient_most_recent_thyroid_treatment_status_is_not_in_range_2_to_3 = PatientFactory(
        postcode="ineligible_patient_most_recent_thyroid_treatment_status_is_not_in_range_2_to_3",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # most recent observation for item 37 (based on visit date) is not 1
        visit__thyroid_treatment_status=1,
    )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(
        pz_code="PZ130", calculation_date=AUDIT_START_DATE
    )

    EXPECTED_TOTAL_ELIGIBLE = 2
    EXPECTED_TOTAL_INELIGIBLE = 3

    EXPECTED_KPIRESULT = KPIResult(
        total_eligible=EXPECTED_TOTAL_ELIGIBLE,
        total_passed=EXPECTED_TOTAL_ELIGIBLE,
        total_ineligible=EXPECTED_TOTAL_INELIGIBLE,
        total_failed=EXPECTED_TOTAL_INELIGIBLE,
    )

    # First set self.total_kpi_1_eligible_pts_base_query_set result
    # of total eligible
    calc_kpis.calculate_kpi_1_total_eligible()

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT,
        actual=calc_kpis.calculate_kpi_11_total_thyroids(),
    )


@pytest.mark.django_db
def test_kpi_calculation_12(AUDIT_START_DATE):
    """Tests that KPI12 is calculated correctly.

    KPI1 PLUS
        * most recent observation for item 45 (based on visit date) is 1 = Yes
            // NOTE: item45 is _Was the patient using (or trained to use) blood ketone testing equipment at time of visit? _
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create  Patients and Visits that should be included
    eligible_patient_most_recent_ketone_meter_training_is_1 = PatientFactory(
        postcode="eligible_patient_most_recent_ketone_meter_training_is_1",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # most recent observation for item 45 (based on visit date) is 1 = Yes
        visit__ketone_meter_training=1,
    )

    # Create Patients and Visits that should be excluded
    # Visit date before audit period
    ineligible_patient_visit_date: List[Patient] = PatientFactory(
        postcode="ineligible_patient_visit_date",
        visit__visit_date=AUDIT_START_DATE - relativedelta(days=10),
    )
    # Above age 25 at start of audit period
    ineligible_patient_too_old: List[Patient] = PatientFactory(
        postcode="ineligible_patient_too_old",
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 26),
    )

    # KPI11 specific
    ineligible_patient_most_recent_ketone_meter_training_is_not_1 = PatientFactory(
        postcode="ineligible_patient_most_recent_ketone_meter_training_is_not_1",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # most recent observation for item 37 (based on visit date) is not 1
        visit__ketone_meter_training=2,
    )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(
        pz_code="PZ130", calculation_date=AUDIT_START_DATE
    )

    EXPECTED_TOTAL_ELIGIBLE = 1
    EXPECTED_TOTAL_INELIGIBLE = 3

    EXPECTED_KPIRESULT = KPIResult(
        total_eligible=EXPECTED_TOTAL_ELIGIBLE,
        total_passed=EXPECTED_TOTAL_ELIGIBLE,
        total_ineligible=EXPECTED_TOTAL_INELIGIBLE,
        total_failed=EXPECTED_TOTAL_INELIGIBLE,
    )

    # First set self.total_kpi_1_eligible_pts_base_query_set result
    # of total eligible
    calc_kpis.calculate_kpi_1_total_eligible()

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT,
        actual=calc_kpis.calculate_kpi_12_total_ketone_test_equipment(),
    )


# Set up test params for kpis 13-20, as they all have the same denominator
# and the only thing being changed is value for visit__treatment
# the final option (9 - unknown) is not a KPI calculation so excluded
TX_TYPE_PARAMS = []
for treatment_type in TREATMENT_TYPES[:-1]:
    expected_result = KPIResult(
        total_eligible=8,
        total_passed=1,
        total_ineligible=2,
        total_failed=7,
    )
    TX_TYPE_PARAMS.append((treatment_type[0], expected_result))


@pytest.mark.parametrize(("treatment", "expected_result"), TX_TYPE_PARAMS)
@pytest.mark.django_db
def test_kpi_calculations_13_to_20(
    AUDIT_START_DATE, treatment: int, expected_result: KPIResult
):
    """Tests that KPIS13-20 are calculated correctly.

    Numerator: Number of eligible patients whose most recent entry (based on visit date) for treatment regimen (item 20) is `treatment` (int 1-9)

    Denominator: Total number of eligible patients (measure 1)
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create  Patients and Visits that should be eligible
    eligible_criteria = {
        "visit__visit_date": AUDIT_START_DATE + relativedelta(days=2),
        "date_of_birth": AUDIT_START_DATE - relativedelta(days=365 * 10),
    }
    passing = PatientFactory(
        # KPI1 eligible
        **eligible_criteria,
        # most recent observation for treatment regimen (item 20) is `treatment`
        visit__treatment=treatment,
    )

    # TODO: query are these 'failing' or just 'not passing'?
    # Create failing patients (remember exclude final option 9 - unknown)
    for val, _ in TREATMENT_TYPES[:-1]:
        if val != treatment:

            failing = PatientFactory(
                # KPI1 eligible
                **eligible_criteria,
                # most recent observation for treatment regimen (item 20) is NOT `treatment`
                visit__treatment=val,
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

    # First set self.total_kpi_1_eligible_pts_base_query_set result
    # of total eligible
    calc_kpis.calculate_kpi_1_total_eligible()

    # Dynamically get the kpi calc method based on treatment type
    #   `treatment` is an int between 1-8
    #   these kpi calulations start at 13
    #   so just offset by 12 to get kpi number
    kpi_number = treatment + 12
    kpi_method_name = calc_kpis.kpis_names_map[kpi_number]
    kpi_calc_method = getattr(calc_kpis, f"calculate_{kpi_method_name}")
    assert_kpi_result_equal(
        expected=expected_result,
        actual=kpi_calc_method(),
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

    # First set self.total_kpi_1_eligible_pts_base_query_set result
    # of total eligible
    calc_kpis.calculate_kpi_1_total_eligible()

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
    calc_kpis = CalculateKPIS(
        pz_code="PZ130", calculation_date=AUDIT_START_DATE
    )

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

    # First set self.total_kpi_1_eligible_pts_base_query_set result
    # of total eligible
    calc_kpis.calculate_kpi_1_total_eligible()

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT,
        actual=calc_kpis.calculate_kpi_22_real_time_cgm_with_alarms(),
    )


@pytest.mark.django_db
def test_kpi_calculation_23(AUDIT_START_DATE):
    """Tests that KPI23 is calculated correctly.

    Numerator: Total number of eligible patients with Type 1 diabetes (measure 2)

    Denominator: Number of eligible patients whose most recent entry (based on visit date) for blood glucose monitoring (item 22) is  4 = Real time continuous glucose monitor with alarms
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
    calc_kpis = CalculateKPIS(
        pz_code="PZ130", calculation_date=AUDIT_START_DATE
    )

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


@pytest.mark.django_db
def test_kpi_calculation_24(AUDIT_START_DATE):
    """Tests that KPI24 is calculated correctly.

    Numerator: Total number of eligible patients (measure 1)

    Denominator: Number of eligible patients whose most recent entry (based on visit date) for treatment regimen (item 20) is either
        * 3 = insulin pump
        * or 6 = Insulin pump therapy plus other blood glucose lowering medication

        AND whose most recent entry for item 21 (based on visit date) is either
        * 2 = Closed loop system (licenced)
        * or 3 = Closed loop system (DIY, unlicenced)
        * or 4 = Closed loop system (licence status unknown)
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create  Patients and Visits that should be eligible (KPI1)
    eligible_criteria = {
        "visit__visit_date": AUDIT_START_DATE + relativedelta(days=2),
        "date_of_birth": AUDIT_START_DATE - relativedelta(days=365 * 10),
    }
    for treatment_val in (3, 6):

        # Now create the passing patients
        passing_closed_loop_2 = PatientFactory(
            postcode=f"passing_closed_loop_2_{treatment_val}",
            # KPI1 eligible
            **eligible_criteria,
            # KPI24 eligible
            visit__treatment=treatment_val,
            # 2 = Closed loop system (licenced)
            visit__closed_loop_system=2,
        )
        passing_closed_loop_3 = PatientFactory(
            postcode=f"passing_closed_loop_2_{treatment_val}",
            # KPI1 eligible
            **eligible_criteria,
            # KPI24 eligible
            visit__treatment=treatment_val,
            # 3 = Closed loop system (DIY, unlicenced)
            visit__closed_loop_system=3,
        )
        passing_closed_loop_4 = PatientFactory(
            postcode=f"passing_closed_loop_2_{treatment_val}",
            # KPI1 eligible
            **eligible_criteria,
            # KPI24 eligible
            visit__treatment=treatment_val,
            # 4 = Closed loop system (licence status unknown)
            visit__closed_loop_system=4,
        )

        # Failing patients
        # A 'failing' pt who has pump therapy but not closed loop system
        failing_closed_loop = PatientFactory(
            postcode=f"failing_closed_loop_{treatment_val}",
            # KPI1 eligible
            **eligible_criteria,
            # KPI24 eligible
            visit__treatment=treatment_val,
            # AND whose most recent entry for item 21 (based on visit date) is NOT
            # either [2,3,4]
            visit__closed_loop_system=1,
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

    # KPI24 specific
    # tx regimen not 3 or 6
    for treatment_val in (1, 2, 4, 5, 7, 8):
        ineligible_tx_regimen = PatientFactory(
            postcode=f"ineligible_tx_regimen_{treatment_val}",
            # KPI1 eligible
            **eligible_criteria,
            # ineligible tx regimen
            visit__treatment=treatment_val,
        )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(
        pz_code="PZ130", calculation_date=AUDIT_START_DATE
    )

    EXPECTED_TOTAL_ELIGIBLE = 8
    EXPECTED_TOTAL_INELIGIBLE = 8
    EXPECTED_TOTAL_PASSED = 6
    EXPECTED_TOTAL_FAILED = 2

    EXPECTED_KPIRESULT = KPIResult(
        total_eligible=EXPECTED_TOTAL_ELIGIBLE,
        total_passed=EXPECTED_TOTAL_PASSED,
        total_ineligible=EXPECTED_TOTAL_INELIGIBLE,
        total_failed=EXPECTED_TOTAL_FAILED,
    )

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT,
        actual=calc_kpis.calculate_kpi_24_hybrid_closed_loop_system(),
    )


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

    calc_kpis = CalculateKPIS(
        pz_code="PZ130",
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
        actual=calc_kpis.calculate_kpi_33_hba1c_4plus(),
    )
